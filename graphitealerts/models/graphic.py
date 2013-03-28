import logging
from sqlalchemy import BigInteger, Column, ForeignKey, Unicode, UnicodeText
from orm import Base, TimestampMixin
logger = logging.getLogger(__name__)

class Graphic(TimestampMixin, Base):
    __tablename__ = 'graphics'
    user_id  = Column(BigInteger)
    title = Column(Unicode(254))
    source = Column(UnicodeText)
    url = Column(UnicodeText)
    dashboard_id = Column(BigInteger)
    width = Column(BigInteger)
    height = Column(BigInteger)
    from_ = Column(UnicodeText)
    ob = Column(BigInteger)



