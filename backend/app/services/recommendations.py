"""Personalized recommendations - the "what should I do next?" engine.

Rule-based synthesis across every subsystem: deadlines, checklist state,
competitiveness subscores, skill gaps, essay status, and list balance.
(Phase 3 keeps this deterministic; an LLM can later turn these facts into
prose, but the prioritization logic stays inspectable.)
"""

from datetime import date, timedelta

from sqlalchemy.orm import Session, joinedload

from ..models import Application, Essay, StudentProfile, Task, User
from .analyzer import profile_scores, university_fit

SUBSCORE_LABELS = {
    "academics": "academics",
    "course_rigor": "course rigor",
    "activities": "activities",
    "leadership": "leadership",
    "awards": "awards",
    "major_preparation": "major preparation",
}


def build_recommendations(db: Session, user: User) -> list[dict]:
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    applications = (
        db.query(Application)
        .options(joinedload(Application.university))
        .filter(Application.user_id == user.id)
        .all()
    )
    tasks = db.query(Task).filter(Task.user_id == user.id, Task.status != "done").all()
    essays = (
        db.query(Essay)
        .options(joinedload(Essay.drafts))
        .filter(Essay.user_id == user.id)
        .all()
    )

    today = date.today()
    recs: list[dict] = []

    def add(category, title, reason, link=None):
        recs.append({"category": category, "title": title, "reason": reason, "link": link})

    # 1. overdue tasks - always first
    overdue = sorted(
        (t for t in tasks if t.due_date and t.due_date < today), key=lambda t: t.due_date
    )
    if overdue:
        t = overdue[0]
        extra = f" (+{len(overdue) - 1} more overdue)" if len(overdue) > 1 else ""
        add("deadline", t.title, f"Overdue since {t.due_date.isoformat()}{extra}.", "/applications")

    # 2. due within 7 days
    soon = sorted(
        (t for t in tasks if t.due_date and today <= t.due_date <= today + timedelta(days=7)),
        key=lambda t: t.due_date,
    )
    if soon:
        t = soon[0]
        add("deadline", t.title, f"Due {t.due_date.isoformat()} - your nearest deadline.", "/applications")

    # 3. essays needing work
    for essay in essays:
        if not essay.drafts:
            add("essays", f'Write the first draft of "{essay.title}"',
                "The essay exists but has no draft yet.", "/essays")
            break
        latest = essay.drafts[-1]
        if latest.feedback is None:
            add("essays", f'Analyze your latest draft of "{essay.title}"',
                f"Draft {latest.version} hasn't been through the essay coach yet.", "/essays")
            break
        if latest.feedback.overall_score < 70:
            weakest = (
                min(latest.feedback.scores, key=latest.feedback.scores.get)
                if latest.feedback.scores else None
            )
            focus = f" - focus on {weakest.replace('_', ' ')}" if weakest else ""
            add("essays", f'Revise "{essay.title}" (scored {latest.feedback.overall_score}/100)',
                f"The essay coach found room to grow{focus}.", "/essays")
            break

    # 4. profile / competitiveness levers
    if profile is not None:
        scores = profile_scores(profile)
        sub = {k: v for k, v in scores["subscores"].items() if v is not None}
        if scores["subscores"]["academics"] is None:
            add("profile", "Add your GPA and test scores",
                "Without them, competitiveness estimates are nearly meaningless.", "/profile")
        elif sub:
            weakest_key = min(sub, key=sub.get)
            if sub[weakest_key] < 50:
                link = "/advisor" if weakest_key == "major_preparation" else "/profile"
                add("growth", f"Strengthen your {SUBSCORE_LABELS[weakest_key]}",
                    f"It's your lowest competitiveness subscore ({sub[weakest_key]}/100).", link)

        # 5. list balance
        if applications:
            classes = [
                university_fit(profile, app.university)["classification"]
                for app in applications
            ]
            if all(c == "reach" for c in classes) and len(classes) >= 2:
                add("list_balance", "Add target and likely schools",
                    "Every school on your list is a reach - a balanced list protects you.", "/finder")
        else:
            add("list_balance", "Add your first university",
                "Build your list to unlock checklists and deadline tracking.", "/finder")

    # 6. no essays at all but applications exist
    if applications and not essays:
        add("essays", "Start your personal statement",
            "You have applications but no essays in the coach yet - drafts take longer than you think.",
            "/essays")

    return recs[:6]
