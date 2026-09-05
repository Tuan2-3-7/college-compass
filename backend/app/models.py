from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    profile: Mapped["StudentProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    applications: Mapped[list["Application"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)

    full_name: Mapped[str] = mapped_column(String(255), default="")
    student_type: Mapped[str] = mapped_column(String(20), default="domestic")  # domestic|international
    applicant_level: Mapped[str] = mapped_column(String(20), default="first_year")  # first_year|transfer|graduate
    country: Mapped[str] = mapped_column(String(100), default="United States")

    gpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    gpa_scale: Mapped[float] = mapped_column(Float, default=4.0)
    sat: Mapped[int | None] = mapped_column(Integer, nullable=True)
    act: Mapped[int | None] = mapped_column(Integer, nullable=True)
    toefl: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ielts: Mapped[float | None] = mapped_column(Float, nullable=True)

    intended_major: Mapped[str | None] = mapped_column(String(100), nullable=True)
    financial_aid_needed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Lists stored as JSON for the MVP; normalized into tables in Phase 2.
    courses: Mapped[list] = mapped_column(JSON, default=list)
    activities: Mapped[list] = mapped_column(JSON, default=list)
    awards: Mapped[list] = mapped_column(JSON, default=list)
    languages: Mapped[list] = mapped_column(JSON, default=list)

    user: Mapped[User] = relationship(back_populates="profile")


class University(Base):
    __tablename__ = "universities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(2), index=True)
    control: Mapped[str] = mapped_column(String(10))  # public|private
    undergrad_enrollment: Mapped[int | None] = mapped_column(Integer, nullable=True)

    acceptance_rate: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0..1
    sat_25: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sat_75: Mapped[int | None] = mapped_column(Integer, nullable=True)
    act_25: Mapped[int | None] = mapped_column(Integer, nullable=True)
    act_75: Mapped[int | None] = mapped_column(Integer, nullable=True)
    test_policy: Mapped[str] = mapped_column(String(20), default="optional")  # required|optional|blind

    tuition_in_state: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tuition_out_state: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_of_attendance: Mapped[int | None] = mapped_column(Integer, nullable=True)

    toefl_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ielts_min: Mapped[float | None] = mapped_column(Float, nullable=True)

    offers_intl_aid: Mapped[bool] = mapped_column(Boolean, default=False)
    intl_support_notes: Mapped[str] = mapped_column(Text, default="")

    app_platforms: Mapped[list] = mapped_column(JSON, default=list)
    majors: Mapped[list] = mapped_column(JSON, default=list)
    # e.g. {"early_decision": "11-01", "early_action": "11-01", "regular": "01-05",
    #       "transfer": "03-01", "rolling": false}
    deadlines: Mapped[dict] = mapped_column(JSON, default=dict)
    supplemental_essay_count: Mapped[int] = mapped_column(Integer, default=0)
    application_fee: Mapped[int | None] = mapped_column(Integer, nullable=True)

    links: Mapped[dict] = mapped_column(JSON, default=dict)
    data_source: Mapped[str] = mapped_column(
        String(255), default="sample_seed_v1 (illustrative only - verify before relying on it)"
    )
    last_verified: Mapped[date | None] = mapped_column(Date, nullable=True)

    applications: Mapped[list["Application"]] = relationship(back_populates="university")


APPLICATION_STATUSES = ["not_started", "in_progress", "completed", "submitted", "decision_received"]
APPLICATION_ROUNDS = ["early_decision", "early_action", "regular", "rolling", "transfer"]


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("user_id", "university_id", name="uq_user_university"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    university_id: Mapped[int] = mapped_column(ForeignKey("universities.id"))

    round: Mapped[str] = mapped_column(String(20), default="regular")
    status: Mapped[str] = mapped_column(String(20), default="not_started")
    decision: Mapped[str | None] = mapped_column(String(20), nullable=True)  # accepted|rejected|waitlisted|deferred
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped[User] = relationship(back_populates="applications")
    university: Mapped[University] = relationship(back_populates="applications")
    tasks: Mapped[list["Task"]] = relationship(back_populates="application", cascade="all, delete-orphan")


class Scholarship(Base):
    __tablename__ = "scholarships"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    provider: Mapped[str] = mapped_column(String(255), default="")
    amount_max: Mapped[int | None] = mapped_column(Integer, nullable=True)  # USD, per award
    renewable: Mapped[bool] = mapped_column(Boolean, default=False)
    eligibility: Mapped[str] = mapped_column(String(20), default="both")  # domestic|international|both
    min_gpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    majors: Mapped[list] = mapped_column(JSON, default=list)  # empty = any major
    deadline: Mapped[str | None] = mapped_column(String(5), nullable=True)  # "MM-DD", recurs yearly
    description: Mapped[str] = mapped_column(Text, default="")
    data_source: Mapped[str] = mapped_column(
        String(255), default="sample_seed_v1 (illustrative only - verify before relying on it)"
    )
    last_verified: Mapped[date | None] = mapped_column(Date, nullable=True)


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (UniqueConstraint("user_id", "dedupe_key", name="uq_user_dedupe"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    dedupe_key: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(30), default="deadline")
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text, default="")
    link: Mapped[str] = mapped_column(String(100), default="")
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


ESSAY_TYPES = ["personal_statement", "supplemental", "scholarship", "other"]


class Essay(Base):
    __tablename__ = "essays"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("applications.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255))
    prompt: Mapped[str] = mapped_column(Text, default="")
    essay_type: Mapped[str] = mapped_column(String(30), default="personal_statement")
    word_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    drafts: Mapped[list["EssayDraft"]] = relationship(
        back_populates="essay", cascade="all, delete-orphan", order_by="EssayDraft.version"
    )


class EssayDraft(Base):
    __tablename__ = "essay_drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    essay_id: Mapped[int] = mapped_column(ForeignKey("essays.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    essay: Mapped[Essay] = relationship(back_populates="drafts")
    feedback: Mapped["EssayFeedback | None"] = relationship(
        back_populates="draft", uselist=False, cascade="all, delete-orphan"
    )


class EssayFeedback(Base):
    __tablename__ = "essay_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("essay_drafts.id"), unique=True)
    overall_score: Mapped[int] = mapped_column(Integer)
    scores: Mapped[dict] = mapped_column(JSON, default=dict)          # per-dimension 0-100
    paragraph_feedback: Mapped[list] = mapped_column(JSON, default=list)
    weaknesses: Mapped[list] = mapped_column(JSON, default=list)
    suggestions: Mapped[list] = mapped_column(JSON, default=list)
    questions: Mapped[list] = mapped_column(JSON, default=list)       # coaching questions
    flags: Mapped[dict] = mapped_column(JSON, default=dict)           # cliches, repetition
    provider: Mapped[str] = mapped_column(String(30), default="mock")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    draft: Mapped[EssayDraft] = relationship(back_populates="feedback")


class TutorMessage(Base):
    __tablename__ = "tutor_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(10))  # user|assistant
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


TASK_STATUSES = ["todo", "in_progress", "done"]
TASK_CATEGORIES = [
    "account", "academics", "testing", "essays", "recommendations",
    "documents", "financial_aid", "submission", "post_admission", "custom",
]


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("applications.id"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(30), default="custom")
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    priority: Mapped[str] = mapped_column(String(10), default="medium")  # low|medium|high
    status: Mapped[str] = mapped_column(String(20), default="todo")
    auto_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped[User] = relationship(back_populates="tasks")
    application: Mapped[Application | None] = relationship(back_populates="tasks")
