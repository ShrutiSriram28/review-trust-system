from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    facility_type: Mapped[str] = mapped_column(String(100), nullable=False)

    location: Mapped[str] = mapped_column(String(255), nullable=False)

    # Price is usually $, $$, $$$, ...
    price: Mapped[str] = mapped_column(String(20), nullable=False)

    reviews: Mapped[list["Review"]] = relationship(
        back_populates="business",
        cascade="all, delete-orphan",
    )


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False,
    )

    review: Mapped[str] = mapped_column(Text, nullable=False)

    rating: Mapped[float] = mapped_column(Float, nullable=False)

    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    business: Mapped["Business"] = relationship(
        back_populates="reviews",
    )

    __table_args__ = (
        UniqueConstraint(
            "business_id",
            # "review", ## too long to be stored
            "published_at",
            name="uq_review",
        ),
    )