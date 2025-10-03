import os
import tempfile
import base64
import re
from datetime import datetime
import streamlit as st

def generate_markdown_report(stock_info, agents_results, discussion_result, final_decision):
    """生成Markdown格式的分析报告"""
    
    # 获取当前时间
    current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
    
    markdown_content = f"""
# AI股票分析报告

**生成时间**: {current_time}

---

## 📊 股票基本信息

| 项目 | 值 |
|------|-----|
| **股票代码** | {stock_info.get('symbol', 'N/A')} |
| **股票名称** | {stock_info.get('name', 'N/A')} |
| **当前价格** | {stock_info.get('current_price', 'N/A')} |
| **涨跌幅** | {stock_info.get('change_percent', 'N/A')}% |
| **市盈率(PE)** | {stock_info.get('pe_ratio', 'N/A')} |
| **市净率(PB)** | {stock_info.get('pb_ratio', 'N/A')} |
| **市值** | {stock_info.get('market_cap', 'N/A')} |
| **市场** | {stock_info.get('market', 'N/A')} |
| **交易所** | {stock_info.get('exchange', 'N/A')} |

---

## 🔍 各分析师详细分析

"""

    # 添加各分析师的分析结果
    agent_names = {
        'technical': '📈 技术分析师',
        'fundamental': '📊 基本面分析师',
        'fund_flow': '💰 资金面分析师',
        'risk_management': '⚠️ 风险管理师',
        'market_sentiment': '📈 市场情绪分析师'
    }
    
    for agent_key, agent_name in agent_names.items():
        if agent_key in agents_results:
            agent_result = agents_results[agent_key]
            if isinstance(agent_result, dict):
                analysis_text = agent_result.get('analysis', '暂无分析')
            else:
                analysis_text = str(agent_result)
            
            markdown_content += f"""
### {agent_name}

{analysis_text}

---

"""

    # 添加团队讨论结果
    markdown_content += f"""
## 🤝 团队综合讨论

{discussion_result}

---

## 📋 最终投资决策

"""
    
    # 处理最终决策的显示
    if isinstance(final_decision, dict) and "decision_text" not in final_decision:
        # JSON格式的决策
        markdown_content += f"""
**投资评级**: {final_decision.get('rating', '未知')}

**目标价位**: {final_decision.get('target_price', 'N/A')}

**操作建议**: {final_decision.get('operation_advice', '暂无建议')}

**进场区间**: {final_decision.get('entry_range', 'N/A')}

**止盈位**: {final_decision.get('take_profit', 'N/A')}

**止损位**: {final_decision.get('stop_loss', 'N/A')}

**持有周期**: {final_decision.get('holding_period', 'N/A')}

**仓位建议**: {final_decision.get('position_size', 'N/A')}

**信心度**: {final_decision.get('confidence_level', 'N/A')}/10

**风险提示**: {final_decision.get('risk_warning', '无')}
"""
    else:
        # 文本格式的决策
        decision_text = final_decision.get('decision_text', str(final_decision))
        markdown_content += decision_text

    markdown_content += """

---

## 📝 免责声明

本报告由AI系统生成，仅供参考，不构成投资建议。投资有风险，入市需谨慎。请在做出投资决策前咨询专业的投资顾问。

---

*报告生成时间: {current_time}*
*AI股票分析系统 v1.0*
"""

    return markdown_content

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

def generate_html_content(markdown_content):
    """将Markdown转换为HTML"""
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>AI股票分析报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
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
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin-top: 30px;
        }}
        h3 {{
            color: #2980b9;
            margin-top: 25px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
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
            height: 2px;
            background-color: #ecf0f1;
            margin: 20px 0;
        }}
        strong {{
            color: #2c3e50;
        }}
    </style>
</head>
<body>
    <div class="container">
"""
    
    # 简单的Markdown到HTML转换
    html_body = markdown_content
    html_body = html_body.replace('\n# ', '\n<h1>').replace('\n## ', '\n<h2>').replace('\n### ', '\n<h3>')
    html_body = html_body.replace('# ', '<h1>').replace('## ', '<h2>').replace('### ', '<h3>')
    html_body = html_body.replace('\n---\n', '\n<hr>\n')
    
    # 处理粗体文本
    html_body = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_body)
    
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
            processed_lines.append(line)
            in_table = False
        else:
            processed_lines.append(line)
    
    if in_table:
        processed_lines.append('</table>')
    
    html_body = '\n'.join(processed_lines)
    
    # 处理段落
    paragraphs = html_body.split('\n\n')
    processed_paragraphs = []
    for para in paragraphs:
        para = para.strip()
        if para and not para.startswith('<') and not para.startswith('---'):
            processed_paragraphs.append(f'<p>{para}</p>')
        else:
            processed_paragraphs.append(para)
    
    html_body = '\n'.join(processed_paragraphs)
    
    html_content += html_body + """
    </div>
</body>
</html>
"""
    
    return html_content

def display_pdf_export_section(stock_info, agents_results, discussion_result, final_decision):
    """显示PDF导出区域 - 修复报告生成问题"""
    
    st.markdown("---")
    st.markdown("## 📄 导出分析报告")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # 生成报告按钮
        import uuid
        import time
        button_key = f"generate_report_btn_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        if st.button("📊 生成并下载报告", type="primary", use_container_width=True, key=button_key):
            with st.spinner("正在生成报告..."):
                try:
                    # 生成Markdown内容
                    markdown_content = generate_markdown_report(stock_info, agents_results, discussion_result, final_decision)
                    
                    # 生成HTML内容
                    html_content = generate_html_content(markdown_content)
                    
                    # 生成文件名
                    stock_symbol = stock_info.get('symbol', 'unknown')
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"股票分析报告_{stock_symbol}_{timestamp}"
                    
                    st.success("✅ 报告生成成功！")
                    st.balloons()
                    
                    # 立即显示下载链接
                    st.markdown("### 📄 报告下载")
                    
                    # 创建下载链接
                    md_link = create_download_link(
                        markdown_content, 
                        f"{filename}.md", 
                        "📝 下载Markdown报告"
                    )
                    
                    html_link = create_html_download_link(
                        html_content,
                        f"{filename}.html",
                        "🌐 下载HTML报告"
                    )
                    
                    # 显示下载链接
                    st.markdown(f"""
                    <div style="text-align: center; margin: 20px 0;">
                        {md_link}
                        {html_link}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.info("💡 提示：点击上方按钮即可下载对应格式的报告文件")
                    
                except Exception as e:
                    st.error(f"❌ 生成报告时出错: {str(e)}")
                    import traceback
                    st.error(f"详细错误信息: {traceback.format_exc()}")