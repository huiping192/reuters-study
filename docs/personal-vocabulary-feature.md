# 个人词汇库功能设计文档

## 📋 功能概述

个人词汇库是一个智能的英语学习辅助功能，用于记录、管理和复习用户在阅读新闻过程中遇到的词汇。该功能将帮助用户建立个性化的学习档案，提供科学的复习机制，提升英语学习效率。

## 🎯 功能目标

### 主要目标
- **词汇收集**：自动记录用户查看过的词汇
- **智能管理**：提供词汇分类、标记和搜索功能
- **学习追踪**：记录学习进度和掌握程度
- **复习提醒**：基于遗忘曲线的智能复习系统

### 用户价值
- 建立个人专属的英语词汇库
- 科学化的词汇学习和复习流程
- 可视化的学习进度追踪
- 提高词汇学习的效率和效果

## 🔍 功能详细分析

### 1. 词汇收集机制
#### 1.1 自动收集
- **触发时机**：用户点击翻译按钮时自动收集词汇
- **收集内容**：
  - 词汇本身（word）
  - 词性（part of speech）
  - 中文释义（definition）
  - 例句（example）
  - 来源文章信息（source article）
  - 学习时间（learned_at）

#### 1.2 手动添加
- 用户可以手动添加自定义词汇

### 2. 词汇管理功能
#### 2.1 词汇分类
- **按难度分类**：A1-C2 CEFR等级
- **按主题分类**：新闻类别（政治、经济、科技等）
- **按掌握程度**：未学习、学习中、已掌握、需复习
- **自定义标签**：用户可添加个人标签

#### 2.2 词汇操作
- **查看详情**：完整的词汇信息展示
- **编辑修改**：允许用户修改释义和例句
- **删除移除**：从词汇库中移除词汇
- **标记状态**：标记掌握程度和学习状态

#### 2.3 搜索和筛选
- **关键词搜索**：按词汇、释义搜索
- **多维度筛选**：按时间、难度、主题、状态筛选
- **排序功能**：按时间、字母、频率排序

### 3. 学习进度追踪
#### 3.1 学习统计
- **词汇数量统计**：总词汇数、新增词汇数
- **学习时间统计**：每日/每周/每月学习时长
- **掌握程度分布**：各等级词汇掌握情况
- **学习趋势分析**：学习进度曲线图

#### 3.2 成就系统
- **学习里程碑**：词汇数量达成奖励
- **连续学习奖励**：连续学习天数奖励
- **专题掌握证书**：特定主题词汇掌握认证

### 4. 智能复习系统
#### 4.1 复习算法
- **艾宾浩斯遗忘曲线**：科学的复习间隔计算
- **个性化调整**：根据用户掌握情况调整复习频率
- **优先级排序**：重要词汇优先复习

#### 4.2 复习模式
- **卡片复习**：翻卡片式词汇复习
- **测试模式**：选择题、填空题等测试
- **情境复习**：在原文语境中复习词汇

## 🏗️ 技术架构设计

### 1. 数据库设计

