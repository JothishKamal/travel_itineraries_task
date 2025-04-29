from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.database.db import engine, get_db
from app.models.models import Base
from app.routers import itinerary
from app.database.seed import seed_data


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Travel Itinerary System",
    description="API for managing travel itineraries for Thailand destinations",
    version="1.0.0",
)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Travel Itinerary System"}


@app.post("/seed-data")
def initialize_seed_data(db: Session = Depends(get_db)):
    """
    Initialize the database with seed data (for development purposes only).
    """
    seed_data(db)
    return {"message": "Database seeded successfully"}


app.include_router(itinerary.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
