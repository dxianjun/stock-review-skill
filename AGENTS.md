# AGENTS.md - A股复盘技能 Agent 配置

## 技能 Agent 配置

### 主 Agent: 叶文洁 (main)

**角色**: A股复盘分析师

**职责**:
- 每日A股市场复盘
- 连板天梯分析
- 大资金方向追踪
- 生成复盘报告

**配置**:
```yaml
agent_id: main
name: 叶文洁
skill: stock-review-skill
model: moonshot/kimi-k2.6
```

**调用方式**:
```javascript
// 生成连板分析
sessions_spawn({
  agentId: "main",
  task: "生成今日A股连板天梯分析",
  mode: "run"
})

// 生成完整复盘报告
sessions_spawn({
  agentId: "main",
  task: "生成A股高级复盘报告并保存到桌面",
  mode: "run"
})
```

---

## 子 Agent 配置

### 数据抓取 Agent

**角色**: 市场数据获取

**职责**:
- 从AKShare获取涨停数据
- 从东方财富获取行情数据
- 数据清洗和格式化

**配置**:
```yaml
agent_id: stock-data-fetcher
parent: main
script: scripts/review_v3.py
```

### 报告生成 Agent

**角色**: Word报告生成

**职责**:
- 生成格式化Word文档
- 图表和表格制作
- 报告排版和美化

**配置**:
```yaml
agent_id: report-generator
parent: main
script: scripts/generate_word.py
```

---

## 技能调用协议

### 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| mode | string | 否 | 运行模式: lianban(连板) / full(完整) |
| output | string | 否 | 输出路径，默认桌面 |
| date | string | 否 | 指定日期，默认今日 |

### 输出格式

```json
{
  "status": "success",
  "data": {
    "report_path": "~/Desktop/A股高级复盘报告_20260507.docx",
    "lianban_count": 19,
    "top_sectors": ["通信线缆", "激光设备"],
    "risk_level": "low"
  }
}
```

### 调用示例

```bash
# 命令行调用
openclaw skill run stock-review-skill --mode full --output ~/Desktop

# Agent内部调用
const result = await exec("python3 scripts/review_v3.py lianban")
```

---

## 工作流配置

### 定时复盘任务

```yaml
# ~/.openclaw/cron/stock-review.yaml
jobs:
  - name: "每日复盘"
    schedule: "0 15 * * 1-5"  # 工作日15:00
    script: "scripts/review_v3.py"
    output: "~/Desktop"
    
  - name: "连板监控"
    schedule: "0 9,13 * * 1-5"  # 盘中监控
    script: "scripts/review_v3.py lianban"
```

### 事件触发

```yaml
# 涨停事件触发
triggers:
  - event: "stock_limit_up"
    condition: "连板数 >= 3"
    action: "notify_user"
    
  - event: "sector_surge"
    condition: "板块涨幅 >= 5%"
    action: "generate_report"
```

---

## 权限配置

```yaml
permissions:
  # 文件读写
  read: true
  write: true
  
  # 网络请求
  network: true
  
  # 执行脚本
  exec: true
  
  # 受限操作（需确认）
  delete: false
  send_email: false
```

---

## 内存管理

### 短期记忆

- 当日市场数据
- 连板股票列表
- 板块涨跌情况

### 长期记忆

- 历史复盘报告路径
- 用户偏好设置
- 常用股票池

### 记忆文件

```
memory/
├── stock_review/           # 复盘记忆
│   ├── 2026-05-07.md      # 每日复盘
│   └── lianban_history.json  # 连板历史
└── user_preferences.yaml   # 用户偏好
```

---

## 安全规范

### 数据安全

- 不存储用户交易密码
- 不泄露持仓信息
- API Key加密存储

### 操作安全

- 只读市场数据
- 不执行交易操作
- 报告本地生成

### 合规要求

- 免责声明必须包含
- 不构成投资建议
- 数据仅供参考

---

## 监控与日志

### 日志位置

```
logs/
├── stock-review.log      # 技能日志
├── data-fetch.log        # 数据获取日志
└── error.log             # 错误日志
```

### 监控指标

| 指标 | 说明 | 阈值 |
|------|------|------|
| data_latency | 数据延迟 | < 5s |
| success_rate | 成功率 | > 95% |
| report_gen_time | 报告生成时间 | < 30s |

---

## 故障排查

### 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 数据获取失败 | AKShare超时 | 检查网络，重试 |
| 报告生成失败 | 模板缺失 | 检查templates目录 |
| 中文乱码 | 字体缺失 | 安装中文字体 |
| 权限不足 | 文件权限 | chmod 755 |

### 紧急恢复

```bash
# 重启技能
openclaw skill restart stock-review-skill

# 清除缓存
rm -rf ~/.cache/akshare

# 重新安装
openclaw skill reinstall stock-review-skill
```

---

## 更新维护

### 自动更新

```bash
# 检查更新
openclaw skill check-update stock-review-skill

# 自动更新
openclaw skill update stock-review-skill
```

### 版本管理

```yaml
version: 3.0.0
changelog:
  - version: "3.0.0"
    date: "2026-05-08"
    changes:
      - "使用AKShare获取正确连板数据"
      - "修正连板定义"
      - "添加Word报告生成"
```

---

*最后更新：2026-05-08*
*版本：v3.0.0*
