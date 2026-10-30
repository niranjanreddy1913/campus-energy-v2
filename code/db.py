"""db.py — where the readings are kept: one SQLite file, readings.db, next to this file, with one table.
SQLAlchemy describes the table as a Python class, so the rest of the code works with objects, not SQL strings."""
from datetime import datetime
from pathlib import Path

from sqlalchemy import DateTime, Float, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DB_FILE = Path(__file__).resolve().parent / "readings.db"      # next to this file, whichever folder you run from
engine = create_engine(f"sqlite:///{DB_FILE}")
Session = sessionmaker(engine)


class Base(DeclarativeBase):
    pass


class Reading(Base):
    """One 15-minute reading of the campus substation. The time is the key: there can't be two readings for one moment."""
    __tablename__ = "readings"
    timestamp: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
    load_kw: Mapped[float] = mapped_column(Float)             # what the whole campus uses
    solar_kw: Mapped[float] = mapped_column(Float)            # what the rooftop solar makes
    ambient_c: Mapped[float] = mapped_column(Float)           # air temperature
    irradiance_wm2: Mapped[float] = mapped_column(Float)      # sunlight on the panels


Base.metadata.create_all(engine)                              # create the table the first time; does nothing after that
