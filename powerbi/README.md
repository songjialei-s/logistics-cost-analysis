# Power BI 独立物流成本演示
状态：已生成 PBIP、模型、三页图表配置、DAX 和固定合成 CSV；**待 Desktop 验证**。
未生成二进制 PBIX，也没有经过 Desktop 刷新、渲染或截图验证。
所有实现独立编写；只读取本演示项目的数据，不依赖任何公司文件或服务。

## 1. 打开哪个文件
打开 powerbi/LogisticsCostDemo/LogisticsCostDemo.pbip。
必须保留旁边 .Report 和 .SemanticModel 目录。使用支持 PBIP/PBIR 的 Power BI Desktop。
项目自动生成格式依照微软公开 JSON schemas；schema通过不等于Desktop可用性保证。
若版本不支持PBIP，先更新Desktop；若仍打不开，按末尾手工方案重建。

## 2. 修改路径并载入
打开后进入 转换数据 -> 管理参数 -> DataFolder。
本机默认值指向本项目 data/demo。下载者改为自己克隆目录下 data/demo 的绝对路径，
建议用正斜杠，例如 D:/GitHubProjects/logistics-cost-analysis/data/demo。
参数不上传凭据；数据源仅为本地CSV。
关闭并应用，再刷新演示数据。PBIP不含数据缓存，首次打开必须载入。
不要选择本机其他业务文件或连接任何数据库。

## 3. 检查模型
模型视图确认：
Date[Date] 1 -> * parcels[ship_date]；
parcels[parcel_key] 1 -> * charges[parcel_key]；
均活动、单向。rejected独立无关系。
Date是2026完整日历；在表工具“标记为日期表”选择Date[Date]。
日期使用Date表，服务商使用parcels[provider]，费用类别使用charges[category]。
包裹键为 provider|tracking_id|yyyy-MM-dd；构建器已检查本样本没有分隔符冲突。
费用表的item_count隐藏，禁止把费用行的件数相加。

## 4. 核对结果
清除三个页面的所有筛选，查看第一页：
Total Cost CNY = 7,947.00；Parcels = 72；Items = 144。
Freight CNY = 7,179；Freight per Parcel CNY = 99.708333；
Freight per Item CNY = 49.854167。
月度：2026-01=2,360，02=2,488，03=3,099。
环比：1月空白；2月约5.4237%；3月约24.5579%。
质量页：144有效费用行、18全量拒绝记录、1待核查费用行、500元待核查金额。
点选一个服务商时费用与包裹一起变化；类别只影响费用，不改变包裹/件数分母。
仅选handling时Freight卡片空白。拒绝数据始终18，标题明确其不随筛选。
检查首月环比为空、跨月日期筛选、费用总数与Python/SQL一致。
在数据窗格选择度量值查看DAX，全部公式也在 measures.dax。

## 5. 页面与异常筛选
三个页面已配置，不代表已经人工检查布局。请检查是否有空白或报错图表、文本截断。
第三页费用表已默认使用is_anomaly=1的视觉对象筛选器聚焦高费用，
再核对source_file/source_row。异常仅是>400元的模拟规则，不代表实际错账。
截图时确认该表仅显示500元的合成费用，并记录筛选范围。

## 6. 保存PBIX与截图
验证后 文件 -> 另存为 -> Power BI文件(.pbix)，保存到
powerbi/logistics_cost_demo.pbix。不要仅修改扩展名。
保留载入后的合成数据；关闭再打开，检查无须原机器目录即可查看缓存图表。
需要刷新时仍须设置DataFolder。
截图：各页调到适合页面，收起不必要窗格，使用Windows截图工具Win+Shift+S，
保存到powerbi/screenshots/01-overview.png、02-structure.png、03-quality.png。
这些应是真实Desktop截图；本项目不提供冒充报表的渲染图片。

## 7. GitHub提交
保留：src、sql、config、tests、requirements、data/sample、data/demo、
powerbi/LogisticsCostDemo完整项目、DAX/M/说明、经验证PBIX及实际截图。
不提交：runtime、.venv、.env、__pycache__、任何.pbi目录或本机缓存/凭据。
现有data/output被忽略，固定data/demo可提交。
发布前审查Changes/暂存区，仅在独立项目提交；本次没有init、commit、push或远程发布。
文档及README中的“待Desktop验证”应在实际操作通过后才更新。

## 8. 若PBIP打不开：手工兜底
新建空白PBIX。转换数据中新建文本参数DataFolder，指向data/demo。
建三个空白查询，分别命名charges、parcels、rejected；
把powerbi/queries中同名.pq粘到高级编辑器，关闭并应用。
新建日期表 Date = CALENDAR(DATE(2026,1,1),DATE(2026,12,31))；
增加 Month = FORMAT('Date'[Date], "yyyy-MM")、
MonthIndex = YEAR('Date'[Date])*100+MONTH('Date'[Date])，
Month按MonthIndex排序，标记日期表。
按第3节建立关系；按measures.dax逐个“新建度量值”，不要整段作为一个公式粘贴。
根据page_configuration.json和page_layout.md建立三页，用内置卡片、柱/条形图、
折线图、环形图、表格、文本框、日期/服务商/类别切片器。
核对所有第4节数值后再保存PBIX。

## 自动检查的复现方式（可选）
项目根目录执行：
python powerbi/validate_demo.py
默认检查CSV、原SQL、模型关系、图表绑定及原有ETL测试，不需要数据库或网络。
官方JSON Schema额外检查：
python -m pip install --no-cache-dir --target runtime/powerbi_validation_deps -r powerbi/requirements-validation.txt
python powerbi/validate_demo.py --schemas
仅从developer.microsoft.com读取公开规范；缓存放在被Git忽略的runtime内。
首次缺少Python依赖时，先按根README安装requirements.txt。
构建器会更新固定CSV快照及项目定义，不是平常查看报表的必要步骤，
只有主动更新合成样本后才运行 python powerbi/build_demo.py，然后重新校验。
不要在Desktop同时编辑项目时重跑构建器，以免覆盖你的演示页面调整。
