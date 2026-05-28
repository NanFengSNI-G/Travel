from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class Flight(Base):
    __tablename__ = "flights"

    flight_id: Mapped[int] = mapped_column("flight_id", Integer, primary_key=True)
    flight_no: Mapped[str] = mapped_column(String(20), nullable=False)
    departure_airport: Mapped[str] = mapped_column(String(10), nullable=False)
    arrival_airport: Mapped[str] = mapped_column(String(10), nullable=False)
    scheduled_departure: Mapped[str] = mapped_column(String(50), nullable=False)
    scheduled_arrival: Mapped[str] = mapped_column(String(50), nullable=False)

    ticket_flights: Mapped[list["TicketFlight"]] = relationship(back_populates="flight")


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_no: Mapped[str] = mapped_column(String(50), primary_key=True)
    book_ref: Mapped[str] = mapped_column(String(20), nullable=False)
    passenger_id: Mapped[str] = mapped_column(String(30), nullable=False)
    passenger_name: Mapped[str | None] = mapped_column(String(50))

    ticket_flights: Mapped[list["TicketFlight"]] = relationship(back_populates="ticket")


class TicketFlight(Base):
    __tablename__ = "ticket_flights"

    ticket_no: Mapped[str] = mapped_column(String(50), ForeignKey("tickets.ticket_no"), primary_key=True)
    flight_id: Mapped[int] = mapped_column(Integer, ForeignKey("flights.flight_id"), primary_key=True)
    fare_conditions: Mapped[str | None] = mapped_column(String(20))

    ticket: Mapped["Ticket"] = relationship(back_populates="ticket_flights")
    flight: Mapped["Flight"] = relationship(back_populates="ticket_flights")


class BoardingPass(Base):
    __tablename__ = "boarding_passes"

    ticket_no: Mapped[str] = mapped_column(String(50), ForeignKey("tickets.ticket_no"), primary_key=True)
    flight_id: Mapped[int] = mapped_column(Integer, ForeignKey("flights.flight_id"), primary_key=True)
    boarding_no: Mapped[int | None] = mapped_column(Integer)
    seat_no: Mapped[str | None] = mapped_column(String(10))