#### 1.1 用户表 (users)
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(50) UNIQUE NOT NULL,  -- 用户唯一标识
    username VARCHAR(100),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    settings JSON  -- 用户偏好设置
);
```

#### 1.2 词汇表 (vocabulary)
```sql
CREATE TABLE vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(50) NOT NULL,
    word VARCHAR(100) NOT NULL,
    pos VARCHAR(20),  -- 词性
    definition_cn TEXT,  -- 中文释义
    definition_en TEXT,  -- 英文释义
    example TEXT,  -- 例句
    pronunciation VARCHAR(100),  -- 发音
    difficulty_level VARCHAR(10),  -- CEFR等级
    frequency INTEGER DEFAULT 0,  -- 出现频率
    source_article_id INTEGER,  -- 来源文章ID
    source_url TEXT,  -- 来源URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, word)  -- 同一用户不能重复添加相同词汇
);
```

#### 1.3 学习记录表 (learning_records)
```sql
CREATE TABLE learning_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(50) NOT NULL,
    vocabulary_id INTEGER NOT NULL,
    action_type VARCHAR(20) NOT NULL,  -- 'view', 'review', 'test', 'master'
    mastery_level INTEGER DEFAULT 0,  -- 掌握程度 0-5
    response_time INTEGER,  -- 响应时间(毫秒)
    is_correct BOOLEAN,  -- 是否正确(测试时)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (vocabulary_id) REFERENCES vocabulary(id)
);
```

#### 1.4 复习计划表 (review_schedule)
```sql
CREATE TABLE review_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(50) NOT NULL,
    vocabulary_id INTEGER NOT NULL,
    next_review_date DATE NOT NULL,
    review_interval INTEGER DEFAULT 1,  -- 复习间隔(天)
    review_count INTEGER DEFAULT 0,  -- 复习次数
    ease_factor REAL DEFAULT 2.5,  -- 难度因子
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (vocabulary_id) REFERENCES vocabulary(id),
    UNIQUE(user_id, vocabulary_id)
);
```

#### 1.5 词汇标签表 (vocabulary_tags)
```sql
CREATE TABLE vocabulary_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(50) NOT NULL,
    vocabulary_id INTEGER NOT NULL,
    tag_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (vocabulary_id) REFERENCES vocabulary(id)
);
```

### 2. 后端架构

#### 2.1 新增模块文件
```
app/
├── models/
│   ├── __init__.py
│   ├── database.py          # 数据库连接和初始化
│   ├── user.py             # 用户模型
│   ├── vocabulary.py       # 词汇模型
│   └── learning_record.py  # 学习记录模型
├── services/
│   ├── __init__.py
│   ├── vocabulary_service.py    # 词汇管理服务
│   ├── learning_service.py      # 学习记录服务
│   └── review_service.py        # 复习计划服务
├── utils/
│   ├── __init__.py
│   ├── session_manager.py   # 会话管理
│   └── spaced_repetition.py # 间隔重复算法
└── templates/
    ├── vocabulary/
    │   ├── vocabulary_list.html    # 词汇库列表
    │   ├── vocabulary_detail.html  # 词汇详情
    │   └── review_session.html     # 复习会话
    └── dashboard/
        └── learning_stats.html     # 学习统计
```

#### 2.2 核心服务类设计

##### VocabularyService
```python
class VocabularyService:
    def add_vocabulary(self, user_id, vocab_data)
    def get_user_vocabulary(self, user_id, filters=None)
    def update_vocabulary(self, vocab_id, updates)
    def delete_vocabulary(self, vocab_id)
    def search_vocabulary(self, user_id, query)
    def get_vocabulary_stats(self, user_id)
```

##### LearningService
```python
class LearningService:
    def record_learning_action(self, user_id, vocab_id, action_type)
    def update_mastery_level(self, user_id, vocab_id, level)
    def get_learning_history(self, user_id, vocab_id=None)
    def get_learning_stats(self, user_id, period='week')
```

##### ReviewService
```python
class ReviewService:
    def schedule_review(self, user_id, vocab_id)
    def get_due_reviews(self, user_id)
    def update_review_schedule(self, user_id, vocab_id, performance)
    def calculate_next_review(self, current_interval, ease_factor, performance)
