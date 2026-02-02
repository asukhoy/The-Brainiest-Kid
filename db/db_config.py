from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, \
    async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config import conn_string


engine = create_async_engine(
    conn_string,
    echo=True
)

session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def init_db():
    print("Initializing DB")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    if session_factory is None:
        await init_db()

    async with session_factory() as session:
        yield session


async def close_db():
    if engine:
        await engine.dispose()