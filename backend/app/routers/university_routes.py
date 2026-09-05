from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import University
from ..schemas import UniversityOut

router = APIRouter(prefix="/api/universities", tags=["universities"])

# competitiveness buckets by acceptance rate
COMPETITIVENESS = {
    "most_selective": (0.0, 0.10),
    "very_selective": (0.10, 0.25),
    "selective": (0.25, 0.50),
    "less_selective": (0.50, 1.01),
}

SIZE_BUCKETS = {
    "small": (0, 5000),
    "medium": (5000, 15000),
    "large": (15000, 1_000_000),
}


@router.get("", response_model=list[UniversityOut])
def search(
    db: Session = Depends(get_db),
    q: str | None = Query(default=None, description="Name search"),
    major: str | None = None,
    state: str | None = None,
    control: str | None = Query(default=None, pattern="^(public|private)$"),
    max_cost: int | None = Query(default=None, description="Max total cost of attendance"),
    competitiveness: str | None = None,
    size: str | None = None,
    intl_aid: bool | None = Query(default=None, description="Only schools offering intl aid"),
    test_policy: str | None = None,
    sort: str = Query(default="name", pattern="^(name|acceptance_rate|cost)$"),
):
    query = db.query(University)
    if q:
        query = query.filter(University.name.ilike(f"%{q}%"))
    if state:
        query = query.filter(University.state == state.upper())
    if control:
        query = query.filter(University.control == control)
    if max_cost is not None:
        query = query.filter(University.cost_of_attendance <= max_cost)
    if intl_aid is not None:
        query = query.filter(University.offers_intl_aid == intl_aid)
    if test_policy:
        query = query.filter(University.test_policy == test_policy)
    if competitiveness:
        bounds = COMPETITIVENESS.get(competitiveness)
        if bounds is None:
            raise HTTPException(422, f"competitiveness must be one of {list(COMPETITIVENESS)}")
        query = query.filter(
            University.acceptance_rate >= bounds[0], University.acceptance_rate < bounds[1]
        )
    if size:
        bounds = SIZE_BUCKETS.get(size)
        if bounds is None:
            raise HTTPException(422, f"size must be one of {list(SIZE_BUCKETS)}")
        query = query.filter(
            University.undergrad_enrollment >= bounds[0],
            University.undergrad_enrollment < bounds[1],
        )

    results = query.all()

    # major filter on the JSON list (SQLite-friendly: filter in Python)
    if major:
        needle = major.lower().replace(" ", "_")
        results = [u for u in results if needle in (u.majors or [])]

    if sort == "acceptance_rate":
        results.sort(key=lambda u: u.acceptance_rate if u.acceptance_rate is not None else 2)
    elif sort == "cost":
        results.sort(key=lambda u: u.cost_of_attendance if u.cost_of_attendance is not None else 10**9)
    else:
        results.sort(key=lambda u: u.name)
    return results


@router.get("/{university_id}", response_model=UniversityOut)
def get_university(university_id: int, db: Session = Depends(get_db)):
    uni = db.get(University, university_id)
    if uni is None:
        raise HTTPException(status_code=404, detail="University not found")
    return uni