```

### 3. 前端界面设计

#### 3.1 词汇库主页面
- **词汇列表**：卡片式展示，支持网格和列表视图
- **筛选器**：多维度筛选和排序选项
- **搜索框**：实时搜索功能
- **统计面板**：学习进度概览

#### 3.2 词汇详情页面
- **词汇信息**：完整的词汇详情展示
- **学习记录**：该词汇的学习历史
- **相关词汇**：同根词、同义词推荐
- **操作按钮**：编辑、删除、标记等

#### 3.3 复习界面
- **卡片模式**：翻卡片式复习
- **进度条**：当前复习进度
- **操作按钮**：认识/不认识、难度评级
- **统计信息**：复习效果统计

## 📝 实现计划 (TODO)

### Phase 1: 基础架构搭建 (Week 1-2)

#### 1.1 数据库设计和初始化
- [ ] 创建数据库模型文件 `models/database.py`
- [ ] 设计并创建所有数据表
- [ ] 编写数据库初始化脚本
- [ ] 添加数据库迁移支持

#### 1.2 用户会话管理
- [ ] 实现简单的用户识别机制（基于浏览器指纹或UUID）
- [ ] 创建会话管理工具 `utils/session_manager.py`
- [ ] 在现有路由中集成用户识别

#### 1.3 基础模型类
- [ ] 创建 `models/user.py` - 用户模型
- [ ] 创建 `models/vocabulary.py` - 词汇模型
- [ ] 创建 `models/learning_record.py` - 学习记录模型
- [ ] 编写基础的CRUD操作方法

### Phase 2: 词汇收集功能 (Week 2-3)

#### 2.1 修改现有翻译功能
- [ ] 修改 `news_analytics.py` 中的词汇解析逻辑
- [ ] 在翻译API中集成词汇保存功能
- [ ] 为每个词汇添加"收藏"按钮
- [ ] 实现词汇去重逻辑

#### 2.2 词汇服务层
- [ ] 创建 `services/vocabulary_service.py`
- [ ] 实现词汇添加、查询、更新、删除功能
- [ ] 添加词汇统计和分析功能
- [ ] 实现词汇搜索和筛选功能

#### 2.3 API端点
- [ ] `POST /api/vocabulary` - 添加词汇
- [ ] `GET /api/vocabulary` - 获取用户词汇列表
- [ ] `PUT /api/vocabulary/<id>` - 更新词汇
- [ ] `DELETE /api/vocabulary/<id>` - 删除词汇
- [ ] `GET /api/vocabulary/search` - 搜索词汇

### Phase 3: 词汇库界面 (Week 3-4)

#### 3.1 词汇库主页面
- [ ] 创建 `templates/vocabulary/vocabulary_list.html`
- [ ] 实现词汇卡片组件
- [ ] 添加筛选和排序功能
- [ ] 实现搜索功能
- [ ] 添加批量操作功能

#### 3.2 词汇详情页面
- [ ] 创建 `templates/vocabulary/vocabulary_detail.html`
- [ ] 显示完整词汇信息
- [ ] 添加编辑功能
- [ ] 显示学习历史记录
- [ ] 实现相关词汇推荐

#### 3.3 前端交互
- [ ] 创建 `static/js/vocabulary.js`
- [ ] 实现AJAX词汇操作
- [ ] 添加实时搜索功能
- [ ] 实现拖拽排序功能

### Phase 4: 学习记录和统计 (Week 4-5)

#### 4.1 学习记录服务
- [ ] 创建 `services/learning_service.py`
- [ ] 实现学习行为记录功能
- [ ] 添加掌握程度评估算法
- [ ] 实现学习统计计算

#### 4.2 统计界面
- [ ] 创建 `templates/dashboard/learning_stats.html`
- [ ] 实现学习进度图表（使用Chart.js）
- [ ] 添加词汇掌握情况统计
- [ ] 实现学习时间统计

#### 4.3 API端点
- [ ] `POST /api/learning/record` - 记录学习行为
- [ ] `GET /api/learning/stats` - 获取学习统计
- [ ] `GET /api/learning/progress` - 获取学习进度

### Phase 5: 智能复习系统 (Week 5-6)

#### 5.1 间隔重复算法
- [ ] 创建 `utils/spaced_repetition.py`
- [ ] 实现艾宾浩斯遗忘曲线算法
- [ ] 添加个性化调整机制
- [ ] 实现复习优先级计算

#### 5.2 复习服务
- [ ] 创建 `services/review_service.py`
- [ ] 实现复习计划生成
- [ ] 添加复习提醒功能
- [ ] 实现复习效果评估

#### 5.3 复习界面
- [ ] 创建 `templates/vocabulary/review_session.html`
- [ ] 实现卡片式复习界面
- [ ] 添加复习进度显示
- [ ] 实现复习结果统计

### Phase 6: 高级功能 (Week 6-7)

#### 6.1 词汇标签系统
- [ ] 实现自定义标签功能
- [ ] 添加标签管理界面
- [ ] 实现按标签筛选功能

#### 6.2 导入导出功能
- [ ] 实现CSV格式词汇导出
- [ ] 添加词汇导入功能
- [ ] 支持Anki格式导出

#### 6.3 高级搜索
- [ ] 实现模糊搜索
- [ ] 添加正则表达式搜索
- [ ] 实现语义搜索（可选）

### Phase 7: 优化和测试 (Week 7-8)

#### 7.1 性能优化
- [ ] 数据库查询优化
- [ ] 添加缓存机制
- [ ] 前端性能优化

#### 7.2 测试
- [ ] 编写单元测试
- [ ] 进行集成测试
- [ ] 用户体验测试

#### 7.3 文档和部署
- [ ] 更新项目文档
- [ ] 更新Docker配置
- [ ] 准备生产环境部署

## 🔧 技术实现细节

### 1. 用户识别方案
由于当前项目没有用户认证系统，采用以下方案：
- **浏览器指纹**：结合IP、User-Agent、屏幕分辨率等生成唯一标识
- **本地存储**：使用localStorage存储用户ID
- **Cookie会话**：使用Flask session管理用户状态

### 2. 数据库选择
- **开发环境**：SQLite（轻量级，易于开发）
- **生产环境**：PostgreSQL（支持JSON字段，性能更好）
- **ORM框架**：SQLAlchemy（Python标准ORM）

### 3. 前端技术栈
- **CSS框架**：继续使用Tailwind CSS
- **JavaScript**：原生JS + 少量jQuery
- **图表库**：Chart.js（学习统计图表）
- **图标库**：Font Awesome（已集成）

### 4. 缓存策略
- **词汇数据**：Redis缓存热门词汇
- **统计数据**：定时计算并缓存统计结果
- **复习计划**：缓存用户的复习队列

## 📊 数据流程图

```
用户阅读新闻 → 点击翻译 → AI分析词汇 → 自动保存到词汇库
                                    ↓
