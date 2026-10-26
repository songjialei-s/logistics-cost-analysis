# 验证记录
已完成：
- 固定CSV与独立合成生成规则逐字段核对，含金额、虚构标识、来源行号及拒绝记录。
- 唯一键、包裹与费用的一对多完整性、72包裹/144件/144费用行验证。
- 原SQL五条查询在CSV载入的内存SQLite中执行通过。
- 总费用7947元、运费7179元、月度2360/2488/3099元、1条高费用及18条拒绝记录符合预期。
- 32个图表的字段/度量值引用存在，位置在画布范围内。
- 40份报表/项目JSON通过微软公开schema检查。
- 原有ETL的3个测试通过；样本生成与测试文件只在独立项目runtime临时目录运行。
- 模型只引用data/demo本地CSV；未使用公司文件、接口、数据库或原始报表。

待 Desktop 验证：
- PBIP实际打开、model.bim语义模型解析、M载入与数据类型。
- DAX实际求值、日期表标记与关系筛选。
- 三页渲染、图表标题/字体/布局、交互及切片器。
- PBIX保存与重新打开、真实Desktop截图。

JSON schema通过只能证明已校验的JSON结构符合规范，
不能证明TOM模型、DAX、M或视觉对象已通过Desktop测试。
如Desktop打不开，可按README第8节手工新建，复用独立M与DAX代码。

详细机器结果：validation_report.json；原测试输出：pipeline_test_results.txt。

## Desktop 首次打开反馈修复
用户反馈 Date[Date] 的 InferredName 类型错误。
已将 CALENDAR 返回的 Date 列显式声明为 calculatedTableColumn，
并同步修复生成器与静态回归检查。
原检查覆盖JSON结构，未覆盖该模型语义规则，这是此前检查的缺口。
修复后的 Desktop 再次打开、载入与渲染仍待用户验证。

## Desktop 页面呈现反馈
用户日志提示 Cannot read properties of undefined (reading 'visualContainers')。
检查发现生成器误将PBIR内容版本写成4.0.0；已按微软官方样例改为2.0.0，
definition.pbir的版本仍为4.0。同步增加版本区分和活动页面引用检查。
该不一致已修复，但日志没有给出唯一根因，不能断言已解决所有呈现问题；
修复后的Desktop重开与页面呈现仍待用户验证。

## 用户截图核查
用户提供三页Desktop截图，已确认项目打开并呈现基础图表。
可见：总费用7947、72包裹、144件、单票运费99.71、单件运费49.85；
月度2360/2488/3099，环比显示5.4%/24.6%；1条待核查、500元、18条拒绝、144有效费用行。
这验证了截图中这些结果，不代表所有筛选交互已测试。
发现并修订：环比总计误显0%、筛选器截断、卡片单位缩写、异常表默认未过滤、标题对比度及说明截断。
修改后的渲染和交互需要Desktop重新打开验证。

## 发布修复验证
快照统一UTF-8无BOM/LF、Git属性及哈希已更新；全部8项测试通过。
其中5项快照回归含Git三种autocrlf设置的无写入clean过滤检查。
旧截图已完整移至screenshots/archive/pre-polish并明确标历史版本。
新版布局仍待Desktop验证，不因测试通过而标为Desktop已通过。
详细见../docs/test_report.md与../docs/release_check.md。
