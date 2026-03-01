import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import create_engine, String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "./recipes.db")

# ── Predefined allowlists ─────────────────────────────────────────────────────

CATEGORIES = [
    "Uncategorized",
    "Pasta",
    "Chicken",
    "Beef",
    "Seafood",
    "Vegetarian",
    "Dessert",
    "Breakfast",
    "Soup",
    "Salad",
    "Snack",
    "Other",
]

MOODS = [
    "None",
    "Quick",
    "Date Night",
    "Healthy",
    "Comfort Food",
    "Fancy",
    "Lazy Day",
    "Meal Prep",
]

# ── ORM ───────────────────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    pass


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    shortcode: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, default="Uncategorized")
    mood: Mapped[str] = mapped_column(String, default="None")
    date_added: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "url": self.url,
            "shortcode": self.shortcode,
            "category": self.category,
            "mood": self.mood,
            "date_added": self.date_added.isoformat(),
        }


# ── Engine & session ──────────────────────────────────────────────────────────


def get_engine():
    engine = create_engine(
        f"sqlite:///{DB_PATH}",
        connect_args={"check_same_thread": False},
    )
    # Enable WAL mode for concurrent bot + web access
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode=WAL")
    return engine


_engine = get_engine()
_SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)


def get_session():
    """Return a SQLAlchemy session as a context manager."""
    return _SessionLocal()


def init_db():
    """Create all tables if they don't exist. Safe to call multiple times."""
    Base.metadata.create_all(_engine)
