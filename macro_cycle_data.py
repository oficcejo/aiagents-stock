"""
宏观周期分析 - 数据采集模块
采集宏观经济数据（GDP、CPI/PPI、PMI、利率、M2、大宗商品等）
用于康波周期和美林投资时钟分析
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import warnings
import time
import logging
import traceback

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class MacroCycleDataFetcher:
    """宏观经济数据采集器"""

    def __init__(self):
        print("[宏观周期] 数据采集器初始化...")
        self.max_retries = 3

    def _safe_request(self, func, *args, **kwargs):
        """安全请求，带重试"""
        for i in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if i < self.max_retries - 1:
                    time.sleep(2)
                else:
                    logger.warning(f"请求失败: {e}")
                    return None

    def get_all_macro_data(self) -> dict:
        """
        获取所有宏观经济数据
        Returns:
            dict: 包含多维度宏观数据的字典
        """
        print("\n[宏观周期] 开始采集宏观经济数据...")
        data = {
            "success": False,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "gdp": {},
            "cpi_ppi": {},
            "pmi": {},
            "money_supply": {},
            "interest_rate": {},
            "market_indices": {},
            "commodities": {},
            "real_estate": {},
            "employment": {},
            "news": [],
            "errors": []
        }

        # 1. GDP
        print("  1/9 获取GDP数据...")
        try:
            gdp_data = self._get_gdp_data()
            if gdp_data:
                data["gdp"] = gdp_data
                print("    ✓ GDP数据获取成功")
        except Exception as e:
            data["errors"].append(f"GDP: {e}")
            print(f"    ✗ GDP数据获取失败: {e}")

        # 2. CPI/PPI
        print("  2/9 获取CPI/PPI数据...")
        try:
            cpi_ppi = self._get_cpi_ppi_data()
            if cpi_ppi:
                data["cpi_ppi"] = cpi_ppi
                print("    ✓ CPI/PPI数据获取成功")
        except Exception as e:
            data["errors"].append(f"CPI/PPI: {e}")
            print(f"    ✗ CPI/PPI获取失败: {e}")

        # 3. PMI
        print("  3/9 获取PMI数据...")
        try:
            pmi = self._get_pmi_data()
            if pmi:
                data["pmi"] = pmi
                print("    ✓ PMI数据获取成功")
        except Exception as e:
            data["errors"].append(f"PMI: {e}")
            print(f"    ✗ PMI获取失败: {e}")

        # 4. 货币供应量 M2
        print("  4/9 获取货币供应数据...")
        try:
            money = self._get_money_supply()
            if money:
                data["money_supply"] = money
                print("    ✓ 货币供应数据获取成功")
        except Exception as e:
            data["errors"].append(f"货币供应: {e}")
            print(f"    ✗ 货币供应获取失败: {e}")

        # 5. 利率
        print("  5/9 获取利率数据...")
        try:
            rate = self._get_interest_rate()
            if rate:
                data["interest_rate"] = rate
                print("    ✓ 利率数据获取成功")
        except Exception as e:
            data["errors"].append(f"利率: {e}")
            print(f"    ✗ 利率获取失败: {e}")

        # 6. 市场指数
        print("  6/9 获取市场指数...")
        try:
            indices = self._get_market_indices()
            if indices:
                data["market_indices"] = indices
                print("    ✓ 市场指数获取成功")
        except Exception as e:
            data["errors"].append(f"市场指数: {e}")
            print(f"    ✗ 市场指数获取失败: {e}")

        # 7. 大宗商品
        print("  7/9 获取大宗商品数据...")
        try:
            commodities = self._get_commodities_data()
            if commodities:
                data["commodities"] = commodities
                print("    ✓ 大宗商品数据获取成功")
        except Exception as e:
            data["errors"].append(f"大宗商品: {e}")
            print(f"    ✗ 大宗商品获取失败: {e}")

        # 8. 房地产
        print("  8/9 获取房地产数据...")
        try:
            real_estate = self._get_real_estate_data()
            if real_estate:
                data["real_estate"] = real_estate
                print("    ✓ 房地产数据获取成功")
        except Exception as e:
            data["errors"].append(f"房地产: {e}")
            print(f"    ✗ 房地产获取失败: {e}")

        # 9. 财经新闻
        print("  9/9 获取财经新闻...")
        try:
            news = self._get_macro_news()
            if news:
                data["news"] = news
                print(f"    ✓ 获取{len(news)}条新闻")
        except Exception as e:
            data["errors"].append(f"新闻: {e}")
            print(f"    ✗ 新闻获取失败: {e}")

        # 判断是否有足够数据
        valid_count = sum(1 for k in ["gdp", "cpi_ppi", "pmi", "money_supply",
                                       "interest_rate", "market_indices", "commodities"]
                         if data.get(k))
        if valid_count >= 3:
            data["success"] = True
            print(f"\n[宏观周期] 数据采集完成，成功获取 {valid_count}/7 项核心数据")
        else:
            print(f"\n[宏观周期] 数据不足（仅 {valid_count}/7 项），分析可能不够准确")
            data["success"] = True  # 仍允许分析

        return data

    def _get_gdp_data(self) -> dict:
        """获取GDP数据"""
        result = {}
        try:
            # 中国GDP年度
            df = self._safe_request(ak.macro_china_gdp)
            if df is not None and not df.empty:
                recent = df.tail(8)
                result["yearly"] = []
                for _, row in recent.iterrows():
                    item = {}
                    for col in df.columns:
                        item[col] = str(row[col])
                    result["yearly"].append(item)
        except Exception as e:
            logger.warning(f"GDP年度数据获取失败: {e}")

        try:
            # 季度GDP增速
            df = self._safe_request(ak.macro_china_gdp_yearly)
            if df is not None and not df.empty:
                recent = df.tail(12)
                result["quarterly_growth"] = []
                for _, row in recent.iterrows():
                    item = {}
                    for col in df.columns:
                        item[col] = str(row[col])
                    result["quarterly_growth"].append(item)
        except Exception as e:
            logger.warning(f"GDP季度数据获取失败: {e}")

        return result if result else None

    def _get_cpi_ppi_data(self) -> dict:
        """获取CPI和PPI数据"""
        result = {}
        try:
            # CPI月度
            df = self._safe_request(ak.macro_china_cpi_monthly)
            if df is not None and not df.empty:
                recent = df.tail(12)
                result["cpi_monthly"] = []
                for _, row in recent.iterrows():
                    item = {}
                    for col in df.columns:
                        item[col] = str(row[col])
                    result["cpi_monthly"].append(item)
        except Exception as e:
            logger.warning(f"CPI数据获取失败: {e}")

        try:
            # PPI月度
            df = self._safe_request(ak.macro_china_ppi_yearly)
            if df is not None and not df.empty:
                recent = df.tail(12)
                result["ppi_monthly"] = []
                for _, row in recent.iterrows():
                    item = {}
                    for col in df.columns:
                        item[col] = str(row[col])
                    result["ppi_monthly"].append(item)
        except Exception as e:
            logger.warning(f"PPI数据获取失败: {e}")

        return result if result else None

    def _get_pmi_data(self) -> dict:
        """获取PMI数据"""
        result = {}
        try:
            # 制造业PMI
            df = self._safe_request(ak.macro_china_pmi_yearly)
            if df is not None and not df.empty:
                recent = df.tail(12)
                result["manufacturing_pmi"] = []
                for _, row in recent.iterrows():
                    item = {}
                    for col in df.columns:
                        item[col] = str(row[col])
                    result["manufacturing_pmi"].append(item)
        except Exception as e:
            logger.warning(f"制造业PMI获取失败: {e}")

        try:
            # 非制造业PMI（财新）
            df = self._safe_request(ak.macro_china_cx_pmi_yearly)
            if df is not None and not df.empty:
                recent = df.tail(12)
                result["caixin_pmi"] = []
                for _, row in recent.iterrows():
                    item = {}
                    for col in df.columns:
                        item[col] = str(row[col])
                    result["caixin_pmi"].append(item)
        except Exception as e:
            logger.warning(f"财新PMI获取失败: {e}")

        return result if result else None

    def _get_money_supply(self) -> dict:
        """获取货币供应量"""
        result = {}
        try:
            df = self._safe_request(ak.macro_china_money_supply)
            if df is not None and not df.empty:
                recent = df.tail(12)
                result["m2_data"] = []
                for _, row in recent.iterrows():
                    item = {}
                    for col in df.columns:
                        item[col] = str(row[col])
                    result["m2_data"].append(item)
        except Exception as e:
            logger.warning(f"货币供应数据获取失败: {e}")

        return result if result else None

    def _get_interest_rate(self) -> dict:
        """获取利率数据"""
        result = {}
        try:
            # LPR利率
            df = self._safe_request(ak.macro_china_lpr)
            if df is not None and not df.empty:
                recent = df.tail(12)
                result["lpr"] = []
                for _, row in recent.iterrows():
                    item = {}
                    for col in df.columns:
                        item[col] = str(row[col])
                    result["lpr"].append(item)
        except Exception as e:
            logger.warning(f"LPR利率获取失败: {e}")

        return result if result else None

    def _get_market_indices(self) -> dict:
        """获取主要市场指数"""
        result = {}
        indices = {
            "sh_index": "sh000001",     # 上证指数
            "sz_index": "sz399001",     # 深证成指
            "cyb_index": "sz399006",    # 创业板指
        }

        for name, code in indices.items():
            try:
                df = self._safe_request(
                    ak.stock_zh_index_daily,
                    symbol=code
                )
                if df is not None and not df.empty:
                    latest = df.tail(1).iloc[0]
                    prev = df.tail(2).iloc[0] if len(df) >= 2 else latest

                    change_pct = 0
                    if prev["close"] > 0:
                        change_pct = (latest["close"] - prev["close"]) / prev["close"] * 100

                    # 计算近期涨跌
                    recent_60 = df.tail(60)
                    pct_60d = 0
                    if len(recent_60) >= 60:
                        pct_60d = (latest["close"] - recent_60.iloc[0]["close"]) / recent_60.iloc[0]["close"] * 100

                    result[name] = {
                        "close": round(float(latest["close"]), 2),
                        "change_pct": round(change_pct, 2),
                        "pct_60d": round(pct_60d, 2),
                        "high_52w": round(float(df.tail(250)["high"].max()), 2) if len(df) >= 250 else None,
                        "low_52w": round(float(df.tail(250)["low"].min()), 2) if len(df) >= 250 else None,
                    }
            except Exception as e:
                logger.warning(f"指数{name}获取失败: {e}")

        return result if result else None

    def _get_commodities_data(self) -> dict:
        """获取大宗商品数据"""
        result = {}

        # 黄金
        try:
            df = self._safe_request(ak.futures_main_sina, symbol="AU0", start_date=(datetime.now() - timedelta(days=365)).strftime("%Y%m%d"), end_date=datetime.now().strftime("%Y%m%d"))
            if df is not None and not df.empty:
                latest = df.tail(1).iloc[0]
                first = df.head(1).iloc[0]
                ytd_pct = (float(latest["收盘价"]) - float(first["收盘价"])) / float(first["收盘价"]) * 100 if float(first["收盘价"]) > 0 else 0
                result["gold"] = {
                    "price": round(float(latest["收盘价"]), 2),
                    "ytd_change_pct": round(ytd_pct, 2),
                    "name": "沪金主力"
                }
        except Exception as e:
            logger.warning(f"黄金数据获取失败: {e}")

        # 原油
        try:
            df = self._safe_request(ak.futures_main_sina, symbol="SC0", start_date=(datetime.now() - timedelta(days=365)).strftime("%Y%m%d"), end_date=datetime.now().strftime("%Y%m%d"))
            if df is not None and not df.empty:
                latest = df.tail(1).iloc[0]
                first = df.head(1).iloc[0]
                ytd_pct = (float(latest["收盘价"]) - float(first["收盘价"])) / float(first["收盘价"]) * 100 if float(first["收盘价"]) > 0 else 0
                result["crude_oil"] = {
                    "price": round(float(latest["收盘价"]), 2),
                    "ytd_change_pct": round(ytd_pct, 2),
                    "name": "原油主力"
                }
        except Exception as e:
            logger.warning(f"原油数据获取失败: {e}")

        # 铜
        try:
            df = self._safe_request(ak.futures_main_sina, symbol="CU0", start_date=(datetime.now() - timedelta(days=365)).strftime("%Y%m%d"), end_date=datetime.now().strftime("%Y%m%d"))
            if df is not None and not df.empty:
                latest = df.tail(1).iloc[0]
                first = df.head(1).iloc[0]
                ytd_pct = (float(latest["收盘价"]) - float(first["收盘价"])) / float(first["收盘价"]) * 100 if float(first["收盘价"]) > 0 else 0
                result["copper"] = {
                    "price": round(float(latest["收盘价"]), 2),
                    "ytd_change_pct": round(ytd_pct, 2),
                    "name": "沪铜主力"
                }
        except Exception as e:
            logger.warning(f"铜数据获取失败: {e}")

        return result if result else None

    def _get_real_estate_data(self) -> dict:
        """获取房地产相关数据"""
        result = {}
        try:
            df = self._safe_request(ak.macro_china_real_estate)
            if df is not None and not df.empty:
                recent = df.tail(12)
                result["data"] = []
                for _, row in recent.iterrows():
                    item = {}
                    for col in df.columns:
                        item[col] = str(row[col])
                    result["data"].append(item)
        except Exception as e:
            logger.warning(f"房地产数据获取失败: {e}")

        return result if result else None

    def _get_macro_news(self) -> list:
        """获取宏观经济相关新闻"""
        news_list = []
        try:
            df = self._safe_request(ak.stock_info_global_em)
            if df is not None and not df.empty:
                for _, row in df.head(50).iterrows():
                    news_list.append({
                        "title": str(row.get("标题", "")),
                        "publish_time": str(row.get("发布时间", "")),
                        "content": str(row.get("概要", ""))[:300]
                    })
        except Exception as e:
            logger.warning(f"新闻获取失败: {e}")

        return news_list

    def format_data_for_ai(self, data: dict) -> str:
        """将数据格式化为AI分析所需的文本"""
        parts = []
        parts.append(f"===== 宏观经济数据报告 =====")
        parts.append(f"数据采集时间: {data.get('timestamp', '未知')}")
        parts.append("")

        # GDP
        if data.get("gdp"):
            parts.append("【一、GDP数据】")
            gdp = data["gdp"]
            if gdp.get("yearly"):
                parts.append("近年GDP:")
                for item in gdp["yearly"][-4:]:
                    parts.append(f"  {item}")
            if gdp.get("quarterly_growth"):
                parts.append("季度GDP增速:")
                for item in gdp["quarterly_growth"][-8:]:
                    parts.append(f"  {item}")
            parts.append("")

        # CPI/PPI
        if data.get("cpi_ppi"):
            parts.append("【二、CPI/PPI通胀数据】")
            cp = data["cpi_ppi"]
            if cp.get("cpi_monthly"):
                parts.append("近12个月CPI:")
                for item in cp["cpi_monthly"]:
                    parts.append(f"  {item}")
            if cp.get("ppi_monthly"):
                parts.append("近12个月PPI:")
                for item in cp["ppi_monthly"]:
                    parts.append(f"  {item}")
            parts.append("")

        # PMI
        if data.get("pmi"):
            parts.append("【三、PMI景气指数】")
            pmi = data["pmi"]
            if pmi.get("manufacturing_pmi"):
                parts.append("制造业PMI（50为荣枯线）:")
                for item in pmi["manufacturing_pmi"]:
                    parts.append(f"  {item}")
            if pmi.get("caixin_pmi"):
                parts.append("财新PMI:")
                for item in pmi["caixin_pmi"]:
                    parts.append(f"  {item}")
            parts.append("")

        # 货币供应
        if data.get("money_supply"):
            parts.append("【四、货币供应量】")
            ms = data["money_supply"]
            if ms.get("m2_data"):
                parts.append("M0/M1/M2数据:")
                for item in ms["m2_data"]:
                    parts.append(f"  {item}")
            parts.append("")

        # 利率
        if data.get("interest_rate"):
            parts.append("【五、利率数据】")
            ir = data["interest_rate"]
            if ir.get("lpr"):
                parts.append("LPR利率:")
                for item in ir["lpr"]:
                    parts.append(f"  {item}")
            parts.append("")

        # 市场指数
        if data.get("market_indices"):
            parts.append("【六、市场指数】")
            mi = data["market_indices"]
            for name, info in mi.items():
                label = {"sh_index": "上证指数", "sz_index": "深证成指", "cyb_index": "创业板指"}.get(name, name)
                parts.append(f"  {label}: {info['close']} (日涨跌: {info['change_pct']:+.2f}%, 60日涨跌: {info.get('pct_60d', 0):+.2f}%)")
                if info.get("high_52w"):
                    parts.append(f"    52周最高: {info['high_52w']}  52周最低: {info['low_52w']}")
            parts.append("")

        # 大宗商品
        if data.get("commodities"):
            parts.append("【七、大宗商品】")
            for name, info in data["commodities"].items():
                parts.append(f"  {info['name']}: {info['price']} (年涨跌: {info['ytd_change_pct']:+.2f}%)")
            parts.append("")

        # 房地产
        if data.get("real_estate"):
            parts.append("【八、房地产数据】")
            re_data = data["real_estate"]
            if re_data.get("data"):
                for item in re_data["data"][-4:]:
                    parts.append(f"  {item}")
            parts.append("")

        # 新闻
        if data.get("news"):
            parts.append("【九、近期宏观经济新闻】")
            for idx, news in enumerate(data["news"][:20], 1):
                parts.append(f"  {idx}. [{news.get('publish_time', '')}] {news.get('title', '')}")
                if news.get('content'):
                    parts.append(f"     {news['content'][:150]}")
            parts.append("")

        return "\n".join(parts)


# 测试
if __name__ == "__main__":
    print("=" * 60)
    print("测试宏观周期数据采集")
    print("=" * 60)

    fetcher = MacroCycleDataFetcher()
    data = fetcher.get_all_macro_data()

    if data.get("success"):
        formatted = fetcher.format_data_for_ai(data)
        print(formatted[:5000])
        print(f"\n... (总长度: {len(formatted)} 字符)")
    else:
        print(f"数据采集失败: {data.get('errors')}")
