# 数据库持久化配置说明

## 📊 数据库持久性问题

根据不同的部署方式，数据库的持久性会有所不同：

### 🏠 本地开发环境
- **数据库文件**: `vocabulary.db`（项目根目录）
- **持久性**: ✅ 永久保存，除非手动删除
- **配置**: 无需额外配置

### 🐳 Docker部署
- **默认情况**: ❌ 容器重启后数据丢失
- **解决方案**: ✅ 使用数据卷挂载

#### Docker数据持久化配置

1. **使用docker-compose（推荐）**:
```bash
# 启动服务
docker-compose up -d

# 数据会保存在 ./data 目录中
# 即使容器重启，数据也不会丢失
```

2. **手动Docker运行**:
```bash
# 创建数据目录
mkdir -p ./data

# 运行容器并挂载数据卷
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -e DATABASE_URL=sqlite:///data/vocabulary.db \
  your-app-name
```

### ☁️ 云平台部署

#### 方案1: 使用云数据库（推荐）
```env
# PostgreSQL示例
DATABASE_URL=postgresql://username:password@host:port/database

# MySQL示例  
DATABASE_URL=mysql://username:password@host:port/database
```

#### 方案2: 使用持久化存储
- **Railway**: 自动提供持久化存储
- **Render**: 支持持久化磁盘
- **DigitalOcean**: 使用Volume挂载

## 🔧 配置步骤

### 1. 本地开发
无需额外配置，数据自动保存在 `vocabulary.db` 文件中。

### 2. Docker部署
```bash
# 1. 确保docker-compose.yml已更新
# 2. 创建数据目录
mkdir -p data

# 3. 启动服务
docker-compose up -d

# 4. 检查数据目录
ls -la data/  # 应该看到 vocabulary.db 文件
```

### 3. 云数据库配置
```env
# 在 .env 文件中配置云数据库
DATABASE_URL=postgresql://user:pass@host:5432/vocab_db
```

## 📁 数据目录结构

```
项目根目录/
├── data/                    # 数据目录（Docker挂载）
│   └── vocabulary.db       # SQLite数据库文件
├── vocabulary.db           # 本地开发数据库文件
└── docker-compose.yml      # Docker配置
```

## 🔍 数据备份建议

### 自动备份脚本
```bash
#!/bin/bash
# backup_vocab.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"
DB_FILE="./data/vocabulary.db"  # 或 ./vocabulary.db

mkdir -p $BACKUP_DIR
cp $DB_FILE "$BACKUP_DIR/vocabulary_backup_$DATE.db"
echo "数据库备份完成: vocabulary_backup_$DATE.db"

# 保留最近7天的备份
find $BACKUP_DIR -name "vocabulary_backup_*.db" -mtime +7 -delete
```

### 定期备份（crontab）
```bash
# 每天凌晨2点自动备份
0 2 * * * /path/to/backup_vocab.sh
```

## ⚠️ 重要提醒

1. **生产环境建议**: 使用PostgreSQL等专业数据库
2. **定期备份**: 无论使用哪种方案，都要定期备份数据
3. **测试恢复**: 定期测试备份文件是否可以正常恢复
4. **监控空间**: 注意数据库文件大小，避免磁盘空间不足

## 🚀 快速检查数据持久性

```bash
# 检查数据库文件是否存在
ls -la vocabulary.db  # 本地开发
ls -la data/vocabulary.db  # Docker部署

# 检查数据库内容
sqlite3 vocabulary.db ".tables"  # 查看表结构
sqlite3 vocabulary.db "SELECT COUNT(*) FROM vocabulary;"  # 查看词汇数量
``` 