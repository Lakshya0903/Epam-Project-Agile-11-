from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

import os
import shutil

# Backward-compatibility check: migrate legacy farm2market.db to farmcart.db if needed
if settings.database_url.startswith("sqlite"):
    raw_path = settings.database_url.replace("sqlite:///", "")
    # Normalize path relative to working directory or file
    if not os.path.isabs(raw_path):
        raw_path = os.path.abspath(raw_path)
    if not os.path.exists(raw_path):
        db_dir = os.path.dirname(raw_path)
        legacy_path = os.path.join(db_dir, "farm2market.db")
        if os.path.exists(legacy_path):
            shutil.copy2(legacy_path, raw_path)

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
