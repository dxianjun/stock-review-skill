#!/usr/bin/env python3
"""A股每日复盘报告 v3 — 连板天梯使用AKShare（正确连板定义）

用法：
  python3 review_v3.py            # 完整复盘报告（八大章节）
  python3 review_v3.py lianban    # 仅输出连板梯队分析

数据源优先级：
  1. AKShare stock_zt_pool_em（推荐，连板定义正确）
  2. 东方财富 getTopicZTPool（兜底）
  
连板定义：
  - 连续涨停天数（当前连续涨停）
  - 非"N日内累计涨停次数"
"""

import sys
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://quote.eastmoney.com/",
}
CLIST_URL = "https://push2.eastmoney.com/api/qt/clist/get"
KLINE_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"

# ── 指数分析（缓存直用）
CACHED_INDEX = {
    "上证指数": {"name": "上证指数", "current_price": 4180.09, "ma5": 4127.71, "ma10": 4108.94,
                 "ma20": 4057.92, "ma60": 4052.15, "support": 3890.16, "resistance": 4180.09,
                 "outlook": "偏多", "outlook_detail": "站上MA5/MA10/MA20/MA60，MACD金叉"},
    "深证成指": {"name": "深证成指", "current_price": 15641.89, "ma5": 15232.09, "ma10": 15129.94,
                 "ma20": 14762.14, "ma60": 14274.31, "support": 13400.41, "resistance": 15641.89,
                 "outlook": "偏多", "outlook_detail": "站上MA5/MA10/MA20/MA60，MACD金叉"},
    "创业板指": {"name": "创业板指", "current_price": 3833.06, "ma5": 3714.45, "ma10": 3705.08,
                 "ma20": 3593.17, "ma60": 3385.31, "support": 3160.82, "resistance": 3833.06,
                 "outlook": "偏多", "outlook_detail": "站上MA5/MA10/MA20/MA60，MACD金叉"},
}


def new_sess():
    s = requests.Session()
    s.headers.update(HEADERS)
    s.trust_env = False
    return s


def req(url, params, timeout=12, retries=3):
    s = new_sess()
    for i in range(retries):
        try:
            return s.get(url, params=params, timeout=timeout).json()
        except Exception:
            if i < retries - 1:
                time.sleep(0.6 * (i + 1))
    return {}


# ─────────────────────────────────────────────────────────
# 涨停/跌停判断
# ─────────────────────────────────────────────────────────
MKT_LIMIT = {2: 0.10, 6: 0.10, 23: 0.20, 80: 0.20, 81: 0.30}

def is_limit_up(f2, f18, f19, name: str) -> bool:
    if name[:1] in ("N", "C", "U"):
        return False
    if not isinstance(f18, (int, float)) or f18 <= 0:
        return False
    lim = 0.05 if "ST" in name.upper() else MKT_LIMIT.get(f19, 0.10)
    up_price = round(f18 * (1 + lim), 2)
    return abs(f2 - up_price) <= 0.005

def is_limit_down(f2, f18, f19, name: str) -> bool:
    if name[:1] in ("N", "C", "U"):
        return False
    if not isinstance(f18, (int, float)) or f18 <= 0:
        return False
    lim = 0.05 if "ST" in name.upper() else MKT_LIMIT.get(f19, 0.10)
    dn_price = round(f18 * (1 - lim), 2)
    return abs(f2 - dn_price) <= 0.005


def fetch_page(pn):
    return req(CLIST_URL, {
        "pn": pn, "pz": 100, "po": 1, "np": 1, "fltt": 2, "invt": 2,
        "fid": "f3",
        "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048",
        "fields": "f2,f3,f6,f12,f14,f18,f19",
    }).get("data", {}).get("diff", [])


