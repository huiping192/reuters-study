# 个人词汇库功能设置说明（单用户版本）

## 功能简化说明

由于这是个人使用的网站，我们简化了用户管理系统：
- **固定用户ID**: 使用 `"single_user"` 作为唯一用户标识
- **无需注册**: 系统自动创建和管理唯一用户
- **简化会话**: 移除了复杂的浏览器指纹识别机制

## 环境变量配置

请在项目根目录创建 `.env` 文件，并添加以下配置：

```env
# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.deepseek.com

# 数据库配置
DATABASE_URL=sqlite:///vocabulary.db
# 生产环境可使用PostgreSQL: postgresql://user:pass@localhost/vocab_db

# Flask配置
SECRET_KEY=single-user-secret-key
FLASK_ENV=development

# 功能开关
ENABLE_VOCABULARY_FEATURE=true
VOCABULARY_AUTO_SAVE=true

# 缓存配置（可选）
# REDIS_URL=redis://localhost:6379/0
```

## 功能说明

### 自动词汇收集
- 当您点击翻译按钮时，系统会自动将AI分析出的词汇保存到个人词汇库
- 使用固定用户ID `"single_user"`，所有词汇都归属于这个用户
- 词汇会自动去重，重复词汇会增加出现频率

### API端点
- `GET /api/vocabulary` - 获取词汇列表
- `GET /api/vocabulary/stats` - 获取词汇统计信息
- `GET /api/vocabulary/<id>` - 获取词汇详情
- `DELETE /api/vocabulary/<id>` - 删除词汇

### 数据库表结构
- `users` - 用户表（只有一个固定用户）
- `vocabulary` - 词汇表
- `learning_records` - 学习记录表

## 使用方法

1. 启动应用后，数据库表会自动创建
2. 系统会自动创建默认用户（用户名：用户，ID：single_user）
3. 访问新闻详情页面
4. 点击翻译按钮，词汇会自动收集到个人词汇库
5. 可通过API端点查看和管理词汇

## 优势

- **简化架构**: 移除了复杂的多用户管理逻辑
- **更快启动**: 无需复杂的用户识别和会话管理
- **专注功能**: 专注于词汇学习功能本身
- **易于维护**: 代码更简洁，易于理解和维护

## 下一步开发

根据文档计划，接下来需要实现：
- 词汇库界面 (Phase 3)
- 学习记录和统计 (Phase 4)
- 智能复习系统 (Phase 5) 