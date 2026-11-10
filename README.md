# 跨境物流费用分析｜Logistics Cost Analysis

配置驱动的物流账单清洗与成本分析作品：将六类物流商的异构 Excel 账单转换为统一费用明细，并提供订单关联、汇率折算与 Power BI 分析的 SQL 和数据流说明。

> 本仓库为匿名化作品展示版本。物流商名称与示例数据均为演示用途，不包含生产凭据、客户记录或真实业务金额。

![物流成本分析看板（合成数据）](assets/dashboard.png)

## ✨ 核心功能

| 模块 | 当前实现 |
| --- | --- |
| 多物流商适配 | 六套配置定义目录、工作表、表头行、币种及字段映射 |
| 账单标准化 | 日期、数值、字段名清洗，统一输出十个标准字段 |
| 增量识别 | SHA-256 文件哈希与配置指纹识别需要重新处理的文件 |
| 批内去重 | 运单或仓库订单标识结合日期、物流商、费用类型及金额生成业务键 |
| 订单关联 | SQL 示例按物流商选择运单号或仓库订单号关联 |
| 汇率折算 | SQL 示例分别折算账单费用与订单销售额 |
| 异常分析 | 展示缺失订单映射、物流成本占比及 11% 阈值分析思路 |
| 看板展示 | 提供合成数据看板截图与 CSV 示例，便于理解分析模型 |

## 📌 业务背景

跨境物流账单的列名、表头位置、工作表及币种并不统一。直接汇总会增加人工核对成本，也容易遗漏缺失运单、重复费用与费用冲销。

本项目通过“原始账单 → 统一费用明细 → 订单关联 → 月度汇率折算 → 成本分析”的流程，展示 Python 数据处理、SQL 建模和业务指标设计能力。

## 🛠 技术栈

| 技术 | 用途 |
| --- | --- |
| Python 3.10+ | ETL 脚本与命令行入口 |
| pandas / openpyxl | Excel 读取、清洗及 CSV 输出 |
| SQL（MySQL 风格） | 订单关联、月度汇率连接与异常标记示例 |
| Power BI | 分析模型与看板展示；仓库提供截图，未附 PBIX 文件 |
| SQLAlchemy / PyMySQL | 依赖清单中保留的数据库工具；当前 ETL 不直接连接数据库 |

## 🏗 数据流程

```mermaid
flowchart LR
    A[六类物流商 Excel 账单] --> B[配置驱动清洗]
    B --> C[统一费用 CSV]
    C --> D[SQL 订单关联]
    E[月度汇率] --> F[费用与销售额折算]
    D --> F
    F --> G[Power BI 分析模型]
    G --> H[成本指标与异常复核]
```

ETL 脚本负责账单标准化；订单关联和折算逻辑由 `sql/mapping.sql` 展示，需要自行准备数据库表后运行，不会随 ETL 自动执行。详细说明见 [数据流程文档](docs/data-flow.md)。

## 🚀 快速开始

### 1. 安装依赖

在仓库根目录运行：

```bash
python -m venv .venv
```

Windows PowerShell 激活：

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS / Linux 激活：

```bash
source .venv/bin/activate
```

```bash
python -m pip install -r requirements.txt
```

### 2. 浏览示例

`sample_data/` 提供标准物流明细、订单映射和月度汇率 CSV，可直接用于理解输出结构。这些 CSV 不是 ETL 的原始 Excel 输入。

### 3. 准备原始账单并执行 ETL

自行准备 Excel 账单，按 `etl/logistics_etl.py` 中的 `PROVIDERS` 配置放入输入目录：

```text
sample_data/provider_invoices/
├── provider_a/    # Charge Details 工作表，首行为表头
├── provider_b/
├── provider_c/
├── provider_d/    # Invoice Details 工作表，第 3 行为表头
├── provider_e/    # 第 4 行为表头
└── provider_f/    # Expense Records 工作表
```

```bash
python etl/logistics_etl.py --input sample_data/provider_invoices --output output/logistics_standardized.csv --tracker output/etl_tracker.json
```

仓库未附原始账单。输入目录为空或不存在时，脚本仍会生成只有表头的 CSV，不能据此判断真实账单处理成功。建议使用 `.xlsx` 文件，读取引擎为 openpyxl。

**增量输出行为：** 每次输出仅包含本次新处理或变更文件的数据，并覆盖指定 CSV；它不是累计明细表。复用 tracker 且文件未变时，输出可能为空。需要保留历史批次时，请使用不同输出文件名；当前去重范围仅限单次运行。

## 📂 项目结构

```text
.
├── README.md
├── requirements.txt
├── etl/
│   └── logistics_etl.py
├── sql/
│   └── mapping.sql
├── docs/
│   └── data-flow.md
├── sample_data/
│   ├── logistics_sample.csv
│   ├── order_mapping_sample.csv
│   └── currency_rates_sample.csv
└── assets/
    └── dashboard.png
```

## 📊 数据模型与业务规则

| 输出字段 | 含义 |
| --- | --- |
| `provider` | 匿名物流商 |
| `billing_date` | 账单或业务日期 |
| `currency` | 账单币种 |
| `tracking_number` | 运单号 |
| `warehouse_order_number` | 仓库订单号 |
| `weight_kg` | 重量（公斤） |
| `fee_type` / `fee_detail` | 费用大类与明细 |
| `amount` | 原币费用，保留正负金额 |
| `source_file` | 来源文件名 |

- Provider A 固定使用 EUR，Provider B 使用 CAD；Provider C 取发货时间作为业务日期。
- 运单号缺失时，ETL 使用仓库订单号构造业务键；两种标识均缺失的记录不进入标准输出。
- SQL 对 Provider E 使用仓库订单号关联，其余物流商使用运单号。
- 费用金额参与去重键，避免直接合并不同金额的费用；生产场景仍需稳定的来源行标识。
- 账单费用与销售额分别按账单日期对应月份、各自币种折算。

### 指标口径

| 指标 | 分析口径 |
| --- | --- |
| 物流成本占比 | 总物流成本 ÷ 去重后的运单销售额 |
| 单票成本 | 总物流成本 ÷ 去重运单数 |
| 单件成本 | 总物流成本 ÷ 发货件数 |
| 合包率 | 发货件数 ÷ 去重运单数 |
| 异常成本 | 按运单汇总后，物流成本占比达到 11% 时进入复核 |
| 映射缺失 | 订单关联后缺少主 SKU 的记录，按 SQL 示例标记 |

看板还可从月份、物流商、国家、仓库和 SKU 维度观察成本、销售额、票数、件数与环比。

注意：当前 SQL 的 `cost_exception_flag` 在费用明细行上计算，尚未实现运单汇总后的 11% 判断；构建实际看板时需先统一粒度，避免多条费用行重复累计订单销售额。缺失汇率及销售额非正值也需要单独复核，不能仅依赖该标记。

## 🔒 数据与展示边界

本仓库不包含生产账号、IP 地址、网络路径、客户信息或真实订单。截图与 CSV 使用合成数据，不能用于推断实际业务收益。

当前版本展示 ETL、SQL 和分析设计，未提供生产调度、数据库自动导入、完整 Power BI 工程或自动化测试套件；不将展示截图等同于可直接部署的分析系统。

## 🧭 后续完善方向

- 增加合成 Excel 输入和自动化回归测试，覆盖缺失字段、负数冲销与重复账单。
- 分离批次输出与累计存储，增加稳定的来源行标识和跨批去重。
- 补充缺失汇率、连接一对多及订单销售额去重检查。
- 统一运单级异常口径，并补充可复现的 Power BI 模型与度量值。
