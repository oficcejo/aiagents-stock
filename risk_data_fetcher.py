"""
风险数据获取模块
使用pywencai获取股票风险相关信息：
1. 限售解禁数据
2. 大股东减持公告
3. 近期重要事件
"""

import pywencai
import pandas as pd
from typing import Dict, Any
import time
import warnings
import os

# 屏蔽pywencai的Node.js警告信息（不影响功能）
warnings.filterwarnings('ignore', category=DeprecationWarning)
os.environ['PYTHONWARNINGS'] = 'ignore::DeprecationWarning'
os.environ['NODE_NO_WARNINGS'] = '1'  # 屏蔽Node.js警告


class RiskDataFetcher:
    """风险数据获取类"""
    
    def __init__(self):
        """初始化"""
        pass
    
    def get_risk_data(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票风险相关数据
        
        Args:
            symbol: 股票代码（如：600000）
            
        Returns:
            包含风险数据的字典
        """
        print(f"\n正在获取 {symbol} 的风险数据...")
        
        risk_data = {
            'symbol': symbol,
            'data_success': False,
            'lifting_ban': None,  # 限售解禁数据
            'shareholder_reduction': None,  # 大股东减持数据
            'important_events': None,  # 重要事件数据
            'error': None
        }
        
        try:
            # 1. 获取限售解禁数据
            print("   查询限售解禁数据...")
            lifting_ban = self._get_lifting_ban_data(symbol)
            risk_data['lifting_ban'] = lifting_ban
            if lifting_ban and lifting_ban.get('has_data'):
                print(f"   获取到限售解禁数据")
            else:
                print(f"   暂无限售解禁数据")
            
            time.sleep(1)  # 避免请求过快
            
            # 2. 获取大股东减持公告
            print("   查询大股东减持公告...")
            reduction = self._get_shareholder_reduction_data(symbol)
            risk_data['shareholder_reduction'] = reduction
            if reduction and reduction.get('has_data'):
                print(f"   获取到大股东减持数据")
            else:
                print(f"   暂无大股东减持数据")
            
            time.sleep(1)  # 避免请求过快
            
            # 3. 获取近期重要事件
            print("   查询近期重要事件...")
            events = self._get_important_events_data(symbol)
            risk_data['important_events'] = events
            if events and events.get('has_data'):
                print(f"   获取到重要事件数据")
            else:
                print(f"   暂无重要事件数据")
            
            # 如果至少有一个数据源成功，则认为获取成功
            if (lifting_ban and lifting_ban.get('has_data')) or \
               (reduction and reduction.get('has_data')) or \
               (events and events.get('has_data')):
                risk_data['data_success'] = True
                print(f"风险数据获取完成")
            else:
                print(f"未获取到风险相关数据")
                
        except Exception as e:
            print(f"风险数据获取失败: {str(e)}")
            risk_data['error'] = str(e)
        
        return risk_data
    
    def _get_lifting_ban_data(self, symbol: str) -> Dict[str, Any]:
        """获取限售解禁数据"""
        result = {
            'has_data': False,
            'query': f"{symbol}限售解禁",
            'data': None,
            'summary': None
        }
        
        try:
            # 构建问句
            query = f"{symbol}限售解禁"
            
            # 使用pywencai查询
            response = pywencai.get(query=query, loop=True)
            
            if response is None:
                return result
            
            # 处理返回结果
            df_result = self._convert_to_dataframe(response)
            
            if df_result is None or df_result.empty:
                return result
            
            # 提取有用的信息
            result['has_data'] = True
            result['data'] = df_result
            
            # 生成摘要
            summary = []
            
            # 尝试提取关键字段
            if '解禁时间' in df_result.columns or '限售解禁日' in df_result.columns:
                time_col = '解禁时间' if '解禁时间' in df_result.columns else '限售解禁日'
                summary.append(f"发现 {len(df_result)} 条解禁记录")
                
                # 提取最近的解禁记录
                recent_records = df_result.head(5)
                for idx, row in recent_records.iterrows():
                    record_info = []
                    if time_col in row.index:
                        record_info.append(f"日期: {row[time_col]}")
                    if '解禁股数' in row.index:
                        record_info.append(f"解禁股数: {row['解禁股数']}")
                    if '解禁市值' in row.index:
                        record_info.append(f"解禁市值: {row['解禁市值']}")
                    if '股东名称' in row.index:
                        record_info.append(f"股东: {row['股东名称']}")
                    
                    if record_info:
                        summary.append(" | ".join(record_info))
            else:
                # 如果没有标准字段，只记录有数据
                summary.append(f"获取到 {len(df_result)} 条相关记录")
            
            result['summary'] = "\n".join(summary) if summary else "有限售解禁数据"
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _get_shareholder_reduction_data(self, symbol: str) -> Dict[str, Any]:
        """获取大股东减持公告数据"""
        result = {
            'has_data': False,
            'query': f"{symbol}大股东减持公告",
            'data': None,
            'summary': None
        }
        
        try:
            # 构建问句
            query = f"{symbol}大股东减持公告"
            
            # 使用pywencai查询
            response = pywencai.get(query=query, loop=True)
            
            if response is None:
                return result
            
            # 处理返回结果
            df_result = self._convert_to_dataframe(response)
            
            if df_result is None or df_result.empty:
                return result
            
            # 提取有用的信息
            result['has_data'] = True
            result['data'] = df_result
            
            # 生成摘要
            summary = []
            
            # 尝试提取关键字段
            if '公告日期' in df_result.columns or '减持日期' in df_result.columns:
                date_col = '公告日期' if '公告日期' in df_result.columns else '减持日期'
                summary.append(f"发现 {len(df_result)} 条减持公告")
                
                # 提取最近的减持记录
                recent_records = df_result.head(5)
                for idx, row in recent_records.iterrows():
                    record_info = []
                    if date_col in row.index:
                        record_info.append(f"日期: {row[date_col]}")
                    if '股东名称' in row.index:
                        record_info.append(f"股东: {row['股东名称']}")
                    if '减持股数' in row.index:
                        record_info.append(f"减持股数: {row['减持股数']}")
                    if '减持比例' in row.index:
                        record_info.append(f"减持比例: {row['减持比例']}")
                    
                    if record_info:
                        summary.append(" | ".join(record_info))
            else:
                # 如果没有标准字段，只记录有数据
                summary.append(f"获取到 {len(df_result)} 条相关记录")
            
            result['summary'] = "\n".join(summary) if summary else "有大股东减持数据"
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _get_important_events_data(self, symbol: str) -> Dict[str, Any]:
        """获取近期重要事件数据"""
        result = {
            'has_data': False,
            'query': f"{symbol}近期重要事件",
            'data': None,
            'summary': None
        }
        
        try:
            # 构建问句
            query = f"{symbol}近期重要事件"
            
            # 使用pywencai查询
            response = pywencai.get(query=query, loop=True)
            
            if response is None:
                return result
            
            # 处理返回结果
            df_result = self._convert_to_dataframe(response)
            
            if df_result is None or df_result.empty:
                return result
            
            # 提取有用的信息
            result['has_data'] = True
            result['data'] = df_result
            
            # 生成摘要
            summary = []
            
            # 尝试提取关键字段
            if '事件时间' in df_result.columns or '公告日期' in df_result.columns:
                time_col = '事件时间' if '事件时间' in df_result.columns else '公告日期'
                summary.append(f"发现 {len(df_result)} 条重要事件")
                
                # 提取最近的事件
                recent_events = df_result.head(10)
                for idx, row in recent_events.iterrows():
                    event_info = []
                    if time_col in row.index:
                        event_info.append(f"时间: {row[time_col]}")
                    if '事件类型' in row.index:
                        event_info.append(f"类型: {row['事件类型']}")
                    if '事件内容' in row.index:
                        content = str(row['事件内容'])[:100]  # 限制长度
                        event_info.append(f"内容: {content}")
                    elif '标题' in row.index:
                        title = str(row['标题'])[:100]
                        event_info.append(f"标题: {title}")
                    
                    if event_info:
                        summary.append(" | ".join(event_info))
            else:
                # 如果没有标准字段，只记录有数据
                summary.append(f"获取到 {len(df_result)} 条相关记录")
            
            result['summary'] = "\n".join(summary) if summary else "有重要事件数据"
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _convert_to_dataframe(self, result) -> pd.DataFrame:
        """将pywencai返回结果转换为DataFrame"""
        try:
            if result is None:
                return None
            
            df_result = None
            
            if isinstance(result, dict):
                try:
                    df_result = pd.DataFrame([result])
                except Exception:
                    return None
            elif isinstance(result, pd.DataFrame):
                df_result = result
            else:
                return None
            
            if df_result is None or df_result.empty:
                return None
            
            # 处理嵌套结构（tableV1）
            if 'tableV1' in df_result.columns and len(df_result.columns) == 1:
                table_v1_data = df_result.iloc[0]['tableV1']
                if isinstance(table_v1_data, pd.DataFrame):
                    df_result = table_v1_data
                elif isinstance(table_v1_data, list) and len(table_v1_data) > 0:
                    df_result = pd.DataFrame(table_v1_data)
                else:
                    return None
            
            # 处理嵌套结构（title_content等单列嵌套）
            # 如果只有一列，且该列的值是DataFrame，则展开
            if len(df_result.columns) == 1:
                col_name = df_result.columns[0]
                first_value = df_result.iloc[0][col_name]
                if isinstance(first_value, pd.DataFrame):
                    print(f"   检测到嵌套DataFrame（列名: {col_name}），正在展开...")
                    df_result = first_value
            
            return df_result if not df_result.empty else None
            
        except Exception as e:
            print(f"   转换DataFrame时出错: {str(e)}")
            return None
    
    def format_risk_data_for_ai(self, risk_data: Dict[str, Any]) -> str:
        """格式化风险数据供AI分析使用 - 直接转换DataFrame为字符串"""
        if not risk_data or not risk_data.get('data_success'):
            return "未获取到风险数据"
        
        formatted_text = []
        
        try:
            # 1. 限售解禁数据
            lifting_ban = risk_data.get('lifting_ban')
            if lifting_ban and lifting_ban.get('has_data') and lifting_ban.get('data') is not None:
                formatted_text.append("=" * 80)
                formatted_text.append("【限售解禁数据】")
                formatted_text.append("=" * 80)
                formatted_text.append(f"查询语句: {lifting_ban.get('query', '')}")
                formatted_text.append("")
                
                # 直接将DataFrame转换为字符串（最多50行）
                df = lifting_ban.get('data')
                try:
                    df_str = df.head(50).to_string(index=False, max_rows=50, max_cols=20)
                    formatted_text.append(f"共 {len(df)} 条记录，显示前50条：")
                    formatted_text.append(df_str)
                except Exception as e:
                    formatted_text.append(f"数据转换失败: {str(e)}")
                formatted_text.append("")
        
            # 2. 大股东减持数据
            reduction = risk_data.get('shareholder_reduction')
            if reduction and reduction.get('has_data') and reduction.get('data') is not None:
                formatted_text.append("=" * 80)
                formatted_text.append("【大股东减持数据】")
                formatted_text.append("=" * 80)
                formatted_text.append(f"查询语句: {reduction.get('query', '')}")
                formatted_text.append("")
                
                # 直接将DataFrame转换为字符串（最多50行）
                df = reduction.get('data')
                try:
                    df_str = df.head(50).to_string(index=False, max_rows=50, max_cols=20)
                    formatted_text.append(f"共 {len(df)} 条记录，显示前50条：")
                    formatted_text.append(df_str)
                except Exception as e:
                    formatted_text.append(f"数据转换失败: {str(e)}")
                formatted_text.append("")
        
            # 3. 重要事件数据
            events = risk_data.get('important_events')
            if events and events.get('has_data') and events.get('data') is not None:
                formatted_text.append("=" * 80)
                formatted_text.append("【重要事件数据】")
                formatted_text.append("=" * 80)
                formatted_text.append(f"查询语句: {events.get('query', '')}")
                formatted_text.append("")
                
                # 直接将DataFrame转换为字符串（最多50行）
                df = events.get('data')
                try:
                    df_str = df.head(50).to_string(index=False, max_rows=50, max_cols=20)
                    formatted_text.append(f"共 {len(df)} 条记录，显示前50条：")
                    formatted_text.append(df_str)
                except Exception as e:
                    formatted_text.append(f"数据转换失败: {str(e)}")
                formatted_text.append("")
            
            return "\n".join(formatted_text) if formatted_text else "暂无风险数据"
            
        except Exception as e:
            print(f"格式化风险数据时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"格式化风险数据时出错: {str(e)}"
    
    def _format_dataframe_for_ai(self, df: pd.DataFrame, data_type: str) -> str:
        """将DataFrame格式化为AI易读的文本格式"""
        lines = []
        
        # 显示数据总数
        lines.append(f"共 {len(df)} 条{data_type}记录")
        lines.append("")
        
        # 显示列名
        lines.append(f"数据字段：{', '.join(df.columns.tolist())}")
        lines.append("")
        
        # 逐行显示数据（最多显示50条，避免数据过大）
        max_rows = min(50, len(df))
        
        for idx, row in df.head(max_rows).iterrows():
            lines.append(f"【记录 {idx + 1}】")
            
            # 显示每个字段的值
            for col in df.columns:
                value = row[col]
                
                # 处理不同类型的值
                if pd.isna(value):
                    value_str = "无数据"
                elif isinstance(value, (int, float)):
                    value_str = str(value)
                else:
                    value_str = str(value)
                    # 限制过长的字符串
                    if len(value_str) > 200:
                        value_str = value_str[:200] + "..."
                
                lines.append(f"  {col}: {value_str}")
            
            lines.append("")
        
        if len(df) > max_rows:
            lines.append(f"... 还有 {len(df) - max_rows} 条记录（已省略）")
            lines.append("")
        
        return "\n".join(lines)


# 测试代码
if __name__ == "__main__":
    fetcher = RiskDataFetcher()
    
    # 测试获取风险数据
    test_symbol = "600000"
    print(f"测试获取 {test_symbol} 的风险数据...")
    
    risk_data = fetcher.get_risk_data(test_symbol)
    
    print("\n" + "=" * 60)
    print("获取结果:")
    print("=" * 60)
    print(f"数据获取成功: {risk_data['data_success']}")
    
    if risk_data['data_success']:
        print("\n格式化的风险数据:")
        print(fetcher.format_risk_data_for_ai(risk_data))

