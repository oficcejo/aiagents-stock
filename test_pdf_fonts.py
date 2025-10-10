#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF中文字体测试脚本
用于验证Docker环境中字体是否正确安装
"""

import os
import sys
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def check_system_fonts():
    """检查系统中可用的中文字体"""
    print("=" * 60)
    print("检查系统中的中文字体")
    print("=" * 60)
    
    # Windows字体路径
    windows_paths = [
        'C:/Windows/Fonts/simsun.ttc',
        'C:/Windows/Fonts/simhei.ttf',
        'C:/Windows/Fonts/msyh.ttc',
        'C:/Windows/Fonts/msyh.ttf',
    ]
    
    # Linux字体路径
    linux_paths = [
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',
    ]
    
    all_paths = windows_paths + linux_paths
    
    found_fonts = []
    for font_path in all_paths:
        if os.path.exists(font_path):
            print(f"✅ 找到字体: {font_path}")
            found_fonts.append(font_path)
        else:
            print(f"❌ 未找到: {font_path}")
    
    print(f"\n总计找到 {len(found_fonts)} 个中文字体文件")
    return found_fonts

def test_font_registration():
    """测试字体注册"""
    print("\n" + "=" * 60)
    print("测试字体注册")
    print("=" * 60)
    
    fonts = check_system_fonts()
    
    if not fonts:
        print("\n❌ 错误：未找到任何中文字体")
        print("建议：")
        print("  - Windows: 确保系统已安装中文字体")
        print("  - Linux/Docker: 运行 'apt-get install fonts-noto-cjk fonts-wqy-zenhei'")
        return False
    
    # 尝试注册第一个找到的字体
    test_font = fonts[0]
    try:
        pdfmetrics.registerFont(TTFont('TestChineseFont', test_font))
        print(f"\n✅ 成功注册字体: {test_font}")
        print(f"   注册名称: TestChineseFont")
        return True
    except Exception as e:
        print(f"\n❌ 字体注册失败: {e}")
        return False

def test_pdf_generation():
    """测试PDF生成"""
    print("\n" + "=" * 60)
    print("测试PDF生成")
    print("=" * 60)
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        from reportlab.lib.styles import ParagraphStyle
        import io
        
        # 导入字体注册函数
        from pdf_generator import register_chinese_fonts
        
        # 注册字体
        font_name = register_chinese_fonts()
        print(f"\n使用字体: {font_name}")
        
        # 创建测试PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        # 创建样式
        style = ParagraphStyle(
            'TestStyle',
            fontName=font_name,
            fontSize=12
        )
        
        # 创建内容
        test_text = "这是一个中文PDF测试 - AI股票分析系统"
        paragraph = Paragraph(test_text, style)
        
        # 生成PDF
        doc.build([paragraph])
        
        # 检查生成的PDF大小
        pdf_size = len(buffer.getvalue())
        print(f"✅ PDF生成成功，大小: {pdf_size} 字节")
        
        # 保存测试PDF
        with open('test_chinese_pdf.pdf', 'wb') as f:
            f.write(buffer.getvalue())
        print(f"✅ 测试PDF已保存到: test_chinese_pdf.pdf")
        print(f"   请打开文件检查中文是否正常显示")
        
        return True
        
    except Exception as e:
        print(f"❌ PDF生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "PDF中文字体测试" + " " * 15 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # 检测操作系统
    import platform
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"Python版本: {sys.version}")
    print()
    
    # 运行测试
    font_check = check_system_fonts()
    font_reg = test_font_registration()
    pdf_gen = test_pdf_generation()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"字体检查: {'✅ 通过' if font_check else '❌ 失败'}")
    print(f"字体注册: {'✅ 通过' if font_reg else '❌ 失败'}")
    print(f"PDF生成: {'✅ 通过' if pdf_gen else '❌ 失败'}")
    
    if font_check and font_reg and pdf_gen:
        print("\n🎉 所有测试通过！PDF中文字体配置正确。")
    else:
        print("\n⚠️ 部分测试失败，请查看上方详细信息进行排查。")
    
    print()

if __name__ == "__main__":
    main()

