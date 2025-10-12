"""
智策报告PDF导出模块
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


class SectorStrategyPDFGenerator:
    """智策报告PDF生成器"""
    
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
        生成智策分析PDF报告
        
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
                output_path = os.path.join(temp_dir, f"智策报告_{timestamp}.pdf")
            
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
            
            # 添加市场概况
            story.extend(self._create_market_overview(result_data))
            story.append(PageBreak())
            
            # 添加核心预测
            story.extend(self._create_predictions_section(result_data))
            story.append(PageBreak())
            
            # 添加智能体分析摘要
            story.extend(self._create_agents_summary(result_data))
            story.append(PageBreak())
            
            # 添加综合研判
            story.extend(self._create_comprehensive_report(result_data))
            
            # 生成PDF
            doc.build(story)
            
            print(f"[PDF] 报告生成成功: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"[PDF] 生成失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _create_title_page(self, data: dict) -> list:
        """创建标题页"""
        styles = self._get_styles()
        elements = []
        
        # 添加空白
        elements.append(Spacer(1, 2*inch))
        
        # 主标题
        title = Paragraph("智策板块策略分析报告", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.5*inch))
        
        # 副标题
        subtitle = Paragraph("AI驱动的多维度板块投资决策支持系统", styles['Heading2'])
        elements.append(subtitle)
        elements.append(Spacer(1, 1*inch))
        
        # 报告信息
        timestamp = data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        info_text = f"""
        <para align=center>
        <b>生成时间:</b> {timestamp}<br/>
        <b>分析周期:</b> 当日市场数据<br/>
        <b>AI模型:</b> DeepSeek Multi-Agent System<br/>
        <b>分析维度:</b> 宏观·板块·资金·情绪
        </para>
        """
        info = Paragraph(info_text, styles['Normal'])
        elements.append(info)
        elements.append(Spacer(1, 1*inch))
        
        # 免责声明
        disclaimer = Paragraph(
            "<para align=center><i>本报告由AI系统自动生成，仅供参考，不构成投资建议。<br/>"
            "投资有风险，决策需谨慎。</i></para>",
            styles['Normal']
        )
        elements.append(disclaimer)
        
        return elements
    
    def _create_market_overview(self, data: dict) -> list:
        """创建市场概况部分"""
        styles = self._get_styles()
        elements = []
        
        # 标题
        elements.append(Paragraph("一、市场概况", styles['Heading1']))
        elements.append(Spacer(1, 0.2*inch))
        
        # 这里需要从原始数据中提取市场概况
        # 由于result_data中可能没有直接的市场数据，我们从agents_analysis中提取
        
        overview_text = f"""
        <para>
        本报告基于{data.get('timestamp', 'N/A')}的实时市场数据，
        通过四位AI智能体的多维度分析，为您提供板块投资策略建议。
        </para>
        """
        elements.append(Paragraph(overview_text, styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # 分析师团队
        team_text = """
        <para>
        <b>分析师团队:</b><br/>
        • 宏观策略师 - 分析宏观经济、政策导向、新闻事件<br/>
        • 板块诊断师 - 分析板块走势、估值水平、轮动特征<br/>
        • 资金流向分析师 - 分析主力资金、北向资金流向<br/>
        • 市场情绪解码员 - 分析市场情绪、热度、赚钱效应
        </para>
        """
        elements.append(Paragraph(team_text, styles['Normal']))
        
        return elements
    
    def _create_predictions_section(self, data: dict) -> list:
        """创建核心预测部分"""
        styles = self._get_styles()
        elements = []
        
        predictions = data.get('final_predictions', {})
        
        if predictions.get('prediction_text'):
            # 文本格式
            elements.append(Paragraph("二、核心预测", styles['Heading1']))
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph(predictions['prediction_text'], styles['Normal']))
            return elements
        
        # JSON格式预测
        elements.append(Paragraph("二、核心预测", styles['Heading1']))
        elements.append(Spacer(1, 0.2*inch))
        
        # 1. 板块多空
        elements.extend(self._create_long_short_section(predictions, styles))
        elements.append(Spacer(1, 0.3*inch))
        
        # 2. 板块轮动
        elements.extend(self._create_rotation_section(predictions, styles))
        elements.append(Spacer(1, 0.3*inch))
        
        # 3. 板块热度
        elements.extend(self._create_heat_section(predictions, styles))
        elements.append(Spacer(1, 0.3*inch))
        
        # 4. 策略总结
        elements.extend(self._create_summary_section(predictions, styles))
        
        return elements
    
    def _create_long_short_section(self, predictions: dict, styles: dict) -> list:
        """创建板块多空部分"""
        elements = []
        
        elements.append(Paragraph("2.1 板块多空预测", styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))
        
        long_short = predictions.get('long_short', {})
        
        # 看多板块
        bullish = long_short.get('bullish', [])
        if bullish:
            elements.append(Paragraph("<b>看多板块:</b>", styles['Normal']))
            
            for idx, item in enumerate(bullish, 1):
                text = f"""
                {idx}. <b>{item.get('sector', 'N/A')}</b> (信心度: {item.get('confidence', 0)}/10)<br/>
                   理由: {item.get('reason', 'N/A')}<br/>
                   风险: {item.get('risk', 'N/A')}
                """
                elements.append(Paragraph(text, styles['Small']))
                elements.append(Spacer(1, 0.05*inch))
        
        # 看空板块
        bearish = long_short.get('bearish', [])
        if bearish:
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph("<b>看空板块:</b>", styles['Normal']))
            
            for idx, item in enumerate(bearish, 1):
                text = f"""
                {idx}. <b>{item.get('sector', 'N/A')}</b> (信心度: {item.get('confidence', 0)}/10)<br/>
                   理由: {item.get('reason', 'N/A')}<br/>
                   风险: {item.get('risk', 'N/A')}
                """
                elements.append(Paragraph(text, styles['Small']))
                elements.append(Spacer(1, 0.05*inch))
        
        return elements
    
    def _create_rotation_section(self, predictions: dict, styles: dict) -> list:
        """创建板块轮动部分"""
        elements = []
        
        elements.append(Paragraph("2.2 板块轮动预测", styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))
        
        rotation = predictions.get('rotation', {})
        
        # 当前强势
        current_strong = rotation.get('current_strong', [])
        if current_strong:
            elements.append(Paragraph("<b>当前强势板块:</b>", styles['Normal']))
            for item in current_strong:
                text = f"""
                • <b>{item.get('sector', 'N/A')}</b><br/>
                  轮动逻辑: {item.get('logic', 'N/A')[:100]}...<br/>
                  时间窗口: {item.get('time_window', 'N/A')}<br/>
                  操作建议: {item.get('advice', 'N/A')}
                """
                elements.append(Paragraph(text, styles['Small']))
                elements.append(Spacer(1, 0.05*inch))
        
        # 潜力接力
        potential = rotation.get('potential', [])
        if potential:
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph("<b>潜力接力板块:</b>", styles['Normal']))
            for item in potential:
                text = f"""
                • <b>{item.get('sector', 'N/A')}</b><br/>
                  轮动逻辑: {item.get('logic', 'N/A')[:100]}...<br/>
                  时间窗口: {item.get('time_window', 'N/A')}<br/>
                  操作建议: {item.get('advice', 'N/A')}
                """
                elements.append(Paragraph(text, styles['Small']))
                elements.append(Spacer(1, 0.05*inch))
        
        return elements
    
    def _create_heat_section(self, predictions: dict, styles: dict) -> list:
        """创建板块热度部分"""
        elements = []
        
        elements.append(Paragraph("2.3 板块热度排行", styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))
        
        heat = predictions.get('heat', {})
        
        # 创建表格数据
        table_data = [['排名', '板块', '热度评分', '趋势', '持续性']]
        
        # 最热板块
        hottest = heat.get('hottest', [])
        for idx, item in enumerate(hottest[:5], 1):
            table_data.append([
                str(idx),
                item.get('sector', 'N/A'),
                str(item.get('score', 0)),
                item.get('trend', 'N/A'),
                item.get('sustainability', 'N/A')
            ])
        
        if len(table_data) > 1:
            # 创建表格
            table = Table(table_data, colWidths=[0.8*inch, 2*inch, 1*inch, 1*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), self.chinese_font),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), self.chinese_font),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            elements.append(table)
        
        return elements
    
    def _create_summary_section(self, predictions: dict, styles: dict) -> list:
        """创建策略总结部分"""
        elements = []
        
        summary = predictions.get('summary', {})
        
        if not summary:
            return elements
        
        elements.append(Paragraph("2.4 策略总结", styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))
        
        # 市场观点
        if summary.get('market_view'):
            elements.append(Paragraph("<b>市场观点:</b>", styles['Normal']))
            elements.append(Paragraph(summary['market_view'], styles['Small']))
            elements.append(Spacer(1, 0.1*inch))
        
        # 核心机会
        if summary.get('key_opportunity'):
            elements.append(Paragraph("<b>核心机会:</b>", styles['Normal']))
            elements.append(Paragraph(summary['key_opportunity'], styles['Small']))
            elements.append(Spacer(1, 0.1*inch))
        
        # 主要风险
        if summary.get('major_risk'):
            elements.append(Paragraph("<b>主要风险:</b>", styles['Normal']))
            elements.append(Paragraph(summary['major_risk'], styles['Small']))
            elements.append(Spacer(1, 0.1*inch))
        
        # 整体策略
        if summary.get('strategy'):
            elements.append(Paragraph("<b>整体策略:</b>", styles['Normal']))
            elements.append(Paragraph(summary['strategy'], styles['Small']))
        
        return elements
    
    def _create_agents_summary(self, data: dict) -> list:
        """创建智能体分析摘要"""
        styles = self._get_styles()
        elements = []
        
        elements.append(Paragraph("三、AI智能体分析摘要", styles['Heading1']))
        elements.append(Spacer(1, 0.2*inch))
        
        agents_analysis = data.get('agents_analysis', {})
        
        for key, agent_data in agents_analysis.items():
            agent_name = agent_data.get('agent_name', '未知分析师')
            agent_role = agent_data.get('agent_role', '')
            analysis = agent_data.get('analysis', '')
            
            # 分析师名称和职责
            elements.append(Paragraph(f"<b>{agent_name}</b>", styles['Heading2']))
            elements.append(Paragraph(f"<i>{agent_role}</i>", styles['Small']))
            elements.append(Spacer(1, 0.1*inch))
            
            # 分析内容（截取前500字）
            analysis_preview = analysis[:500] + "..." if len(analysis) > 500 else analysis
            elements.append(Paragraph(analysis_preview, styles['Small']))
            elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_comprehensive_report(self, data: dict) -> list:
        """创建综合研判部分"""
        styles = self._get_styles()
        elements = []
        
        elements.append(Paragraph("四、综合研判", styles['Heading1']))
        elements.append(Spacer(1, 0.2*inch))
        
        report = data.get('comprehensive_report', '')
        
        if report:
            # 截取前1000字
            report_preview = report[:1000] + "..." if len(report) > 1000 else report
            elements.append(Paragraph(report_preview, styles['Small']))
        else:
            elements.append(Paragraph("暂无综合研判数据", styles['Normal']))
        
        elements.append(Spacer(1, 0.3*inch))
        
        # 添加结束语
        ending = Paragraph(
            "<para align=center><i>--- 报告结束 ---<br/>"
            "本报告由智策AI系统自动生成</i></para>",
            styles['Normal']
        )
        elements.append(ending)
        
        return elements
    
    def _get_styles(self) -> dict:
        """获取样式"""
        styles = getSampleStyleSheet()
        
        # 自定义样式
        custom_styles = {
            'Title': ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontName=self.chinese_font,
                fontSize=24,
                textColor=colors.HexColor('#667eea'),
                spaceAfter=30,
                alignment=TA_CENTER
            ),
            'Heading1': ParagraphStyle(
                'CustomHeading1',
                parent=styles['Heading1'],
                fontName=self.chinese_font,
                fontSize=16,
                textColor=colors.HexColor('#667eea'),
                spaceAfter=12,
                spaceBefore=12
            ),
            'Heading2': ParagraphStyle(
                'CustomHeading2',
                parent=styles['Heading2'],
                fontName=self.chinese_font,
                fontSize=14,
                textColor=colors.HexColor('#764ba2'),
                spaceAfter=10,
                spaceBefore=10
            ),
            'Normal': ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=11,
                leading=16,
                alignment=TA_JUSTIFY
            ),
            'Small': ParagraphStyle(
                'CustomSmall',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=9,
                leading=14,
                alignment=TA_LEFT
            )
        }
        
        return custom_styles


# 测试函数
if __name__ == "__main__":
    # 创建测试数据
    test_data = {
        "success": True,
        "timestamp": "2024-01-15 10:30:00",
        "final_predictions": {
            "long_short": {
                "bullish": [
                    {
                        "sector": "电子",
                        "confidence": 8,
                        "reason": "政策支持，资金持续流入",
                        "risk": "估值偏高，注意回调风险"
                    }
                ],
                "bearish": []
            },
            "rotation": {
                "current_strong": [],
                "potential": [],
                "declining": []
            },
            "heat": {
                "hottest": [
                    {"sector": "电子", "score": 95, "trend": "升温", "sustainability": "强"}
                ]
            },
            "summary": {
                "market_view": "市场整体向好",
                "key_opportunity": "科技板块",
                "major_risk": "估值风险",
                "strategy": "积极配置科技"
            }
        },
        "agents_analysis": {},
        "comprehensive_report": "综合研判内容..."
    }
    
    generator = SectorStrategyPDFGenerator()
    output_path = generator.generate_pdf(test_data)
    print(f"测试PDF生成: {output_path}")

