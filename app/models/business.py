from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Hotel(Base):
    __tablename__ = "hotels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    price_tier: Mapped[str | None] = mapped_column(String(20))
    checkin_date: Mapped[str | None] = mapped_column(String(50))
    checkout_date: Mapped[str | None] = mapped_column(String(50))
    booked: Mapped[int] = mapped_column(Integer, default=0)


class CarRental(Base):
    __tablename__ = "car_rentals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    price_tier: Mapped[str | None] = mapped_column(String(20))
    start_date: Mapped[str | None] = mapped_column(String(50))
    end_date: Mapped[str | None] = mapped_column(String(50))
    booked: Mapped[int] = mapped_column(Integer, default=0)


class TripRecommendation(Base):
    __tablename__ = "trip_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    keywords: Mapped[str | None] = mapped_column(Text)
    details: Mapped[str | None] = mapped_column(Text)
    booked: Mapped[int] = mapped_column(Integer, default=0)
