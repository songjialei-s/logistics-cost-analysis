# Power BI截图状态

用户此前提供的三张真实截图完整保存在 archive/pre-polish/，没有编辑、伪造或丢弃。
它们早于最后布局和指标展示修正，不是最终展示图片；根README明确标成历史预览。

## 请重新截取三页
打开 ../LogisticsCostDemo/LogisticsCostDemo.pbip，清除日期/服务商/类别筛选，
确认只用固定合成数据；收起编辑窗格，点击空白处取消选择框，使用Win+Shift+S截图。

| 页面 | 验证点 | 最终保存路径（相对项目根） |
|---|---|---|
| 01 成本总览 | 7947.00、72、144、99.71、49.85；环比总计空白；筛选器完整 | powerbi/screenshots/01-overview.png |
| 02 费用结构 | 六家虚构服务商、freight/handling；下拉筛选可用；说明完整 | powerbi/screenshots/02-structure.png |
| 03 异常与质量核查 | 1笔500元；有效144行、全量拒绝18条；明细默认只显示异常 | powerbi/screenshots/03-quality.png |

选择一个服务商确认费用和包裹一起变化；费用类别不缩小包裹/件数分母；
handling-only时运费卡片空白。拒绝表始终全量，不随筛选变化。
保存项目后再另存可选 powerbi/logistics_cost_demo.pbix，关闭重开核对。
提供新版截图后才更新根README图片链接和“最终验证”状态。

## 历史预览（非最终版）
![旧成本总览](archive/pre-polish/01-overview.png)
![旧费用结构](archive/pre-polish/02-structure.png)
![旧异常核查](archive/pre-polish/03-quality.png)
