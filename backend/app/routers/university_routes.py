import re

from fastapi import APIRouter, Depends, HTTPException, Query, Response
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

# Students search by the name they say out loud, which is often nowhere in the
# official name ("MIT", "UCLA", "Caltech"). Two mechanisms cover this:
# generated initials handle the regular cases, aliases the irregular ones.
_SKIP_WORDS = {"of", "the", "at", "and", "in", "for", "a", "college", "campus"}
_WORD_SPLIT = re.compile(r"[\s\-,.&]+")

NICKNAMES = {
    "caltech": "california institute of technology",
    "penn": "university of pennsylvania",
    "upenn": "university of pennsylvania",
    "cal": "university of california-berkeley",
    "ucb": "university of california-berkeley",
    "gatech": "georgia institute of technology",
    "vtech": "virginia polytechnic institute",
    "vt": "virginia polytechnic institute",
    "ut austin": "university of texas at austin",
    "umich": "university of michigan",
    "uw": "university of washington",
    "bu": "boston university",
    "bc": "boston college",
    "usc": "university of southern california",
    "asu": "arizona state university",
    "psu": "pennsylvania state university",
    "osu": "ohio state university",
    "cmu": "carnegie mellon university",
    "rpi": "rensselaer polytechnic institute",
    "nyu": "new york university",
    "ucla": "university of california-los angeles",
    "mit": "massachusetts institute of technology",
    # multi-word spoken names that appear nowhere in the official name
    "georgia tech": "georgia institute of technology",
    "virginia tech": "virginia polytechnic institute",
    "ga tech": "georgia institute of technology",
    "uc berkeley": "university of california-berkeley",
    "uc la": "university of california-los angeles",
    "texas a&m": "texas a & m university",
    "mass institute of technology": "massachusetts institute of technology",
}


def name_initials(name: str) -> str:
    """"University of California-Los Angeles" -> "ucla" """
    words = [w for w in _WORD_SPLIT.split(name.lower()) if w and w not in _SKIP_WORDS]
    return "".join(w[0] for w in words)


def match_rank(name: str, q: str) -> int | None:
    """Relevance of `name` for query `q`; lower is better, None means no match.

    Ranking matters at real scale: a bare substring search for "MIT" puts
    "Johnson C Smith University" ahead of the school the student meant, because
    "Smith" contains "mit".
    """
    low, needle = name.lower(), q.lower().strip()
    if not needle:
        return None
    if low == needle:
        return 0
    expanded = NICKNAMES.get(needle)
    if expanded and expanded in low:
        return 1
    if low.startswith(needle):
        return 2
    if 2 <= len(needle) <= 5 and needle.isalpha() and name_initials(name).startswith(needle):
        return 3
    if needle in low:
        return 4
    return None


@router.get("", response_model=list[UniversityOut])
def search(
    response: Response,
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
    limit: int = Query(default=50, ge=1, le=200, description="Max results per page"),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(University)
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

    # name search in Python so abbreviations and nicknames work too
    ranks: dict[int, int] = {}
    if q:
        matched = []
        for u in results:
            rank = match_rank(u.name, q)
            if rank is not None:
                ranks[u.id] = rank
                matched.append(u)
        results = matched

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

    # relevance wins over alphabetical when the student typed a name
    if ranks:
        results.sort(key=lambda u: (ranks[u.id], u.name))

    # 1,500+ real schools - never ship the whole catalog in one response
    response.headers["X-Total-Count"] = str(len(results))
    return results[offset : offset + limit]


@router.get("/{university_id}", response_model=UniversityOut)
def get_university(university_id: int, db: Session = Depends(get_db)):
    uni = db.get(University, university_id)
    if uni is None:
        raise HTTPException(status_code=404, detail="University not found")
    return uni
