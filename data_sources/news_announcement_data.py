"""
新闻公告数据获取模块
使用pywencai获取股票的最新新闻和公告信息
"""

import pandas as pd
import pywencai
import sys
import io
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

# 设置标准输出编码为UTF-8（仅在命令行环境，避免streamlit冲突）
def _setup_stdout_encoding():
    """仅在命令行环境设置标准输出编码"""
    if sys.platform == 'win32' and not hasattr(sys.stdout, '_original_stream'):
        try:
            # 检测是否在streamlit环境中
            import streamlit
            # 在streamlit中不修改stdout
            return
        except ImportError:
            # 不在streamlit环境，可以安全修改
            try:
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='ignore')
            except:
                pass

_setup_stdout_encoding()


class NewsAnnouncementDataFetcher:
    """新闻公告数据获取类"""
    
    def __init__(self):
        self.max_items = 20  # 最多获取的新闻/公告数量
    
    def get_news_and_announcements(self, symbol):
        """
        获取股票的新闻和公告数据
        
        Args:
            symbol: 股票代码（6位数字）
            
        Returns:
            dict: 包含新闻和公告数据的字典
        """
        data = {
            "symbol": symbol,
            "news_data": None,
            "announcement_data": None,
            "data_success": False
        }
        
        # 只支持中国股票
        if not self._is_chinese_stock(symbol):
            data["error"] = "新闻公告数据仅支持中国A股股票"
            return data
        
        try:
            # 获取新闻数据
            print("📰 正在获取最新新闻数据...")
            news_data = self._get_news_data(symbol)
            if news_data:
                data["news_data"] = news_data
                print(f"   ✓ 成功获取 {len(news_data.get('items', []))} 条新闻")
            
            # 获取公告数据
            print("📢 正在获取最新公告数据...")
            announcement_data = self._get_announcement_data(symbol)
            if announcement_data:
                data["announcement_data"] = announcement_data
                print(f"   ✓ 成功获取 {len(announcement_data.get('items', []))} 条公告")
            
            # 如果至少有一个成功，则标记为成功
            if news_data or announcement_data:
                data["data_success"] = True
                print("✅ 新闻公告数据获取完成")
            else:
                print("⚠️ 未能获取到新闻公告数据")
                
        except Exception as e:
            print(f"❌ 获取新闻公告数据失败: {e}")
            data["error"] = str(e)
        
        return data
    
    def _is_chinese_stock(self, symbol):
        """判断是否为中国股票"""
        return symbol.isdigit() and len(symbol) == 6
    
    def _get_news_data(self, symbol):
        """获取新闻数据"""
        try:
            # 构建问句
            query = f"{symbol}新闻"
            
            print(f"   使用问财查询: {query}")
            
            # 使用pywencai查询
            result = pywencai.get(query=query, loop=True)
            
            if result is None:
                print(f"   问财查询返回None")
                return None
            
            # 处理不同类型的返回结果
            df_result = None
            
            if isinstance(result, dict):
                try:
                    df_result = pd.DataFrame([result])
                except Exception as e:
                    print(f"   无法转换为DataFrame: {e}")
                    return None
            elif isinstance(result, pd.DataFrame):
                df_result = result
            else:
                print(f"   问财返回未知类型: {type(result)}")
                return None
            
            if df_result is None or df_result.empty:
                print(f"   查询结果为空")
                return None
            
            # 检查是否是嵌套结构
            if 'tableV1' in df_result.columns and len(df_result.columns) == 1:
                table_v1_data = df_result.iloc[0]['tableV1']
                if isinstance(table_v1_data, pd.DataFrame):
                    df_result = table_v1_data
                elif isinstance(table_v1_data, list) and len(table_v1_data) > 0:
                    df_result = pd.DataFrame(table_v1_data)
                else:
                    print(f"   tableV1数据类型不支持: {type(table_v1_data)}")
                    return None
            
            if df_result is None or df_result.empty:
                return None
            
            # 提取新闻数据
            news_items = []
            
            # 限制数量
            df_result = df_result.head(self.max_items)
            
            for idx, row in df_result.iterrows():
                item = {}
                
                # 尝试提取常见的新闻字段
                for col in df_result.columns:
                    col_lower = str(col).lower()
                    value = row.get(col)
                    
                    # 跳过空值和DataFrame类型
                    if value is None or (isinstance(value, float) and pd.isna(value)):
                        continue
                    if isinstance(value, pd.DataFrame):
                        continue
                    
                    # 保存字段
                    try:
                        item[col] = str(value)
                    except:
                        item[col] = "无法解析"
                
                if item:  # 如果有数据才添加
                    news_items.append(item)
            
            if not news_items:
                return None
            
            return {
                "items": news_items,
                "count": len(news_items),
                "columns": df_result.columns.tolist(),
                "query_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"   获取新闻数据异常: {e}")
            return None
    
    def _get_announcement_data(self, symbol):
        """获取公告数据"""
        try:
            # 构建问句
            query = f"{symbol}公告"
            
            print(f"   使用问财查询: {query}")
            
            # 使用pywencai查询
            result = pywencai.get(query=query, loop=True)
            
            if result is None:
                print(f"   问财查询返回None")
                return None
            
            # 处理不同类型的返回结果
            df_result = None
            
            if isinstance(result, dict):
                try:
                    df_result = pd.DataFrame([result])
                except Exception as e:
                    print(f"   无法转换为DataFrame: {e}")
                    return None
            elif isinstance(result, pd.DataFrame):
                df_result = result
            else:
                print(f"   问财返回未知类型: {type(result)}")
                return None
            
            if df_result is None or df_result.empty:
                print(f"   查询结果为空")
                return None
            
            # 检查是否是嵌套结构
            if 'tableV1' in df_result.columns and len(df_result.columns) == 1:
                table_v1_data = df_result.iloc[0]['tableV1']
                if isinstance(table_v1_data, pd.DataFrame):
                    df_result = table_v1_data
                elif isinstance(table_v1_data, list) and len(table_v1_data) > 0:
                    df_result = pd.DataFrame(table_v1_data)
                else:
                    print(f"   tableV1数据类型不支持: {type(table_v1_data)}")
                    return None
            
            if df_result is None or df_result.empty:
                return None
            
            # 提取公告数据
            announcement_items = []
            
            # 限制数量
            df_result = df_result.head(self.max_items)
            
            for idx, row in df_result.iterrows():
                item = {}
                
                # 尝试提取常见的公告字段
                for col in df_result.columns:
                    value = row.get(col)
                    
                    # 跳过空值和DataFrame类型
                    if value is None or (isinstance(value, float) and pd.isna(value)):
                        continue
                    if isinstance(value, pd.DataFrame):
                        continue
                    
                    # 保存字段
                    try:
                        item[col] = str(value)
                    except:
                        item[col] = "无法解析"
                
                if item:  # 如果有数据才添加
                    announcement_items.append(item)
            
            if not announcement_items:
                return None
            
            return {
                "items": announcement_items,
                "count": len(announcement_items),
                "columns": df_result.columns.tolist(),
                "query_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"   获取公告数据异常: {e}")
            return None
    
    def format_news_announcements_for_ai(self, data):
        """
        将新闻公告数据格式化为适合AI阅读的文本
        """
        if not data or not data.get("data_success"):
            return "未能获取新闻公告数据"
        
        text_parts = []
        
        # 新闻数据
        if data.get("news_data"):
            news_data = data["news_data"]
            text_parts.append(f"""
【最新新闻】
查询时间：{news_data.get('query_time', 'N/A')}
新闻数量：{news_data.get('count', 0)}条

""")
            
            for idx, item in enumerate(news_data.get('items', []), 1):
                text_parts.append(f"新闻 {idx}:")
                for key, value in item.items():
                    # 跳过过长的字段
                    if len(str(value)) > 500:
                        value = str(value)[:500] + "..."
                    text_parts.append(f"  {key}: {value}")
                text_parts.append("")  # 空行分隔
        
        # 公告数据
        if data.get("announcement_data"):
            announcement_data = data["announcement_data"]
            text_parts.append(f"""
【最新公告】
查询时间：{announcement_data.get('query_time', 'N/A')}
公告数量：{announcement_data.get('count', 0)}条

""")
            
            for idx, item in enumerate(announcement_data.get('items', []), 1):
                text_parts.append(f"公告 {idx}:")
                for key, value in item.items():
                    # 跳过过长的字段
                    if len(str(value)) > 500:
                        value = str(value)[:500] + "..."
                    text_parts.append(f"  {key}: {value}")
                text_parts.append("")  # 空行分隔
        
        return "\n".join(text_parts)


# 测试函数
if __name__ == "__main__":
    print("测试新闻公告数据获取...")
    fetcher = NewsAnnouncementDataFetcher()
    
    # 测试平安银行
    symbol = "000001"
    print(f"\n正在获取 {symbol} 的新闻公告数据...\n")
    
    data = fetcher.get_news_and_announcements(symbol)
    
    if data.get("data_success"):
        print("\n" + "="*60)
        print("新闻公告数据获取成功！")
        print("="*60)
        
        formatted_text = fetcher.format_news_announcements_for_ai(data)
        print(formatted_text)
    else:
        print(f"\n获取失败: {data.get('error', '未知错误')}")

