"""Scholarship seed data.

Entries carrying `verified: True` were read from the sponsoring organisation's
own page on the date in VERIFIED_ON, and record that page as `source_url`.
Everything else is illustrative sample data with `last_verified = None`, and
the UI labels it as unverified.

There is no free public API for scholarships the way there is for university
statistics (College Scorecard) or deadlines (Common App grid), so this list is
hand-curated and deliberately small. Amounts and especially deadlines change
every year - re-verify before each application season.
"""

from datetime import date

VERIFIED_ON = date(2026, 9, 5)

CS = "computer_science"
ENG = "engineering"
BIO = "biology"
BUS = "business"
NURS = "nursing"

SAMPLE_SCHOLARSHIPS = [
    # ---------- verified against the sponsor's own site ----------
    dict(name="Coca-Cola Scholars Program", provider="Coca-Cola Scholars Foundation",
         amount_max=20000, renewable=False, eligibility="domestic", min_gpa=3.0, majors=[],
         deadline="09-30", verified=True,
         source_url="https://www.coca-colascholarsfoundation.org/apply/",
         deadline_note="Closes 5pm ET; 150 scholars selected each year",
         description="Achievement-based award for US high-school seniors. Open to citizens, "
                     "nationals, permanent residents, refugees, asylees, Cuban-Haitian entrants, "
                     "and humanitarian parolees with a 3.0+ GPA."),
    dict(name="The Gates Scholarship", provider="Bill & Melinda Gates Foundation",
         amount_max=None, renewable=True, eligibility="domestic", min_gpa=3.3, majors=[],
         deadline="09-15", verified=True,
         source_url="https://www.thegatesscholarship.org/scholarship",
         deadline_note="Last-dollar award covering full cost of attendance",
         description="Covers the full cost of attendance not met by other aid, for Pell-eligible "
                     "US citizens or permanent residents with a 3.3+ weighted GPA."),
    dict(name="QuestBridge National College Match", provider="QuestBridge",
         amount_max=None, renewable=True, eligibility="domestic", min_gpa=None, majors=[],
         deadline="10-01", verified=True,
         source_url="https://www.questbridge.org/high-school-students/national-college-match",
         deadline_note="Closes 11:59pm PT",
         description="Full four-year scholarships to 55 partner colleges - tuition, housing and "
                     "food with no parental contribution and no loans - for high-achieving "
                     "students from households under about $65,000 a year."),
    dict(name="Jack Kent Cooke College Scholarship", provider="Jack Kent Cooke Foundation",
         amount_max=55000, renewable=True, eligibility="domestic", min_gpa=3.5, majors=[],
         deadline="11-11", verified=True,
         source_url="https://www.jkcf.org/our-scholarships/college-scholarship-program/",
         deadline_note="Last-dollar funding after institutional aid",
         description="Up to $55,000 per year for high-achieving high-school seniors with "
                     "financial need. Recent scholars averaged near a 4.0 unweighted GPA."),
    dict(name="Dell Scholars Program", provider="Michael & Susan Dell Foundation",
         amount_max=20000, renewable=False, eligibility="domestic", min_gpa=2.4, majors=[],
         deadline="02-15", verified=True,
         source_url="https://www.dellscholars.org/scholarship/",
         deadline_note="Includes a laptop, book credits and emergency funds",
         description="$20,000 flexible award for Pell-eligible seniors in an approved "
                     "college-readiness program. Notably reachable at a 2.4 GPA."),
    dict(name="#YouAreWelcomeHere Scholarship", provider="Participating US universities",
         amount_max=None, renewable=True, eligibility="international", min_gpa=None, majors=[],
         deadline=None, verified=True,
         source_url="https://www.youarewelcomehereusa.org/scholarship",
         deadline_note="Deadlines vary by institution - typically spring/summer",
         description="Covers a minimum of 50% of tuition, renewable for the full degree, for "
                     "first-year international applicants who show initiative in promoting "
                     "intercultural exchange. Apply directly to each participating university."),
    dict(name="Davis United World College Scholars Program", provider="Shelby Davis / UWC",
         amount_max=None, renewable=True, eligibility="international", min_gpa=None, majors=[],
         deadline=None, verified=True,
         source_url="https://www.davisuwcscholars.org/",
         deadline_note="Apply through your UWC counselor, not centrally",
         description="Need-based aid at 100+ US partner colleges for graduates of the 18 United "
                     "World College schools. Supports 4,600+ scholars from 160+ countries."),

    # ---------- unverified sample data (last_verified stays null) ----------
    dict(name="Horatio Alger National Scholarship", provider="Horatio Alger Association",
         amount_max=25000, renewable=False, eligibility="domestic", min_gpa=2.0, majors=[],
         deadline="10-25",
         description="For students who have overcome significant adversity, with financial need."),
    dict(name="Amazon Future Engineer Scholarship", provider="Amazon",
         amount_max=40000, renewable=True, eligibility="domestic", min_gpa=3.0, majors=[CS, ENG],
         deadline="01-30",
         description="For students pursuing computer science with financial need."),
    dict(name="SMART Scholarship", provider="US Department of Defense",
         amount_max=None, renewable=True, eligibility="domestic", min_gpa=3.0,
         majors=[CS, ENG, BIO], deadline="12-01",
         description="Full tuition for STEM students; includes DoD employment after graduation."),
    dict(name="HENAAC Scholars Program", provider="Great Minds in STEM",
         amount_max=10000, renewable=False, eligibility="both", min_gpa=3.0, majors=[CS, ENG, BIO],
         deadline="04-30",
         description="For STEM students of Hispanic origin or with demonstrated leadership in "
                     "underserved communities."),
    dict(name="Joint Admission-Based International Merit Awards", provider="Many US universities",
         amount_max=25000, renewable=True, eligibility="international", min_gpa=3.5, majors=[],
         deadline=None,
         description="Automatic or application-based merit awards many universities give "
                     "international admits - check each school's aid page."),
    dict(name="AACE International Scholarship", provider="AACE International",
         amount_max=8000, renewable=False, eligibility="both", min_gpa=3.0, majors=[ENG, BUS],
         deadline="05-01",
         description="For students in engineering, construction and cost-management fields."),
    dict(name="HIMSS Foundation Scholarship", provider="HIMSS Foundation",
         amount_max=5000, renewable=False, eligibility="both", min_gpa=3.0, majors=[NURS, CS, BIO],
         deadline="03-15",
         description="For students pursuing health information and technology degrees."),
]

