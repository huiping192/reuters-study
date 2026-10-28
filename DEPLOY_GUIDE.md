# 部署指南

## 快速部署

### 方法1：Docker部署（推荐）

```bash
# 1. 克隆代码
git clone <your-repo-url>
cd reuters-study

# 2. 配置环境变量（可选，如果需要AI翻译和TTS功能）
cp app/.env.example app/.env
# 编辑 app/.env 填入API密钥

# 3. 部署
./deploy.sh
```

应用将在 **http://localhost:8007** 运行

### 方法2：本地部署

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量（可选）
cp app/.env.example app/.env
# 编辑 app/.env 填入API密钥

# 3. 启动应用
cd app
python app.py
```

应用将在 **http://localhost:5000** 运行

---

## 重要更新说明

### 新闻源切换：Reuters → BBC News

**变更原因**：路透社加强了反爬虫措施（DataDome CAPTCHA），导致无法稳定获取新闻。

**新方案**：
- 新闻源：BBC News
- 获取方式：官方RSS Feed + 网页抓取
- 优势：稳定、免费、无反爬虫限制
- 支持分类：World、Business、Technology、Science

**无需额外配置**：
- ✅ BBC新闻不需要API密钥
- ✅ 部署脚本无需修改
- ✅ 所有功能保持一致

---

## 环境变量说明

### 必需环境变量（如果使用AI功能）

创建 `app/.env` 文件：

```env
# OpenAI API（用于翻译和词汇分析）
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1  # 或使用 DeepSeek API

# kokoro TTS 服务地址（可选，见 tts_server/）
TTS_SERVER_URL=http://192.168.11.78:5100
```

### 可选环境变量

```env
# 数据库路径（默认使用SQLite）
DATABASE_URL=sqlite:////app/data/vocabulary.db

# Flask环境
FLASK_ENV=production  # 或 development
```

---

## 部署命令详解

### Docker命令

```bash
# 构建并启动
docker-compose up --build -d

# 查看日志
docker-compose logs -f app

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看容器状态
docker-compose ps
```

### 数据库迁移

```bash
# 进入容器
docker-compose exec app bash

# 运行迁移
flask db upgrade

# 查看当前版本
flask db current
```

---

## 目录结构

```
reuters-study/
├── app/                    # 主应用目录
│   ├── bbc_manager.py     # BBC新闻管理器 ⭐新增
│   ├── app.py             # Flask应用主文件
│   ├── news_analytics.py  # AI分析和翻译
│   ├── audio_manager.py   # 语音合成
│   ├── models/            # 数据模型
│   ├── services/          # 业务逻辑
│   ├── templates/         # 页面模板
│   └── .env               # 环境变量配置
├── data/                   # 数据库文件目录
├── migrations/            # 数据库迁移文件
├── archive/               # 归档的旧代码
│   ├── reuters_manager.py           # 旧路透社管理器
│   └── reuters_manager_playwright.py
├── requirements.txt       # Python依赖
├── docker-compose.yml     # Docker配置
├── Dockerfile            # Docker镜像配置
├── deploy.sh             # 部署脚本
└── start.sh              # 容器启动脚本
```

---

## 功能验证

部署完成后，访问以下页面验证功能：

- **主页**：http://localhost:8007/ （显示BBC新闻列表）
- **词汇库**：http://localhost:8007/vocabulary
- **单词学习**：http://localhost:8007/vocabulary/learn
- **句子复习**：http://localhost:8007/vocabulary/sentence-review

---

## 故障排查

### 问题1：无法访问主页

**检查**：
```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs app
```

**解决**：
```bash
# 重启容器
docker-compose restart
```

### 问题2：新闻无法加载

**原因**：BBC RSS Feed可能暂时不可用

**检查**：
```bash
# 测试RSS连接
curl http://feeds.bbci.co.uk/news/world/rss.xml
```

**解决**：通常RSS很稳定，稍等片刻重试即可

### 问题3：翻译功能不工作

**原因**：未配置OpenAI API密钥

**解决**：
1. 检查 `app/.env` 文件是否存在
2. 确认 `OPENAI_API_KEY` 已正确配置
3. 重启应用

---

## 性能优化建议

### 生产环境部署

1. **使用Gunicorn**：
```bash
# 安装
pip install gunicorn

# 启动（推荐4个worker）
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

2. **使用Nginx反向代理**：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8007;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. **数据库备份**：
```bash
# 备份SQLite数据库
cp data/vocabulary.db data/vocabulary_backup_$(date +%Y%m%d).db
```

---

## 更新应用

```bash
# 使用部署脚本（自动拉取代码并重启）
./deploy.sh

# 或手动更新
git pull origin main
docker-compose up --build -d
```

---

## 支持与反馈

如有问题，请查看：
- `CLAUDE.md`：开发文档
- `REUTERS_FIX_GUIDE.md`：新闻源切换详细说明
- `FINAL_SOLUTIONS.md`：问题解决方案对比

祝使用愉快！🎉
