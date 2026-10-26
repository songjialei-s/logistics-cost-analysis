# logistics-cost-analysis

面向供应链数据分析、供应链数智化和 BI 岗位的独立作品集演示。
**所有服务商、跟踪号、账单、金额、汇率及业务场景均为合成数据，不代表任何公司的实际经营情况。**
本项目独立编写，不含公司原始代码、配置、账单、Power BI 文件或 Git 历史。

## 背景与业务问题
模拟六家虚构物流商在表头、字段名、日期格式、币种和重量单位上的差异，
回答月度成本、服务商费用结构、费用类别占比、单票/单件运费、环比和待核查高费用问题。
结果仅证明数据处理与分析能力，不声称产生真实降本或效率提升。

## 技术栈与流程
Python 3.11+、Pandas、openpyxl、SQLite（默认）、可选 PyMySQL/MySQL 8、Power BI 导入准备。
```
合成 Excel → 配置 Mapping → 类型/单位/费用标准化 → 拒绝与重复检查
→ SQLite 事务与文件指纹 → CSV/质量报告 → SQL 分析 / Power BI 导入
                                      ↘ 可选本地 MySQL
```

## 快速运行
在项目根目录执行（无需数据库、网络或公司资料）：
```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m src.generate_sample
.venv\Scripts\python -m src.etl
.venv\Scripts\python -m src.etl
.venv\Scripts\python -m unittest discover -s tests -v
```
第二次 ETL 应跳过 6 个文件。质量报告 inserted/duplicates/rejected 是本次运行数量，
total_charges/total_parcels/persisted_rejected 是当前库内数量。输入或配置变更后，使用 `python -m src.etl --rebuild`
重建**本项目 runtime 下的本地演示库**。不应将此方案直接用于生产数据。
已提供六份合成 Excel；生成器可复现语义数据，Excel 容器时间戳可能导致文件哈希变化。

## 数据与质量
6 家服务商、3 个月、72 个包裹、144 件商品、144 条有效费用记录。
每份账单额外植入 1 条重复、3 条无效记录；合计跳过 6 条重复、拒绝 18 条，
并标记 1 条人工设计的高费用。字段详见 docs/data_dictionary.md。
包裹件数不能按费用行重复求和；单独导出 parcels.csv 供 BI 建模。

## SQL 与指标
`python -m src.analyze` 可直接执行全部本地查询。
sql/analysis.sql 可用 Python sqlite3 或 SQLite 客户端执行，包含月度费用及环比、
服务商成本结构、类别占比、单票/单件运费和异常清单。
sql/mysql_schema.sql、mysql_analysis.sql 为 MySQL 8 对应版本。
模拟汇率与有效期明确写在 config/fx_rates.json；不同币种不得直接相加。
口径与预期结果见 docs/metrics.md。

## 可选 MySQL（未做服务器集成测试）
仅允许 localhost 回环地址，专用数据库名 logistics_demo；先自行建立本地沙盒库。
使用环境变量 DEMO_MYSQL_USER / DEMO_MYSQL_PASSWORD，端口可设 DEMO_MYSQL_PORT。
随后执行 `python -m src.load_mysql`。不提供真实凭据，不连接远程数据库。

## Power BI 与实现边界
已实现合成账单、多格式清洗、单位与币种转换、事务入库、文件增量、重复/冲突检查、
CSV 导出、质量核查及本地 SQL 验证。测试结果见 docs/test_report.md。MySQL 入库适配器已编写，尚未连接服务器验证。
powerbi/README.md 提供独立 PBIP、模型、三页图表定义及操作步骤；**待 Power BI Desktop 验证，尚无二进制 PBIX 或实际截图**。
尚未实现自动调度、生产部署、动态汇率和真实业务异常归因。

## GitHub 展示与安全
data/sample 是可公开合成样本；data/demo 是 Power BI 固定合成 CSV 快照。runtime、data/output、缓存、.env 不应提交。
不包含任何公司历史、内部地址、真实凭据或经营数据。未选择代码许可证；公开前自行确认。
在 GitHub Desktop 选择 Add existing repository 前需先 Create repository，
或在新目录初始化独立仓库；检查 Changes，提交后再手动决定 Publish repository。
不要对原始实习目录执行发布。本项目未自动 git init、commit、push 或创建远程。

## Power BI 演示项目
打开 powerbi/LogisticsCostDemo/LogisticsCostDemo.pbip；
设置DataFolder到data/demo后载入合成CSV。详见powerbi/README.md。
项目文件静态检查与原ETL测试不能替代Desktop实测；当前仍待Desktop验证。
