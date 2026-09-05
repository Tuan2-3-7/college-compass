"""International Student Center - the post-application pathway, explained.

Static curated content: each stage of the journey from application to arrival,
with plain-language explanations of the unfamiliar terms. Process details
(fees, form names) change - students must verify on official government and
university pages (studyinthestates.dhs.gov, travel.state.gov, the school's
international office).
"""

PATHWAY_STAGES = [
    {
        "key": "application",
        "title": "Application",
        "summary": "Submit your applications with the international-specific pieces in place.",
        "explains": {
            "English proficiency": "TOEFL/IELTS scores most schools require unless your schooling was in English.",
            "Credential evaluation": "A service (e.g. WES) that translates your transcript into US terms - only some schools require it.",
        },
        "actions": [
            "Complete applications before each deadline",
            "Send English-proficiency scores where required",
            "Check whether transcripts need evaluation or certified translation",
        ],
    },
    {
        "key": "admission",
        "title": "Admission decisions",
        "summary": "Decisions arrive; compare offers with cost and aid in mind, then commit to one school.",
        "explains": {
            "Enrollment deposit": "A payment (often $100-800) that reserves your seat at the school you choose.",
            "Financial aid award letter": "The school's statement of grants/scholarships - read the net cost, not the sticker price.",
        },
        "actions": [
            "Compare offers (cost after aid, program fit)",
            "Commit to one school and pay the enrollment deposit",
            "Decline other offers politely",
        ],
    },
    {
        "key": "financial_documentation",
        "title": "Financial documentation",
        "summary": "Prove you can fund your first year so the school can issue your I-20.",
        "explains": {
            "Proof of funds": "Bank statements, sponsor letters, or scholarship awards covering at least year one of tuition + living costs.",
            "Sponsor affidavit": "A signed form where a parent/sponsor states they will fund your studies.",
        },
        "actions": [
            "Gather bank statements and sponsor letters",
            "Submit the school's financial certification form",
            "Include scholarship award letters if any",
        ],
    },
    {
        "key": "i20",
        "title": "I-20",
        "summary": "The school issues your I-20 - the document your visa process is built on.",
        "explains": {
            "I-20": "The 'Certificate of Eligibility' the school issues after admission + proof of funds. You need it for the SEVIS fee and the visa interview.",
            "SEVIS ID": "The N-number printed on your I-20 identifying you in the US student-tracking system.",
        },
        "actions": [
            "Check every field on the I-20 for errors (name spelling, dates, funding)",
            "Keep it safe - you will carry it when you travel",
        ],
    },
    {
        "key": "sevis",
        "title": "SEVIS fee",
        "summary": "Pay the SEVIS I-901 fee before scheduling your visa interview.",
        "explains": {
            "SEVIS": "The US government's Student and Exchange Visitor Information System.",
            "I-901 fee": "A one-time fee (approx. $350 for F-1 - verify current amount at fmjfee.com) paid online; bring the receipt to your interview.",
        },
        "actions": [
            "Pay the I-901 fee at fmjfee.com using your SEVIS ID",
            "Print the payment confirmation",
        ],
    },
    {
        "key": "visa",
        "title": "F-1 visa",
        "summary": "Apply for the student visa and attend your embassy interview.",
        "explains": {
            "F-1": "The standard US student visa for full-time academic study.",
            "DS-160": "The online visa application form; its confirmation page is required at the interview.",
            "Ties to home": "Evidence you intend to return home after study - officers may ask about plans, family, or property.",
        },
        "actions": [
            "Complete the DS-160 and pay the visa fee",
            "Schedule the interview early - waits can be months in peak season",
            "Bring: passport, I-20, SEVIS receipt, DS-160 confirmation, financial documents, admission letter",
        ],
    },
    {
        "key": "housing",
        "title": "Housing",
        "summary": "Arrange where you will live before you fly.",
        "explains": {
            "On-campus housing": "Dorms run by the university - simplest for the first year and often required for freshmen.",
            "Guarantor": "Off-campus landlords may require a US-based co-signer; some schools and services can stand in.",
        },
        "actions": [
            "Apply for on-campus housing as soon as the portal opens",
            "If off-campus, never wire money before verifying the listing",
        ],
    },
    {
        "key": "arrival",
        "title": "Travel & arrival",
        "summary": "Book travel, clear immigration, and land on your feet.",
        "explains": {
            "Port of entry": "Where you clear US immigration; carry your I-20 and documents in hand luggage, never checked bags.",
            "30-day rule": "You may enter the US no earlier than 30 days before the program start date on your I-20.",
            "International student orientation": "Your school's mandatory onboarding - immigration check-in happens here.",
        },
        "actions": [
            "Book flights within the 30-day window",
            "Attend international orientation and complete immigration check-in",
            "Set up essentials: bank account, SIM card, student ID",
        ],
    },
]

DISCLAIMER = (
    "Immigration steps, fees, and forms change. Always verify on official sources: "
    "studyinthestates.dhs.gov, travel.state.gov, fmjfee.com, and your university's "
    "international student office."
)
