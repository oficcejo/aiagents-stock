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

def display_pdf_export_section(stock_info, agents_results, discussion_result, final_decision):
    """显示PDF导出区域 - 修复报告生成问题"""
    
    st.markdown("---")
    st.markdown("## 📄 导出分析报告")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # 生成报告按钮
        import uuid
        import time
        pdf_button_key = f"generate_report_btn_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        markdown_button_key = f"generate_markdown_btn_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # 生成PDF和HTML报告按钮
        if st.button("📊 生成并下载报告(PDF/HTML)", type="primary", width='content', key=pdf_button_key):
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
        
        # 单独生成Markdown报告按钮
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
                    
                    # 创建下载链接
                    md_link = create_download_link(
                        markdown_content, 
                        filename, 
                        "📝 下载Markdown报告"
                    )
                    
                    # 显示下载链接
                    st.markdown(f"""
                    <div style="text-align: center; margin: 20px 0;">
                        {md_link}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.info("💡 提示：点击上方按钮即可下载Markdown格式的报告文件")
                    
                except Exception as e:
                    st.error(f"❌ 生成Markdown报告时出错: {str(e)}")
                    import traceback
                    st.error(f"详细错误信息: {traceback.format_exc()}")

