from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

SessionFactory = sessionmaker[Session]

_ENGINE_CACHE: dict[tuple[str, int, int], Engine] = {}
_SESSION_FACTORY_CACHE: dict[tuple[str, int, int], SessionFactory] = {}


def get_engine(database_url: str, pool_size: int = 4, max_overflow: int = 2) -> Engine:
    cache_key = (database_url, pool_size, max_overflow)
    if cache_key not in _ENGINE_CACHE:
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        engine_kwargs = {
            "future": True,
            "pool_pre_ping": True,
            "connect_args": connect_args,
        }
        if not database_url.startswith("sqlite"):
            engine_kwargs["pool_size"] = pool_size
            engine_kwargs["max_overflow"] = max_overflow
        _ENGINE_CACHE[cache_key] = create_engine(database_url, **engine_kwargs)
    return _ENGINE_CACHE[cache_key]


def get_session_factory(database_url: str, pool_size: int = 4, max_overflow: int = 2) -> SessionFactory:
    cache_key = (database_url, pool_size, max_overflow)
    if cache_key not in _SESSION_FACTORY_CACHE:
        engine = get_engine(database_url, pool_size=pool_size, max_overflow=max_overflow)
        _SESSION_FACTORY_CACHE[cache_key] = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return _SESSION_FACTORY_CACHE[cache_key]
