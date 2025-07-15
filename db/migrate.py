#!/usr/bin/env python3
"""数据库迁移执行脚本"""
import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from repository.database import DatabaseManager


def get_alembic_config() -> Config:
    """获取Alembic配置"""
    # 获取alembic.ini文件路径
    alembic_ini_path = Path(__file__).parent / "alembic.ini"
    
    if not alembic_ini_path.exists():
        raise FileNotFoundError(f"找不到 alembic.ini 文件: {alembic_ini_path}")
    
    config = Config(str(alembic_ini_path))
    return config


async def check_database_connection():
    """检查数据库连接"""
    print("检查数据库连接...")
    db_manager = DatabaseManager()
    
    try:
        db_manager.initialize()
        async for session in db_manager.get_session():
            # 执行一个简单的查询来测试连接
            result = await session.execute(text("SELECT 1"))
            result.fetchone()
            print("✅ 数据库连接成功")
            break
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("\n请确保:")
        print("1. PostgreSQL 服务正在运行")
        print("2. 数据库连接参数正确 (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)")
        print("3. 目标数据库已存在")
        sys.exit(1)
    finally:
        await db_manager.close()


def upgrade_database():
    """执行数据库升级迁移"""
    print("执行数据库迁移...")
    config = get_alembic_config()
    
    try:
        command.upgrade(config, "head")
        print("✅ 数据库迁移成功完成")
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        sys.exit(1)


def downgrade_database(revision: str = "-1"):
    """执行数据库降级迁移"""
    print(f"执行数据库回滚到版本: {revision}")
    config = get_alembic_config()
    
    try:
        command.downgrade(config, revision)
        print("✅ 数据库回滚成功完成")
    except Exception as e:
        print(f"❌ 数据库回滚失败: {e}")
        sys.exit(1)


def show_current_revision():
    """显示当前数据库版本"""
    config = get_alembic_config()
    
    try:
        command.current(config)
    except Exception as e:
        print(f"❌ 获取当前版本失败: {e}")
        sys.exit(1)


def show_migration_history():
    """显示迁移历史"""
    config = get_alembic_config()
    
    try:
        command.history(config)
    except Exception as e:
        print(f"❌ 获取迁移历史失败: {e}")
        sys.exit(1)


async def init_database():
    """初始化数据库（创建所有表）"""
    print("初始化数据库...")
    
    # 首先检查连接
    await check_database_connection()
    
    # 执行迁移
    upgrade_database()


def print_usage():
    """打印使用说明"""
    print("数据库迁移工具使用说明:")
    print("  python db/migrate.py init          - 初始化数据库")
    print("  python db/migrate.py upgrade       - 升级到最新版本")
    print("  python db/migrate.py downgrade [n] - 回滚n个版本(默认1个)")
    print("  python db/migrate.py current       - 显示当前版本")
    print("  python db/migrate.py history       - 显示迁移历史")
    print("  python db/migrate.py check         - 检查数据库连接")


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print_usage()
        return
    
    command_name = sys.argv[1].lower()
    
    if command_name == "init":
        await init_database()
    elif command_name == "upgrade":
        await check_database_connection()
        upgrade_database()
    elif command_name == "downgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "-1"
        await check_database_connection()
        downgrade_database(revision)
    elif command_name == "current":
        show_current_revision()
    elif command_name == "history":
        show_migration_history()
    elif command_name == "check":
        await check_database_connection()
    else:
        print(f"未知命令: {command_name}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    # 设置环境变量默认值（开发环境）
    if not os.getenv("DB_HOST"):
        os.environ.setdefault("DB_HOST", "localhost")
        os.environ.setdefault("DB_PORT", "5432")
        os.environ.setdefault("DB_NAME", "context_service")
        os.environ.setdefault("DB_USER", "postgres")
        os.environ.setdefault("DB_PASSWORD", "postgres")
    
    asyncio.run(main()) 