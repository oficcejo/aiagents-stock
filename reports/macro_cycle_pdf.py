"""
宏观周期分析 - PDF报告生成模块
生成康波周期 × 美林投资时钟 × 中国政策分析的完整PDF报告
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import os
import tempfile
import re


class MacroCyclePDFGenerator:
    """宏观周期分析PDF报告生成器"""

    def __init__(self):
        """初始化PDF生成器"""
        self.setup_fonts()

    def setup_fonts(self):
        """设置中文字体"""
        try:
            font_paths = [
                'C:/Windows/Fonts/msyh.ttc',   # 微软雅黑
                'C:/Windows/Fonts/simsun.ttc',  # 宋体
                'C:/Windows/Fonts/simhei.ttf',  # 黑体
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',  # Linux
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
            ]

            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        self.chinese_font = 'ChineseFont'
                        print(f"[宏观PDF] 成功加载字体: {font_path}")
                        return
                    except:
                        continue

            self.chinese_font = 'Helvetica'
            print("[宏观PDF] 警告: 未找到中文字体，使用默认字体")

        except Exception as e:
            print(f"[宏观PDF] 字体设置失败: {e}")
            self.chinese_font = 'Helvetica'

    def generate_pdf(self, result_data: dict, output_path: str = None) -> str:
        """
        生成宏观周期分析PDF报告

        Args:
            result_data: 分析结果数据
            output_path: 输出路径，如果为None则生成临时文件

        Returns:
            PDF文件路径
        """
        try:
            if output_path is None:
                temp_dir = tempfile.gettempdir()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(temp_dir, f"宏观周期报告_{timestamp}.pdf")

            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=0.5*inch,
                leftMargin=0.5*inch,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch
            )

            story = []

            # 1. 标题页
            story.extend(self._create_title_page(result_data))
            story.append(PageBreak())

            # 2. 首席宏观策略师综合研判（最重要，放最前面）
            story.extend(self._create_chief_section(result_data))
            story.append(PageBreak())

            # 3. 康波周期分析
            story.extend(self._create_kondratieff_section(result_data))
            story.append(PageBreak())

            # 4. 美林投资时钟分析
            story.extend(self._create_merrill_section(result_data))
            story.append(PageBreak())

            # 5. 中国政策分析
            story.extend(self._create_policy_section(result_data))

            # 6. 结束语
            story.extend(self._create_ending())

            # 生成PDF
            doc.build(story)

            print(f"[宏观PDF] 报告生成成功: {output_path}")
            return output_path

        except Exception as e:
            print(f"[宏观PDF] 生成失败: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _clean_markdown(self, text: str) -> str:
        """清理Markdown标记，转换为适合PDF的纯文本/HTML"""
        if not text:
            return ""
        # 移除markdown粗体 **text** → text
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        # 移除markdown斜体 *text* → text
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        # 移除markdown标题 ## → 空
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # 移除markdown链接 [text](url) → text
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        # 移除markdown表格分隔线
        text = re.sub(r'\|[-:]+\|[-:| ]+\|', '', text)
        # 替换换行
        text = text.replace('\n', '<br/>')
        return text

    def _split_text_to_paragraphs(self, text: str, styles: dict, max_chars: int = 0) -> list:
        """将长文本分段为多个Paragraph，避免单段过长溢出"""
        elements = []
        if not text:
            return elements

        if max_chars > 0 and len(text) > max_chars:
            text = text[:max_chars] + "...（更多内容请查看网页版完整报告）"

        # 按段落分割
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            # 清理markdown
            cleaned = self._clean_markdown(para)
            if cleaned:
                try:
                    elements.append(Paragraph(cleaned, styles['Small']))
                    elements.append(Spacer(1, 0.08*inch))
                except Exception:
                    # 如果格式化失败，用纯文本
                    plain = re.sub(r'<[^>]+>', '', cleaned)
                    elements.append(Paragraph(plain, styles['Small']))
                    elements.append(Spacer(1, 0.08*inch))

        return elements

    def _create_title_page(self, data: dict) -> list:
        """创建标题页"""
        styles = self._get_styles()
        elements = []

        elements.append(Spacer(1, 1.5*inch))

        # 主标题
        elements.append(Paragraph("宏观周期分析报告", styles['Title']))
        elements.append(Spacer(1, 0.3*inch))

        # 副标题
        elements.append(Paragraph(
            "康波周期 × 美林投资时钟 × 中国政策分析",
            styles['Heading2']
        ))
        elements.append(Spacer(1, 0.8*inch))

        # 报告信息
        timestamp = data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        info_text = f"""
        <para align=center>
        <b>生成时间:</b> {timestamp}<br/>
        <b>分析框架:</b> 三维周期定位系统<br/>
        <b>AI分析师:</b> 4位专业分析师协同研判<br/>
        <b>分析维度:</b> 康波长周期 · 美林中短周期 · 中国政策环境<br/>
        <b>数据来源:</b> AKShare宏观经济数据
        </para>
        """
        elements.append(Paragraph(info_text, styles['Normal']))
        elements.append(Spacer(1, 0.5*inch))

        # 分析师团队
        team_text = """
        <para align=center>
        <b>AI分析师团队:</b><br/>
        康波周期分析师 · 美林时钟分析师 · 中国政策分析师 · 首席宏观策略师
        </para>
        """
        elements.append(Paragraph(team_text, styles['Normal']))
        elements.append(Spacer(1, 0.8*inch))

        # 免责声明
        elements.append(Paragraph(
            "<para align=center><i>本报告由AI系统自动生成，仅供学习研究参考，不构成投资建议。<br/>"
            "周期理论是认知框架而非精确预测工具。投资有风险，入市需谨慎。</i></para>",
            styles['Small']
        ))

        return elements

    def _create_chief_section(self, data: dict) -> list:
        """创建首席宏观策略师综合研判部分"""
        styles = self._get_styles()
        elements = []

        elements.append(Paragraph("一、首席宏观策略师 — 综合研判", styles['Heading1']))
        elements.append(Spacer(1, 0.15*inch))
        elements.append(Paragraph(
            "<i>整合康波周期、美林投资时钟、中国政策三个维度，构建周期仪表盘，给出最终综合投资策略。</i>",
            styles['Small']
        ))
        elements.append(Spacer(1, 0.15*inch))

        chief = data.get('agents_analysis', {}).get('chief', {})
        analysis = chief.get('analysis', '暂无分析结果')
        elements.extend(self._split_text_to_paragraphs(analysis, styles, max_chars=5000))

        return elements

    def _create_kondratieff_section(self, data: dict) -> list:
        """创建康波周期分析部分"""
        styles = self._get_styles()
        elements = []

        elements.append(Paragraph("二、康波周期分析 — 60年长周期定位", styles['Heading1']))
        elements.append(Spacer(1, 0.15*inch))
        elements.append(Paragraph(
            "<i>基于康德拉季耶夫长波理论（周金涛\"人生发财靠康波\"），判断当前处于第五轮信息技术康波的阶段位置。</i>",
            styles['Small']
        ))
        elements.append(Spacer(1, 0.15*inch))

        kondratieff = data.get('agents_analysis', {}).get('kondratieff', {})
        analysis = kondratieff.get('analysis', '暂无分析结果')
        elements.extend(self._split_text_to_paragraphs(analysis, styles, max_chars=5000))

        return elements

    def _create_merrill_section(self, data: dict) -> list:
        """创建美林投资时钟分析部分"""
        styles = self._get_styles()
        elements = []

        elements.append(Paragraph("三、美林投资时钟 — 中短周期定位", styles['Heading1']))
        elements.append(Spacer(1, 0.15*inch))
        elements.append(Paragraph(
            "<i>基于经济增长与通胀两大维度，结合中国政策方向（第三维度），判断当前处于美林时钟的哪个象限。</i>",
            styles['Small']
        ))
        elements.append(Spacer(1, 0.15*inch))

        merrill = data.get('agents_analysis', {}).get('merrill', {})
        analysis = merrill.get('analysis', '暂无分析结果')
        elements.extend(self._split_text_to_paragraphs(analysis, styles, max_chars=5000))

        return elements

    def _create_policy_section(self, data: dict) -> list:
        """创建中国政策分析部分"""
        styles = self._get_styles()
        elements = []

        elements.append(Paragraph("四、中国政策环境分析", styles['Heading1']))
        elements.append(Spacer(1, 0.15*inch))
        elements.append(Paragraph(
            "<i>深度分析货币政策、财政政策、产业政策、房地产政策，评估政策对周期的影响和投资机会。</i>",
            styles['Small']
        ))
        elements.append(Spacer(1, 0.15*inch))

        policy = data.get('agents_analysis', {}).get('policy', {})
        analysis = policy.get('analysis', '暂无分析结果')
        elements.extend(self._split_text_to_paragraphs(analysis, styles, max_chars=5000))

        return elements

    def _create_ending(self) -> list:
        """创建结束语"""
        styles = self._get_styles()
        elements = []

        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph(
            "<para align=center><i>--- 报告结束 ---<br/>"
            "本报告由宏观周期AI分析系统自动生成<br/>"
            "康波是罗盘，美林是航海图，政策是季风<br/>"
            "愿你在经济的海洋中，驶向属于自己的财富彼岸</i></para>",
            styles['Normal']
        ))

        return elements

    def _get_styles(self) -> dict:
        """获取样式"""
        styles = getSampleStyleSheet()

        custom_styles = {
            'Title': ParagraphStyle(
                'MacroTitle',
                parent=styles['Title'],
                fontName=self.chinese_font,
                fontSize=26,
                textColor=colors.HexColor('#302b63'),
                spaceAfter=30,
                alignment=TA_CENTER
            ),
            'Heading1': ParagraphStyle(
                'MacroHeading1',
                parent=styles['Heading1'],
                fontName=self.chinese_font,
                fontSize=16,
                textColor=colors.HexColor('#0f0c29'),
                spaceAfter=12,
                spaceBefore=12
            ),
            'Heading2': ParagraphStyle(
                'MacroHeading2',
                parent=styles['Heading2'],
                fontName=self.chinese_font,
                fontSize=14,
                textColor=colors.HexColor('#302b63'),
                spaceAfter=10,
                spaceBefore=10,
                alignment=TA_CENTER
            ),
            'Normal': ParagraphStyle(
                'MacroNormal',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=11,
                leading=16,
                alignment=TA_JUSTIFY
            ),
            'Small': ParagraphStyle(
                'MacroSmall',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=9,
                leading=14,
                alignment=TA_LEFT
            )
        }

        return custom_styles


def generate_macro_cycle_markdown(result_data: dict) -> str:
    """生成宏观周期分析的Markdown报告"""
    parts = []
    timestamp = result_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    parts.append("# 🧭 宏观周期分析报告\n")
    parts.append(f"**生成时间**: {timestamp}\n")
    parts.append("**分析框架**: 康波周期 × 美林投资时钟 × 中国政策分析\n")
    parts.append("---\n")

    agents = result_data.get('agents_analysis', {})

    # 首席策略师
    chief = agents.get('chief', {})
    if chief:
        parts.append("## 👔 一、首席宏观策略师 — 综合研判\n")
        parts.append(chief.get('analysis', '暂无分析结果'))
        parts.append("\n\n---\n")

    # 康波周期
    kondratieff = agents.get('kondratieff', {})
    if kondratieff:
        parts.append("## 🌊 二、康波周期分析 — 60年长周期定位\n")
        parts.append(kondratieff.get('analysis', '暂无分析结果'))
        parts.append("\n\n---\n")

    # 美林时钟
    merrill = agents.get('merrill', {})
    if merrill:
        parts.append("## ⏰ 三、美林投资时钟 — 中短周期定位\n")
        parts.append(merrill.get('analysis', '暂无分析结果'))
        parts.append("\n\n---\n")

    # 政策分析
    policy = agents.get('policy', {})
    if policy:
        parts.append("## 🏛️ 四、中国政策环境分析\n")
        parts.append(policy.get('analysis', '暂无分析结果'))
        parts.append("\n\n---\n")

    # 免责声明
    parts.append("\n> ⚠️ **免责声明**: 本报告由AI系统自动生成，仅供学习研究参考，不构成投资建议。")
    parts.append("周期理论是认知框架而非精确预测工具。投资有风险，入市需谨慎。\n")

    return "\n".join(parts)


# 测试
if __name__ == "__main__":
    print("=" * 60)
    print("测试宏观周期PDF生成器")
    print("=" * 60)

    test_data = {
        "success": True,
        "timestamp": "2026-02-27 14:00:00",
        "agents_analysis": {
            "chief": {"analysis": "综合研判测试内容..."},
            "kondratieff": {"analysis": "康波分析测试内容..."},
            "merrill": {"analysis": "美林时钟测试内容..."},
            "policy": {"analysis": "政策分析测试内容..."},
        }
    }

    generator = MacroCyclePDFGenerator()
    output_path = generator.generate_pdf(test_data)
    print(f"测试PDF生成: {output_path}")