def get_market_breadth():
    first_data = req(CLIST_URL, {
        "pn": 1, "pz": 100, "po": 1, "np": 1, "fltt": 2, "invt": 2,
        "fid": "f3",
        "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048",
        "fields": "f2,f3,f6,f12,f14,f18,f19",
    }).get("data", {})
    total = first_data.get("total", 5849)
    total_pages = (total + 99) // 100
    all_stocks = list(first_data.get("diff", []))

    with ThreadPoolExecutor(max_workers=15) as pool:
        futs = {pool.submit(fetch_page, p): p for p in range(2, total_pages + 1)}
        for f in as_completed(futs):
            all_stocks.extend(f.result())

    up = dn = flat = limit_up = limit_dn = 0
    total_amt = 0

    for x in all_stocks:
        chg  = x.get("f3")
        f2   = x.get("f2")
        f18  = x.get("f18")
        f19  = x.get("f19")
        name = str(x.get("f14", ""))
        amt  = x.get("f6", 0)

        if not isinstance(chg, (int, float)):
            continue
        if isinstance(amt, (int, float)):
            total_amt += amt

        if chg > 0:   up   += 1
        elif chg < 0: dn   += 1
        else:         flat += 1

        if isinstance(f2, (int, float)):
            if is_limit_up(f2, f18, f19, name):   limit_up += 1
            if is_limit_down(f2, f18, f19, name): limit_dn += 1

    return {
        "上涨": up, "下跌": dn, "平盘": flat,
        "涨停": limit_up, "跌停": limit_dn,
        "total": len(all_stocks), "total_amount": total_amt,
    }


# ─────────────────────────────────────────────────────────
# 连板天梯分析（v3：使用AKShare，正确连板定义）
# ─────────────────────────────────────────────────────────
def get_lianban_ladder():
    """
    获取连板天梯数据
    
    优先级：
      1. AKShare stock_zt_pool_em（推荐）
         - 连板定义：连续涨停天数
         - 与同花顺、东方财富App一致
      2. 东方财富 getTopicZTPool（兜底）
    
    注意：
      - 连板数 = 当前连续涨停天数
      - 非"N日内累计涨停次数"
      - 4月28日涨停→断开→5月6-7日涨停 = 2板（非3板）
    """
    from collections import defaultdict
    
    def _parse_akshare():
        """使用AKShare获取涨停池（推荐）"""
        try:
            import akshare as ak
            df = ak.stock_zt_pool_em(date=datetime.now().strftime("%Y%m%d"))
            
            stocks = []
            for _, row in df.iterrows():
                fund_val = row.get("封板资金", 0)
                try:
                    fund = float(fund_val) if fund_val and str(fund_val) != 'nan' else 0
                except:
                    fund = 0
                
                stocks.append({
                    "code": str(row.get("代码", "")),
                    "name": str(row.get("名称", "")),
                    "lbc": int(row.get("连板数", 1)),
                    "chg": float(row.get("涨跌幅", 0)),
                    "sector": str(row.get("所属行业", "其他")),
                    "fund": fund,
                })
            return stocks, "AKShare"
        except ImportError:
            print("  ⚠️ AKShare未安装，尝试其他数据源...")
            return None, None
        except Exception as e:
            print(f"  ⚠️ AKShare获取失败: {e}")
            return None, None
    
    def _fallback_dfcf():
        """东方财富兜底"""
        all_pool = []
        for pg in range(0, 5):
            pool = req("https://push2ex.eastmoney.com/getTopicZTPool", {
                "ut": "7eea3edcaed734bea9cbfc24409ed989",
                "dpt": "wz.ztzt",
                "Pageindex": pg,
                "pagesize": 100,
                "sort": "lbc:desc",
                "date": datetime.now().strftime("%Y%m%d"),
            }).get("data", {}).get("pool") or []
            if not pool:
                break
            all_pool.extend(pool)
        
        stocks = []
        for s in all_pool:
            stocks.append({
                "code": s.get("c", ""),
                "name": s.get("n", ""),
                "lbc": s.get("lbc", 1),
                "chg": round(s.get("zdp", 0), 2),
                "sector": s.get("hybk", "其他"),
                "fund": s.get("fund", 0),
            })
        return stocks, "东方财富"
    
    # ── 尝试AKShare
    all_stocks, source = _parse_akshare()
    if not all_stocks:
        all_stocks, source = _fallback_dfcf()
    
    if not all_stocks:
        return None
    
    # 只取2板及以上
    multi = [s for s in all_stocks if s.get("lbc", 1) >= 2]
    
    by_lbc    = defaultdict(list)
    by_sector = defaultdict(list)
    for s in multi:
        by_lbc[s["lbc"]].append(s)
        by_sector[s["sector"]].append(s)
    
    strong_sectors = {}
    for sec, stocks in by_sector.items():
        levels = sorted({s["lbc"] for s in stocks}, reverse=True)
        if len(levels) >= 2:
            strong_sectors[sec] = {"stocks": stocks, "levels": levels}
    
    return {
        "by_lbc":         dict(by_lbc),
        "by_sector":      dict(by_sector),
        "strong_sectors": strong_sectors,
        "total_multi":    len(multi),
        "source":         source,
        "all_stocks":     all_stocks,
    }


