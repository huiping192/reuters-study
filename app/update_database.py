#!/usr/bin/env python3
"""
数据库更新脚本 - 为learning_records表添加新字段
"""
import sqlite3
import os
import sys

def update_database():
    """更新数据库结构"""
    # 获取数据库文件路径
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'vocabulary.db')
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查是否已有新字段
        cursor.execute("PRAGMA table_info(learning_records)")
        columns = [column[1] for column in cursor.fetchall()]
        
        updates_needed = []
        
        if 'sentence_mastery' not in columns:
            updates_needed.append("ALTER TABLE learning_records ADD COLUMN sentence_mastery INTEGER DEFAULT 0")
        
        if 'context_type' not in columns:
            updates_needed.append("ALTER TABLE learning_records ADD COLUMN context_type VARCHAR(20)")
        
        if not updates_needed:
            print("✅ 数据库结构已是最新版本")
            return True
        
        # 执行更新
        for sql in updates_needed:
            print(f"执行: {sql}")
            cursor.execute(sql)
        
        conn.commit()
        conn.close()
        
        print("✅ 数据库更新完成")
        return True
        
    except Exception as e:
        print(f"❌ 数据库更新失败: {str(e)}")
        return False

if __name__ == "__main__":
    update_database()