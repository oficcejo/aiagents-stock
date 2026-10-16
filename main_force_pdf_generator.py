import os
import base64
import re
from datetime import datetime
import streamlit as st
import pandas as pd

from utils.pywencai_helper import flatten_cell

def generate_main_force_markdown_report(analyzer, result):
    """生成主力选股Markdown格式的分析报告"""
    
    # 获取当前时间
    current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
    
    # 获取分析参数
    params = result.get('params', {})
    start_date = params.get('start_date', 'N/A')
    min_cap = params.get('min_market_cap', 50)
    max_cap = params.get('max_market_cap', 5000)
    max_change = params.get('max_range_change', 50)
    
    markdown_content = f"""
# 主力选股AI分析报告

**生成时间**: {current_time}

---

## 📊 选股参数

| 项目 | 值 |
|------|-----|
| **起始日期** | {start_date} |
| **市值范围** | {min_cap}亿 - {max_cap}亿 |
| **最大涨跌幅** | {max_change}% |
| **初始数据量** | {result.get('total_fetched', 0)}只 |
| **筛选后数量** | {result.get('filtered_count', 0)}只 |
| **最终推荐** | {len(result.get('final_recommendations', []))}只 |

---

## 🤖 AI分析师团队报告

"""

    # 添加资金流向分析
    if hasattr(analyzer, 'fund_flow_analysis') and analyzer.fund_flow_analysis:
        markdown_content += f"""
### 💰 资金流向分析师

{analyzer.fund_flow_analysis}

---

"""
    
    # 添加行业板块分析
    if hasattr(analyzer, 'industry_analysis') and analyzer.industry_analysis:
        markdown_content += f"""
### 📊 行业板块及市场热点分析师

{analyzer.industry_analysis}

---

"""
    
    # 添加财务基本面分析
    if hasattr(analyzer, 'fundamental_analysis') and analyzer.fundamental_analysis:
        markdown_content += f"""
### 📈 财务基本面分析师

{analyzer.fundamental_analysis}

---

"""

    # 添加精选推荐
    markdown_content += """
## ⭐ 精选推荐股票

"""
    
    final_recommendations = result.get('final_recommendations', [])
    if final_recommendations:
        for rec in final_recommendations:
            markdown_content += f"""
### 【第{rec['rank']}名】{rec['symbol']} - {rec['name']}

**推荐理由**:
{rec.get('reason', '暂无')}

**关键指标**:
"""
            if 'stock_data' in rec:
                stock_data = rec['stock_data']
                markdown_content += f"""
- **所属行业**: {stock_data.get('industry', 'N/A')}
- **市值**: {stock_data.get('market_cap', 'N/A')}
- **主力资金流向**: {stock_data.get('main_fund_inflow', 'N/A')}
- **区间涨跌幅**: {stock_data.get('range_change', 'N/A')}%
- **市盈率**: {stock_data.get('pe_ratio', 'N/A')}
- **市净率**: {stock_data.get('pb_ratio', 'N/A')}

"""
            
            if 'scores' in rec.get('stock_data', {}):
                scores = rec['stock_data']['scores']
                if scores:
                    markdown_content += "**能力评分**:\n"
                    for score_name, score_value in scores.items():
                        markdown_content += f"- {score_name}: {score_value}\n"
                    markdown_content += "\n"
            
            markdown_content += "---\n\n"
    else:
        markdown_content += "暂无推荐股票\n\n---\n\n"

    # 添加候选股票列表（前100名，按主力资金排序）
    if analyzer and analyzer.raw_stocks is not None and not analyzer.raw_stocks.empty:
        markdown_content += """
## 📋 候选股票完整列表（按主力资金净流入排序）

"""
        
        # 获取主力资金列名
        df = analyzer.raw_stocks
        main_fund_col = None
        main_fund_patterns = [
            '区间主力资金流向', '区间主力资金净流入', 
            '主力资金流向', '主力资金净流入', '主力净流入'
        ]
        for pattern in main_fund_patterns:
            matching = [col for col in df.columns if pattern in col]
            if matching:
                main_fund_col = matching[0]
                break
        
        # 按主力资金排序
        if main_fund_col:
            df_sorted = df.copy()
            df_sorted[main_fund_col] = pd.to_numeric(df_sorted[main_fund_col], errors='coerce')
            df_sorted = df_sorted.sort_values(by=main_fund_col, ascending=False).head(100)
        else:
            df_sorted = df.head(100)
        
        # 选择要显示的列
        display_cols = []
        if '股票代码' in df_sorted.columns:
            display_cols.append('股票代码')
        if '股票简称' in df_sorted.columns:
            display_cols.append('股票简称')
        
        # 行业
        industry_cols = [col for col in df_sorted.columns if '行业' in col]
        if industry_cols:
            display_cols.append(industry_cols[0])
        
        # 主力资金
        if main_fund_col:
            display_cols.append(main_fund_col)
        
        # 涨跌幅
        change_cols = [col for col in df_sorted.columns if '涨跌幅' in col]
        if change_cols:
            display_cols.append(change_cols[0])
        
        # 市值、市盈率、市净率
        for col_name in ['总市值', '市盈率', '市净率']:
            matching_cols = [col for col in df_sorted.columns if col_name in col]
            if matching_cols:
                display_cols.append(matching_cols[0])
        
        # 生成表格
        if display_cols:
            final_display_cols = [col for col in display_cols if col in df_sorted.columns]
            markdown_content += "| 序号 | " + " | ".join(final_display_cols) + " |\n"
            markdown_content += "|------|" + "|".join(['-----' for _ in final_display_cols]) + "|\n"
            
            for idx, (_, row) in enumerate(df_sorted[final_display_cols].iterrows(), 1):
                row_data = [str(idx)]
                for col in final_display_cols:
                    value = flatten_cell(row[col])
                    if pd.isna(value):
                        row_data.append('N/A')
                    else:
                        row_data.append(str(value))
                markdown_content += "| " + " | ".join(row_data) + " |\n"
            
            markdown_content += "\n"

    # 添加免责声明
    markdown_content += f"""
---

## 📝 免责声明

本报告由AI系统生成，仅供参考，不构成投资建议。投资有风险，入市需谨慎。请在做出投资决策前咨询专业的投资顾问。

---

*报告生成时间: {current_time}*  
*主力选股AI分析系统 v1.0*
"""

    return markdown_content


