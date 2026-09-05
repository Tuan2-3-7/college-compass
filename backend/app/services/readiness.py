"""Application Readiness Score - one dashboard number combining progress
across the whole platform (spec #16), with the highest-impact improvement."""

from sqlalchemy.orm import Session, joinedload

from ..models import Application, Essay, StudentProfile, Task, User
from .analyzer import profile_scores

WEIGHTS = {
    "academics": 0.25,
    "activities": 0.15,
    "essays": 0.20,
    "major_preparation": 0.15,
    "application_tasks": 0.15,
    "financial_preparation": 0.10,
}

LEVER_ACTIONS = {
    "academics": ("Add or improve GPA and test scores in your profile", "/profile"),
    "activities": ("Deepen your activities and leadership - quality over quantity", "/advisor"),
    "essays": ("Draft and revise your essays with the coach", "/essays"),
    "major_preparation": ("Close your skill gaps for your intended major", "/advisor"),
    "application_tasks": ("Work through your application checklists", "/applications"),
    "financial_preparation": ("Complete your financial-aid tasks", "/aid"),
}


def readiness(db: Session, user: User) -> dict:
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    essays = (
        db.query(Essay).options(joinedload(Essay.drafts)).filter(Essay.user_id == user.id).all()
    )
    tasks = db.query(Task).filter(Task.user_id == user.id).all()
    has_applications = (
        db.query(Application).filter(Application.user_id == user.id).count() > 0
    )

    notes: list[str] = []

    # -- profile-driven components --
    if profile is not None:
        scores = profile_scores(profile)["subscores"]
        academics = scores["academics"] if scores["academics"] is not None else 0
        activities = round(
            ((scores["activities"] or 0) + (scores["leadership"] or 0)) / 2
        )
        major_prep = scores["major_preparation"]
        if major_prep is None:
            major_prep = 0
            notes.append("Pick an intended major to make major preparation count.")
        if scores["academics"] is None:
            notes.append("No GPA or test scores on file yet.")
    else:
        academics = activities = major_prep = 0

    # -- essays: average of each essay's latest analyzed draft --
    latest_scores = []
    for essay in essays:
        for draft in reversed(essay.drafts):
            if draft.feedback is not None:
                latest_scores.append(draft.feedback.overall_score)
                break
    if latest_scores:
        essays_score = round(sum(latest_scores) / len(latest_scores))
    else:
        essays_score = 0
        notes.append("No analyzed essays yet - the essay coach can score your drafts.")

    # -- application tasks --
    if tasks:
        done = sum(1 for t in tasks if t.status == "done")
        tasks_score = round(done / len(tasks) * 100)
    else:
        tasks_score = 0
        if not has_applications:
            notes.append("Add universities to generate checklists and start tracking readiness.")

    # -- financial preparation --
    if profile is not None and not profile.financial_aid_needed:
        fin_score = 100
        fin_note = "not applicable (no aid requested) - counted as complete"
    else:
        fin_tasks = [t for t in tasks if t.category == "financial_aid"]
        if fin_tasks:
            fin_score = round(
                sum(1 for t in fin_tasks if t.status == "done") / len(fin_tasks) * 100
            )
            fin_note = None
        else:
            fin_score = 0
            fin_note = None
            if profile is not None and profile.financial_aid_needed:
                notes.append("You need financial aid but have no aid tasks yet - add universities or plan in the Aid tab.")
    components = {
        "academics": academics,
        "activities": activities,
        "essays": essays_score,
        "major_preparation": major_prep,
        "application_tasks": tasks_score,
        "financial_preparation": fin_score,
    }
    overall = round(sum(components[k] * w for k, w in WEIGHTS.items()))

    # highest-impact improvement: lowest weighted headroom
    lever_key = max(WEIGHTS, key=lambda k: (100 - components[k]) * WEIGHTS[k])
    action, link = LEVER_ACTIONS[lever_key]

    return {
        "overall": overall,
        "components": components,
        "highest_impact": {
            "component": lever_key,
            "action": action,
            "link": link,
        },
        "notes": notes + ([f"Financial preparation: {fin_note}."] if fin_note else []),
        "disclaimer": (
            "Readiness measures your preparation progress inside College Compass - "
            "it is not an admission prediction."
        ),
    }
