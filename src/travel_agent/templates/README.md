# 旅行代理模板系统

## 概述

本目录包含旅行代理系统使用的所有 Jinja2 模板文件，用于生成各种格式的输出（Markdown、HTML 等）。

系统采用三层降级策略：

1. **主模板**: `route_template.j2` - 功能完整，支持高级特性
2. **备用模板**: `fallback_template.j2` - 兼容性更好，作为降级方案
3. **纯字符串拼接**: 最后的备用方案，确保系统稳定运行

## 目录结构

```
templates/
├── __init__.py              # 包初始化文件
├── manager.py               # 模板管理器
├── route_template.j2        # 旅行路线模板
├── README.md                # 本说明文档
└── ...                      # 其他模板文件
```

## 模板文件

### unified_route_template.j2

- **用途**: 统一的路线生成模板（支持两种格式）
- **特点**: 通过 `format_level` 参数控制输出格式
- **支持字段**:
  - `route_title`: 路线标题
  - `daily_plans`: 每日计划数组
  - `summary`: 路线总结
  - `tips`: 旅行建议
  - `transport_info`: 交通信息
  - `accommodation_info`: 住宿信息
  - `budget_info`: 预算信息
  - `format_level`: 格式级别（"full", "simple"）
- **格式级别**:
  - `"full"`: 完整格式，显示所有信息和扩展内容
  - `"simple"`: 简化格式，只显示核心信息，标题更简洁
- **使用场景**: 所有路线生成的统一解决方案

### unified_response_template.j2

- **用途**: 统一的响应格式化模板（支持三种格式）
- **特点**: 通过 `format_level` 参数控制输出格式
- **支持字段**:
  - `destination`: 目的地
  - `duration`: 旅行天数
  - `budget`: 预算信息
  - `preferences`: 旅行偏好
  - `route_content`: 路线内容
  - `format_level`: 格式级别（"full", "simple", "basic"）
- **格式级别**:
  - `"full"`: 完整格式，显示所有信息和详细提示
  - `"simple"`: 简化格式，显示基本信息和提示
  - `"basic"`: 基础格式，只显示必要信息
- **使用场景**: 所有响应格式化的统一解决方案

## 使用方法

### 1. 基本使用

```python
from travel_agent.templates.manager import template_manager

# 渲染模板
result = template_manager.render_template("route_template.j2",
    route_title="我的旅行",
    daily_plans=[...],
    summary="旅行总结"
)
```

### 2. 模板管理器功能

```python
# 列出所有模板
templates = template_manager.list_templates()

# 重新加载特定模板
template_manager.reload_template("route_template.j2")

# 重新加载所有模板
template_manager.reload_all_templates()
```

### 3. 添加新模板

1. 在 `templates/` 目录下创建新的 `.j2` 文件
2. 使用 Jinja2 语法编写模板
3. 模板会自动被管理器发现和加载

## Jinja2 语法示例

### 条件渲染

```jinja2
{% if daily_plans %}
## 📅 每日行程安排
{% endif %}
```

### 循环处理

```jinja2
{% for plan in daily_plans %}
| {{ plan.day }} | {{ plan.date }} |
{% endfor %}
```

### 默认值

```jinja2
{{ plan.day or '待定' }}
```

### 过滤器

```jinja2
{{ items | join('、') }}
```

## 最佳实践

1. **模板命名**: 使用描述性的名称，如 `route_template.j2`
2. **注释**: 在模板中添加注释说明各部分用途
3. **错误处理**: 使用 `or` 提供默认值
4. **性能**: 模板会被自动缓存，无需重复加载
5. **维护**: 修改模板后可以热重载，无需重启应用

## 扩展性

- 支持多语言模板
- 支持主题定制
- 支持动态模板选择
- 支持模板版本管理

## 故障排除

### 模板未找到

- 检查模板文件是否在正确位置
- 检查文件名是否正确
- 检查文件权限

### 渲染失败

- 检查模板语法是否正确
- 检查传入的数据格式
- 查看日志中的错误信息

### 性能问题

- 模板会自动缓存，首次加载后性能很好
- 如需重新加载，使用 `reload_template()` 方法
