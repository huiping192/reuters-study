#!/bin/bash
# 词汇数据库备份脚本

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"

# 检测数据库文件位置
if [ -f "./data/vocabulary.db" ]; then
    DB_FILE="./data/vocabulary.db"
    echo "发现Docker部署数据库文件"
elif [ -f "./vocabulary.db" ]; then
    DB_FILE="./vocabulary.db"
    echo "发现本地开发数据库文件"
else
    echo "❌ 未找到数据库文件！"
    echo "请检查以下位置："
    echo "  - ./vocabulary.db (本地开发)"
    echo "  - ./data/vocabulary.db (Docker部署)"
    exit 1
fi

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
cp $DB_FILE "$BACKUP_DIR/vocabulary_backup_$DATE.db"

if [ $? -eq 0 ]; then
    echo "✅ 数据库备份完成: vocabulary_backup_$DATE.db"
    
    # 显示备份文件大小
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/vocabulary_backup_$DATE.db" | cut -f1)
    echo "📁 备份文件大小: $BACKUP_SIZE"
    
    # 显示词汇数量（如果sqlite3可用）
    if command -v sqlite3 &> /dev/null; then
        VOCAB_COUNT=$(sqlite3 $DB_FILE "SELECT COUNT(*) FROM vocabulary;" 2>/dev/null)
        if [ $? -eq 0 ]; then
            echo "📚 当前词汇数量: $VOCAB_COUNT"
        fi
    fi
    
    # 清理7天前的备份
    find $BACKUP_DIR -name "vocabulary_backup_*.db" -mtime +7 -delete 2>/dev/null
    
    # 显示备份历史
    echo ""
    echo "📋 备份历史:"
    ls -lah $BACKUP_DIR/vocabulary_backup_*.db 2>/dev/null | tail -5
    
else
    echo "❌ 备份失败！"
    exit 1
fi 