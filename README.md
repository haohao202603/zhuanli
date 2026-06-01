# Patent Insight Tracker

多靶点项目专利追踪与 SAR 结构分析平台原型。当前版本聚焦后端 MVP：项目/规则/专利/事件闭环、定时采集任务骨架、项目分析与多格式周报导出。

## 1. 当前状态

- **应用入口**：FastAPI 服务，根路径 `/` 提供浏览器 Demo 页面，`/docs` 提供 Swagger API 文档。
- **数据存储**：默认 SQLite（`sqlite:///./patent_tracker.db`），可通过 `DATABASE_URL` 切换。
- **部署方式**：支持 Docker、本地 Python、Render Blueprint。
- **测试方式**：`pytest`、`scripts/smoke_test.sh`、浏览器 Demo 页面。

## 2. 在线/网页测试入口

部署成功后直接访问：

- Demo 页面：`https://<你的-render-域名>/`
- API 文档：`https://<你的-render-域名>/docs`
- 健康检查：`https://<你的-render-域名>/health`

> 如果 Render 返回 503 或 Build failed，请先查看 Render Deploy Logs，并确认本仓库的 `render.yaml`、`Dockerfile` 和 `pyproject.toml` 已同步到 GitHub。

## 3. 本地快速启动

### Docker（推荐）

```bash
docker compose up --build
```

启动后打开：

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`

### Python（可选）

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

## 4. Render 部署

仓库已包含 `render.yaml`，Render Blueprint 会按 Docker 服务部署。

1. 将本仓库推送到 GitHub。
2. Render 选择 **New +** → **Blueprint**。
3. 选择该 GitHub 仓库。
4. 创建服务并等待构建完成。
5. 打开 Render 分配的 `https://xxx.onrender.com/` 测试。

## 5. 核心功能

- 项目管理：创建、查询、更新、删除项目。
- 监控规则：创建、查询、更新关键词/公司/IPC-CPC/告警等级规则。
- 专利入库：单条入库、批量入库、按项目/申请人/关键词查询。
- 事件自动化：专利入库后自动生成 `new_patent_ingested` 事件。
- 项目分析：项目概览、Top assignee、法域分布、近期专利与事件。
- 周报导出：text / Markdown / HTML / JSON / CSV。
- 采集任务骨架：ingest job 创建、列表、手动运行、重试状态流转。

## 6. 常用 API

### 项目与规则

- `POST /projects`
- `GET /projects?offset=&limit=`
- `GET /projects/{project_id}`
- `PATCH /projects/{project_id}`
- `DELETE /projects/{project_id}`
- `POST /projects/{project_id}/rules`
- `GET /projects/{project_id}/rules?offset=&limit=`
- `PATCH /projects/{project_id}/rules/{rule_id}`
- `GET /projects/{project_id}/summary`

### 专利与事件

- `POST /patents`
- `POST /patents/bulk`
- `GET /patents?project_id=&assignee=&q=&offset=&limit=`
- `GET /patents/{patent_id}`
- `POST /events`
- `GET /events?project_id=&severity=&event_type=&offset=&limit=`
- `GET /projects/{project_id}/events?severity=&offset=&limit=`
- `POST /projects/{project_id}/events/refresh`

### 分析、报告与采集任务

- `GET /analytics/projects/{project_id}/overview`
- `GET /reports/projects/{project_id}/weekly?days=`
- `GET /reports/projects/{project_id}/weekly.md?days=`
- `GET /reports/projects/{project_id}/weekly.html?days=`
- `GET /reports/projects/{project_id}/weekly.json?days=`
- `GET /reports/projects/{project_id}/weekly.csv?days=`
- `POST /ingest/jobs`
- `GET /ingest/jobs?status=`
- `POST /ingest/jobs/run`

## 7. 项目文件结构

详细说明见 [`docs/REPOSITORY_STRUCTURE.md`](docs/REPOSITORY_STRUCTURE.md)。

```text
app/                         FastAPI 应用代码
  routes/                    API 路由
  services/                  业务服务/后台任务
  static/                    Demo 页面

docs/                        PRD、技术说明、任务清单、文件结构说明
scripts/                     冒烟测试与迁移脚本
tests/                       API 集成测试
Dockerfile                   容器部署入口
docker-compose.yml           本地 Docker 启动
render.yaml                  Render Blueprint 配置
pyproject.toml               Python 包与依赖配置
```

## 8. 测试与检查

```bash
python -m compileall app tests
pytest -q
bash scripts/smoke_test.sh http://127.0.0.1:8000
```

> 当前测试文件带依赖保护：如果环境未安装 FastAPI，`pytest` 会跳过 API 集成测试，而不是在导入阶段崩溃。

## 9. 迁移到新仓库

```bash
bash scripts/migrate_to_repo.sh https://github.com/<你的用户名>/<你的仓库>.git
```

如果当前环境无法访问 GitHub，可在本机执行同样命令，或将仓库打包后通过 GitHub 网页上传。
