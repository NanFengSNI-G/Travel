from datetime import date, datetime
from typing import Optional, Union

from langchain_core.tools import tool
from sqlalchemy import select

from app.models import sm, row_to_dict
from app.models.business import CarRental


@tool
def search_car_rentals(
    location: Optional[str] = None,
    name: Optional[str] = None,
) -> list[dict]:
    """按位置和名称搜索租车服务。"""
    session = sm()
    try:
        stmt = select(CarRental)
        if location:
            stmt = stmt.where(CarRental.location.like(f"%{location}%"))
        if name:
            stmt = stmt.where(CarRental.name.like(f"%{name}%"))
        cars = session.execute(stmt).scalars().all()
        return [row_to_dict(c) for c in cars]
    finally:
        session.close()


@tool
def book_car_rental(rental_id: int) -> str:
    """预订租车。"""
    session = sm()
    try:
        car = session.get(CarRental, rental_id)
        if not car:
            return f"未找到ID为 {rental_id} 的汽车租赁服务。"
        car.booked = 1
        session.commit()
        return f"汽车租赁 {rental_id} 成功预订。"
    finally:
        session.close()


@tool
def update_car_rental(
    rental_id: int,
    start_date: Optional[Union[datetime, date]] = None,
    end_date: Optional[Union[datetime, date]] = None,
) -> str:
    """更新租车预订的起止日期。"""
    session = sm()
    try:
        car = session.get(CarRental, rental_id)
        if not car:
            return f"未找到ID为 {rental_id} 的汽车租赁服务。"
        if start_date:
            car.start_date = str(start_date)
        if end_date:
            car.end_date = str(end_date)
        session.commit()
        return f"汽车租赁 {rental_id} 成功更新。"
    finally:
        session.close()


@tool
def cancel_car_rental(rental_id: int) -> str:
    """取消租车预订。"""
    session = sm()
    try:
        car = session.get(CarRental, rental_id)
        if not car:
            return f"未找到ID为 {rental_id} 的汽车租赁服务。"
        car.booked = 0
        session.commit()
        return f"汽车租赁 {rental_id} 成功取消。"
    finally:
        session.close()
