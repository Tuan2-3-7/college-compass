"""Personalized checklist generation.

Given a student profile, a university, and an application (round), produce the
list of tasks the student actually needs — an international CS first-year gets
a different checklist from a domestic biology transfer.

Pure functions: no DB access, so this module is easy to unit-test.
"""

from datetime import date, timedelta


def resolve_deadline(deadlines: dict, round_name: str, today: date | None = None) -> date | None:
    """Turn a stored "MM-DD" deadline for the chosen round into the next real date.

    Application deadlines recur annually; we pick the next occurrence from today.
    Rolling admissions have no fixed date -> None.
    """
    today = today or date.today()
    raw = deadlines.get(round_name)
    if not raw or not isinstance(raw, str):
        return None
    try:
        month, day = (int(p) for p in raw.split("-"))
        candidate = date(today.year, month, day)
    except ValueError:
        return None
    if candidate < today:
        candidate = date(today.year + 1, month, day)
    return candidate


def _offset(deadline: date | None, days_before: int) -> date | None:
    if deadline is None:
        return None
    due = deadline - timedelta(days=days_before)
    return max(due, date.today())


def generate_tasks(profile, university, round_name: str, today: date | None = None) -> list[dict]:
    """Build the personalized task list for one application.

    `profile` and `university` are the ORM objects (or anything with the same
    attributes). Returns dicts ready to insert as Task rows.
    """
    today = today or date.today()
    deadline = resolve_deadline(university.deadlines or {}, round_name, today)
    tasks: list[dict] = []
    order = 0

    def add(title, category, days_before=0, description="", priority="medium"):
        nonlocal order
        tasks.append(
            {
                "title": title,
                "description": description,
                "category": category,
                "due_date": _offset(deadline, days_before),
                "priority": priority,
                "auto_generated": True,
                "sort_order": order,
            }
        )
        order += 1

    platforms = university.app_platforms or []
    platform_label = ", ".join(p.replace("_", " ").title() for p in platforms) or "the university portal"
    is_intl = profile.student_type == "international"
    is_transfer = profile.applicant_level == "transfer"
    is_grad = profile.applicant_level == "graduate"
    has_test = bool(profile.sat or profile.act)

    # --- account & basics ---
    add(
        f"Create an account on {platform_label}",
        "account",
        days_before=60,
        description="Register and start the application for this university.",
    )

    # --- academics / documents ---
    if is_transfer:
        add(
            "Request official college transcript",
            "documents",
            days_before=30,
            description="Ask your current college registrar to send an official transcript.",
            priority="high",
        )
        add(
            "Request College Report from your current institution",
            "documents",
            days_before=30,
            description="Many transfer applications require a College/Registrar Report confirming your standing.",
        )
    add(
        "Request official high school transcript",
        "documents",
        days_before=30,
        description="Ask your school counselor or registrar to send your transcript.",
        priority="high",
    )
    if is_intl:
        add(
            "Check whether transcripts need a credential evaluation or certified English translation",
            "documents",
            days_before=45,
            description=(
                "Some universities require WES/ECE evaluation or certified translations of "
                "non-US transcripts. Confirm on the official admissions site."
            ),
        )

    # --- testing ---
    if university.test_policy == "required" and not has_test:
        add(
            "Register for the SAT or ACT",
            "testing",
            days_before=90,
            description="This university requires standardized test scores and your profile has none yet.",
            priority="high",
        )
    if university.test_policy == "required" or (university.test_policy == "optional" and has_test):
        add(
            "Send official SAT/ACT scores",
            "testing",
            days_before=21,
            description="Order official score reports through College Board or ACT.",
        )
    if university.test_policy == "optional" and not has_test:
        add(
            "Decide whether to apply test-optional",
            "testing",
            days_before=45,
            description="This university is test-optional. Decide whether taking the SAT/ACT would strengthen your application.",
            priority="low",
        )
    if is_intl:
        has_english_test = bool(profile.toefl or profile.ielts)
        if not has_english_test:
            add(
                "Register for TOEFL or IELTS",
                "testing",
                days_before=75,
                description=(
                    "English proficiency is typically required for international applicants. "
                    "Check the university site for minimum scores and waiver rules "
                    "(e.g. English-medium schooling)."
                ),
                priority="high",
            )
        add(
            "Send official English-proficiency scores",
            "testing",
            days_before=21,
            description="Send TOEFL/IELTS scores through the testing agency.",
        )

    # --- essays ---
    if is_grad:
        add(
            "Write statement of purpose",
            "essays",
            days_before=30,
            description="Draft, revise, and finalize your statement of purpose for this program.",
            priority="high",
        )
        add(
            "Update CV/resume",
            "documents",
            days_before=30,
        )
    else:
        add(
            "Finalize personal statement / main essay",
            "essays",
            days_before=21,
            description="Complete your main application essay.",
            priority="high",
        )
    supp = university.supplemental_essay_count or 0
    if supp > 0:
        add(
            f"Write {supp} supplemental essay{'s' if supp != 1 else ''} for {university.name}",
            "essays",
            days_before=21,
            description="Check the current prompts in the application portal.",
            priority="high",
        )

    # --- recommendations ---
    rec_count = 3 if is_grad else 2
    add(
        f"Request {rec_count} letters of recommendation",
        "recommendations",
        days_before=45,
        description="Ask recommenders early and give them your resume/brag sheet.",
        priority="high",
    )
    if not is_grad:
        add(
            "Request counselor recommendation and school report",
            "recommendations",
            days_before=45,
        )

    # --- financial aid ---
    if profile.financial_aid_needed:
        if is_intl:
            if university.offers_intl_aid:
                add(
                    "Complete this university's international financial aid forms",
                    "financial_aid",
                    days_before=14,
                    description=(
                        "This school offers aid to international students (per sample data - verify). "
                        "Common forms: CSS Profile or ISFAA."
                    ),
                    priority="high",
                )
            else:
                add(
                    "Research external scholarships for international students",
                    "financial_aid",
                    days_before=30,
                    description=(
                        "Sample data suggests this university offers little or no institutional aid "
                        "to international students - verify, and look for outside scholarships."
                    ),
                )
        else:
            add(
                "Submit FAFSA",
                "financial_aid",
                days_before=14,
                description="File the FAFSA at studentaid.gov and add this school's code.",
                priority="high",
            )
            add(
                "Check whether this university requires the CSS Profile",
                "financial_aid",
                days_before=21,
            )

    # --- fee & submission ---
    fee = university.application_fee
    fee_text = f"Pay the application fee (~${fee})" if fee else "Pay the application fee"
    add(
        f"{fee_text} or request a fee waiver",
        "submission",
        days_before=3,
    )
    add(
        f"Review and submit the application to {university.name}",
        "submission",
        days_before=1,
        description="Do a final review of every section before submitting.",
        priority="high",
    )

    # --- post-admission (international pathway, Phase 4 expands this) ---
    if is_intl:
        add(
            "After admission: request I-20 and prepare proof of funds",
            "post_admission",
            days_before=0,
            description=(
                "If admitted, you will need financial documentation for the I-20, then pay the "
                "SEVIS fee and schedule an F-1 visa interview. Only relevant after a decision."
            ),
            priority="low",
        )

    return tasks
