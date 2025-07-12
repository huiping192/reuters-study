# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

基于 Flask 的智能英语新闻学习平台，支持路透社新闻抓取、AI翻译、词汇管理和语音合成功能。

## 常用开发命令

### 运行应用
```bash
# 开发环境 (从app目录运行)
cd app && python app.py

# Docker环境 
docker-compose up -d

# 访问地址：本地 http://localhost:5000，Docker http://localhost:8007
```

### 数据库操作
```bash
# 数据库迁移（必须从app目录运行）
cd app
FLASK_APP=app.py flask db migrate -m "描述信息"
FLASK_APP=app.py flask db upgrade

# 初始化数据库（仅首次部署）
python init_db.py
```

### 测试
```bash
# 运行词汇系统功能测试
python test_vocabulary.py
```

## 核心架构

### 项目结构
- **app/**: 主应用目录，包含Flask应用和所有核心模块
- **models/**: SQLAlchemy数据模型 (vocabulary, user, learning_record)
- **services/**: 业务逻辑层 (vocabulary_service, sentence_review_service)
- **migrations/**: 数据库迁移文件，支持Docker和本地环境智能路径检测

### 核心模块
- **reuters_manager.py**: 路透社新闻抓取和解析
- **news_analytics.py**: AI文章分析和翻译 (DeepSeek/OpenAI)
- **audio_manager.py**: Replicate API语音合成
- **config.py**: 环境变量配置管理

### 数据库设计
- 使用SQLAlchemy ORM + Flask-Migrate
- 智能路径检测：Docker环境和本地开发自动适配
- 默认SQLite数据库，支持DATABASE_URL环境变量

## 重要配置

### 环境变量 (.env文件)
```env
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://api.deepseek.com/v1  # 可选
REPLICATE_API_TOKEN=your_token
```

### 关键API端点
- `GET /`: 新闻列表
- `GET /news/<url>`: 新闻详情
- `POST /translate`: AI翻译
- `GET|POST /api/vocabulary`: 词汇管理
- `GET /vocabulary/learn`: 单词学习
- `GET /vocabulary/sentence-review`: 句子复习
- `POST /tts`: 语音合成

## 开发注意事项

### Flask-Migrate路径配置
- 迁移命令必须从`app/`目录运行
- 使用`FLASK_APP=app.py`环境变量
- 应用自动检测Docker和本地环境的不同路径结构

### 句子复习系统
- 基于遗忘曲线的智能推荐算法
- learning_records表扩展支持句子复习功能
- 支持填空、选择、翻译等多种复习模式

### 安全和性能
- API密钥通过环境变量管理
- 所有数据库操作使用SQLAlchemy ORM
- 网络请求120秒超时设置
- TTS音频文件本地缓存在static/tts/目录