def generate_html_content(markdown_content):
    """将Markdown转换为HTML

    修复 issue #56：原先标题标签不闭合，导致后续正文全部落入 h1，
    呈现为「全是粗体、字号超大」。现改为正确闭合标签，并使用宋体正文、
    仅标题/强调加粗。
    """
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>主力选股AI分析报告</title>
    <style>
        body {{
            font-family: 'SimSun', '宋体', 'Songti SC', serif;
            font-size: 14px;
            font-weight: 400;
            line-height: 1.7;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            font-family: 'Microsoft YaHei', '微软雅黑', sans-serif;
            font-size: 22px;
            font-weight: 700;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 8px;
            margin: 0 0 16px 0;
        }}
        h2 {{
            font-family: 'Microsoft YaHei', '微软雅黑', sans-serif;
            font-size: 18px;
            font-weight: 700;
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 12px;
            margin-top: 28px;
        }}
        h3 {{
            font-family: 'Microsoft YaHei', '微软雅黑', sans-serif;
            font-size: 16px;
            font-weight: 700;
            color: #2980b9;
            margin-top: 22px;
        }}
        p {{
            margin: 8px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
            font-size: 13px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
            font-weight: 600;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #f0f0f0;
        }}
        .disclaimer {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 15px;
            margin-top: 30px;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #7f8c8d;
            font-style: italic;
        }}
        hr {{
            border: none;
            height: 1px;
            background-color: #ecf0f1;
            margin: 20px 0;
        }}
        strong {{
            font-weight: 600;
            color: #2c3e50;
        }}
        ul, ol {{
            margin: 10px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 4px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
"""

    def _close_heading(match):
        level = len(match.group(1))
        text = match.group(2).strip()
        return f'<h{level}>{text}</h{level}>'

    html_body = markdown_content
    # 标题：正确闭合标签（# / ## / ###）
    html_body = re.sub(r'(?m)^(#{1,3})\s+(.*)$', _close_heading, html_body)
    html_body = html_body.replace('\n---\n', '\n<hr>\n')

    # 加粗（成对替换，避免全部变成 <strong>）
    html_body = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_body)

    # 处理表格
    lines = html_body.split('\n')
    in_table = False
    processed_lines = []

    for line in lines:
        if '|' in line and not in_table and line.strip().startswith('|'):
            processed_lines.append('<table>')
            in_table = True
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            processed_lines.append('<tr>')
            for cell in cells:
                processed_lines.append(f'<th>{cell}</th>')
            processed_lines.append('</tr>')
        elif '|' in line and in_table:
            if '---' not in line:
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                processed_lines.append('<tr>')
                for cell in cells:
                    processed_lines.append(f'<td>{cell}</td>')
                processed_lines.append('</tr>')
        elif in_table and '|' not in line:
            processed_lines.append('</table>')
            in_table = False
            processed_lines.append(line)
        else:
            processed_lines.append(line)

    if in_table:
        processed_lines.append('</table>')

    html_body = '\n'.join(processed_lines)

    # 处理列表
    html_body = re.sub(r'\n- (.*)', r'\n<li>\1</li>', html_body)
    html_body = re.sub(r'(<li>.*</li>)\n(?!<li>)', r'<ul>\1</ul>\n', html_body)
    html_body = re.sub(r'(<li>.*</li>\n)+', lambda m: '<ul>\n' + m.group(0) + '</ul>\n', html_body)

    # 处理换行
    html_body = html_body.replace('\n\n', '</p><p>')
    html_body = '<p>' + html_body + '</p>'
    # 清理空段落与标题被包进 p 的情况
    html_body = re.sub(r'<p>\s*(<h[1-3]>.*?</h[1-3]>)\s*', r'\1<p>', html_body)
    html_body = html_body.replace('<p></p>', '')

    html_content += html_body
    html_content += """
    </div>
</body>
</html>
"""

    return html_content


def create_download_link(content, filename, link_text):
    """创建下载链接"""
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:text/markdown;base64,{b64}" download="{filename}" style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; margin: 5px;">{link_text}</a>'
    return href


def create_html_download_link(content, filename, link_text):
    """创建HTML下载链接"""
    b64 = base64.b64encode(content.encode('utf-8')).decode()
    href = f'<a href="data:text/html;base64,{b64}" download="{filename}" style="display: inline-block; padding: 10px 20px; background-color: #2196F3; color: white; text-decoration: none; border-radius: 5px; margin: 5px;">{link_text}</a>'
    return href


def display_report_download_section(analyzer, result):
    """显示报告下载区域"""
    
    st.markdown("---")
    st.markdown("### 📥 下载分析报告")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📄 Markdown格式")
        st.caption("适合编辑和进一步处理")
        
        # 生成Markdown报告
        markdown_content = generate_main_force_markdown_report(analyzer, result)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        md_filename = f"主力选股分析报告_{timestamp}.md"
        
        # 创建下载链接
        md_link = create_download_link(markdown_content, md_filename, "📥 下载Markdown报告")
        st.markdown(md_link, unsafe_allow_html=True)
        
        # 显示预览
        with st.expander("👀 预览Markdown内容"):
            st.code(markdown_content[:2000] + "..." if len(markdown_content) > 2000 else markdown_content)
    
    with col2:
        st.markdown("#### 🌐 HTML格式")
        st.caption("可在浏览器中打开查看")
        
        # 生成HTML报告
        html_content = generate_html_content(markdown_content)
        
        # 生成文件名
        html_filename = f"主力选股分析报告_{timestamp}.html"
        
        # 创建下载链接
        html_link = create_html_download_link(html_content, html_filename, "📥 下载HTML报告")
        st.markdown(html_link, unsafe_allow_html=True)
        
        # 显示说明
        st.info("💡 HTML报告可以直接在浏览器中打开，格式美观易读")
    
    # 添加CSV下载（候选股票列表）
    if analyzer and analyzer.raw_stocks is not None and not analyzer.raw_stocks.empty:
        st.markdown("---")
        st.markdown("#### 📊 候选股票数据")
        
        # 按主力资金排序
        df = analyzer.raw_stocks.copy()
        main_fund_col = None
        main_fund_patterns = [
            '区间主力资金流向', '区间主力资金净流入', 
            '主力资金流向', '主力资金净流入', '主力净流入'
        ]
        for pattern in main_fund_patterns:
            matching = [col for col in df.columns if pattern in col]
            if matching:
                main_fund_col = matching[0]
                break
        
        if main_fund_col:
            df[main_fund_col] = pd.to_numeric(df[main_fund_col], errors='coerce')
            df = df.sort_values(by=main_fund_col, ascending=False)
        
        # 导出为CSV
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        csv_filename = f"主力选股候选列表_{timestamp}.csv"
        
        st.download_button(
            label="📥 下载候选股票CSV",
            data=csv,
            file_name=csv_filename,
            mime="text/csv",
            width='content'
        )

