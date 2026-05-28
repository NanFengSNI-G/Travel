# 携程AI智能助手 (Travel AI Assistant)

基于 **LangGraph 多智能体** 架构的 AI 旅行助手，支持航班查询与改签、酒店预订、租车、景点推荐等功能。前端采用 SSE 流式对话，后端使用 FastAPI + MySQL，集成 **人工审批**（Human-in-the-Loop）机制，确保写操作安全可控。

## 技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI | Python 异步 Web 框架 |
| Agent 框架 | LangGraph | 多智能体编排与状态管理 |
| LLM | 通义千问 (DeepSeek-v4-flash) | 阿里云 DashScope API |
| 嵌入模型 | DashScope text-embedding-v3 | FAQ 文档向量化 |
| 数据库 | MySQL 9.6.0 | 航班/酒店/租车/推荐数据存储 |
| ORM | SQLAlchemy 2.0 | Python 数据库映射 |
| 配置 | Dynaconf | 多环境配置管理 |
| 部署 | Docker + Docker Compose | 容器化部署 |

## 功能

- **航班查询**：按出发/到达城市搜索航班
- **机票改签**：更换航班、取消机票（需人工审批）
- **酒店预订**：搜索、预订、修改、取消酒店
- **租车服务**：搜索、预订、修改、取消租车
- **景点推荐**：搜索行程推荐、预订、修改、取消
- **政策咨询**：基于 RAG 的 FAQ 文档检索（Swiss Air 政策）
- **人工审批**：所有写操作（预订/取消/修改）在 LLM 生成工具调用后挂起，用户确认后执行

## 多智能体架构

```
用户 → 主助手 (Primary Assistant)
                │
   ┌────────────┼────────────┬────────────┐
   ▼            ▼            ▼            ▼
航班助手     酒店助手      租车助手      景点助手
(改签/取消)   (预订/取消)   (预订/取消)   (预订/取消)
```

- **主助手**：入口，处理航班搜索、政策查询，路由到子助手
- **子助手**：各自负责对应领域的读写操作
- **安全机制**：读操作（搜索）直接执行，写操作（预订/取消/修改）触发人工审批中断

## 快速开始（Docker 部署）

### 前置条件

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- 阿里云 [DashScope API Key](https://dashscope.console.aliyun.com/)

### 步骤

1. **克隆仓库**

```bash
git clone https://github.com/NanFengSNI-G/Travel.git
cd Travel
```

2. **配置环境变量**

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的配置：

```env
MySQL_PASSWORD=your_mysql_password
API_KEY=your_dashscope_api_key
```

3. **启动服务**

```bash
docker compose up -d
```

启动后访问 `http://localhost:8000`。

4. **查看日志**

```bash
docker compose logs -f app
```

5. **停止服务**

```bash
docker compose down
```

添加 `-v` 可同时删除数据库数据卷：`docker compose down -v`

## 本地部署

### 前置条件

- Python 3.11.15
- MySQL 9.6.0（运行中，已创建 `Travel` 数据库）
- 阿里云 DashScope API Key

### 步骤

1. **克隆仓库并安装依赖**

```bash
git clone https://github.com/NanFengSNI-G/Travel.git
cd Travel
pip install -r requirements.txt
```

2. **初始化数据库**

```bash
mysql -u root -p Travel < init.sql
```

3. **配置环境变量**

```bash
export MySQL_PASSWORD=your_mysql_password
export API_KEY=your_dashscope_api_key
```

4. **启动应用**

```bash
python main.py
```

访问 `http://localhost:8000`。

## 配置说明

项目使用 [Dynaconf](https://www.dynaconf.com/) 管理配置，配置文件位于 `config/development.yml`。

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|----------|--------|------|
| HOST | `EMP_CONF_HOST` | `127.0.0.1` | 服务绑定地址 |
| PORT | `EMP_CONF_PORT` | `8000` | 服务端口 |
| DATABASE.HOST | `EMP_CONF_DATABASE__HOST` | `127.0.0.1` | 数据库地址 |
| DATABASE.PORT | `EMP_CONF_DATABASE__PORT` | `3306` | 数据库端口 |
| DATABASE.PASSWORD | `MySQL_PASSWORD` | — | 数据库密码（必填） |
| API_KEY | `API_KEY` | — | DashScope API Key（必填） |

Dynaconf 使用 `EMP_CONF` 前缀，嵌套键使用 `__`（双下划线）分隔。

## API 接口

### `GET /`

返回聊天前端页面。

### `POST /api/graph/`

SSE 流式 AI 对话接口。

**请求体：**

```json
{
  "message": "帮我查一下北京到上海的航班",
  "thread_id": "uuid (可选，自动生成)",
  "passenger_id": "3442 587242 (可选，默认值)"
}
```

**SSE 事件类型：**

| 事件 | 说明 |
|------|------|
| `{"content": "...", "type": "token"}` | LLM 流式输出 |
| `{"content": "...", "type": "approval"}` | 人工审批提示 |
| `[DONE]` | 流结束 |
| `{"error": "...", "type": "error"}` | 错误信息 |

## 项目结构

```
Travel/
├── main.py                     # 应用入口
├── requirements.txt            # Python 依赖
├── init.sql                    # 数据库初始化 + 示例数据
├── FAQ.md                      # Swiss Air FAQ（RAG 知识库）
├── Dockerfile                  # Docker 镜像构建文件
├── docker-compose.yml          # Docker 编排配置
├── .env.example                # 环境变量示例
├── config/
│   └── development.yml         # 应用配置
├── static/
│   └── chat.html               # 聊天前端
└── app/
    ├── api/
    │   └── graph.py            # SSE 对话 API
    ├── agents/
    │   ├── workflow.py         # 主图构建与编译
    │   ├── assistants.py       # 5 个智能体定义
    │   ├── children.py         # 子图构建器
    │   ├── state.py            # 状态与对话栈管理
    │   ├── llm.py              # LLM 初始化
    │   ├── entry.py            # 子工作流入口工厂
    │   └── models.py           # Pydantic 路由模型
    ├── tools/
    │   ├── flights.py          # 航班搜索/改签/取消工具
    │   ├── hotels.py           # 酒店搜索/预订/取消工具
    │   ├── cars.py             # 租车搜索/预订/取消工具
    │   ├── trips.py            # 景点搜索/预订/取消工具
    │   ├── retriever.py        # RAG FAQ 检索工具
    │   └── handler.py          # ToolNode + 工具错误处理
    ├── models/
    │   ├── flight.py           # 航班/机票/登机牌 ORM
    │   └── business.py         # 酒店/租车/推荐 ORM
    ├── middleware/
    │   ├── cors.py             # CORS 中间件
    │   └── errors.py           # HTTP 异常处理
    └── core/
        ├── config.py           # 配置加载
        └── logging.py          # 日志配置
```

## 示例数据

`init.sql` 包含以下种子数据：

- **10 个航班**：苏黎世 ↔ 北京/上海/巴黎、北京 ↔ 上海
- **4 张机票**：乘客 "张伟" (ID: 3442 587242)
- **8 家酒店**：覆盖北京、上海、巴黎、苏黎世、日内瓦
- **6 个租车服务**：覆盖北京、上海、苏黎世、巴黎、日内瓦
- **8 个旅行推荐**：长城、故宫、外滩、阿尔卑斯山、卢浮宫等
