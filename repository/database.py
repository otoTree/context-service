"""数据库连接管理模块"""
import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool


class Base(DeclarativeBase):
    """SQLAlchemy Base类"""
    pass


class DatabaseManager:
    """数据库连接管理器"""
    
    def __init__(self):
        self._engine = None
        self._session_factory = None
    
    def get_database_url(self) -> str:
        """从环境变量获取数据库连接URL"""
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "context_service")
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "postgres")
        
        return f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    def initialize(self) -> None:
        """初始化数据库连接"""
        database_url = self.get_database_url()
        
        self._engine = create_async_engine(
            database_url,
            poolclass=NullPool,
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
            future=True
        )
        
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话"""
        if not self._session_factory:
            raise RuntimeError("数据库未初始化，请先调用 initialize() 方法")
        
        async with self._session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self) -> None:
        """关闭数据库连接"""
        if self._engine:
            await self._engine.dispose()


# 全局数据库管理器实例
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的便捷函数"""
    async for session in db_manager.get_session():
        yield session


async def init_database() -> None:
    """初始化数据库连接"""
    db_manager.initialize()


async def close_database() -> None:
    """关闭数据库连接"""
    await db_manager.close() 