"""
智瞰龙虎PDF报告生成模块
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import os
import tempfile


class LonghubangPDFGenerator:
    """龙虎榜PDF报告生成器"""
    
    def __init__(self):
        """初始化PDF生成器"""
        self.setup_fonts()
        
    def setup_fonts(self):
        """设置中文字体"""
        try:
            # 尝试注册常见的中文字体
            font_paths = [
                'C:/Windows/Fonts/msyh.ttc',  # 微软雅黑
                'C:/Windows/Fonts/simsun.ttc',  # 宋体
                'C:/Windows/Fonts/simhei.ttf',  # 黑体
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        self.chinese_font = 'ChineseFont'
                        print(f"[PDF] 成功加载字体: {font_path}")
                        return
                    except:
                        continue
            
            # 如果都失败，使用默认字体
            self.chinese_font = 'Helvetica'
            print("[PDF] 警告: 未找到中文字体，使用默认字体")
            
        except Exception as e:
            print(f"[PDF] 字体设置失败: {e}")
            self.chinese_font = 'Helvetica'
    
    def generate_pdf(self, result_data: dict, output_path: str = None) -> str:
        """
        生成龙虎榜分析PDF报告
        
        Args:
            result_data: 分析结果数据
            output_path: 输出路径，如果为None则生成临时文件
            
        Returns:
            PDF文件路径
        """
        try:
            # 如果没有指定输出路径，创建临时文件
            if output_path is None:
                temp_dir = tempfile.gettempdir()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(temp_dir, f"智瞰龙虎报告_{timestamp}.pdf")
            
            # 创建PDF文档
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=0.5*inch,
                leftMargin=0.5*inch,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch
            )
            
            # 构建内容
            story = []
            
            # 添加标题页
            story.extend(self._create_title_page(result_data))
            story.append(PageBreak())
            
            # 添加数据概况
            story.extend(self._create_data_overview(result_data))
            story.append(PageBreak())
            
            # 添加推荐股票
            story.extend(self._create_recommended_stocks(result_data))
            story.append(PageBreak())
            
            # 添加AI分析师报告
            story.extend(self._create_agents_analysis(result_data))
            
            # 生成PDF
            doc.build(story)
            
            print(f"[PDF] 龙虎榜报告生成成功: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"[PDF] 生成失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _get_styles(self) -> dict:
        """获取样式"""
        styles = getSampleStyleSheet()
        
        # 自定义样式
        custom_styles = {
            'Title': ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName=self.chinese_font
            ),
            'Heading1': ParagraphStyle(
                'CustomHeading1',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=12,
                spaceBefore=12,
                fontName=self.chinese_font
            ),
            'Heading2': ParagraphStyle(
                'CustomHeading2',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#2c5aa0'),
                spaceAfter=10,
                spaceBefore=10,
                fontName=self.chinese_font
            ),
            'Heading3': ParagraphStyle(
                'CustomHeading3',
                parent=styles['Heading3'],
                fontSize=12,
                textColor=colors.HexColor('#3d6db5'),
                spaceAfter=8,
                spaceBefore=8,
                fontName=self.chinese_font
            ),
            'Normal': ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                fontName=self.chinese_font,
                alignment=TA_JUSTIFY
            ),
            'Small': ParagraphStyle(
                'CustomSmall',
                parent=styles['Normal'],
                fontSize=9,
                leading=12,
                fontName=self.chinese_font
            )
        }
        
        return custom_styles
    
    def _create_title_page(self, data: dict) -> list:
        """创建标题页"""
        styles = self._get_styles()
        elements = []
        
        # 添加空白
        elements.append(Spacer(1, 2*inch))
        
        # 主标题
        title = Paragraph("智瞰龙虎榜分析报告", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.5*inch))
        
        # 副标题
        subtitle = Paragraph("AI驱动的龙虎榜多维度分析系统", styles['Heading2'])
        elements.append(subtitle)
        elements.append(Spacer(1, 1*inch))
        
        # 报告信息
        timestamp = data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        data_info = data.get('data_info', {})
        
        info_text = f"""
        <para align=center>
        <b>生成时间:</b> {timestamp}<br/>
        <b>数据记录:</b> {data_info.get('total_records', 0)} 条<br/>
        <b>涉及股票:</b> {data_info.get('total_stocks', 0)} 只<br/>
        <b>涉及游资:</b> {data_info.get('total_youzi', 0)} 个<br/>
        <b>AI分析师:</b> 5位专业分析师团队<br/>
        <b>分析模型:</b> DeepSeek AI Multi-Agent System
        </para>
        """
        info = Paragraph(info_text, styles['Normal'])
        elements.append(info)
        elements.append(Spacer(1, 1*inch))
        
        # 免责声明
        disclaimer = Paragraph(
            "<para align=center><i>本报告由AI系统基于龙虎榜公开数据自动生成，仅供参考，不构成投资建议。<br/>"
            "市场有风险，投资需谨慎。请投资者独立判断并承担投资风险。</i></para>",
            styles['Normal']
        )
        elements.append(disclaimer)
        
        return elements
    
    def _create_data_overview(self, data: dict) -> list:
        """创建数据概况部分"""
        styles = self._get_styles()
        elements = []
        
        # 标题
        elements.append(Paragraph("一、数据概况", styles['Heading1']))
        elements.append(Spacer(1, 0.2*inch))
        
        data_info = data.get('data_info', {})
        summary = data_info.get('summary', {})
        
        # 基本统计
        overview_text = f"""
        <para>
        本次分析共涵盖 <b>{data_info.get('total_records', 0)}</b> 条龙虎榜记录，
        涉及 <b>{data_info.get('total_stocks', 0)}</b> 只股票和 
        <b>{data_info.get('total_youzi', 0)}</b> 个游资席位。<br/><br/>
        
        <b>资金概况:</b><br/>
        • 总买入金额: {summary.get('total_buy_amount', 0):,.2f} 元<br/>
        • 总卖出金额: {summary.get('total_sell_amount', 0):,.2f} 元<br/>
        • 净流入金额: {summary.get('total_net_inflow', 0):,.2f} 元
        </para>
        """
        elements.append(Paragraph(overview_text, styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # TOP游资
        if summary.get('top_youzi'):
            elements.append(Paragraph("1.1 活跃游资 TOP10", styles['Heading2']))
            elements.append(Spacer(1, 0.1*inch))
            
            table_data = [['排名', '游资名称', '净流入金额(元)']]
            for idx, (name, amount) in enumerate(list(summary['top_youzi'].items())[:10], 1):
                table_data.append([str(idx), name, f"{amount:,.2f}"])
            
            table = Table(table_data, colWidths=[0.8*inch, 3.5*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))
        
        # TOP股票
        if summary.get('top_stocks'):
            elements.append(Paragraph("1.2 资金净流入 TOP20 股票", styles['Heading2']))
            elements.append(Spacer(1, 0.1*inch))
            
            table_data = [['排名', '股票代码', '股票名称', '净流入金额(元)']]
            for idx, stock in enumerate(summary['top_stocks'][:20], 1):
                table_data.append([
                    str(idx),
                    stock['code'],
                    stock['name'],
                    f"{stock['net_inflow']:,.2f}"
                ])
            
            table = Table(table_data, colWidths=[0.8*inch, 1.2*inch, 2*inch, 2.3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))
        
        # 热门概念
        if summary.get('hot_concepts'):
            elements.append(Paragraph("1.3 热门概念 TOP15", styles['Heading2']))
            elements.append(Spacer(1, 0.1*inch))
            
            concepts_text = ""
            for idx, (concept, count) in enumerate(list(summary['hot_concepts'].items())[:15], 1):
                concepts_text += f"{idx}. {concept} ({count}次)　"
                if idx % 3 == 0:
                    concepts_text += "<br/>"
            
            elements.append(Paragraph(concepts_text, styles['Normal']))
        
        return elements
    
    def _create_recommended_stocks(self, data: dict) -> list:
        """创建推荐股票部分"""
        styles = self._get_styles()
        elements = []
        
        # 标题
        elements.append(Paragraph("二、AI推荐股票", styles['Heading1']))
        elements.append(Spacer(1, 0.2*inch))
        
        recommended = data.get('recommended_stocks', [])
        
        if not recommended:
            elements.append(Paragraph("暂无推荐股票", styles['Normal']))
            return elements
        
        # 说明
        intro_text = f"""
        <para>
        基于5位AI分析师的综合分析，系统识别出以下 <b>{len(recommended)}</b> 只潜力股票，
        这些股票在资金流向、游资关注度、题材热度等多个维度表现突出。
        </para>
        """
        elements.append(Paragraph(intro_text, styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # 推荐股票表格
        table_data = [['排名', '股票代码', '股票名称', '净流入金额', '确定性', '持有周期']]
        for stock in recommended[:10]:
            table_data.append([
                str(stock.get('rank', '-')),
                stock.get('code', '-'),
                stock.get('name', '-'),
                f"{stock.get('net_inflow', 0):,.0f}",
                stock.get('confidence', '-'),
                stock.get('hold_period', '-')
            ])
        
        table = Table(table_data, colWidths=[0.7*inch, 1.2*inch, 1.5*inch, 1.5*inch, 0.9*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # 详细推荐理由
        elements.append(Paragraph("2.1 推荐理由详解", styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))
        
        for stock in recommended[:5]:  # 只详细展示前5只
            stock_text = f"""
            <para>
            <b>{stock.get('rank', '-')}. {stock.get('name', '-')} ({stock.get('code', '-')})</b><br/>
            推荐理由: {stock.get('reason', '暂无')}<br/>
            确定性: {stock.get('confidence', '-')} | 持有周期: {stock.get('hold_period', '-')}
            </para>
            """
            elements.append(Paragraph(stock_text, styles['Small']))
            elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _create_agents_analysis(self, data: dict) -> list:
        """创建AI分析师报告部分"""
        styles = self._get_styles()
        elements = []
        
        agents_analysis = data.get('agents_analysis', {})
        
        if not agents_analysis:
            return elements
        
        # 标题
        elements.append(Paragraph("三、AI分析师报告", styles['Heading1']))
        elements.append(Spacer(1, 0.2*inch))
        
        # 分析师介绍
        intro_text = """
        <para>
        本报告由5位AI专业分析师从不同维度进行分析，综合形成投资建议：<br/>
        • <b>游资行为分析师</b> - 分析游资操作特征和意图<br/>
        • <b>个股潜力分析师</b> - 挖掘次日大概率上涨的股票<br/>
        • <b>题材追踪分析师</b> - 识别热点题材和轮动机会<br/>
        • <b>风险控制专家</b> - 识别高风险股票和市场陷阱<br/>
        • <b>首席策略师</b> - 综合研判并给出最终建议
        </para>
        """
        elements.append(Paragraph(intro_text, styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # 各分析师报告
        agent_titles = {
            'youzi': '3.1 游资行为分析师',
            'stock': '3.2 个股潜力分析师',
            'theme': '3.3 题材追踪分析师',
            'risk': '3.4 风险控制专家',
            'chief': '3.5 首席策略师综合研判'
        }
        
        for agent_key, agent_title in agent_titles.items():
            agent_data = agents_analysis.get(agent_key, {})
            if agent_data:
                elements.append(Paragraph(agent_title, styles['Heading2']))
                elements.append(Spacer(1, 0.1*inch))
                
                analysis_text = agent_data.get('analysis', '暂无分析')
                # 截断过长的文本
                if len(analysis_text) > 3000:
                    analysis_text = analysis_text[:3000] + "\n...(内容过长，已截断)"
                
                elements.append(Paragraph(analysis_text, styles['Small']))
                elements.append(Spacer(1, 0.2*inch))
                
                if agent_key != 'chief':
                    elements.append(PageBreak())
        
        return elements


# 测试函数
if __name__ == "__main__":
    print("=" * 60)
    print("测试智瞰龙虎PDF生成模块")
    print("=" * 60)
    
    # 创建测试数据
    test_data = {
        'timestamp': '2024-01-15 18:30:00',
        'data_info': {
            'total_records': 150,
            'total_stocks': 50,
            'total_youzi': 30,
            'summary': {
                'total_buy_amount': 500000000,
                'total_sell_amount': 200000000,
                'total_net_inflow': 300000000,
                'top_youzi': {
                    '92科比': 14455321,
                    '赵老哥': 12000000
                },
                'top_stocks': [
                    {'code': '001337', 'name': '四川黄金', 'net_inflow': 14455321}
                ],
                'hot_concepts': {
                    '黄金概念': 10,
                    '新能源': 8
                }
            }
        },
        'recommended_stocks': [
            {
                'rank': 1,
                'code': '001337',
                'name': '四川黄金',
                'net_inflow': 14455321,
                'reason': '游资大幅买入',
                'confidence': '高',
                'hold_period': '短线'
            }
        ],
        'agents_analysis': {
            'chief': {
                'analysis': '综合分析显示...'
            }
        }
    }
    
    # 生成PDF
    generator = LonghubangPDFGenerator()
    pdf_path = generator.generate_pdf(test_data)
    print(f"\nPDF已生成: {pdf_path}")

