from datetime import date, datetime
from typing import Optional, Union

from langchain_core.tools import tool
from sqlalchemy import select

from app.models import sm, row_to_dict
from app.models.business import Hotel


@tool
def search_hotels(
    location: Optional[str] = None,
    name: Optional[str] = None,
) -> list[dict]:
    """按位置和名称搜索酒店。"""
    session = sm()
    try:
        stmt = select(Hotel)
        if location:
            stmt = stmt.where(Hotel.location.like(f"%{location}%"))
        if name:
            stmt = stmt.where(Hotel.name.like(f"%{name}%"))
        hotels = session.execute(stmt).scalars().all()
        return [row_to_dict(h) for h in hotels]
    finally:
        session.close()


@tool
def book_hotel(hotel_id: int) -> str:
    """预订酒店。"""
    session = sm()
    try:
        hotel = session.get(Hotel, hotel_id)
        if not hotel:
            return f"未找到ID为 {hotel_id} 的酒店。"
        hotel.booked = 1
        session.commit()
        return f"Hotel {hotel_id} 成功预定。"
    finally:
        session.close()


@tool
def update_hotel(
    hotel_id: int,
    checkin_date: Optional[Union[datetime, date]] = None,
    checkout_date: Optional[Union[datetime, date]] = None,
) -> str:
    """更新酒店预订的入住/退房日期。"""
    session = sm()
    try:
        hotel = session.get(Hotel, hotel_id)
        if not hotel:
            return f"未找到ID为 {hotel_id} 的酒店。"
        if checkin_date:
            hotel.checkin_date = str(checkin_date)
        if checkout_date:
            hotel.checkout_date = str(checkout_date)
        session.commit()
        return f"Hotel {hotel_id} 成功更新。"
    finally:
        session.close()


@tool
def cancel_hotel(hotel_id: int) -> str:
    """取消酒店预订。"""
    session = sm()
    try:
        hotel = session.get(Hotel, hotel_id)
        if not hotel:
            return f"未找到ID为 {hotel_id} 的酒店。"
        hotel.booked = 0
        session.commit()
        return f"Hotel {hotel_id} 成功取消。"
    finally:
        session.close()
