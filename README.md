# Superstore零售经营分析

商业数据分析期末项目，使用官方公开的虚构零售教学数据，以 Python 完成数据获取、清洗、多表关联、五类商业模型、30幅教材模板复现图、19幅分析图（含9幅业务模型图）和 Streamlit 联动大屏。
## 快速开始

建议 Python 3.12（固定依赖版本需 Python 3.11及以上）。下面命令在 **VS Code 终端** 运行，不要写到 `.py` 文件第一行。建议使用单独的虚拟环境。

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python run_all.py
.venv\Scripts\python -m streamlit run dashboard.py
```

macOS / Linux 中把 `.venv\Scripts\python` 换成 `.venv/bin/python`。项目数据已附带，一键分析正常情况下不需要再次联网下载。若缺少原件，程序仅访问下方指定官方二进制文件地址，并验证 SHA256。未编写网页爬虫、网页解析、模拟登录代码。

### Jupyter Notebook

打开 `商业数据分析.ipynb`，在 VS Code 选择上述虚拟环境作为内核，依次运行即可。若使用 JupyterLab，可在虚拟环境安装 `jupyterlab`，再执行 `python -m jupyterlab`。Notebook 已保存一次实际执行的表格与图形输出。脚本与 Notebook 复用同一套函数，防止计算口径分叉。

## 研究结论

- 9,994条明细，5,009个独立订单，793位客户，1,862个商品ID；2018-01-03至2021-12-30。
- 销售额2,297,200.86 USD，利润286,397.02 USD，综合利润率12.47%。
- 2021年RFM高价值活跃190人，占当年693位客户27.42%，贡献47.97%销售额；另100位历史客户2021年没有交易，单列为未交易客户，未混入八分类。
- A类商品414个，占22.23%，贡献80.04%销售额。
- Holt-Winters留出集MAPE18.50%，RMSE14,124.15 USD；季节朴素基线MAPE24.52%，RMSE18,985.70 USD。历史外推至2022年1—6月只用于模型演示，不是2026年的现实经营预测。

## 数据来源与授权说明

| 项目 | 内容 |
|---|---|
| 名称 | Tableau Sample Superstore，属于课程推荐的官方示例数据 |
| 官方介绍 | https://help.tableau.com/current/guides/get-started-tutorial/en-us/get-started-tutorial-connect.htm |
| 下载入口 | https://www.tableau.com/learn/tutorials/on-demand/getting-started-part3 |
| 官方文件 | https://www.tableau.com/sites/default/files/2021-05/Sample%20-%20Superstore.xls |
| 获取方式 | 官方XLS文件一次性直接下载；未使用Tableau软件绘图 |
| 获取日期 | 2026-11-04（北京时间日期记录） |
| 文件SHA256 | `03d9e99f29755e641075b0caedf00d10e9416fda3668039dc7c9982500a329fc` |
| 数据性质 | 官方明确为虚构零售公司的教学样例；不是实际企业交易 |
| License | 下载页未单列独立开放数据许可，不推定为CC0、CC BY或公有领域；保留来源，仅作为课程教学样例使用，第三方原始数据不在项目代码许可范围内 |
| 抽样与补造 | 全量使用，无抽样，无Faker补充；42仅用于预测残差重采样 |

## 治理与指标口径

1. Orders主键为Row ID；Order ID对应多个商品明细，不能据此删重。原始主表无完全重复和关键字段缺失。
2. 11个缺失邮编标记`UNKNOWN`。销售额、数量、日期、折扣的合法性均通过检查。1,167个销售额IQR上界标记只作为业务复核线索，未直接删除；1,871条负利润明细是经营事实，予以保留。
3. Returns原800行含504条订单键重复，先归并为296个独立退货订单，再以`many_to_one`关联。People以Region关联，同样校验为多对一；关联前后行数、销售额和利润对账一致。
4. 32个商品ID对应多个名称，维表只保留一致的ID、Category和Sub-Category，原始名称留在明细。Customer ID的姓名和Segment映射没有冲突。
5. 退货标识是订单级布尔标记；未提供退款金额或退货数量，不推算净销售额，不将整单利润再次扣减。
6. 综合利润率=利润合计/销售额合计，不是明细利润率的算术平均。金额保持原精度计算，展示四舍五入至分；金额单位按美国区教学样例记为USD。

详细字段字典见 `docs/数据字典.md`，数据质量日志见 `outputs/tables/cleaning_audit.json`。

## 模型与参数

| 模型 | 实现与依据 | 核心输出 |
|---|---|---|
| RFM八分类 | 2021年观察窗，2021-12-31基准；R≤58天、F≥2个独立订单、M≥604.91 USD为各维高组；中位数切分且保留并列 | fig11、12 |
| 帕累托ABC | 商品按累计销售降序；A覆盖至少80%、A+B至少95%；跨阈值商品归前组；相同金额按ID排序 | fig13、14 |
| 同期群 | 首次被观察购买月份为同期群；每月客户去重；未到观察期为NaN；留存分母只纳入有足够观察期的客户 | fig15、16 |
| 同比环比 | 月销售额按日期排序；同比12期、环比1期；首期缺值不填0 | fig01、02、17 |
| Holt-Winters | 加性季节、12期、加性阻尼趋势；前36月训练、后12月留出；3000条中心化残差bootstrap路径，seed42 | fig18、19 |

预测区间是固定拟合参数条件下未来观测的95%预测区间，不是均值置信区间；没有覆盖参数不确定性。回测误差只在留出集计算，基线仅用上一年的同月数值。分群和描述分析使用全量历史不会进入留出预测训练。


- `outputs/templates/`：30幅200dpi的Matplotlib复现PNG，全部以Superstore实际指标重新计算绘制。
- `outputs/tables/template_mapping.csv`：30行对应关系，记录PPT页码、页内图块、图形名称、指标口径、布局、配色、标签、图例位置、标题设计和业务适配说明。
- `outputs/tables/template_inputs.json`：每幅图的真实输入数值，可独立复核。
- `docs/模板复现逐图对照.html`：离线打开，逐图比较原参考与Python输出。
- `assets/reference/source_index.json`：原PPT的shape_id与图块定位，保留来源。
- `outputs/figures/`：原19幅分析图，前10幅为描述分析，后9幅为RFM、ABC、同期群、趋势与预测模型图；不再将这10幅描述图冒充教材复现。

复现采用从原图取样的深蓝背景`#1A1E43`，蓝色`#188EFC`、红色`#E74E69`、青色`#62C7D8`与黄色`#F5C353`等主色，保留左上粗体标题、其下副标题和左下数据来源结构。图形类型与布局逐项参考原图，数值与业务文字换成真实指标，**不承诺逐像素相同**。

