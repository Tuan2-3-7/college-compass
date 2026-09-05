from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .models import APPLICATION_ROUNDS, APPLICATION_STATUSES, TASK_STATUSES


# ---------- auth ----------

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    created_at: datetime


# ---------- profile ----------

class ProfileIn(BaseModel):
    full_name: str = ""
    student_type: str = "domestic"
    applicant_level: str = "first_year"
    country: str = "United States"
    gpa: float | None = None
    gpa_scale: float = 4.0
    sat: int | None = Field(default=None, ge=400, le=1600)
    act: int | None = Field(default=None, ge=1, le=36)
    toefl: int | None = Field(default=None, ge=0, le=120)
    ielts: float | None = Field(default=None, ge=0, le=9)
    intended_major: str | None = None
    financial_aid_needed: bool = False
    courses: list[str] = []
    activities: list[dict] = []
    awards: list[str] = []
    languages: list[str] = []

    @field_validator("student_type")
    @classmethod
    def _check_type(cls, v: str) -> str:
        if v not in ("domestic", "international"):
            raise ValueError("student_type must be domestic or international")
        return v

    @field_validator("applicant_level")
    @classmethod
    def _check_level(cls, v: str) -> str:
        if v not in ("first_year", "transfer", "graduate"):
            raise ValueError("applicant_level must be first_year, transfer, or graduate")
        return v


class ProfileOut(ProfileIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int


# ---------- universities ----------

class UniversityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    city: str
    state: str
    control: str
    undergrad_enrollment: int | None
    acceptance_rate: float | None
    sat_25: int | None
    sat_75: int | None
    act_25: int | None
    act_75: int | None
    test_policy: str
    tuition_in_state: int | None
    tuition_out_state: int | None
    cost_of_attendance: int | None
    toefl_min: int | None
    ielts_min: float | None
    offers_intl_aid: bool
    intl_support_notes: str
    app_platforms: list
    majors: list
    deadlines: dict
    supplemental_essay_count: int
    application_fee: int | None
    links: dict
    data_source: str
    last_verified: date | None


# ---------- applications ----------

class ApplicationIn(BaseModel):
    university_id: int
    round: str = "regular"

    @field_validator("round")
    @classmethod
    def _check_round(cls, v: str) -> str:
        if v not in APPLICATION_ROUNDS:
            raise ValueError(f"round must be one of {APPLICATION_ROUNDS}")
        return v


class ApplicationUpdate(BaseModel):
    round: str | None = None
    status: str | None = None
    decision: str | None = None
    notes: str | None = None

    @field_validator("status")
    @classmethod
    def _check_status(cls, v: str | None) -> str | None:
        if v is not None and v not in APPLICATION_STATUSES:
            raise ValueError(f"status must be one of {APPLICATION_STATUSES}")
        return v


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    university_id: int
    round: str
    status: str
    decision: str | None
    deadline: date | None
    notes: str
    created_at: datetime
    university: UniversityOut


# ---------- tasks ----------

class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    category: str = "custom"
    due_date: date | None = None
    priority: str = "medium"
    application_id: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    due_date: date | None = None
    priority: str | None = None
    status: str | None = None

    @field_validator("status")
    @classmethod
    def _check_status(cls, v: str | None) -> str | None:
        if v is not None and v not in TASK_STATUSES:
            raise ValueError(f"status must be one of {TASK_STATUSES}")
        return v


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    application_id: int | None
    title: str
    description: str
    category: str
    due_date: date | None
    priority: str
    status: str
    auto_generated: bool
    sort_order: int
