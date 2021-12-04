from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import session, sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@database-1.crbz1kwmx22c.us-east-1.rds.amazonaws.com:5432"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

session = SessionLocal()

Base = declarative_base()