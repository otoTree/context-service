#!/usr/bin/env python3
"""数据库连接和基本功能测试"""
import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from repository.database import DatabaseManager


async def test_database_connection():
    """测试数据库连接"""
    print("测试数据库连接...")
    
    # 设置测试环境变量
    os.environ.setdefault("DB_HOST", "localhost")
    os.environ.setdefault("DB_PORT", "5432")
    os.environ.setdefault("DB_NAME", "context_service_test")
    os.environ.setdefault("DB_USER", "postgres")
    os.environ.setdefault("DB_PASSWORD", "postgres")
    
    db_manager = DatabaseManager()
    
    try:
        print("初始化数据库连接...")
        db_manager.initialize()
        
        print("测试数据库会话...")
        async for session in db_manager.get_session():
            from sqlalchemy import text
            result = await session.execute(text("SELECT version()"))
            version = result.fetchone()
            print(f"✅ 数据库连接成功！PostgreSQL版本: {version[0] if version else 'Unknown'}")
            break
            
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {e}")
        return False
    finally:
        await db_manager.close()
    
    return True


async def test_database_url_generation():
    """测试数据库URL生成"""
    print("\n测试数据库URL生成...")
    
    # 设置测试环境变量
    os.environ.setdefault("DB_HOST", "localhost")
    os.environ.setdefault("DB_PORT", "5432")
    os.environ.setdefault("DB_NAME", "context_service_test")
    os.environ.setdefault("DB_USER", "postgres")
    os.environ.setdefault("DB_PASSWORD", "postgres")
    
    db_manager = DatabaseManager()
    url = db_manager.get_database_url()
    print(f"数据库URL: {url}")
    
    # 验证URL格式
    expected_parts = ["postgresql+asyncpg://", "localhost", "5432", "context_service_test"]
    for part in expected_parts:
        if part not in url:
            print(f"❌ URL格式错误，缺少: {part}")
            return False
    
    print("✅ 数据库URL生成正确")
    return True


async def main():
    """主测试函数"""
    print("=== Context Service 数据库测试 ===\n")
    
    # 测试URL生成
    if not await test_database_url_generation():
        sys.exit(1)
    
    # 测试数据库连接
    if await test_database_connection():
        print("\n✅ 所有数据库测试通过！")
    else:
        print("\n❌ 数据库连接测试失败")
        print("\n注意: 如果您没有运行PostgreSQL，这是正常的。")
        print("要运行完整测试，请:")
        print("1. 启动 PostgreSQL 服务")
        print("2. 创建测试数据库: createdb context_service_test")
        print("3. 重新运行此脚本")


if __name__ == "__main__":
    asyncio.run(main()) 