# 🧳 智能旅行规划助手 (Travel Agent)

一个基于 LangGraph 和 Python 的智能旅行规划系统，支持国内外路线规划，能够为用户提供个性化的旅行建议、路线规划、预算分配等服务。

[![CI](https://github.com/langchain-ai/langgraph-fullstack-python/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/langchain-ai/langgraph-fullstack-python/actions/workflows/unit-tests.yml)
[![Integration Tests](https://github.com/langchain-ai/langgraph-fullstack-python/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/langchain-ai/langgraph-fullstack-python/actions/workflows/integration-tests.yml)

## ✨ 主要特性

- 🎯 **智能路线规划**: 根据用户需求自动生成最优旅行路线
- 🌍 **全球城市支持**: 支持所有国家所有城市，无需预先配置
- 🏨 **住宿推荐**: 基于预算和偏好推荐合适的酒店
- 🍽️ **美食指南**: 推荐当地特色餐厅和美食
- 💰 **多货币预算管理**: 支持 8 种货币的智能预算分配
- 🚄 **交通建议**: 提供多种交通方式选择
- 🛂 **签证信息**: 提供详细的签证类型和申请要求
- 📱 **现代化 UI**: 美观的 Web 界面，支持实时对话
- 📊 **数据驱动**: 基于本地 Excel 数据的智能推荐

## 🌍 全球城市支持

### 🚀 动态城市创建

- **无需预先配置**: 支持所有国家所有城市
- **智能识别**: 自动识别城市所属国家、地区、货币、语言
- **实时创建**: 用户查询时自动创建城市信息

### 🏠 国内城市

- 支持所有中国城市（北京、上海、广州、深圳等）
- 自动识别为国内城市，使用人民币结算

### 🌏 国际城市

- 支持所有国际城市（东京、巴黎、纽约、悉尼等）
- 自动识别国家、货币、语言、签证要求
- 支持亚洲、欧洲、北美、南美、非洲、大洋洲

### 💱 多货币支持

支持 8 种主要货币：CNY、USD、EUR、JPY、KRW、GBP、AUD、CAD

### 🛂 签证信息

- 国内城市免签
- 国际城市提供签证类型和申请要求
- 支持申根签证等特殊签证类型

## 🏗️ 项目架构

```
src/travel_agent/
├── config/          # 配置管理
│   ├── settings.py      # 应用配置
│   └── logging_config.py # 日志配置
├── core/            # 核心模型
│   └── models.py    # 数据模型定义
├── data/            # 数据管理
│   └── manager.py   # 数据管理器
├── tools/           # 业务工具
│   ├── flights.py       # 航班查询
│   ├── hotels.py        # 酒店查询
│   ├── places.py        # 景点/路线
│   ├── currency.py      # 汇率转换
│   ├── weather.py       # 天气查询
│   ├── rag.py           # 知识库检索
│   └── planner.py       # 旅行规划器
├── ui/              # 用户界面
│   └── app.py       # Web应用
├── graph.py         # LangGraph主图
└── __init__.py      # 模块初始化
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.11+
- LangGraph 0.2.6+
- pandas, openpyxl

### 2. 安装依赖

```bash
# 使用项目脚本
./start.sh

# 或手动安装
pip install -e .
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
# 使用启动脚本
./start.sh

# 或直接启动
python -m uvicorn travel_agent.ui.app:app --host 0.0.0.0 --port 8001 --reload
```

### 5. 访问应用

- **Web 界面**: http://localhost:8001
- **API 文档**: http://localhost:8001/docs

## 📊 数据模型

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

### 国际旅行查询

```
用户: 我想去东京玩5天，预算10000元
助手: 🎉 为您制定东京5日游计划！
      📍 目的地: 东京
      🗾 国家: 日本
      💴 货币: JPY
      🛂 签证: 旅游签证
      ...

用户: 我想去巴塞罗那玩3天
助手: 🎉 为您制定巴塞罗那3日游计划！
      📍 目的地: 巴塞罗那
      🇪🇸 国家: 西班牙
      💶 货币: EUR
      🛂 签证: 申根签证
      ...
```

## 🔧 自定义配置

### 修改预算分配比例

在`src/travel_agent/config/settings.py`中：

```python
"budget_breakdown": {
    "hotel": 0.40,      # 住宿40%
    "transport": 0.25,   # 交通25%
    "attractions": 0.20, # 景点20%
    "other": 0.15        # 其他15%
}
```

### 添加新城市

系统现在支持所有城市，无需预先配置：

```python
# 用户查询任何城市时，系统会自动创建城市信息
city_info = config.get_or_create_city("里约热内卢", "巴西")
print(f"城市: {city_info.name}")
print(f"国家: {city_info.country}")
print(f"货币: {city_info.currency.value}")
print(f"语言: {city_info.language}")
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

## 🛠️ 核心工具

### 🛫 航班查询 (flights.py)

- 航班搜索和比较
- 价格分析和推荐
- 航线建议

### 🏨 酒店查询 (hotels.py)

- 酒店搜索和筛选
- 价格比较和推荐
- 设施和评分信息

### 🏛️ 景点规划 (places.py)

- 景点搜索和分类
- 路线规划和推荐
- 门票和时长信息

### 💱 汇率转换 (currency.py)

- 多货币支持
- 实时汇率转换
- 旅行成本计算

### 🌤️ 天气查询 (weather.py)

- 当前天气信息
- 天气预报
- 旅行天气建议

### 📚 知识库检索 (rag.py)

- 旅行攻略搜索
- 签证信息查询
- 智能问答

## 📋 管理脚本

### 启动和停止

```bash
# 启动应用
./start.sh

# 停止应用
./stop.sh
```

### 查看城市信息

```bash
# 显示所有支持的国内外城市
./cities.sh
```

### 测试工具功能

```bash
# 测试所有工具
python3 test_tools.py
```

### 日志管理

```bash
# 实时查看日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log

# 清理旧日志
python3 -c "from src.travel_agent.config.logging_config import cleanup_logs; cleanup_logs(7)"
```

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

系统使用结构化日志记录，支持每天自动归档：

- **主日志**: `logs/app.log` (保留 30 天)
- **错误日志**: `logs/error.log` (保留 30 天)
- **调试日志**: `logs/debug.log` (保留 7 天，仅调试模式)

```python
from src.travel_agent.config.logging_config import get_logger

logger = get_logger("your_module")
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
- [ ] 添加更多非洲和南美城市
- [ ] 集成实时汇率 API
- [ ] 实现移动端应用
- [ ] 集成支付系统
- [ ] 添加社交分享功能
- [ ] 实现 AI 语音助手
- [ ] 支持多语言界面
- [ ] 添加城市安全等级信息

## 🌟 特色功能

### 智能预算分配

- 根据目的地自动调整预算比例
- 支持多货币转换
- 实时汇率更新

### 签证助手

- 详细的签证申请流程
- 申根签证多国通行
- 落地签和电子签支持

### 最佳旅行季节

- 基于气候数据推荐
- 考虑旅游旺季因素
- 个性化季节建议

---

**享受您的智能旅行规划体验！** ✈️🌍

## 📚 相关链接

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Uvicorn Documentation](https://www.uvicorn.org)
