import os
import tempfile
import base64
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
        'technical_analyst': '📈 技术分析师',
        'fundamental_analyst': '📊 基本面分析师',
        'fund_analyst': '💰 资金面分析师',
        'risk_analyst': '⚠️ 风险管理师',
        'sentiment_analyst': '📈 市场情绪分析师'
    }
    
    for agent_key, agent_name in agent_names.items():
        if agent_key in agents_results:
            markdown_content += f"""
### {agent_name}

{agents_results[agent_key]}

---

"""

    # 添加团队讨论结果
    markdown_content += f"""
## 🤝 团队综合讨论

{discussion_result}

---

## 📋 最终投资决策

{final_decision}

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
    href = f'<a href="data:text/markdown;base64,{b64}" download="{filename}">{link_text}</a>'
    return href

def generate_pdf_report(stock_info, agents_results, discussion_result, final_decision):
    """生成PDF报告并提供下载"""
    try:
        # 生成Markdown内容
        markdown_content = generate_markdown_report(stock_info, agents_results, discussion_result, final_decision)
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_md:
            temp_md.write(markdown_content)
            temp_md_path = temp_md.name
        
        # 生成文件名
        stock_symbol = stock_info.get('symbol', 'unknown')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"股票分析报告_{stock_symbol}_{timestamp}"
        
        # 提供Markdown下载
        st.markdown("### 📄 报告下载")
        
        # Markdown下载链接
        md_download_link = create_download_link(
            markdown_content, 
            f"{filename}.md", 
            "📝 下载Markdown报告"
        )
        st.markdown(md_download_link, unsafe_allow_html=True)
        
        # 提供HTML预览和下载
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
    </style>
</head>
<body>
    <div class="container">
"""
        
        # 将Markdown转换为HTML（简单版本）
        html_body = markdown_content.replace('\n# ', '\n<h1>').replace('\n## ', '\n<h2>').replace('\n### ', '\n<h3>')
        html_body = html_body.replace('\n---\n', '\n<hr>\n')
        html_body = html_body.replace('**', '<strong>').replace('**', '</strong>')
        html_body = html_body.replace('\n\n', '</p><p>')
        html_body = f"<p>{html_body}</p>"
        
        # 处理表格
        lines = html_body.split('\n')
        in_table = False
        processed_lines = []
        
        for line in lines:
            if '|' in line and not in_table:
                processed_lines.append('<table>')
                in_table = True
                if line.strip().startswith('|'):
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
        
        html_content += html_body + """
    </div>
</body>
</html>
"""
        
        # HTML下载链接
        html_b64 = base64.b64encode(html_content.encode('utf-8')).decode()
        html_href = f'<a href="data:text/html;base64,{html_b64}" download="{filename}.html">🌐 下载HTML报告</a>'
        st.markdown(html_href, unsafe_allow_html=True)
        
        # 清理临时文件
        try:
            os.unlink(temp_md_path)
        except:
            pass
            
        st.success("✅ 报告生成成功！请点击上方链接下载报告文件。")
        
        return True
        
    except Exception as e:
        st.error(f"❌ 生成报告时出错: {str(e)}")
        return False

def display_pdf_export_section(stock_info, agents_results, discussion_result, final_decision):
    """显示PDF导出区域"""
    st.markdown("---")
    st.markdown("## 📄 导出分析报告")
    
    # 使用session_state来避免页面重置
    if 'show_download_links' not in st.session_state:
        st.session_state.show_download_links = False
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        pdf_button_key = "generate_report_btn"
        markdown_button_key = "generate_markdown_btn"
        
        # 生成PDF报告按钮
        if st.button("📊 生成并下载报告(PDF/HTML)", type="primary", width='content', key=pdf_button_key):
            st.session_state.show_download_links = True
            with st.spinner("正在生成报告..."):
                success = generate_pdf_report(stock_info, agents_results, discussion_result, final_decision)
                if success:
                    st.balloons()
        
        # 生成Markdown报告按钮
        if st.button("📝 生成并下载Markdown报告", type="secondary", width='content', key=markdown_button_key):
            with st.spinner("正在生成Markdown报告..."):
                try:
                    # 生成Markdown内容
                    markdown_content = generate_markdown_report(stock_info, agents_results, discussion_result, final_decision)
                    
                    # 生成文件名
                    stock_symbol = stock_info.get('symbol', 'unknown')
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"股票分析报告_{stock_symbol}_{timestamp}.md"
                    
                    st.success("✅ Markdown报告生成成功！")
                    st.balloons()
                    
                    # 显示下载链接
                    st.markdown("### 📄 报告下载")
                    
                    # Markdown下载链接
                    md_download_link = create_download_link(
                        markdown_content, 
                        filename, 
                        "📝 下载Markdown报告"
                    )
                    st.markdown(md_download_link, unsafe_allow_html=True)
                    
                    st.info("💡 提示：点击上方按钮即可下载Markdown格式的报告文件")
                    
                except Exception as e:
                    st.error(f"❌ 生成Markdown报告时出错: {str(e)}")
    
    # 如果已经生成了报告，显示下载链接
    if st.session_state.show_download_links:
        generate_pdf_report(stock_info, agents_results, discussion_result, final_decision)