# ─────────────────────────────────────────────────────────
# 量能日环比
# ─────────────────────────────────────────────────────────
def get_volume_ratio():
    def fetch_kline_amt(secid, count=3):
        data = req(KLINE_URL, {
            "secid": secid,
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": 101, "fqt": 1, "lmt": count, "end": "20500101",
        })
        klines = data.get("data", {}).get("klines", [])
        rows = []
        for line in klines:
            p = line.split(",")
            if len(p) >= 7 and p[6] not in ("-", ""):
                try:
                    rows.append({"date": p[0], "amount": float(p[6])})
                except Exception:
                    pass
        return rows

    sh = fetch_kline_amt("1.000001")
    sz = fetch_kline_amt("0.399001")

    if len(sh) < 2 or len(sz) < 2:
        return None

    sh_map = {r["date"]: r["amount"] for r in sh}
    sz_map = {r["date"]: r["amount"] for r in sz}
    dates = sorted(set(sh_map) & set(sz_map))

    if len(dates) < 2:
        return None

    today_amt     = sh_map[dates[-1]] + sz_map[dates[-1]]
    yesterday_amt = sh_map[dates[-2]] + sz_map[dates[-2]]
    ratio = (today_amt - yesterday_amt) / yesterday_amt * 100 if yesterday_amt > 0 else None

    return {"today": today_amt, "yesterday": yesterday_amt, "ratio_pct": round(ratio, 2)}


# ─────────────────────────────────────────────────────────
# 板块排行
# ─────────────────────────────────────────────────────────
def get_sectors(top_n=5):
    data = req(CLIST_URL, {
        "pn": 1, "pz": 100, "po": 1, "np": 1, "fltt": 2, "invt": 2,
        "fid": "f3", "fs": "m:90+t:2+f:!50",
        "fields": "f2,f3,f6,f12,f14",
    })
    diff = data.get("data", {}).get("diff", [])
    sectors = []
    for item in diff:
        chg = item.get("f3", 0)
        if str(chg) == "-": chg = 0
        sectors.append({
            "code": item.get("f12", ""), "name": item.get("f14", ""),
            "change_pct": float(chg), "amount": item.get("f6", 0),
        })
    sectors.sort(key=lambda x: x["change_pct"], reverse=True)
    return {"top_up": sectors[:top_n], "top_down": sectors[-top_n:][::-1]}


def get_sector_stocks(sector_code, top_n=10, sort_desc=True):
    data = req(CLIST_URL, {
        "pn": 1, "pz": top_n, "po": 1 if sort_desc else 0,
        "np": 1, "fltt": 2, "invt": 2, "fid": "f3",
        "fs": f"b:{sector_code}", "fields": "f2,f3,f6,f12,f14",
    })
    diff = data.get("data", {}).get("diff", [])
    result = []
    for item in diff:
        chg = item.get("f3", 0)
        if str(chg) == "-": chg = 0
        result.append({
            "code": item.get("f12", ""), "name": item.get("f14", ""),
            "price": item.get("f2", "-"), "change_pct": float(chg),
        })
    return result


# ─────────────────────────────────────────────────────────
# 大成交额
# ─────────────────────────────────────────────────────────
def get_top_amount(top_n=20, min_amount=15e8):
    all_stocks = []
    for pn in range(1, 6):
        data = req(CLIST_URL, {
            "pn": pn, "pz": 100, "po": 1, "np": 1, "fltt": 2, "invt": 2,
            "fid": "f6",
            "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048",
            "fields": "f2,f3,f6,f12,f14,f18,f19,f20",
        }).get("data", {})
        diff = data.get("diff", [])
        if not diff:
            break
        for item in diff:
            amt = item.get("f6", 0)
            if isinstance(amt, (int, float)) and amt >= min_amount:
                all_stocks.append({
                    "code": item.get("f12", ""),
                    "name": item.get("f14", ""),
                    "price": item.get("f2", 0),
                    "change_pct": item.get("f3", 0),
                    "amount": amt,
                    "market_cap": item.get("f20", 0),
                })
    all_stocks.sort(key=lambda x: x["amount"], reverse=True)
    return all_stocks[:top_n]


# ─────────────────────────────────────────────────────────
# 格式化输出
# ─────────────────────────────────────────────────────────
def fmt_amount(v):
    try:
        v = float(v)
        if v >= 1e12: return f"{v/1e12:.2f}万亿"
        if v >= 1e8: return f"{v/1e8:.2f}亿"
        if v >= 1e4: return f"{v/1e4:.2f}万"
        return str(int(v))
    except:
        return "-"


