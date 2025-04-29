from pydantic import BaseModel, field_validator, Field
from typing import List, Optional
from datetime import date


class LocationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    region: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class HotelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    location_id: int = Field(..., gt=0)
    star_rating: Optional[float] = Field(None, ge=0, le=5)
    price_per_night: float = Field(..., gt=0)
    description: Optional[str] = None

    @field_validator("star_rating")
    def validate_star_rating(cls, v):
        if v is not None and (v < 0 or v > 5):
            raise ValueError("Star rating must be between 0 and 5")
        return v


class ActivityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    location_id: int = Field(..., gt=0)
    duration_hours: float = Field(..., gt=0)
    price: float = Field(..., ge=0)
    description: Optional[str] = None

    @field_validator("duration_hours")
    def validate_duration(cls, v):
        if v <= 0:
            raise ValueError("Duration must be positive")
        if v > 24:
            raise ValueError("Duration cannot exceed 24 hours")
        return v


class TransferBase(BaseModel):
    from_location_id: int = Field(..., gt=0)
    to_location_id: int = Field(..., gt=0)
    mode: str = Field(..., min_length=1, max_length=50)
    duration_hours: float = Field(..., gt=0)
    price: float = Field(..., ge=0)

    @field_validator("to_location_id")
    def validate_different_locations(cls, v, info):
        if (
            hasattr(info, "data")
            and "from_location_id" in info.data
            and v == info.data["from_location_id"]
        ):
            raise ValueError("From and to locations must be different")
        return v

    @field_validator("duration_hours")
    def validate_transfer_duration(cls, v):
        if v <= 0:
            raise ValueError("Duration must be positive")
        if v > 24:
            raise ValueError("Duration should not exceed 24 hours")
        return v


class AccommodationCreate(BaseModel):
    hotel_id: int = Field(..., gt=0)
    check_in_date: date
    nights: int = Field(..., gt=0, le=30)

    @field_validator("check_in_date")
    def validate_not_past_date(cls, v):
        if v < date.today():
            raise ValueError("Check-in date cannot be in the past")
        return v

    @field_validator("nights")
    def validate_nights(cls, v):
        if v <= 0:
            raise ValueError("Nights must be positive")
        if v > 30:
            raise ValueError("Maximum stay is 30 nights")
        return v


class ItineraryTransferCreate(BaseModel):
    transfer_id: int = Field(..., gt=0)
    day: int = Field(..., gt=0)


class ItineraryActivityCreate(BaseModel):
    activity_id: int = Field(..., gt=0)
    day: int = Field(..., gt=0)
    time_slot: str = Field(..., min_length=1)

    @field_validator("time_slot")
    def validate_time_slot(cls, v):
        valid_slots = ["morning", "afternoon", "evening", "full-day"]
        if v.lower() not in valid_slots:
            raise ValueError(f"Time slot must be one of: {', '.join(valid_slots)}")
        return v.lower()


class ItineraryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    duration_nights: int = Field(..., gt=0, le=30)
    description: Optional[str] = None
    accommodations: List[AccommodationCreate] = Field(..., min_items=1)
    transfers: List[ItineraryTransferCreate] = Field(...)
    activities: List[ItineraryActivityCreate] = Field(...)

    @field_validator("duration_nights")
    def validate_duration(cls, v):
        if v <= 0:
            raise ValueError("Duration must be positive")
        if v > 30:
            raise ValueError("Maximum duration is 30 nights")
        return v

    @field_validator("accommodations")
    def validate_accommodation_exists(cls, v):
        if not v:
            raise ValueError("At least one accommodation is required")
        return v

    @field_validator("activities")
    def validate_activities_time_slots(cls, v):
        activity_slots = {}
        for activity in v:
            day = activity.day
            time_slot = activity.time_slot.lower()

            if day not in activity_slots:
                activity_slots[day] = set()

            if time_slot in activity_slots[day]:
                raise ValueError(
                    f"Multiple activities scheduled for day {day} in the {time_slot} time slot"
                )

            activity_slots[day].add(time_slot)

        return v

    @field_validator("transfers")
    def validate_transfers_days(cls, v, info):
        if hasattr(info, "data") and "duration_nights" in info.data:
            duration = info.data["duration_nights"]
            for transfer in v:
                if transfer.day < 1 or transfer.day > duration + 1:
                    raise ValueError(
                        f"Transfer day {transfer.day} is outside the itinerary duration"
                    )
        return v

    @field_validator("activities")
    def validate_activities_days(cls, v, info):
        if hasattr(info, "data") and "duration_nights" in info.data:
            duration = info.data["duration_nights"]
            for activity in v:
                if activity.day < 1 or activity.day > duration + 1:
                    raise ValueError(
                        f"Activity day {activity.day} is outside the itinerary duration"
                    )
        return v


class Location(LocationBase):
    id: int

    model_config = {"from_attributes": True}


class Hotel(HotelBase):
    id: int
    location: Location

    model_config = {"from_attributes": True}


class Activity(ActivityBase):
    id: int
    location: Location

    model_config = {"from_attributes": True}


class Transfer(TransferBase):
    id: int

    model_config = {"from_attributes": True}


class Accommodation(AccommodationCreate):
    id: int
    hotel: Hotel

    model_config = {"from_attributes": True}


class ItineraryTransfer(ItineraryTransferCreate):
    id: int
    transfer: Transfer

    model_config = {"from_attributes": True}


class ItineraryActivity(ItineraryActivityCreate):
    id: int
    activity: Activity

    model_config = {"from_attributes": True}


class Itinerary(BaseModel):
    id: int
    name: str
    duration_nights: int
    total_price: float
    is_recommended: bool
    description: Optional[str] = None
    accommodations: List[Accommodation]
    transfers: List[ItineraryTransfer]
    activities: List[ItineraryActivity]

    model_config = {"from_attributes": True}


class RecommendedItinerary(BaseModel):
    id: int
    name: str
    duration_nights: int
    total_price: float
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class RecommendedItinerariesResponse(BaseModel):
    status: str = "success"
    message: str = "Recommended itineraries retrieved successfully"
    data: List[RecommendedItinerary]
