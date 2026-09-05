"""Sample scholarship seed data.

Like the university seed: illustrative, approximate, and UNVERIFIED
(last_verified is intentionally null). Real names of well-known programs are
used so the data feels realistic, but amounts, deadlines, and eligibility
must be confirmed on the provider's official site before anyone relies on
them. The UI must always show the data_source label.
"""

CS = "computer_science"
ENG = "engineering"
BIO = "biology"
BUS = "business"
NURS = "nursing"

SAMPLE_SCHOLARSHIPS = [
    dict(name="Coca-Cola Scholars Program", provider="Coca-Cola Scholars Foundation",
         amount_max=20000, renewable=False, eligibility="domestic", min_gpa=3.0, majors=[],
         deadline="10-01",
         description="Achievement-based award for US high-school seniors emphasizing leadership and service."),
    dict(name="Gates Scholarship", provider="Bill & Melinda Gates Foundation",
         amount_max=None, renewable=True, eligibility="domestic", min_gpa=3.3, majors=[],
         deadline="09-15",
         description="Full cost of attendance for outstanding Pell-eligible minority students."),
    dict(name="Dell Scholars Program", provider="Michael & Susan Dell Foundation",
         amount_max=20000, renewable=False, eligibility="domestic", min_gpa=2.4, majors=[],
         deadline="12-01",
         description="For students with financial need who participate in a college-readiness program."),
    dict(name="Jack Kent Cooke College Scholarship", provider="Jack Kent Cooke Foundation",
         amount_max=55000, renewable=True, eligibility="domestic", min_gpa=3.5, majors=[],
         deadline="11-18",
         description="Large renewable award for high-achieving students with financial need."),
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
         majors=[CS, ENG, BIO],
         deadline="12-01",
         description="Full tuition for STEM students; includes DoD employment after graduation."),
    dict(name="HENAAC Scholars Program", provider="Great Minds in STEM",
         amount_max=10000, renewable=False, eligibility="both", min_gpa=3.0, majors=[CS, ENG, BIO],
         deadline="04-30",
         description="For STEM students of Hispanic origin or demonstrated leadership in underserved communities."),
    dict(name="#YouAreWelcomeHere Scholarship", provider="Participating US universities",
         amount_max=None, renewable=True, eligibility="international", min_gpa=None, majors=[],
         deadline="12-15",
         description="At least 50% tuition at participating universities for international students who bridge cultures."),
    dict(name="Joint Admission-Based International Merit Awards", provider="Many US universities",
         amount_max=25000, renewable=True, eligibility="international", min_gpa=3.5, majors=[],
         deadline=None,
         description="Automatic or application-based merit awards many universities give international admits - check each school's aid page."),
    dict(name="AACE International Scholarship", provider="AACE International",
         amount_max=8000, renewable=False, eligibility="both", min_gpa=3.0, majors=[ENG, BUS],
         deadline="05-01",
         description="For students in engineering, construction, and cost-management related fields."),
    dict(name="Foot Locker Scholar Athletes", provider="Foot Locker Foundation",
         amount_max=20000, renewable=False, eligibility="domestic", min_gpa=3.0, majors=[],
         deadline="12-15",
         description="For student athletes who demonstrate leadership in sports and community."),
    dict(name="HIMSS Foundation Scholarship", provider="HIMSS Foundation",
         amount_max=5000, renewable=False, eligibility="both", min_gpa=3.0, majors=[NURS, CS, BIO],
         deadline="03-15",
         description="For students pursuing health information and technology related degrees."),
]


def seed_scholarships(db) -> int:
    from ..models import Scholarship

    if db.query(Scholarship).count() > 0:
        return 0
    for row in SAMPLE_SCHOLARSHIPS:
        db.add(Scholarship(**row))
    db.commit()
    return len(SAMPLE_SCHOLARSHIPS)
