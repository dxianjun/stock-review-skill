# SKILL.md - A股高级复盘技能

## 技能信息

- **名称**: stock-review-skill
- **版本**: 3.0.0
- **作者**: 叶文洁
- **更新日期**: 2026-05-08

## 功能描述

自动生成A股每日高级复盘Word报告，包含：
1. **大资金方向** - 大成交额Top20
2. **连板天梯** - AKShare正确连板数据
3. **跌停风险** - 非ST跌停监控
4. **大涨板块** - 板块涨幅Top5
5. **主线判断** - 市场主线方向
6. **股票池** - 次日跟踪标的

## 核心特性

### 连板天梯（重点）

**数据源**: AKShare `stock_zt_pool_em`

**连板定义**: 
- 连续涨停天数（当前连续涨停）
- 非"N日内累计涨停次数"

**示例**:
```
5板: 金螳螂(1只)
3板: 中国长城、福达合金(2只)
2板: 东阳光、德林海等(16只)
1板: 81只
```

### 大资金追踪

**筛选条件**: 成交额 ≥ 15亿

**输出**: Top20股票列表

## 使用方法

### 命令行

```bash
# 连板天梯
python3 scripts/review_v3.py lianban

# 完整复盘
python3 scripts/review_v3.py

# 生成Word报告
python3 scripts/generate_word.py
```

### OpenClaw Agent

```javascript
// 调用技能
exec("python3 ~/.openclaw/skills/stock-review-skill/scripts/review_v3.py lianban")

// 生成报告
exec("python3 ~/.openclaw/skills/stock-review-skill/scripts/generate_word.py")
```

## 数据源

| 数据 | 来源 | 可靠性 |
|------|------|--------|
| 连板数据 | AKShare | ⭐⭐⭐⭐⭐ |
| 行情数据 | 东方财富 | ⭐⭐⭐⭐ |
| 板块数据 | 东方财富 | ⭐⭐⭐⭐ |

## 输出文件

```
~/Desktop/
├── A股高级复盘报告_YYYYMMDD.docx
└── 连板天梯_YYYYMMDD.txt
```

## 依赖

```
akshare>=1.10.0
python-docx>=0.8.11
requests>=2.28.0
pandas>=1.5.0
```

## 更新日志

### v3.0.0 (2026-05-08)
- 使用AKShare获取正确连板数据
- 修正连板定义
- 添加Word报告生成

### v2.0.0
- 基础复盘功能
- 同花顺数据源

## 许可证

MIT License