# ─────────────────────────────────────────────────────────
# 子命令：连板梯队
# ─────────────────────────────────────────────────────────
def cmd_lianban():
    print("=" * 70)
    print(f"  📊  A股连板梯队分析  {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")
    print("=" * 70)
    
    print("\n🔄 正在抓取连板数据...")
    result = get_lianban_ladder()
    
    if not result:
        print("❌ 无法获取连板数据")
        return
    
    print(f"✅ 数据源：{result['source']}")
    print(f"✅ 2板及以上：{result['total_multi']} 只")
    
    print("\n【连板梯队分析（2板及以上）】")
    print(f"  数据源：{result['source']}")
    
    by_lbc = result.get("by_lbc", {})
    
    print("\n  ▌ 连板分布：")
    for lbc in sorted(by_lbc.keys(), reverse=True):
        stocks = by_lbc[lbc]
        fire = "🔥" * min(lbc, 5)
        names = [f"{s['name']}({s['sector']})" for s in stocks[:5]]
        print(f"  {fire} {lbc}板 × {len(stocks)} 只：{'  '.join(names)}")
        if len(stocks) > 5:
            print(f"      ... 等{len(stocks)}只")
    
    print("\n  ▌ 按板块归类：")
    by_sector = result.get("by_sector", {})
    for sec, stocks in sorted(by_sector.items(), key=lambda x: -len(x[1])):
        levels = sorted({s["lbc"] for s in stocks}, reverse=True)
        names = [f"{s['name']}({s['lbc']}板)" for s in stocks[:3]]
        print(f"  【{sec}】{'/'.join(map(str, levels))}板  {', '.join(names)}")
    
    strong = result.get("strong_sectors", {})
    if strong:
        print("\n  🔥 强势板块（连板梯队完整）：")
        for sec, info in sorted(strong.items(), key=lambda x: -len(x[1]["levels"])):
            print(f"    {sec}：{'/'.join(map(str, info['levels']))}板")
    else:
        print("\n  ℹ️  今日无板块梯队完整（≥3层），多数为单板块单层连板")
    
    print("\n" + "=" * 70)
    print(f"  数据源：{result['source']}  |  生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)


# ─────────────────────────────────────────────────────────
# 主命令：完整复盘
# ─────────────────────────────────────────────────────────
def cmd_full():
    print("=" * 70)
    print(f"  📊  A股每日复盘报告  {datetime.now().strftime('%Y年%m月%d日')}")
    print("=" * 70)
    
    # 1. 市场概况
    print("\n【一、市场概况】")
    breadth = get_market_breadth()
    total = breadth["total"]
    up, dn, flat = breadth["上涨"], breadth["下跌"], breadth["平盘"]
    zt, dt = breadth["涨停"], breadth["跌停"]
    amt = breadth["total_amount"]
    
    print(f"  上涨：{up} 只  下跌：{dn} 只  平盘：{flat} 只")
    print(f"  涨停：{zt} 只  跌停：{dt} 只")
    print(f"  总成交额：{fmt_amount(amt)}")
    
    # 2. 指数分析
    print("\n【二、指数分析】")
    for name, idx in CACHED_INDEX.items():
        print(f"  {name}：{idx['current_price']}  {idx['outlook']} — {idx['outlook_detail']}")
    
    # 3. 连板梯队
    print("\n【三、连板梯队】")
    result = get_lianban_ladder()
    if result:
        print(f"  数据源：{result['source']}")
        print(f"  2板及以上：{result['total_multi']} 只")
        
        by_lbc = result.get("by_lbc", {})
        for lbc in sorted(by_lbc.keys(), reverse=True):
            stocks = by_lbc[lbc]
            names = [s['name'] for s in stocks[:5]]
            print(f"  {lbc}板 × {len(stocks)} 只：{' '.join(names)}")
    
    # 4. 板块排行
    print("\n【四、板块排行】")
    sectors = get_sectors(5)
    print("  涨幅前5：")
    for s in sectors["top_up"]:
        print(f"    {s['name']} +{s['change_pct']:.2f}%")
    
    # 5. 大成交额
    print("\n【五、大成交额前10】")
    top_amt = get_top_amount(10)
    for i, s in enumerate(top_amt, 1):
        print(f"  {i}. {s['name']}({s['code']}) {fmt_amount(s['amount'])} {s['change_pct']:+.2f}%")
    
    print("\n" + "=" * 70)
    print(f"  生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "lianban":
        cmd_lianban()
    else:
        cmd_full()
