from mcp.server.fastmcp import FastMCP
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.config import DATABASE_URL
from app.models.models import Itinerary


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


mcp = FastMCP("Travel Itinerary Recommender")


@mcp.tool()
def get_recommended_itineraries(nights: int) -> list:
    """
    Get recommended travel itineraries for a specific number of nights.

    Args:
        nights: Number of nights for the itinerary

    Returns:
        A list of recommended itineraries with details
    """
    db = SessionLocal()
    try:
        itineraries = (
            db.query(Itinerary)
            .filter(Itinerary.duration_nights == nights, Itinerary.is_recommended)
            .all()
        )

        result = []
        for itinerary in itineraries:
            accommodations = []
            for acc in itinerary.accommodations:
                hotel = acc.hotel
                location = hotel.location
                accommodations.append(
                    {
                        "hotel_name": hotel.name,
                        "location": location.name,
                        "check_in_date": acc.check_in_date.isoformat(),
                        "nights": acc.nights,
                        "price_per_night": hotel.price_per_night,
                    }
                )

            activities = []
            for act in itinerary.activities:
                activity = act.activity
                activities.append(
                    {
                        "name": activity.name,
                        "location": activity.location.name,
                        "day": act.day,
                        "time_slot": act.time_slot,
                        "duration_hours": activity.duration_hours,
                        "price": activity.price,
                    }
                )

            transfers = []
            for trans in itinerary.transfers:
                transfer = trans.transfer
                transfers.append(
                    {
                        "from": transfer.from_location.name,
                        "to": transfer.to_location.name,
                        "mode": transfer.mode,
                        "day": trans.day,
                        "duration_hours": transfer.duration_hours,
                        "price": transfer.price,
                    }
                )

            itinerary_data = {
                "id": itinerary.id,
                "name": itinerary.name,
                "duration_nights": itinerary.duration_nights,
                "total_price": itinerary.total_price,
                "description": itinerary.description,
                "accommodations": accommodations,
                "activities": activities,
                "transfers": transfers,
            }

            result.append(itinerary_data)

        return result
    finally:
        db.close()
