from datetime import date, timedelta
from sqlalchemy.orm import Session
import json
import os
import pathlib

from app.models.models import (
    Location,
    Hotel,
    Activity,
    Transfer,
    Itinerary,
    Accommodation,
    ItineraryTransfer,
    ItineraryActivity,
)


def seed_data(db: Session):
    db.query(ItineraryActivity).delete()
    db.query(ItineraryTransfer).delete()
    db.query(Accommodation).delete()
    db.query(Itinerary).delete()
    db.query(Transfer).delete()
    db.query(Activity).delete()
    db.query(Hotel).delete()
    db.query(Location).delete()

    current_dir = pathlib.Path(__file__).parent.absolute()
    json_file_path = os.path.join(current_dir, "seed_data.json")

    with open(json_file_path, "r") as f:
        data = json.load(f)

    location_mapping = {}
    for location_data in data["locations"]:
        location = Location(
            name=location_data["name"],
            region=location_data["region"],
            description=location_data["description"],
        )
        db.add(location)
        db.flush()
        location_mapping[location.name] = location

    db.commit()

    hotel_mapping = {}
    for hotel_data in data["hotels"]:
        location = location_mapping.get(hotel_data["location"])
        if location:
            hotel = Hotel(
                name=hotel_data["name"],
                location_id=location.id,
                star_rating=hotel_data["star_rating"],
                price_per_night=hotel_data["price_per_night"],
                description=hotel_data["description"],
            )
            db.add(hotel)
            db.flush()
            hotel_mapping[hotel.name] = hotel

    db.commit()

    activity_mapping = {}
    for activity_data in data["activities"]:
        location = location_mapping.get(activity_data["location"])
        if location:
            activity = Activity(
                name=activity_data["name"],
                location_id=location.id,
                duration_hours=activity_data["duration_hours"],
                price=activity_data["price"],
                description=activity_data["description"],
            )
            db.add(activity)
            db.flush()
            activity_mapping[activity.name] = activity

    db.commit()

    transfer_mapping = {}
    for transfer_data in data["transfers"]:
        from_location = location_mapping.get(transfer_data["from_location"])
        to_location = location_mapping.get(transfer_data["to_location"])
        if from_location and to_location:
            transfer = Transfer(
                from_location_id=from_location.id,
                to_location_id=to_location.id,
                mode=transfer_data["mode"],
                duration_hours=transfer_data["duration_hours"],
                price=transfer_data["price"],
            )
            db.add(transfer)
            db.flush()

            key = f"{from_location.name}_{to_location.name}"
            transfer_mapping[key] = transfer

    db.commit()

    create_itineraries_from_json(
        db,
        data["itineraries"],
        hotel_mapping,
        activity_mapping,
        transfer_mapping,
        location_mapping,
    )


def create_itineraries_from_json(
    db: Session,
    itineraries_data,
    hotel_mapping,
    activity_mapping,
    transfer_mapping,
    location_mapping,
):
    start_date = date.today() + timedelta(days=30)

    for itinerary_data in itineraries_data:
        itinerary = Itinerary(
            name=itinerary_data["name"],
            duration_nights=itinerary_data["duration_nights"],
            total_price=itinerary_data["total_price"],
            is_recommended=itinerary_data["is_recommended"],
            description=itinerary_data["description"],
        )
        db.add(itinerary)
        db.flush()

        current_date = start_date
        for accom_data in itinerary_data["accommodations"]:
            hotel = hotel_mapping.get(accom_data["hotel"])
            if hotel:
                accommodation = Accommodation(
                    itinerary_id=itinerary.id,
                    hotel_id=hotel.id,
                    check_in_date=current_date,
                    nights=accom_data["nights"],
                )
                db.add(accommodation)
                current_date += timedelta(days=accom_data["nights"])

        for activity_data in itinerary_data["activities"]:
            activity = activity_mapping.get(activity_data["activity"])
            if activity:
                itinerary_activity = ItineraryActivity(
                    itinerary_id=itinerary.id,
                    activity_id=activity.id,
                    day=activity_data["day"],
                    time_slot=activity_data["time_slot"],
                )
                db.add(itinerary_activity)

        for transfer_data in itinerary_data["transfers"]:
            if (
                isinstance(transfer_data["transfer"], list)
                and len(transfer_data["transfer"]) == 2
            ):
                from_loc = transfer_data["transfer"][0]
                to_loc = transfer_data["transfer"][1]
                key = f"{from_loc}_{to_loc}"
                transfer = transfer_mapping.get(key)
                if transfer:
                    itinerary_transfer = ItineraryTransfer(
                        itinerary_id=itinerary.id,
                        transfer_id=transfer.id,
                        day=transfer_data["day"],
                    )
                    db.add(itinerary_transfer)

    db.commit()
