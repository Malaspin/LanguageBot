from sqlalchemy.orm import Session, sessionmaker
from config import sync_engine
from database.model_db import Base

__sessionmaker = sessionmaker(
        sync_engine,
        class_= Session
    )

def create_table():
    Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)

