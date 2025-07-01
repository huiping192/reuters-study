# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个基于 Flask 的智能英语新闻学习平台，主要功能包括：
- 抓取路透社新闻并进行分类展示
- AI 驱动的翻译、词汇分析和语音合成
- 个人词汇库管理和学习记录
- 支持 SQLite 数据库的持久化存储

## 常用开发命令

### 环境准备
```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量（需要创建 .env 文件）
# OPENAI_API_KEY=your_openai_api_key
# OPENAI_BASE_URL=https://api.deepseek.com/v1  # 可选
# REPLICATE_API_TOKEN=your_replicate_token
```

### 运行应用
```bash
# 开发环境运行
cd app
python app.py

# 使用 Flask 命令运行
flask run --host=0.0.0.0

# Docker 运行
docker-compose up -d
```

### 数据库操作
```bash
# 初始化数据库（首次部署）
python init_db.py

# 初始化数据库迁移
flask db init

# 创建迁移文件
flask db migrate -m "migration message"

# 应用迁移
flask db upgrade

# 降级数据库
flask db downgrade
```

### 服务器部署注意事项
```bash
# 服务器首次部署或更新代码后
git pull origin main
pip install -r requirements.txt

# 初始化数据库（如果 data/vocabulary.db 不存在）
python init_db.py

# 启动应用
python app.py
```

**重要**: 数据库文件 `data/vocabulary.db` 已被添加到 `.gitignore` 中，不会被版本控制。服务器上的数据库文件会保持独立，避免每次部署时的数据冲突。

## 架构设计

### 核心模块结构
- **app.py**: Flask 主应用，定义所有路由和 API 端点
- **models/**: 数据模型层
  - `database.py`: 数据库连接和初始化
  - `vocabulary.py`: 词汇表模型
  - `user.py`: 用户模型
  - `learning_record.py`: 学习记录模型
- **services/**: 业务逻辑层
  - `vocabulary_service.py`: 词汇管理服务
- **utils/**: 工具类
  - `session_manager.py`: 会话管理
- **核心功能模块**:
  - `reuters_manager.py`: 路透社新闻抓取和解析
  - `news_analytics.py`: AI 文章分析和翻译
  - `audio_manager.py`: 语音合成服务
  - `config.py`: 配置管理

### 数据库设计
- 使用 SQLAlchemy ORM 和 Flask-Migrate
- 默认 SQLite 数据库：`data/vocabulary.db`
- 支持通过 `DATABASE_URL` 环境变量切换数据库

### AI 服务集成
- **翻译服务**: OpenAI API（支持 DeepSeek API）
- **语音合成**: Replicate API
- **词汇分析**: 自动识别 CEFR C1/C2 级别词汇

## 重要 API 端点

### 新闻相关
- `GET /`: 新闻列表页面
- `GET /news/<encoded_url>`: 新闻详情页面
- `POST /translate`: 文本翻译 API

### 词汇管理
- `GET|POST /api/vocabulary`: 词汇列表和添加
- `GET /api/vocabulary/stats`: 词汇统计
- `GET /api/vocabulary/<id>`: 词汇详情
- `POST /api/vocabulary/<id>/update`: AI 更新词汇信息
- `DELETE /api/vocabulary/<id>`: 删除词汇

### 学习功能
- `GET /vocabulary/learn`: 单词学习页面
- `GET /api/vocabulary/learn/start`: 开始学习会话
- `POST /api/vocabulary/learn/record`: 记录学习结果

### 语音合成
- `POST /tts`: 语音合成 API
- `GET /tts/<filename>`: 音频文件服务

## 开发注意事项

### 安全配置
- API 密钥通过环境变量管理，不应提交到代码库
- 所有用户输入都进行验证和清理
- 数据库操作使用 SQLAlchemy ORM 防止注入攻击

### 文件存储
- TTS 音频文件存储在 `static/tts/` 目录
- 数据库文件默认存储在 `data/` 目录

### 错误处理
- 所有 API 端点都有完整的异常处理
- 网络请求设置 120 秒超时
- 数据库操作自动回滚异常事务

### 代码规范
- 使用 Flask 蓝图模式组织路由（虽然当前在单文件中）
- 数据库操作通过 Service 层封装
- 模板使用 Jinja2 引擎，支持模板继承