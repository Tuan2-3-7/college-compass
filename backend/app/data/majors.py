"""Major knowledge base: what each major typically values.

Curated general guidance (not tied to any specific university). Drives the
Major Advisor, the Skill-Gap Analysis, and the analyzer's major-preparation
subscore. `keywords` are matched (lowercase substring) against the student's
courses, activities, and awards to detect existing evidence.
"""

MAJORS: dict[str, dict] = {
    "computer_science": {
        "label": "Computer Science",
        "academic_prep": [
            {"name": "Calculus (AP Calculus AB/BC or equivalent)", "why": "CS degrees start with calculus; BC signals readiness."},
            {"name": "AP Computer Science A / Principles", "why": "Direct evidence of programming coursework."},
            {"name": "Physics", "why": "Common CS-adjacent requirement; trains problem decomposition."},
            {"name": "Statistics", "why": "Foundation for AI/ML and data-driven work."},
        ],
        "skills": [
            {"key": "programming", "name": "Programming", "keywords": ["computer science", "programming", "coding", "python", "java", "c++", "javascript", "app", "software"],
             "build": "Learn one language deeply (Python or Java). Build small tools you actually use."},
            {"key": "mathematics", "name": "Mathematics", "keywords": ["calculus", "math", "statistics", "amc", "aime", "olympiad"],
             "build": "Take the most rigorous math track available; try AMC-style competition problems."},
            {"key": "projects", "name": "Technical projects", "keywords": ["project", "app", "website", "game", "hackathon", "github", "arduino", "raspberry"],
             "build": "Ship 1-2 substantial projects with public code - depth beats a list of tutorials."},
            {"key": "research", "name": "Research / independent study", "keywords": ["research", "science fair", "isef", "paper", "lab"],
             "build": "Email local professors or join a research program; a science-fair project counts."},
            {"key": "teamwork", "name": "Collaboration & competition", "keywords": ["robotics", "first robotics", "vex", "cyberpatriot", "usaco", "competition", "club"],
             "build": "Join or start a robotics/CS club; USACO and hackathons show sustained interest."},
        ],
        "experiences": [
            {"name": "Personal or open-source project", "why": "The single strongest CS signal - proof you build things unprompted."},
            {"name": "Programming competition (USACO, hackathons)", "why": "Objective benchmark; USACO divisions are widely understood."},
            {"name": "Research or internship", "why": "Shows you can work on unbounded problems."},
            {"name": "Teaching/tutoring CS", "why": "Leadership plus mastery - explaining code proves you understand it."},
        ],
        "evidence": [
            "A project you can describe in one sentence with a real user or result",
            "Sustained involvement (2+ years) in one technical activity, ideally with a leadership arc",
            "Course rigor in math through calculus, plus CS coursework where offered",
        ],
    },
    "engineering": {
        "label": "Engineering",
        "academic_prep": [
            {"name": "Calculus (AB/BC)", "why": "Engineering curricula are calculus-first."},
            {"name": "Physics (AP Physics 1/C preferred)", "why": "Core prerequisite for every engineering discipline."},
            {"name": "Chemistry", "why": "Required for many engineering tracks."},
        ],
        "skills": [
            {"key": "mathematics", "name": "Mathematics", "keywords": ["calculus", "math", "statistics"], "build": "Most rigorous math track available."},
            {"key": "physics", "name": "Physics & mechanics", "keywords": ["physics", "mechanics"], "build": "Take AP Physics; enter physics competitions."},
            {"key": "building", "name": "Hands-on building", "keywords": ["robotics", "cad", "3d print", "arduino", "build", "maker", "engineering"], "build": "Robotics team, maker space, or a documented personal build."},
            {"key": "design", "name": "Design process", "keywords": ["design", "prototype", "cad", "solidworks"], "build": "Learn CAD; document a design-build-test cycle."},
        ],
        "experiences": [
            {"name": "Robotics or engineering team", "why": "Direct evidence of the engineering design cycle."},
            {"name": "A documented build project", "why": "Shows initiative and follow-through."},
            {"name": "Engineering summer program or internship", "why": "Exposure to the discipline before committing."},
        ],
        "evidence": [
            "A build you can show photos or a log of",
            "Physics and calculus on the transcript",
            "Team engineering experience with a defined role",
        ],
    },
    "biology": {
        "label": "Biology",
        "academic_prep": [
            {"name": "AP Biology", "why": "Core subject evidence."},
            {"name": "AP Chemistry", "why": "Bio majors take chemistry early; rigor here matters."},
            {"name": "Statistics", "why": "Modern biology is quantitative."},
        ],
        "skills": [
            {"key": "lab", "name": "Laboratory experience", "keywords": ["lab", "research", "experiment", "biology", "biotech"], "build": "Seek a research lab, summer program, or rigorous class labs."},
            {"key": "science_core", "name": "Science coursework", "keywords": ["biology", "chemistry", "physics", "anatomy"], "build": "Stack the science APs your school offers."},
            {"key": "research", "name": "Research & inquiry", "keywords": ["research", "science fair", "isef", "paper"], "build": "A science-fair project with real methodology is a strong start."},
            {"key": "service", "name": "Health/field service", "keywords": ["hospital", "volunteer", "clinic", "environment", "conservation"], "build": "Volunteer where biology meets the world: clinics, conservation, public health."},
        ],
        "experiences": [
            {"name": "Research project or lab placement", "why": "The defining bio-applicant experience."},
            {"name": "Science fair / olympiad", "why": "External validation of inquiry skills."},
            {"name": "Health or environmental volunteering", "why": "Shows purpose beyond the classroom."},
        ],
        "evidence": [
            "A research question you pursued and can explain",
            "AP-level biology and chemistry",
            "Sustained science activity outside class",
        ],
    },
    "business": {
        "label": "Business",
        "academic_prep": [
            {"name": "Calculus or AP Statistics", "why": "Quantitative readiness is the top academic signal."},
            {"name": "AP Economics (Micro/Macro)", "why": "Closest classroom analog to the major."},
            {"name": "AP English / strong writing", "why": "Business school is communication-heavy."},
        ],
        "skills": [
            {"key": "leadership", "name": "Leadership", "keywords": ["president", "founder", "captain", "lead", "manager", "director"], "build": "Run something: a club, an event, a team - scope matters less than ownership."},
            {"key": "entrepreneurship", "name": "Entrepreneurship", "keywords": ["business", "startup", "company", "sell", "shop", "deca", "fbla", "entrepreneur"], "build": "Start a tiny venture or compete in DECA/FBLA; track real numbers."},
            {"key": "quantitative", "name": "Quantitative skills", "keywords": ["math", "statistics", "calculus", "economics", "finance", "investment"], "build": "Take statistics; learn spreadsheet modeling with real data."},
            {"key": "communication", "name": "Communication", "keywords": ["debate", "speech", "model un", "newspaper", "journal"], "build": "Debate, Model UN, or student journalism build the core toolkit."},
        ],
        "experiences": [
            {"name": "A venture with real revenue or users", "why": "Nothing signals business aptitude like having done business."},
            {"name": "DECA / FBLA competition", "why": "Structured, recognized business competition."},
            {"name": "Work experience", "why": "Any real job teaches operations and accountability."},
        ],
        "evidence": [
            "Numbers you can cite: revenue, members grown, funds raised",
            "A leadership role held for more than a year",
            "Quantitative coursework (calculus or statistics)",
        ],
    },
    "psychology": {
        "label": "Psychology",
        "academic_prep": [
            {"name": "AP Psychology", "why": "Direct subject evidence where offered."},
            {"name": "AP Statistics", "why": "Psychology is a statistical science; this is the quiet differentiator."},
            {"name": "AP Biology", "why": "Neuroscience-adjacent foundation."},
        ],
        "skills": [
            {"key": "research", "name": "Research methods", "keywords": ["research", "survey", "experiment", "psychology", "science fair"], "build": "Design a survey study; join a research program."},
            {"key": "statistics", "name": "Statistics", "keywords": ["statistics", "data", "math"], "build": "AP Statistics plus a data project."},
            {"key": "service", "name": "Human service", "keywords": ["volunteer", "peer", "mentor", "counsel", "hotline", "hospital", "tutor"], "build": "Peer counseling, mentoring, crisis-line volunteering."},
            {"key": "communication", "name": "Writing & communication", "keywords": ["writing", "journal", "newspaper", "debate", "blog"], "build": "Write about behavioral science for a school publication."},
        ],
        "experiences": [
            {"name": "A study or research assistantship", "why": "Shows you know psychology is a science, not just empathy."},
            {"name": "Peer support / mentoring role", "why": "Applied interest in how people work."},
            {"name": "Statistics-based project", "why": "Separates you from the many psych applicants without quantitative evidence."},
        ],
        "evidence": [
            "A research question and how you tested it",
            "Statistics on the transcript",
            "Sustained people-facing service",
        ],
    },
    "mathematics": {
        "label": "Mathematics",
        "academic_prep": [
            {"name": "AP Calculus BC", "why": "The baseline; take it as early as your school allows."},
            {"name": "Post-BC coursework (multivariable, linear algebra)", "why": "Dual enrollment or online courses signal ceiling."},
            {"name": "AP Statistics", "why": "Breadth within the discipline."},
        ],
        "skills": [
            {"key": "competition", "name": "Competition math", "keywords": ["amc", "aime", "olympiad", "math league", "mathcounts", "competition"], "build": "AMC 10/12 -> AIME is the standard progression; even participation matters."},
            {"key": "advanced_courses", "name": "Advanced coursework", "keywords": ["calculus", "linear algebra", "multivariable", "number theory", "math"], "build": "Exhaust the school's track, then dual-enroll."},
            {"key": "proof", "name": "Proof & rigor", "keywords": ["proof", "olympiad", "research", "number theory"], "build": "Work through a proof-based book (e.g. intro number theory)."},
            {"key": "teaching", "name": "Teaching math", "keywords": ["tutor", "teach", "mathcounts coach", "club"], "build": "Tutor younger students or coach a MATHCOUNTS team."},
        ],
        "experiences": [
            {"name": "AMC/AIME participation", "why": "The most legible external signal for math."},
            {"name": "Math circle or summer program", "why": "Community + exposure to real mathematics."},
            {"name": "Independent study beyond the curriculum", "why": "Mathematicians are self-propelled."},
        ],
        "evidence": [
            "Competition scores, whatever they are, with a growth story",
            "Math beyond BC on the transcript",
            "Teaching or club leadership in math",
        ],
    },
    "economics": {
        "label": "Economics",
        "academic_prep": [
            {"name": "AP Economics (Micro & Macro)", "why": "Direct subject evidence."},
            {"name": "AP Calculus", "why": "College economics is mathematical; calculus is the gatekeeper."},
            {"name": "AP Statistics", "why": "Econometrics foundation."},
        ],
        "skills": [
            {"key": "quantitative", "name": "Quantitative foundation", "keywords": ["calculus", "statistics", "math"], "build": "Calculus + statistics beats a second economics elective."},
            {"key": "econ_knowledge", "name": "Economic reasoning", "keywords": ["economics", "econ", "fed challenge", "investment", "finance"], "build": "AP Econ, Fed Challenge, or an investment club with a thesis-driven approach."},
            {"key": "data", "name": "Data analysis", "keywords": ["data", "research", "spreadsheet", "python", "statistics"], "build": "Analyze a public dataset (FRED, World Bank) and write it up."},
            {"key": "writing", "name": "Analytical writing", "keywords": ["essay", "journal", "newspaper", "debate", "writing"], "build": "Write op-eds or enter economics essay competitions."},
        ],
        "experiences": [
            {"name": "Economics competition (Fed Challenge, NEC)", "why": "Structured evidence of the discipline."},
            {"name": "A data project on a real question", "why": "Economics departments love empirical instinct."},
            {"name": "Debate or policy club", "why": "Argumentation is half the field."},
        ],
        "evidence": [
            "Calculus and statistics on the transcript",
            "One empirical or competition project you can defend",
            "Writing that engages with an economic question",
        ],
    },
    "nursing": {
        "label": "Nursing",
        "academic_prep": [
            {"name": "AP Biology", "why": "Direct-entry nursing programs screen on science rigor."},
            {"name": "Chemistry", "why": "Required prerequisite nearly everywhere."},
            {"name": "Anatomy & Physiology", "why": "The clearest subject signal where offered."},
        ],
        "skills": [
            {"key": "clinical", "name": "Clinical exposure", "keywords": ["hospital", "clinic", "cna", "emt", "shadow", "nursing", "health"], "build": "CNA certification, EMT training, hospital volunteering, or shadowing."},
            {"key": "science_core", "name": "Science coursework", "keywords": ["biology", "chemistry", "anatomy", "physiology"], "build": "Biology + chemistry at the highest available level."},
            {"key": "service", "name": "Care & service", "keywords": ["volunteer", "care", "elder", "camp", "tutor", "red cross"], "build": "Sustained service showing you like taking care of people."},
            {"key": "resilience", "name": "Responsibility under pressure", "keywords": ["job", "work", "lifeguard", "captain", "first aid"], "build": "A real job or certification (CPR/first aid) demonstrating reliability."},
        ],
        "experiences": [
            {"name": "Hospital or clinic volunteering", "why": "Programs want evidence you've seen the environment."},
            {"name": "CNA/EMT certification", "why": "The strongest pre-nursing credential available to a high schooler."},
            {"name": "HOSA competition", "why": "Recognized health-careers organization."},
        ],
        "evidence": [
            "Documented patient-adjacent hours",
            "Biology and chemistry rigor",
            "A story about why nursing specifically, grounded in experience",
        ],
    },
}
