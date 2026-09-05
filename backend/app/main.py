from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, SessionLocal, engine
from .data.scholarships import seed_scholarships
from .routers import (
    analyzer_routes,
    application_routes,
    auth_routes,
    compare_routes,
    dashboard_routes,
    essay_routes,
    finaid_routes,
    international_routes,
    major_routes,
    notification_routes,
    profile_routes,
    recommendation_routes,
    task_routes,
    tutor_routes,
    university_routes,
)
from .seed import seed_universities

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_universities(db)
        seed_scholarships(db)
    finally:
        db.close()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="College Compass API",
    description=(
        "Personalized US college application platform. University data in this MVP is "
        "SAMPLE DATA - illustrative and unverified. Always confirm requirements and "
        "deadlines on official university websites."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(profile_routes.router)
app.include_router(university_routes.router)
app.include_router(application_routes.router)
app.include_router(task_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(analyzer_routes.router)
app.include_router(major_routes.router)
app.include_router(essay_routes.router)
app.include_router(tutor_routes.router)
app.include_router(recommendation_routes.router)
app.include_router(finaid_routes.router)
app.include_router(international_routes.router)
app.include_router(compare_routes.router)
app.include_router(notification_routes.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
