from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import settings
from database.models import Base

# Create engine with appropriate settings
if settings.database_url.startswith('sqlite'):
    # SQLite specific settings
    engine = create_async_engine(
        settings.database_url,
        echo=True,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL settings
    engine = create_async_engine(settings.database_url, echo=True)

async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Get database session"""
    async with async_session_maker() as session:
        yield session
