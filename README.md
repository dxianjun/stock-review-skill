# stock-review-skill

A股复盘技能（v3），用于抓取市场数据并输出日内复盘分析，重点是“连板天梯”的正确口径。

## 技能定位

- 目标：自动化生成 A 股每日复盘内容
- 核心价值：统一复盘口径，尤其是连板定义（连续涨停天数）
- 典型使用场景：盘后快速复盘、连板梯队观察、大资金方向跟踪

## 功能分析

根据 `SKILL.md` 与 `AGENTS.md`，技能设计目标包含以下 6 个模块：

1. 大资金方向：按成交额筛选高活跃标的
2. 连板天梯：基于 AKShare 涨停池构建连板分层
3. 跌停风险：识别非 ST 跌停风险
4. 大涨板块：统计板块涨幅排名
5. 主线判断：提炼市场主线方向
6. 股票池：给出次日跟踪标的

当前仓库中已落地的是 `scripts/review_v3.py`，可完成连板分析与控制台版完整复盘输出。

## 技术架构（当前实现）

- 运行入口：`scripts/review_v3.py`
- 主要数据源：
  - 首选：AKShare `stock_zt_pool_em`（连板口径）
  - 兜底：东方财富 `getTopicZTPool`
  - 行情接口：东方财富 `push2`/`push2his`
- 并发策略：`ThreadPoolExecutor` 并发拉取分页行情数据
- 输出形态：终端文本输出（`full` / `lianban`）

## Agent 设计（文档层）

`AGENTS.md` 中定义了主从 Agent：

- 主 Agent：`main`（叶文洁）
  - 职责：复盘统筹、连板分析、资金方向跟踪
- 子 Agent：`stock-data-fetcher`
  - 职责：抓取并清洗市场数据
- 子 Agent：`report-generator`
  - 职责：生成 Word 报告

这套设计适合后续拆分成“数据层 + 报告层”的两阶段流水线。

## 运行方式

```bash
# 完整复盘（终端输出）
python3 scripts/review_v3.py

# 连板天梯（终端输出）
python3 scripts/review_v3.py lianban
```

## 当前状态与文档差异

以下是“文档目标”与“仓库现状”的差异：

1. `AGENTS.md`/`SKILL.md` 提到 `scripts/generate_word.py`，但仓库中暂无该文件
2. 仓库有 `templates/review_template.docx`，说明 Word 报告链路预留了模板但未完整实现
3. `AGENTS.md` 中的内存目录、日志目录、定时任务配置是设计说明，仓库内未见对应落地脚本与目录结构

## 风险与限制

1. 数据依赖外部接口，可能受网络波动、限流或字段变更影响
2. 指数分析使用脚本内置缓存值（`CACHED_INDEX`），不是实时计算
3. 连板数据在 AKShare 不可用时回退东方财富，跨源字段可能存在口径差异

## 建议迭代方向

1. 补齐 `scripts/generate_word.py`，打通模板化报告导出
2. 增加统一输出（JSON + 文本），便于 Agent 与自动化任务消费
3. 增加日志与错误分级（data-fetch/report/system）
4. 将配置（阈值、输出路径、调度参数）外置到 `yaml` 或 `.env`
5. 为关键模块补充测试：连板分组、涨跌停判定、接口兜底逻辑

## 依赖

见 `requirements.txt`：

- akshare
- pandas
- requests
- python-docx