用户访问词汇库 ← 展示词汇列表 ← 从数据库查询词汇
                                    ↓
用户复习词汇 → 记录学习行为 → 更新掌握程度 → 调整复习计划
```

## 🎨 UI/UX 设计要点

### 1. 词汇卡片设计
- **简洁明了**：重要信息突出显示
- **状态标识**：用颜色区分掌握程度
- **快速操作**：hover显示操作按钮
- **响应式**：适配移动端

### 2. 复习界面设计
- **专注模式**：减少干扰元素
- **进度反馈**：清晰的进度指示
- **操作便捷**：大按钮，易于点击
- **成就感**：完成后的正向反馈

### 3. 统计界面设计
- **数据可视化**：直观的图表展示
- **关键指标**：突出重要数据
- **时间维度**：支持不同时间段查看
- **对比分析**：历史数据对比

## 🚀 部署和配置

### 1. 环境变量新增
```env
# 数据库配置
DATABASE_URL=sqlite:///vocabulary.db  # 开发环境
# DATABASE_URL=postgresql://user:pass@localhost/vocab_db  # 生产环境

# 缓存配置
REDIS_URL=redis://localhost:6379/0  # 可选

# 功能开关
ENABLE_VOCABULARY_FEATURE=true
VOCABULARY_AUTO_SAVE=true
```

### 2. 依赖包更新
```txt
# 新增依赖
SQLAlchemy==2.0.23
Flask-SQLAlchemy==3.1.1
alembic==1.12.1  # 数据库迁移
redis==5.0.1     # 缓存（可选）
```

### 3. Docker配置更新
- 添加数据库卷挂载
- 配置Redis服务（可选）
- 更新环境变量

## 📈 成功指标

### 1. 功能指标
- [ ] 词汇自动收集成功率 > 95%
- [ ] 词汇库查询响应时间 < 200ms
- [ ] 复习算法准确性验证
- [ ] 数据导入导出功能正常

### 2. 用户体验指标
- [ ] 界面加载时间 < 2s
- [ ] 移动端适配完整
- [ ] 操作流程顺畅
- [ ] 错误处理完善

### 3. 数据指标
- [ ] 用户词汇库平均词汇数
- [ ] 复习完成率
- [ ] 词汇掌握程度提升
- [ ] 功能使用频率

## 🔮 未来扩展

### 1. AI增强功能
- **智能推荐**：基于学习历史推荐相关词汇
- **难度评估**：AI自动评估词汇难度
- **个性化学习路径**：AI生成学习计划

### 2. 社交功能
- **词汇分享**：分享有趣的词汇
- **学习小组**：创建学习小组
- **排行榜**：学习成就排行

### 3. 多媒体支持
- **图片记忆**：为词汇添加图片
- **视频例句**：真实语境中的词汇使用
- **语音识别**：口语练习功能

---

**注意**：本文档将随着开发进度持续更新，请定期查看最新版本。 