from collections.abc import Callable

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

SessionFactory = Callable[[], Session]

_ENGINE_CACHE: dict[str, Engine] = {}
_SESSION_FACTORY_CACHE: dict[str, sessionmaker[Session]] = {}


def get_engine(database_url: str) -> Engine:
    if database_url not in _ENGINE_CACHE:
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        _ENGINE_CACHE[database_url] = create_engine(
            database_url,
            future=True,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
    return _ENGINE_CACHE[database_url]


def get_session_factory(database_url: str) -> sessionmaker[Session]:
    if database_url not in _SESSION_FACTORY_CACHE:
        engine = get_engine(database_url)
        _SESSION_FACTORY_CACHE[database_url] = sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            class_=Session,
        )
    return _SESSION_FACTORY_CACHE[database_url]

