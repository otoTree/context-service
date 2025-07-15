# 数据库配置说明

## 环境变量配置

在运行数据库迁移之前，请设置以下环境变量：

```bash
# 数据库配置
export DB_HOST=localhost
export DB_PORT=5432  
export DB_NAME=context_service
export DB_USER=postgres
export DB_PASSWORD=postgres
export DB_ECHO=false  # 是否打印SQL日志
```

## 使用说明

### 1. 初始化数据库

首次使用时，执行以下命令初始化数据库：

```bash
python db/migrate.py init
```

### 2. 其他命令

```bash
# 检查数据库连接
python db/migrate.py check

# 升级到最新版本
python db/migrate.py upgrade

# 回滚一个版本
python db/migrate.py downgrade

# 显示当前版本
python db/migrate.py current

# 显示迁移历史
python db/migrate.py history
```

## 数据库表结构

数据库包含以下主要表：

- `event_queue` - 任务调度缓冲池
- `agents` - Agent元数据注册表
- `tasks` - 任务存储表
- `task_slices` - 任务切片表
- `tools` - 工具注册表
- `tool_keywords` - 工具关键词表
- `task_results` - 任务结果存储表
- `review_records` - 结果评估记录表

详细的表结构定义请参考 `doc/database_schema.md`。

## 开发环境快速启动

1. 安装 PostgreSQL 并启动服务
2. 创建数据库：`createdb context_service`
3. 设置环境变量（可选，脚本有默认值）
4. 执行初始化：`python db/migrate.py init` 