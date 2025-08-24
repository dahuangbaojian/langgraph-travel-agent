# 🧳 智能旅行规划助手 (Travel Agent)

一个基于 LangGraph 和 Python 的智能旅行规划系统，能够为用户提供个性化的旅行建议、路线规划、预算分配等服务。

## ✨ 主要特性

- 🎯 **智能路线规划**: 根据用户需求自动生成最优旅行路线
- 🏨 **住宿推荐**: 基于预算和偏好推荐合适的酒店
- 🍽️ **美食指南**: 推荐当地特色餐厅和美食
- 💰 **预算管理**: 智能分配预算到各个项目
- 🚄 **交通建议**: 提供多种交通方式选择
- 📱 **现代化 UI**: 美观的 Web 界面，支持实时对话
- 📊 **数据驱动**: 基于本地 Excel 数据的智能推荐

## 🏗️ 项目架构

```
src/travel_agent/
├── config/          # 配置管理
│   └── settings.py  # 应用配置
├── core/            # 核心模型
│   └── models.py    # 数据模型定义
├── data/            # 数据管理
│   └── manager.py   # 数据管理器
├── tools/           # 业务工具
│   └── planner.py   # 旅行规划器
├── ui/              # 用户界面
│   └── app.py       # Web应用
├── graph.py         # LangGraph主图
└── __init__.py      # 模块初始化
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.11+
- LangGraph 0.6.6+
- pandas, openpyxl

### 2. 安装依赖

```bash
pip install "langgraph>=0.6.6" "langchain-openai>=0.1.22" pandas openpyxl
```

### 3. 配置环境变量

创建`.env`文件：

```env
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai-proxy.org/v1

# 应用配置
TRAVEL_AGENT_DEBUG=true
TRAVEL_AGENT_MODEL=gpt-4o
TRAVEL_AGENT_DATA_DIR=travel_data
```

### 4. 启动服务

```bash
# 启动LangGraph开发服务器
langgraph dev --no-browser

# 或者启动Web界面
python src/travel_agent/ui/app.py
```

### 5. 访问应用

- **LangGraph API**: http://127.0.0.1:2024
- **Web 界面**: http://127.0.0.1:8000
- **API 文档**: http://127.0.0.1:2024/docs

## 📊 数据模型

### 支持的城市

- 北京、上海、广州、深圳
- 杭州、成都、西安、南京
- 苏州、青岛、厦门、大连

### 景点类别

- 历史文化、自然风光、城市景观
- 现代建筑、娱乐休闲、购物中心

### 菜系类型

- 中餐、西餐、日料、韩料、泰餐、当地特色

### 交通方式

- 高铁、飞机、火车、大巴、自驾

## 💬 使用示例

### 基础查询

```
用户: 我想去北京玩3天，预算5000元，2个人
助手: 🎉 为您制定了详细的旅行计划！
      📍 目的地: 北京
      📅 行程天数: 3天
      💰 总预算: 5000元
      👥 人数: 2人
      ...
```

### 偏好查询

```
用户: 推荐广州的历史文化景点和粤菜餐厅
助手: 为您推荐广州的历史文化景点和粤菜餐厅...
```

### 预算优化

```
用户: 帮我优化预算，控制在3000元以内
助手: 根据您的预算，我建议以下调整...
```

## 🔧 自定义配置

### 修改预算分配比例

在`src/travel_agent/config/settings.py`中：

```python
budget_ratios = {
    "hotel": 0.4,      # 住宿40%
    "restaurant": 0.25, # 餐饮25%
    "attractions": 0.15, # 景点15%
    "transport": 0.15,   # 交通15%
    "other": 0.05       # 其他5%
}
```

### 添加新城市

在配置文件中添加新城市：

```python
supported_cities = [
    "北京", "上海", "广州", "深圳",
    "杭州", "成都", "西安", "南京",
    "苏州", "青岛", "厦门", "大连",
    "新城市"  # 添加新城市
]
```

### 自定义数据

将您的 Excel 文件放入`travel_data/`目录：

- `hotels.xlsx` - 酒店信息
- `attractions.xlsx` - 景点信息
- `restaurants.xlsx` - 餐厅信息
- `transport.xlsx` - 交通信息

## 📁 数据文件格式

### 酒店数据 (hotels.xlsx)

| 字段            | 说明     | 示例                            |
| --------------- | -------- | ------------------------------- |
| name            | 酒店名称 | 北京王府井希尔顿酒店            |
| city            | 城市     | 北京                            |
| district        | 区域     | 东城区                          |
| address         | 地址     | 北京市东城区王府井金鱼胡同 8 号 |
| price_per_night | 每晚价格 | 800                             |
| rating          | 评分     | 4.6                             |
| amenities       | 设施     | WiFi,健身房,游泳池,餐厅         |
| description     | 描述     | 位于王府井商业区，交通便利      |

### 景点数据 (attractions.xlsx)

| 字段           | 说明     | 示例                       |
| -------------- | -------- | -------------------------- |
| name           | 景点名称 | 故宫博物院                 |
| city           | 城市     | 北京                       |
| category       | 类别     | 历史文化                   |
| ticket_price   | 门票价格 | 60                         |
| duration_hours | 游览时长 | 4                          |
| description    | 描述     | 明清两代皇宫，世界文化遗产 |
| opening_hours  | 开放时间 | 8:30-17:00                 |
| best_time      | 最佳时间 | 春秋季节                   |
| tips           | 贴士     | 建议提前预约，避开节假日   |

## 🛠️ 开发指南

### 添加新功能

1. 在`core/models.py`中定义新的数据模型
2. 在`data/manager.py`中实现数据管理逻辑
3. 在`tools/planner.py`中添加业务逻辑
4. 在`graph.py`中集成新功能
5. 更新 Web 界面以支持新功能

### 扩展 AI 能力

1. 修改系统提示词
2. 添加新的工具函数
3. 实现更复杂的推理逻辑
4. 集成外部 API 服务

### 性能优化

1. 实现数据缓存
2. 优化数据库查询
3. 使用异步处理
4. 实现负载均衡

## 🧪 测试

```bash
# 运行单元测试
python -m pytest tests/

# 运行集成测试
python -m pytest tests/integration_tests/

# 运行所有测试
python -m pytest
```

## 📈 监控和日志

系统使用结构化日志记录：

```python
import logging
logger = logging.getLogger(__name__)
logger.info("成功创建旅行计划")
logger.error("创建旅行计划失败")
```

## 🔒 安全考虑

- API 密钥存储在环境变量中
- 输入验证和清理
- 错误信息不暴露敏感数据
- 支持 HTTPS 和 WSS

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

MIT License

## 🆘 支持

- 查看[Issues](../../issues)
- 阅读[文档](docs/)
- 联系开发团队

## 🔮 未来计划

- [ ] 集成实时天气数据
- [ ] 添加多语言支持
- [ ] 实现移动端应用
- [ ] 集成支付系统
- [ ] 添加社交分享功能
- [ ] 实现 AI 语音助手

---

**享受您的智能旅行规划体验！** ✈️🌍
