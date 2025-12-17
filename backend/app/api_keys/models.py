from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql.expression import text

from ..database import Base


class ApiKey(Base):
    __tablename__ = "api_key"

    id = Column(Integer, primary_key=True, nullable=False)
    apiKey_id = Column(String(255), unique=True, nullable=False)
    apiKey = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
