# College Compass — Product Spec

**Goal**: A personalized platform that helps domestic and international students prepare
for US university applications from the beginning of high school/college planning through
application submission and, for international students, the post-admission process.

**One sentence**: College Compass is an AI-powered personalized college admissions coach
that helps students discover suitable US universities, understand their requirements,
build the skills and experiences needed for their intended major, improve their essays,
estimate their application competitiveness, and manage the entire application process
through personalized guidance and deadlines.

## Features

1. **Student Profile** — account/login; domestic vs. international; first-year/transfer/
   graduate; GPA + scale; SAT/ACT; AP/IB/honors courses; intended major; activities;
   leadership; awards; volunteer/work; research/projects; languages; financial-aid needs.
2. **University Database** — university, programs/majors, application platforms,
   deadlines, admission requirements, testing policies, English-proficiency requirements,
   tuition/cost, financial aid, international requirements, supplemental essays, fees,
   links/sources, last-verified date.
3. **University Finder** — search/filter by major, location, cost, public/private, size,
   competitiveness, financial aid, international support, deadline → build a college list.
4. **Application Manager** — per university: requirements, deadlines, documents, essays,
   recommendations, financial aid, status, post-admission. Statuses: not started →
   in progress → completed → submitted → decision received.
5. **Personalized Checklist** — tasks generated from student + university + major +
   application type (an international CS applicant ≠ a domestic biology transfer).
6. **Deadline & Calendar System** — application/scholarship/financial-aid/testing/
   recommendation/custom deadlines; calendar view; countdown; priorities; reminders.
7. **Application Competitiveness Analyzer** — GPA, rigor, tests, activities, leadership,
   awards, major prep, experiences, essay quality → subscores + overall + Reach/Target/
   Likely. Always framed as an estimate, never a guaranteed probability.
8. **AI Essay Coach** — prompt alignment, storytelling, voice, specificity, reflection,
   structure, grammar, clichés; paragraph-level feedback; guiding questions; revision
   tracking and draft history. Coaches — does not write the essay.
9. **AI Tutor** — explains concepts, gives examples, quizzes, evaluates answers, tracks
   weaknesses, adjusts difficulty.
10. **Major Advisor** — per intended major: academic prep, technical skills, experiences,
    application evidence.
11. **Skill-Gap Analysis** — what the major values vs. the student's profile → missing
    skills → personal improvement plan.
12. **Extracurricular Advisor** — depth over collection: what to continue/deepen, missing
    skills, project/leadership/research opportunities.
13. **Financial-Aid & Scholarship Planner** — domestic: FAFSA, CSS Profile, forms,
    scholarships, deadlines; international: university-specific aid, scholarships,
    financial documentation, proof of funds.
14. **International Student Center** — application → admission → financial docs → I-20 →
    SEVIS → F-1 visa → housing → travel/arrival, with plain-language explanations.
15. **University Comparison** — compare schools by the student's priorities.
16. **Application Readiness Score** — one dashboard score combining progress across
    academics, activities, essays, major prep, tasks, financial prep; highlights the
    highest-impact improvement.
17. **"What Should I Do Next?"** — looks at deadlines, incomplete tasks, weaknesses,
    major, requirements, essay status → tells the student today's highest-priority task.
18. **Progress Tracking** — checklist completion, essay scores over time, skill
    development, readiness history.

## Technical

- Frontend: React + Tailwind. Backend: Python (FastAPI). DB: SQLite for MVP → PostgreSQL.
- AI: LLM API for essay analysis, tutoring, recommendations, skill analysis, Q&A.
- Auth: student accounts, secure login, user profiles.
- Core tables: Users, Students, Universities, Majors, University_Requirements,
  Applications, Tasks, Deadlines, Essays, Essay_Drafts, Essay_Feedback, Activities,
  Skills, Major_Skills, Learning_Modules, Student_Progress, Scholarships, Documents,
  Notifications.

## Privacy & safety (built in from the start)

- Don't store unnecessary personal information; encrypt sensitive data where appropriate.
- Never expose one student's profile to another; users can delete their data.
- Clearly distinguish AI guidance from official university requirements; show source and
  verification date for requirements.
- Never promise admission outcomes; never present AI essay feedback as an admissions
  officer's judgment.

## Build phases

- **Phase 1 — Foundation**: profile → university DB → applications → checklist → dashboard ✅
- **Phase 2 — Intelligence**: competitiveness analyzer → major advisor → skill-gap analysis
- **Phase 3 — AI**: essay coach → AI tutor → personalized recommendations
- **Phase 4 — Advanced**: financial aid → international pathway → scholarships →
  notifications → analytics