## 交互式大屏

侧栏日期、区域、品类、客户类型四个筛选器共同生成一个过滤后的DataFrame，同时驱动4张KPI卡、月度趋势、品类环形、区域散点、子品类排名、客户贡献散点、折扣利润率、明细表和CSV下载。共6张可交互图表，支持悬停、缩放和导出；全局联动是筛选器驱动，不包含点击某一图表反向刷选其他图表。

已验证默认视图、West区域选择和空选择处理；这些是程序化交互检查，不是浏览器截图。可自行运行后录屏，演示“全部→West→Technology→导出”，并在教材模板对照区选择T01—T30查看原图和复现。

## 项目结构

```text
data/raw/                  官方XLS原件与来源记录
data/clean/                清洗明细、客户/商品/退货表、SQLite
scripts/pipeline.py        官方文件获取、治理、五类模型
scripts/visuals.py         19幅分析图
scripts/templates.py       30幅教材模板逐项复现
outputs/figures/           19幅描述与业务模型图
outputs/templates/         30幅教材模板复现图
assets/reference/          30幅原参考图与来源定位
outputs/tables/            指标、参数、质量日志、预测、图表索引
docs/                     论文与数据字典
dashboard.py              Streamlit联动仪表板
商业数据分析.ipynb         已执行的Jupyter Notebook
requirements.txt          固定核心依赖
run_all.py                一键复现入口
```

## 公开仓库与分工

```bash
git remote add origin https://github.com/LJH824-526/Visualization-Python
git branch -M main
git push -u origin main
```
