from datetime import date, datetime
from typing import Optional, List, Dict
import pytz

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload

from app.models import sm, row_to_dict
from app.models.flight import Flight, Ticket, TicketFlight, BoardingPass


@tool
def fetch_user_flight_information(config: RunnableConfig) -> List[Dict]:
    """通过乘客ID获取该乘客的所有机票、航班和座位信息。"""
    passenger_id = config.get("configurable", {}).get("passenger_id", None)
    if not passenger_id:
        raise ValueError("未配置乘客 ID。")

    session = sm()
    try:
        stmt = (
            select(Ticket, Flight, BoardingPass, TicketFlight)
            .join(TicketFlight, Ticket.ticket_no == TicketFlight.ticket_no)
            .join(Flight, TicketFlight.flight_id == Flight.flight_id)
            .join(BoardingPass, (BoardingPass.ticket_no == Ticket.ticket_no) & (BoardingPass.flight_id == Flight.flight_id))
            .where(Ticket.passenger_id == passenger_id)
        )
        rows = session.execute(stmt).all()
        results = []
        for t, f, bp, tf in rows:
            results.append({
                "ticket_no": t.ticket_no,
                "book_ref": t.book_ref,
                "flight_id": f.flight_id,
                "flight_no": f.flight_no,
                "departure_airport": f.departure_airport,
                "arrival_airport": f.arrival_airport,
                "scheduled_departure": f.scheduled_departure,
                "scheduled_arrival": f.scheduled_arrival,
                "seat_no": bp.seat_no,
                "fare_conditions": tf.fare_conditions,
            })
        return results
    finally:
        session.close()


@tool
def search_flights(
    departure_airport: Optional[str] = None,
    arrival_airport: Optional[str] = None,
    start_time: Optional[date | datetime] = None,
    end_time: Optional[date | datetime] = None,
    limit: int = 20,
) -> list[dict]:
    """按出发/到达机场和时间范围搜索航班。"""
    session = sm()
    try:
        stmt = select(Flight)
        if departure_airport:
            stmt = stmt.where(Flight.departure_airport == departure_airport)
        if arrival_airport:
            stmt = stmt.where(Flight.arrival_airport == arrival_airport)
        if start_time:
            stmt = stmt.where(Flight.scheduled_departure >= start_time)
        if end_time:
            stmt = stmt.where(Flight.scheduled_departure <= end_time)
        stmt = stmt.limit(limit)
        flights = session.execute(stmt).scalars().all()
        return [row_to_dict(f) for f in flights]
    finally:
        session.close()


@tool
def update_ticket_to_new_flight(ticket_no: str, new_flight_id: int, *, config: RunnableConfig) -> str:
    """改签机票到新航班。验证乘客身份和起飞前3小时限制。"""
    passenger_id = config.get("configurable", {}).get("passenger_id", None)
    if not passenger_id:
        raise ValueError("未配置乘客 ID。")

    session = sm()
    try:
        new_flight = session.get(Flight, new_flight_id)
        if not new_flight:
            return "提供的新的航班 ID 无效。"

        # 起飞前3小时检查
        timezone = pytz.timezone("Etc/GMT-3")
        current_time = datetime.now(tz=timezone)
        departure_time = datetime.strptime(new_flight.scheduled_departure, "%Y-%m-%d %H:%M:%S.%f%z")
        if (departure_time - current_time).total_seconds() < 3 * 3600:
            return f"不允许重新安排到距离当前时间少于 3 小时的航班。所选航班时间为 {departure_time}。"

        # 确认机票存在
        tf = session.get(TicketFlight, (ticket_no, new_flight_id))
        current_tf = session.execute(
            select(TicketFlight).where(TicketFlight.ticket_no == ticket_no)
        ).scalar_one_or_none()
        if not current_tf:
            return "未找到给定机票号码的现有机票。"

        # 确认乘客拥有此机票
        ticket = session.execute(
            select(Ticket).where(Ticket.ticket_no == ticket_no, Ticket.passenger_id == passenger_id)
        ).scalar_one_or_none()
        if not ticket:
            return f"当前登录的乘客 ID 为 {passenger_id}，不是机票 {ticket_no} 的拥有者。"

        # 更新
        current_tf.flight_id = new_flight_id
        session.commit()
        return "机票已成功更新为新的航班。"
    finally:
        session.close()


@tool
def cancel_ticket(ticket_no: str, *, config: RunnableConfig) -> str:
    """取消机票。验证乘客身份后删除。"""
    passenger_id = config.get("configurable", {}).get("passenger_id", None)
    if not passenger_id:
        raise ValueError("未配置乘客 ID。")

    session = sm()
    try:
        tf = session.execute(
            select(TicketFlight).where(TicketFlight.ticket_no == ticket_no)
        ).scalar_one_or_none()
        if not tf:
            return "未找到给定机票号码的现有机票。"

        ticket = session.execute(
            select(Ticket).where(Ticket.ticket_no == ticket_no, Ticket.passenger_id == passenger_id)
        ).scalar_one_or_none()
        if not ticket:
            return f"当前登录的乘客 ID 为 {passenger_id}，不是机票 {ticket_no} 的拥有者。"

        session.delete(tf)
        session.commit()
        return "机票已成功取消。"
    finally:
        session.close()
