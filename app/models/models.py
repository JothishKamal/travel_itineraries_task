from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    region = Column(String(100), nullable=False)
    description = Column(Text)

    hotels = relationship("Hotel", back_populates="location")
    activities = relationship("Activity", back_populates="location")


class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"))
    star_rating = Column(Float)
    price_per_night = Column(Float, nullable=False)
    description = Column(Text)

    location = relationship("Location", back_populates="hotels")
    accommodations = relationship("Accommodation", back_populates="hotel")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"))
    duration_hours = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(Text)

    location = relationship("Location", back_populates="activities")
    itinerary_activities = relationship("ItineraryActivity", back_populates="activity")


class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True, index=True)
    from_location_id = Column(Integer, ForeignKey("locations.id"))
    to_location_id = Column(Integer, ForeignKey("locations.id"))
    mode = Column(String(50), nullable=False)
    duration_hours = Column(Float, nullable=False)
    price = Column(Float, nullable=False)

    from_location = relationship("Location", foreign_keys=[from_location_id])
    to_location = relationship("Location", foreign_keys=[to_location_id])
    itinerary_transfers = relationship("ItineraryTransfer", back_populates="transfer")


class Itinerary(Base):
    __tablename__ = "itineraries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    duration_nights = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)
    is_recommended = Column(Boolean, default=False)
    description = Column(Text)

    accommodations = relationship("Accommodation", back_populates="itinerary")
    transfers = relationship("ItineraryTransfer", back_populates="itinerary")
    activities = relationship("ItineraryActivity", back_populates="itinerary")


class Accommodation(Base):
    __tablename__ = "accommodations"

    id = Column(Integer, primary_key=True, index=True)
    itinerary_id = Column(Integer, ForeignKey("itineraries.id"))
    hotel_id = Column(Integer, ForeignKey("hotels.id"))
    check_in_date = Column(Date, nullable=False)
    nights = Column(Integer, nullable=False)

    itinerary = relationship("Itinerary", back_populates="accommodations")
    hotel = relationship("Hotel", back_populates="accommodations")


class ItineraryTransfer(Base):
    __tablename__ = "itinerary_transfers"

    id = Column(Integer, primary_key=True, index=True)
    itinerary_id = Column(Integer, ForeignKey("itineraries.id"))
    transfer_id = Column(Integer, ForeignKey("transfers.id"))
    day = Column(Integer, nullable=False)

    itinerary = relationship("Itinerary", back_populates="transfers")
    transfer = relationship("Transfer", back_populates="itinerary_transfers")


class ItineraryActivity(Base):
    __tablename__ = "itinerary_activities"

    id = Column(Integer, primary_key=True, index=True)
    itinerary_id = Column(Integer, ForeignKey("itineraries.id"))
    activity_id = Column(Integer, ForeignKey("activities.id"))
    day = Column(Integer, nullable=False)
    time_slot = Column(String(50))

    itinerary = relationship("Itinerary", back_populates="activities")
    activity = relationship("Activity", back_populates="itinerary_activities")
