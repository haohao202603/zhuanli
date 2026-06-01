# Repository Structure

本文档用于说明当前仓库文件如何组织，方便上传 GitHub、部署 Render、交接给其他开发者继续维护。

## 顶层文件

| 路径 | 用途 |
| --- | --- |
| `README.md` | 项目入口说明：测试地址、启动方式、部署、API 总览。 |
| `pyproject.toml` | Python 项目元数据、依赖、测试配置与 PEP 517 build-system。 |
| `Dockerfile` | Render/Docker 容器构建入口。 |
| `docker-compose.yml` | 本地 Docker Compose 启动配置。 |
| `render.yaml` | Render Blueprint 配置。 |
| `.gitignore` | 忽略虚拟环境、缓存、数据库、本地环境变量等文件。 |
| `.env.example` | 可复制为 `.env` 的环境变量样例。 |

## 应用代码

| 路径 | 用途 |
| --- | --- |
| `app/main.py` | FastAPI 应用入口、生命周期初始化、后台 ingest scheduler 启停、路由挂载。 |
| `app/config.py` | 环境变量读取。 |
| `app/db.py` | SQLModel engine、建表与 session 依赖。 |
| `app/models.py` | 数据库模型：项目、规则、专利、事件、采集任务。 |
| `app/schemas.py` | 请求/响应 schema。 |
| `app/routes/` | API 路由模块。 |
| `app/services/` | 业务服务模块：事件生成、采集任务调度。 |
| `app/static/index.html` | 浏览器 Demo 测试页面。 |

## 路由模块

| 路径 | 用途 |
| --- | --- |
| `app/routes/projects.py` | 项目、规则、项目事件、项目汇总、事件刷新。 |
| `app/routes/patents.py` | 单条/批量专利入库与专利查询。 |
| `app/routes/events.py` | 手动事件创建与全局事件查询。 |
| `app/routes/analytics.py` | 项目概览分析。 |
| `app/routes/reports.py` | text/Markdown/HTML/JSON/CSV 周报。 |
| `app/routes/ingest.py` | 采集任务创建、查询、手动运行。 |

## 文档与脚本

| 路径 | 用途 |
| --- | --- |
| `docs/PRD.md` | 产品需求文档。 |
| `docs/TECH_SPEC.md` | 技术实现说明。 |
| `docs/MVP_JIRA_BACKLOG.md` | MVP 任务拆解。 |
| `docs/REPOSITORY_STRUCTURE.md` | 当前文件结构说明。 |
| `scripts/smoke_test.sh` | 接口冒烟测试脚本。 |
| `scripts/migrate_to_repo.sh` | 迁移当前项目到新 Git 仓库的辅助脚本。 |
| `.github/workflows/deploy-render.yml` | GitHub Actions 调用 Render Deploy Hook。 |

## 建议上传到 GitHub 的文件

上传时应包含：

- `.github/`
- `app/`
- `docs/`
- `scripts/`
- `tests/`
- `.env.example`
- `.gitignore`
- `Dockerfile`
- `README.md`
- `docker-compose.yml`
- `pyproject.toml`
- `render.yaml`

不要上传：

- `.git/`
- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- `patent_tracker.db`
- `.env`
- 任何包含 token/password 的本地配置文件
