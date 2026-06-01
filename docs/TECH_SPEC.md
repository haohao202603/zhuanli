# Patent Insight Tracker 技术实现说明（Tech Spec）

- **版本**：v1.0
- **关联PRD**：`docs/PRD.md`

## 1. 总体架构
采用分层模块化架构：

1. **采集层（Ingestion）**
   - 专利数据抓取任务
   - 增量同步与回补机制
2. **处理层（Processing）**
   - 文本清洗、字段标准化、去重、同族归并
   - 化学结构解析、母核识别、R-group映射
3. **分析层（Analytics）**
   - 事件检测与风险分级
   - 专利深读与差异对比
   - SAR趋势统计
4. **服务层（API）**
   - 项目管理、检索、分析结果查询、报告任务管理
5. **呈现层（Web/Report）**
   - 仪表盘、专利详情页、结构分析页
   - PDF报告导出

## 2. 推荐技术栈
- **后端**：Python + FastAPI
- **任务调度**：Celery/Arq + Redis
- **数据库**：PostgreSQL
- **全文检索**：OpenSearch/Elasticsearch
- **对象存储**：S3兼容存储
- **化学工具链**：RDKit（母核、子结构、R-group）
- **报告引擎**：HTML模板 + WeasyPrint/wkhtmltopdf
- **前端**：React + ECharts

## 3. 核心数据模型（建议）
### 3.1 projects
- id, name, target_name, synonyms_json, status, created_at

### 3.2 monitor_rules
- id, project_id, keywords_json, assignees_json, ipc_cpc_json, smarts_json, severity_policy_json

### 3.3 patents
- id, publication_number, application_number, priority_date, publication_date, assignee, jurisdiction, legal_status, title, abstract, claims_text

### 3.4 patent_families
- id, family_key, family_type, members_json

### 3.5 structures
- id, patent_id, smiles, inchi, source_type, confidence

### 3.6 scaffolds
- id, structure_id, scaffold_smiles, scaffold_hash

### 3.7 rgroup_mappings
- id, scaffold_id, mapping_json, diff_json

### 3.8 events
- id, project_id, patent_id, event_type, severity, detected_at, payload_json

### 3.9 reports
- id, project_id, report_type, period_start, period_end, status, artifact_path

## 4. 数据流
1. 定时任务拉取源数据 -> `raw`落盘
2. 解析/标准化 -> 写入`patents`与`families`
3. 去重与关联 -> 更新同族关系
4. 化学结构处理 -> 写入`structures/scaffolds/rgroup_mappings`
5. 事件检测 -> 写入`events`并触发通知
6. 报告任务 -> 聚合分析结果并生成PDF

## 5. 算法与规则要点
### 5.1 去重与同族归并
- 优先使用公开号/申请号直接匹配
- 其次使用优先权组合与标题相似度辅助

### 5.2 母核识别
- 基于RDKit Bemis-Murcko scaffold
- 项目级自定义规则（例如保留特定杂环）

### 5.3 R-group映射
- 选定基线母核后进行位点编号
- 对比同系列结构，输出差异类型

### 5.4 事件分级
- P1：核心公司 + 核心母核 + 权利要求扩张
- P2：核心公司或核心母核之一命中
- P3：外围信息

## 6. API草案
- `POST /projects`：创建项目
- `POST /projects/{id}/rules`：配置规则
- `GET /projects/{id}/events`：事件列表
- `GET /patents/{id}`：专利详情
- `GET /patents/{id}/sar`：SAR分析结果
- `POST /reports`：创建报告任务
- `GET /reports/{id}`：报告状态与下载地址

## 7. 任务调度草案
- 每日 00:00/12:00 UTC：增量抓取
- 每周日 02:00 UTC：全量校验回补
- 每日 08:00 UTC：自动周报/日报生成（按项目配置）

## 8. 质量与监控
- 数据同步成功率、任务耗时、失败重试次数
- 告警到达率、报告生成成功率
- 结构分析准确率抽检面板

## 9. 实施建议
- 先交付文本结构链路（可控）
- 图像结构识别作为V2增强
- 所有“智能结论”保留证据链接与置信度字段
