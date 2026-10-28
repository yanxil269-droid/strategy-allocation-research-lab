# 策略配置研究报告工具

这是可独立运行的 Python 工具，也可作为兼容 AI 工具的 Skill。给它月度策略收益数据，它会比较七种论文配置方法和动量倾斜，输出历史表现、分时期表现、敞口、假设成本情景及研究报告。

当前版本：0.1.0 研究版。由 Yanxi Liu 在课程研究基础上设计，AI 辅助实现。报告正文目前为英文。无需 OpenAI API、AI 账号或付费数据订阅；安装依赖后，Python 可以离线完成计算。不是自动选股或买卖服务。

## 第一次使用

1. 从 GitHub 下载完整项目并解压，打开终端，进入项目根目录。
2. 准备 Python 3.11/3.12。创建虚拟环境：`python -m venv .venv`。
3. macOS/Linux：`source .venv/bin/activate`；Windows PowerShell：`.\.venv\Scripts\Activate.ps1`。无法激活时，直接使用该环境下的 Python 可执行文件。
4. 安装依赖：`python -m pip install -r requirements.txt`。
5. 运行示例：

```sh
python run_report.py examples/synthetic_excess.csv --strategies Quality Trend Defensive Value --unit decimal --return-type excess --fee-status unknown --out outputs/demo
```

用浏览器打开 `outputs/demo/report.html`。每次使用新的输出目录，工具不覆盖已有文件。示例全部为模拟数据，策略名称不代表真实策略，报告结果不能作为市场证据。

## 使用自己的数据

提供 CSV 或 XLSX，包含 `date` 和至少三个策略收益列。日期采用 YYYY-MM-DD 或 YYYYMMDD；每月一条、月份连续、无缺失值。默认需要36个月历史，至少39个月输入。输入必须是月度简单收益，不能直接使用价格、净值或波动率水平。

```sh
python run_report.py private_data/my_data.xlsx --sheet Returns --strategies A B C --unit decimal --return-type excess --fee-status net --start 2000-01 --target 0.10 --cost-bps 0 5 10 --out outputs/my-report
```

- `decimal`：0.01 表示1%；`percent`：1表示1%。
- `excess`：超额收益；`total`：总收益。总收益需要同表中的无风险月收益列，例如 `--return-type total --rf-column cash`。工具先减去无风险收益，再做超额收益分析。
- `fee-status`：源收益的费用口径，gross/net/unknown。这里只记录口径，不自动计算管理费。
- 所有策略应具有一致的币种基准和收益定义。

## 使用范围

- 比较方法：等权、均值、逆波动率、夏普、Top3夏普、MaxRet、MinVar、动量倾斜。只有三个输入时，TOP3与SR重复。
- 论文模式允许负权重和杠杆，不设置杠杆上限；不能保证适合实盘。
- 目标波动率是历史估计，不保证未来实现。复杂方法不自动优于等权。
- 成本情景使用目标敞口变化的代理，不是真实交易换手或实际扣费业绩。
- 曲线是复合超额收益研究指数，不是真实账户净值。
- 通用报告尚未包含风险因子归因及参数敏感性；外汇Fama–MacBeth是独立可选模块。

完整参数、方法、输出和Skill安装说明见 [README.md](README.md)。调用Skill仍需要一个支持读取Skill并执行Python的AI工具；仅把文档贴进聊天，不会自动运行代码。

公开文件只含代码、方法说明和模拟数据。请将个人真实数据保存在 `private_data/` 中，报告在对外分享前也应检查是否有私人路径和列名。MIT许可证只覆盖项目代码和模拟数据，不覆盖第三方论文或数据库。
