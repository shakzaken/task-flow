from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

AsyncSessionFactory = async_sessionmaker[AsyncSession]

_ENGINE_CACHE: dict[str, AsyncEngine] = {}
_SESSION_FACTORY_CACHE: dict[str, AsyncSessionFactory] = {}


def get_engine(database_url: str) -> AsyncEngine:
    if database_url not in _ENGINE_CACHE:
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        _ENGINE_CACHE[database_url] = create_async_engine(
            database_url,
            future=True,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
    return _ENGINE_CACHE[database_url]


def get_session_factory(database_url: str) -> AsyncSessionFactory:
    if database_url not in _SESSION_FACTORY_CACHE:
        engine = get_engine(database_url)
        _SESSION_FACTORY_CACHE[database_url] = async_sessionmaker(
            bind=engine,
            autoflush=False,
            expire_on_commit=False,
            class_=AsyncSession,
        )
    return _SESSION_FACTORY_CACHE[database_url]