VERIFIED_SOURCE = "Sponsor's official site"
SAMPLE_SOURCE = "sample_seed_v1 (illustrative only - verify before relying on it)"


def seed_scholarships(db) -> int:
    """Insert or refresh scholarships. Idempotent: matches on name so corrected
    amounts and deadlines reach databases seeded by an earlier version."""
    from ..models import Scholarship

    existing = {s.name: s for s in db.query(Scholarship).all()}
    changed = 0
    for row in SAMPLE_SCHOLARSHIPS:
        data = dict(row)
        verified = data.pop("verified", False)
        data["source_url"] = data.get("source_url", "")
        data["deadline_note"] = data.get("deadline_note", "")
        data["data_source"] = VERIFIED_SOURCE if verified else SAMPLE_SOURCE
        data["last_verified"] = VERIFIED_ON if verified else None

        scholarship = existing.get(data["name"])
        if scholarship is None:
            db.add(Scholarship(**data))
            changed += 1
        else:
            for field, value in data.items():
                setattr(scholarship, field, value)
            changed += 1

    # this file is the single source of truth for the table, so drop rows left
    # behind by an earlier version of the seed (renamed or removed entries)
    current_names = {row["name"] for row in SAMPLE_SCHOLARSHIPS}
    for name, scholarship in existing.items():
        if name not in current_names:
            db.delete(scholarship)

    db.commit()
    return changed
