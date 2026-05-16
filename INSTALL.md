# INSTALL.md - A股高级复盘技能安装指南

## 技能名称

**stock-review-skill** - A股每日高级复盘报告生成器

## 功能概述

自动生成A股每日复盘Word报告，包含：
- 大资金方向（大成交额Top20）
- 连板天梯分析（AKShare正确数据）
- 跌停风险监控
- 大涨板块追踪
- 主线方向判断
- 股票池建立

## 系统要求

- **OpenClaw**: v2.0+
- **Python**: 3.11+
- **依赖包**: akshare, python-docx, requests

## 安装步骤

### 1. 安装Python依赖

```bash
pip3 install akshare python-docx requests pandas
```

### 2. 安装技能包

将本技能包复制到OpenClaw技能目录：

```bash
# 方法1：直接复制
cp -r stock-review-skill ~/.openclaw/skills/

# 方法2：使用OpenClaw命令
openclaw skill install stock-review-skill
```

### 3. 配置环境变量（可选）

```bash
# 编辑 ~/.zshrc 或 ~/.bashrc
export AKSHARE_CACHE_DIR="$HOME/.cache/akshare"
```

### 4. 验证安装

```bash
# 测试连板数据获取
python3 ~/.openclaw/skills/stock-review-skill/scripts/review_v3.py lianban

# 测试完整复盘报告
python3 ~/.openclaw/skills/stock-review-skill/scripts/review_v3.py
```

## 目录结构

```
stock-review-skill/
├── SKILL.md              # 技能说明
├── INSTALL.md            # 本文件
├── AGENTS.md             # Agent配置
├── scripts/
│   ├── review_v3.py      # 主程序
│   └── generate_word.py  # Word生成器
├── templates/
│   └── review_template.docx  # Word模板
└── requirements.txt      # Python依赖
```

## 使用方法

### 命令行使用

```bash
# 生成连板天梯分析
python3 scripts/review_v3.py lianban

# 生成完整复盘报告（输出到桌面）
python3 scripts/review_v3.py
```

### OpenClaw Agent调用

```javascript
// 在Agent中调用
exec("python3 ~/.openclaw/skills/stock-review-skill/scripts/review_v3.py lianban")

// 生成Word报告
exec("python3 ~/.openclaw/skills/stock-review-skill/scripts/generate_word.py")
```

### 定时任务配置

```bash
# 编辑 crontab
crontab -e

# 每日收盘后自动生成（15:30）
30 15 * * 1-5 python3 ~/.openclaw/skills/stock-review-skill/scripts/review_v3.py >> /tmp/stock_review.log 2>&1
```

## 数据源说明

| 数据类型 | 来源 | 可靠性 |
|---------|------|--------|
| 连板天梯 | AKShare stock_zt_pool_em | ⭐⭐⭐⭐⭐ |
| 大成交额 | 东方财富 | ⭐⭐⭐⭐ |
| 板块涨幅 | 东方财富 | ⭐⭐⭐⭐ |
| 指数数据 | 东方财富 | ⭐⭐⭐⭐⭐ |

## 常见问题

### Q: AKShare安装失败？
```bash
pip install --upgrade akshare
# 或
pip install akshare -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: 中文显示乱码？
确保系统已安装中文字体：
```bash
# macOS
brew install font-noto-sans-cjk

# Linux
sudo apt-get install fonts-noto-cjk
```

### Q: 数据获取超时？
```bash
# 设置超时参数
export AKSHARE_TIMEOUT=30
```

## 更新日志

### v3.0 (2026-05-08)
- 使用AKShare获取正确连板数据
- 修正连板定义（连续涨停天数）
- 添加Word报告生成功能
- 优化板块归类逻辑

### v2.0 (之前版本)
- 基础复盘功能
- 同花顺数据源

## 支持

- **GitHub**: https://github.com/openclaw/stock-review-skill
- **文档**: https://docs.openclaw.ai/skills/stock-review
- **问题反馈**: 提交Issue到GitHub仓库
