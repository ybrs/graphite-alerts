import logging
from sqlalchemy import BigInteger, Column, ForeignKey, Unicode, UnicodeText
from orm import Base, TimestampMixin
logger = logging.getLogger(__name__)

class Dashboard(TimestampMixin, Base):
    __tablename__ = 'dashboards'
    user_id  = Column(BigInteger)
    title = Column(Unicode(254))
    ob = Column(BigInteger)



