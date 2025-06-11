# Reuters 新闻学习平台

一个基于 Flask 的智能英语新闻学习平台，专门用于抓取路透社新闻并提供AI驱动的翻译、词汇分析和语音合成功能，帮助用户提升英语阅读能力。

## 🌟 功能特性

### 📰 新闻聚合
- **实时抓取**：自动获取路透社最新新闻
- **智能分类**：按主分类和子分类组织新闻内容
- **响应式界面**：支持多设备访问的现代化UI

### 🤖 AI 驱动的学习功能
- **智能翻译**：使用 DeepSeek API 提供地道的中文翻译
- **词汇分析**：自动识别 CEFR C1/C2 级别的高级词汇
- **词汇详解**：提供词性、释义和例句
- **个性化学习**：针对英语学习者优化的内容呈现

### 🔊 语音合成
- **TTS 功能**：使用 Replicate API 生成高质量英语语音
- **多种音色**：支持不同的语音选择
- **离线缓存**：生成的音频文件本地存储

## 🛠️ 技术栈

### 后端技术
- **Flask 3.1.0** - 轻量级 Web 框架
- **BeautifulSoup4** - HTML 解析和网页抓取
- **Requests** - HTTP 请求处理
- **Python-dotenv** - 环境变量管理

### AI 服务集成
- **OpenAI API** - 文本翻译和分析（支持 DeepSeek）
- **Replicate API** - 语音合成服务

### 容器化部署
- **Docker** - 容器化部署
- **Docker Compose** - 多服务编排

## 📁 项目结构

```
reuters-study/
├── app/                          # 应用主目录
│   ├── app.py                   # Flask 主应用
│   ├── reuters_manager.py       # 路透社新闻抓取模块
│   ├── news_analytics.py        # AI 文章分析模块
│   ├── audio_manager.py         # 语音合成模块
│   ├── config.py               # 配置管理
│   ├── templates/              # HTML 模板
│   │   ├── list.html          # 新闻列表页面
│   │   ├── detail.html        # 新闻详情页面
│   │   └── translation_template.html  # 翻译结果模板
│   └── static/                 # 静态资源
│       ├── js/                # JavaScript 文件
│       └── tts/               # 音频文件存储
├── requirements.txt            # Python 依赖
├── Dockerfile                 # Docker 配置
├── docker-compose.yml         # Docker Compose 配置
└── README.md                  # 项目说明
```

## 🚀 快速开始

### 环境要求
- Python 3.11+
- Docker (可选)
- 有效的 API 密钥：
  - OpenAI API Key (或 DeepSeek API Key)
  - Replicate API Token

### 1. 克隆项目
```bash
git clone https://github.com/your-username/reuters-study.git
cd reuters-study
```

### 2. 环境配置
创建 `.env` 文件并配置必要的环境变量：
```env
# AI 服务配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.deepseek.com/v1  # 可选，默认使用 OpenAI
REPLICATE_API_TOKEN=your_replicate_token
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 运行应用
```bash
cd app
python app.py
```

应用将在 `http://localhost:5000` 启动。

## 🐳 Docker 部署

### 使用 Docker Compose（推荐）
```bash
docker-compose up -d
```

应用将在 `http://localhost:8000` 启动。

### 使用 Docker
```bash
# 构建镜像
docker build -t reuters-study .

# 运行容器
docker run -p 8000:5000 --env-file .env reuters-study
```

## 📖 使用指南

### 1. 浏览新闻
- 访问首页查看按分类组织的最新路透社新闻
- 点击新闻标题进入详情页面

### 2. 学习功能
- **翻译**：点击段落旁的翻译按钮获取AI翻译
- **词汇学习**：查看高亮显示的高级词汇及其详细解释
- **语音朗读**：点击语音按钮听取英语朗读

### 3. 个性化学习
- 系统自动识别 C1/C2 级别词汇
- 提供词性、中文释义和实用例句
- 支持段落级别的精准翻译

## ⚙️ 配置说明

### 环境变量
| 变量名 | 必需 | 说明 | 默认值 |
|--------|------|------|--------|
| `OPENAI_API_KEY` | ✅ | OpenAI/DeepSeek API 密钥 | - |
| `OPENAI_BASE_URL` | ❌ | API 基础URL | `https://api.openai.com/v1` |
| `REPLICATE_API_TOKEN` | ✅ | Replicate API 令牌 | - |

### 应用配置
- **端口**：Flask 默认 5000，Docker 映射到 8000
- **音频存储**：`app/static/tts/` 目录
- **请求超时**：120秒（AI API）

## 🔧 开发说明

### 核心模块

#### `reuters_manager.py`
- 负责路透社新闻的抓取和解析
- 实现智能分类和内容清理
- 支持文章全文提取

#### `news_analytics.py`
- 集成 AI 翻译服务
- 实现词汇难度分析
- 提供结构化的学习内容

#### `audio_manager.py`
- 集成 Replicate TTS 服务
- 管理音频文件生成和存储
- 支持多种语音选项

### API 端点
- `GET /` - 新闻列表页面
- `GET /news/<encoded_url>` - 新闻详情页面
- `POST /translate` - 文本翻译API
- `POST /tts` - 语音合成API
- `GET /tts/<filename>` - 音频文件服务

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [路透社](https://www.reuters.com/) - 新闻内容来源
- [DeepSeek](https://www.deepseek.com/) - AI 翻译服务
- [Replicate](https://replicate.com/) - 语音合成服务
- [Flask](https://flask.palletsprojects.com/) - Web 框架

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 创建 [Issue](https://github.com/your-username/reuters-study/issues)
- 发送邮件至：your-email@example.com

---

**注意**：本项目仅用于教育和学习目的，请遵守相关网站的使用条款和版权规定。