from typing import Optional, List

from langchain_core.tools import tool
from sqlalchemy import select

from app.models import sm, row_to_dict
from app.models.business import TripRecommendation


@tool
def search_trip_recommendations(
    location: Optional[str] = None,
    name: Optional[str] = None,
    keywords: Optional[str] = None,
) -> List[dict]:
    """按位置、名称和关键词搜索旅行推荐。"""
    session = sm()
    try:
        stmt = select(TripRecommendation)
        if location:
            stmt = stmt.where(TripRecommendation.location.like(f"%{location}%"))
        if name:
            stmt = stmt.where(TripRecommendation.name.like(f"%{name}%"))
        if keywords:
            for kw in keywords.split(","):
                stmt = stmt.where(TripRecommendation.keywords.like(f"%{kw.strip()}%"))
        trips = session.execute(stmt).scalars().all()
        return [row_to_dict(t) for t in trips]
    finally:
        session.close()


@tool
def book_excursion(recommendation_id: int) -> str:
    """预订旅行推荐。"""
    session = sm()
    try:
        trip = session.get(TripRecommendation, recommendation_id)
        if not trip:
            return f"未找到ID为 {recommendation_id} 的旅行推荐。"
        trip.booked = 1
        session.commit()
        return f"旅行推荐 {recommendation_id} 成功预定。"
    finally:
        session.close()


@tool
def update_excursion(recommendation_id: int, details: str) -> str:
    """更新旅行推荐的详细信息。"""
    session = sm()
    try:
        trip = session.get(TripRecommendation, recommendation_id)
        if not trip:
            return f"未找到ID为 {recommendation_id} 的旅行推荐。"
        trip.details = details
        session.commit()
        return f"旅行推荐 {recommendation_id} 成功更新。"
    finally:
        session.close()


@tool
def cancel_excursion(recommendation_id: int) -> str:
    """取消旅行推荐。"""
    session = sm()
    try:
        trip = session.get(TripRecommendation, recommendation_id)
        if not trip:
            return f"未找到ID为 {recommendation_id} 的旅行推荐。"
        trip.booked = 0
        session.commit()
        return f"旅行推荐 {recommendation_id} 成功取消。"
    finally:
        session.close()
