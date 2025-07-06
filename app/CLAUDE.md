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

# 初始化数据库迁移（仅首次）
flask db init

# 创建迁移文件（从app目录运行）
cd app
FLASK_APP=app.py flask db migrate -m "migration message"

# 应用迁移
FLASK_APP=app.py flask db upgrade

# 查看当前迁移版本
FLASK_APP=app.py flask db current

# 降级数据库
FLASK_APP=app.py flask db downgrade
```

**重要**: Flask-Migrate 配置已优化以支持 Docker 和本地开发环境的不同路径结构。必须从 `app/` 目录运行迁移命令。

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
  - `sentence_review_service.py`: 句子复习服务，智能推荐算法
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
- **路径配置**: 应用自动检测 Docker 和本地开发环境，智能选择数据库和迁移文件路径

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
- `GET /vocabulary/learn`: 单词学习页面（选择题模式）
- `GET /api/vocabulary/learn/start`: 开始学习会话
- `POST /api/vocabulary/learn/record`: 记录学习结果

### 句子复习功能
- `GET /vocabulary/sentence-review`: 句子复习页面
- `GET /api/vocabulary/sentence-review/start`: 开始句子复习会话
- `POST /api/vocabulary/sentence-review/record`: 记录句子复习结果
- `GET /api/vocabulary/sentence-review/stats`: 句子复习统计

### 语音合成
- `POST /tts`: 语音合成 API
- `GET /tts/<filename>`: 音频文件服务

## 句子复习系统架构

### 核心特性
- **智能推荐算法**: 基于遗忘曲线，优先推荐掌握度低、最近未复习的单词
- **多种复习模式**: 填空题、选择题、翻译、语境理解、混合模式
- **个性化配置**: 可调整时间（5-20分钟）和单词数量（5-20个）
- **数据追踪**: 记录句子掌握度、语境类型、响应时间等详细数据

### 学习记录扩展
`learning_records` 表已扩展支持句子复习功能：
- `sentence_mastery`: 句子语境掌握度 (0-5)
- `context_type`: 语境学习类型 ('fill_blank', 'choose_word', 'translate', 'context_meaning')
- `action_type`: 支持新的 'sentence_review' 类型

## 开发注意事项

### 路径配置重要说明
应用使用智能路径检测，自动适配不同环境：
- **本地开发**: 数据库和迁移文件在上级目录 (`../data/`, `../migrations/`)
- **Docker 环境**: 文件在当前目录 (`./migrations/`, 数据通过卷挂载)
- **Flask-Migrate**: 必须从 `app/` 目录运行，使用 `FLASK_APP=app.py` 环境变量

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