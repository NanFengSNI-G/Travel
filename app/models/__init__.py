from datetime import datetime

from sqlalchemy import URL, create_engine, DateTime, func
from sqlalchemy.orm import sessionmaker, DeclarativeBase, declared_attr, Mapped, mapped_column

from app.core.config import settings

url = URL(
    drivername=settings.DATABASE.DRIVER,
    username=settings.DATABASE.get("USERNAME", None),
    password=settings.DATABASE.get("PASSWORD", None),
    host=settings.DATABASE.get("HOST", None),
    port=settings.DATABASE.get("PORT", None),
    database=settings.DATABASE.get("NAME", None),
    query=settings.DATABASE.get("QUERY", None),
)

engine = create_engine(url, echo=False, pool_size=10)
sm = sessionmaker(bind=engine, autoflush=True)


class Base(DeclarativeBase):
    """业务表基类"""
    __table_args__ = {"mysql_engine": "InnoDB"}


class DBModelBase(Base):
    """用户/系统表基类 — 自动 t_ 前缀 + id/create_time/update_time"""

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "t_" + cls.__name__.lower()

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    create_time: Mapped[datetime] = mapped_column(DateTime, insert_default=func.now(), comment="创建时间")
    update_time: Mapped[datetime] = mapped_column(
        DateTime, insert_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


def row_to_dict(row) -> dict:
    """SQLAlchemy 对象 → 字典"""
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}
