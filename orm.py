import logging
import traceback
from datetime import datetime, timedelta

from sqlalchemy import Column, BigInteger, create_engine, DateTime, func, Integer
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text
from sqlalchemy.orm import sessionmaker, scoped_session, Query
from sqlalchemy.orm.exc import ObjectDeletedError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_method
from flask import _app_ctx_stack
logger = logging.getLogger(__name__)


class CustomQuery(Query):

    def chunked_all(self, count, commit=False,
                    skip_errors=False, expunge_all=True):
        """Bring objects in chunks from database.

        :param count: chunk size
        :param commit: commit session after fetching each chunk.
        :param skip_errors: if commit() raises error, skip them.
        :param expunge_all: expunge object after yielding it. This is
            required for objects to be removed session after each iteration.
            If False, objects will remain in session and be sent
            back and forth between client and database that will
            eventually cause slowdown.

        """
        if skip_errors:
            assert commit

        last_id = 0
        while True:
            logger.debug('last_id: %s' % last_id)
            query = self.filter('id>%s' % last_id).order_by("id asc")
            objects = query.limit(count).all()
            if not objects:
                break

            for object in objects:
                try:
                    last_id = object.id
                except ObjectDeletedError:
                    self.session.rollback()
                    last_id += 1
                else:
                    yield object

            if commit:
                if skip_errors:
                    try:
                        self.session.commit()
                    except:
                        self.session.rollback()
                        logger.warning(traceback.format_exc())
                else:
                    self.session.commit()

            if expunge_all:
                self.session.expunge_all()

#uri = 'mysql://%s:%s@%s/%s?charset=utf8&use_unicode=1' % (
#    config.MYSQL_USER,
#    config.MYSQL_PASSWD,
#    config.MYSQL_HOST,
#    config.MYSQL_DB)

uri = 'sqlite:///test.db'

engine = create_engine(uri, echo=False)
Session = sessionmaker(
    bind=engine,
    query_cls=CustomQuery,
    autoflush=True,  # herhangi bir query yapmadan once flush yapar
    autocommit=False,  # True cok tehlikeli
    expire_on_commit=True)  # commit yapildiktan sonra objenin attribute'lerini expire eder. erisim olursa select yapip tekrar ceker.
session = scoped_session(Session, scopefunc=_app_ctx_stack.__ident_func__)


def _get_date():
    return datetime.utcnow()


class TimestampMixin(object):

    created_at = Column(DateTime, default=_get_date)
    updated_at = Column(DateTime, default=_get_date, onupdate=_get_date)

    def touch(self):
        self.update({'updated_at': _get_date()})
    
    @hybrid_method
    def is_stuck(self, mins=10):
        """Is the record has not been updated in last 'mins' minutes?"""
        if not self.updated_at:
            return True
        diff = datetime.utcnow() - self.updated_at
        return diff > timedelta(minutes=mins)

    @is_stuck.expression
    def is_stuck(self, mins=10):
        diff = func.timestampdiff(text('minute'),
                                  self.updated_at, func.utc_timestamp())
        return (self.updated_at == None) | (diff > mins)


class Base(object):
    __table_args__ = {'mysql_engine': 'InnoDB', 'sqlite_autoincrement': True}
    
    id = Column(Integer, primary_key=True)

    # default session is scoped session
    query = session.query_property()

    @property
    def session(self):
        """Return this object's session"""
        return Session.object_session(self)

    def __repr__(self):
        try:
            id = self.id
        except SQLAlchemyError:
            id = 'Unknown'

        return '<%s id=%r>' % (self.__class__.__name__, id)
                
    @classmethod
    def count(cls, expr=None):
        q = session.query(func.count('*'))
        if expr is not None:
            q = q.filter(expr)
        return q.scalar() or 0

    @classmethod
    def get(cls, id):
        """Shortcut for Model.query.get()"""
        return cls.query.get(id)
    
    def save(self, commit=True):
        session.add(self)
        if commit:
            session.commit()
    
    def update(self, update_dict, commit=True, where=None, _session=None):
        if update_dict:
            __session = _session if _session else session

            # id olmadan update gonderince sacmalamasin
            if not self.id:
                __session.add(self)
                __session.flush()

            cls = self.__class__
            
            query = __session.query(cls).filter(cls.id == self.id)
            
            if where:
                query = query.filter_by(**where)

            query.update(update_dict)

            __session.add(self)
            if commit:
                __session.commit()
    
    def delete(self, commit=True):
        session.delete(self)
        if commit:
            session.commit()
    
    def to_dict(self, *fields):
        '''Returns model as dict. If fields is given, returns only given fields.
        If you want to change the field name in returned dict,
        give a tuple like ('real_field_name', 'wanted_field_name') instead of str.'''
        d = {}
        keys = self.__table__.columns.keys()
        if fields:
            keys = fields
            
        for columnName in keys:
            if isinstance(columnName, tuple):
                d[columnName[1]] = getattr(self, columnName[0])
            else:
                d[columnName] = getattr(self, columnName)
        return d
    
    def from_dict(self, d):
        for columnName in d.keys():
            setattr(self, columnName, d[columnName])

Base = declarative_base(bind=engine, cls=Base)
