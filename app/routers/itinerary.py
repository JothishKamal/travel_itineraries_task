from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.database.db import get_db
from app.models.models import (
    Itinerary,
    Accommodation,
    ItineraryTransfer,
    ItineraryActivity,
    Hotel,
    Activity,
    Transfer,
)
from app.schemas.schemas import (
    ItineraryCreate,
    Itinerary as ItinerarySchema,
)


router = APIRouter(
    prefix="/itineraries",
    tags=["itineraries"],
    responses={404: {"description": "Not found"}},
)


def validate_itinerary_data(itinerary: ItineraryCreate, db: Session):
    """
    Validate itinerary data before creating a new itinerary.
    Checks for:
    - Valid hotel IDs
    - Valid transfer IDs
    - Valid activity IDs
    - Logical date constraints
    - Reasonable duration
    """
    errors = []

    if itinerary.duration_nights <= 0 or itinerary.duration_nights > 30:
        errors.append("Duration must be between 1 and 30 nights")

    for acc in itinerary.accommodations:
        hotel = db.query(Hotel).filter(Hotel.id == acc.hotel_id).first()
        if not hotel:
            errors.append(f"Hotel with ID {acc.hotel_id} does not exist")

        if acc.nights <= 0:
            errors.append(f"Nights for hotel {acc.hotel_id} must be positive")

        today = date.today()
        if acc.check_in_date < today:
            errors.append(f"Check-in date {acc.check_in_date} is in the past")

    for transfer in itinerary.transfers:
        transfer_obj = (
            db.query(Transfer).filter(Transfer.id == transfer.transfer_id).first()
        )
        if not transfer_obj:
            errors.append(f"Transfer with ID {transfer.transfer_id} does not exist")

        if transfer.day < 1 or transfer.day > itinerary.duration_nights + 1:
            errors.append(
                f"Transfer day {transfer.day} is outside the itinerary duration"
            )

    for activity in itinerary.activities:
        activity_obj = (
            db.query(Activity).filter(Activity.id == activity.activity_id).first()
        )
        if not activity_obj:
            errors.append(f"Activity with ID {activity.activity_id} does not exist")

        if activity.day < 1 or activity.day > itinerary.duration_nights + 1:
            errors.append(
                f"Activity day {activity.day} is outside the itinerary duration"
            )

        valid_time_slots = ["morning", "afternoon", "evening", "full-day"]
        if activity.time_slot.lower() not in valid_time_slots:
            errors.append(
                f"Time slot '{activity.time_slot}' is not valid. Use: morning, afternoon, evening, or full-day"
            )

    activities_per_day = {}
    for activity in itinerary.activities:
        day = activity.day
        if day not in activities_per_day:
            activities_per_day[day] = {
                "morning": 0,
                "afternoon": 0,
                "evening": 0,
                "full-day": 0,
            }

        time_slot = activity.time_slot.lower()
        activities_per_day[day][time_slot] += 1

        if activities_per_day[day][time_slot] > 1:
            errors.append(
                f"Too many activities scheduled for day {day} in the {time_slot} time slot"
            )

    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})


@router.post("/", response_model=ItinerarySchema)
def create_itinerary(itinerary: ItineraryCreate, db: Session = Depends(get_db)):
    """
    Create a new itinerary with accommodations, transfers, and activities.
    """

    validate_itinerary_data(itinerary, db)

    total_price = 0.0

    db_itinerary = Itinerary(
        name=itinerary.name,
        duration_nights=itinerary.duration_nights,
        total_price=total_price,
        description=itinerary.description,
        is_recommended=False,
    )
    db.add(db_itinerary)
    db.commit()
    db.refresh(db_itinerary)

    for acc in itinerary.accommodations:
        db_accommodation = Accommodation(
            itinerary_id=db_itinerary.id,
            hotel_id=acc.hotel_id,
            check_in_date=acc.check_in_date,
            nights=acc.nights,
        )
        db.add(db_accommodation)

    for transfer in itinerary.transfers:
        db_transfer = ItineraryTransfer(
            itinerary_id=db_itinerary.id,
            transfer_id=transfer.transfer_id,
            day=transfer.day,
        )
        db.add(db_transfer)

    for activity in itinerary.activities:
        db_activity = ItineraryActivity(
            itinerary_id=db_itinerary.id,
            activity_id=activity.activity_id,
            day=activity.day,
            time_slot=activity.time_slot.lower(),
        )
        db.add(db_activity)

    db.commit()

    db_itinerary = calculate_total_price(db_itinerary.id, db)
    db.commit()

    return db_itinerary


@router.get("/", response_model=List[ItinerarySchema])
def get_itineraries(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get all itineraries with pagination.
    """

    if skip < 0:
        raise HTTPException(status_code=422, detail="Skip parameter cannot be negative")
    if limit <= 0 or limit > 100:
        raise HTTPException(status_code=422, detail="Limit must be between 1 and 100")

    itineraries = db.query(Itinerary).offset(skip).limit(limit).all()

    valid_itineraries = []
    for itinerary in itineraries:
        try:
            for acc in itinerary.accommodations:
                if not acc.hotel_id or not acc.hotel or acc.nights <= 0:
                    continue

            for transfer in itinerary.transfers:
                if (
                    not transfer.transfer_id
                    or not transfer.transfer
                    or transfer.day <= 0
                ):
                    continue

            for activity in itinerary.activities:
                if (
                    not activity.activity_id
                    or not activity.activity
                    or activity.day <= 0
                    or activity.time_slot
                    not in ["morning", "afternoon", "evening", "full-day"]
                ):
                    continue

            valid_itineraries.append(itinerary)
        except Exception:
            continue

    return valid_itineraries


@router.get("/{itinerary_id}", response_model=ItinerarySchema)
def get_itinerary(itinerary_id: int, db: Session = Depends(get_db)):
    """
    Get details of a specific itinerary.
    """

    if itinerary_id <= 0:
        raise HTTPException(status_code=422, detail="Itinerary ID must be positive")

    itinerary = db.query(Itinerary).filter(Itinerary.id == itinerary_id).first()
    if itinerary is None:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return itinerary


def calculate_total_price(itinerary_id: int, db: Session) -> Itinerary:
    """
    Calculate the total price of an itinerary based on its accommodations, transfers, and activities.
    """
    itinerary = db.query(Itinerary).filter(Itinerary.id == itinerary_id).first()
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    total_price = 0.0

    for acc in itinerary.accommodations:
        total_price += acc.hotel.price_per_night * acc.nights

    for transfer in itinerary.transfers:
        total_price += transfer.transfer.price

    for activity in itinerary.activities:
        total_price += activity.activity.price

    itinerary.total_price = total_price
    db.add(itinerary)

    return itinerary
