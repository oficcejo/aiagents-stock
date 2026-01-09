"""
智策定时分析服务
支持定时运行板块策略分析并发送邮件通知
"""

import schedule
import threading
import time
from datetime import datetime
from sector_strategy_data import SectorStrategyDataFetcher
from sector_strategy_engine import SectorStrategyEngine
from notification_service import notification_service
import json


class SectorStrategyScheduler:
    """智策定时分析调度器"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.schedule_time = "09:00"  # 默认上午9点
        self.enabled = False
        self.last_run_time = None
        self.last_result = None
        self.last_notification_time = None  # 记录上次通知时间，防止重复
        self._analysis_lock = threading.Lock()  # 添加锁，防止并发执行
        print("[智策定时] 调度器初始化完成")
    
    def start(self, schedule_time="09:00"):
        """
        启动定时任务
        
        Args:
            schedule_time: 定时时间，格式 "HH:MM"
        """
        if self.running:
            print("[智策定时] 调度器已在运行中")
            return False
        
        self.schedule_time = schedule_time
        self.enabled = True
        
        # 先清除所有带sector_strategy标签的任务
        try:
            jobs_to_remove = [job for job in schedule.jobs if 'sector_strategy' in job.tags]
            for job in jobs_to_remove:
                schedule.cancel_job(job)
            print(f"[智策定时] 清除了 {len(jobs_to_remove)} 个旧任务")
        except Exception as e:
            print(f"[智策定时] 清除旧任务时出错: {e}")
        
        # 设置定时任务（确保只添加一次）
        job = schedule.every().day.at(schedule_time).do(self._run_analysis_safe)
        job.tag('sector_strategy')
        print(f"[智策定时] 添加新任务: 每天 {schedule_time}")
        
        # 设置运行标志
        self.running = True
        
        # 启动后台线程
        self.thread = threading.Thread(target=self._schedule_loop, daemon=True)
        self.thread.start()
        
        print(f"[智策定时] ✓ 定时任务已启动，每天 {schedule_time} 运行")
        return True
    
    def stop(self):
        """停止定时任务"""
        if not self.running:
            print("[智策定时] 调度器未运行")
            return False
        
        self.running = False
        self.enabled = False
        
        # 只清除智策的任务，不影响其他模块
        jobs_to_remove = [job for job in schedule.jobs if 'sector_strategy' in job.tags]
        for job in jobs_to_remove:
            schedule.cancel_job(job)
        print(f"[智策定时] 清除了 {len(jobs_to_remove)} 个任务")
        
        print("[智策定时] ✓ 定时任务已停止")
        return True
    
    def _schedule_loop(self):
        """定时任务循环"""
        print("[智策定时] 后台线程已启动")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                print(f"[智策定时] ✗ 调度循环出错: {e}")
                time.sleep(60)
    
    def _run_analysis_safe(self):
        """运行智策分析（带锁保护，防止并发执行）"""
        # 尝试获取锁，如果已被占用则跳过本次执行
        if not self._analysis_lock.acquire(blocking=False):
            print("[智策定时] ⚠️ 上一次分析还未完成，跳过本次执行")
            return
        
        try:
            self._run_analysis()
        finally:
            self._analysis_lock.release()
    
    def _run_analysis(self):
        """运行智策分析"""
        print("\n" + "="*60)
        print(f"[智策定时] 开始定时分析 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        try:
            # 1. 获取数据
            print("[智策定时] [1/3] 获取市场数据...")
            fetcher = SectorStrategyDataFetcher()
            data = fetcher.get_all_sector_data()
            
            if not data.get("success"):
                print("[智策定时] ✗ 数据获取失败")
                self._send_error_notification("数据获取失败")
                return
            
            print("[智策定时] ✓ 数据获取成功")
            
            # 2. 运行AI分析
            print("[智策定时] [2/3] AI智能体分析中...")
            engine = SectorStrategyEngine(model="deepseek-chat")
            result = engine.run_comprehensive_analysis(data)
            
            if not result.get("success"):
                print("[智策定时] ✗ 分析失败")
                self._send_error_notification("AI分析失败")
                return
            
            print("[智策定时] ✓ 分析完成")
            
            # 3. 发送邮件通知
            print("[智策定时] [3/3] 发送邮件通知...")
            self._send_analysis_notification(result)
            
            # 保存最后运行结果
            self.last_run_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.last_result = result
            
            print("="*60)
            print("[智策定时] ✓ 定时分析完成！")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"[智策定时] ✗ 分析过程出错: {e}")
            import traceback
            traceback.print_exc()
            self._send_error_notification(f"分析异常: {str(e)}")
    
    def _send_analysis_notification(self, result):
        """发送分析结果通知（邮件和/或webhook）- 带去重保护"""
        try:
            # 去重检查：如果5分钟内已发送过通知，则跳过
            current_time = datetime.now()
            if self.last_notification_time:
                time_diff = (current_time - self.last_notification_time).total_seconds()
                if time_diff < 300:  # 5分钟 = 300秒
                    print(f"[智策定时] ⚠️ 距离上次通知仅{time_diff:.0f}秒，跳过重复发送")
                    return
            
            config = notification_service.config
            predictions = result.get("final_predictions", {})
            timestamp = result.get("timestamp", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            sent_count = 0
            
            # 尝试发送Webhook
            if config.get('webhook_enabled') and config.get('webhook_url'):
                print("[智策定时] [Webhook] 准备发送...")
                webhook_success = self._send_webhook_direct(predictions, timestamp)
                if webhook_success:
                    print("[智策定时] ✓ Webhook发送成功")
                    sent_count += 1
                else:
                    print("[智策定时] ✗ Webhook发送失败")
            
            # 尝试发送邮件
            if config.get('email_enabled') and all([
                config.get('smtp_server'), 
                config.get('email_from'),
                config.get('email_password'),
                config.get('email_to')
            ]):
                print("[智策定时] [邮件] 准备发送...")
                subject = f"智策板块分析报告 - {timestamp}"
                body = self._format_email_body(predictions, timestamp)
                email_success = self._send_email_direct(subject, body)
                if email_success:
                    print("[智策定时] ✓ 邮件发送成功")
                    sent_count += 1
                else:
                    print("[智策定时] ✗ 邮件发送失败")
            
            # 更新最后通知时间
            if sent_count > 0:
                self.last_notification_time = current_time
                print(f"[智策定时] 📝 已记录通知时间: {current_time.strftime('%H:%M:%S')}")
            
            if sent_count == 0:
                print("[智策定时] ⚠️ 未配置通知方式或发送全部失败")
        
        except Exception as e:
            print(f"[智策定时] ✗ 通知发送异常: {e}")
            import traceback
            traceback.print_exc()
    
    def _send_error_notification(self, error_msg):
        """发送错误通知邮件"""
        try:
            subject = f"智策定时分析失败 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            body = f"""
智策定时分析任务失败

时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
错误: {error_msg}

请检查系统日志获取详细信息。
"""
            self._send_email_direct(subject, body)
        except:
            pass
    
    def _send_webhook_direct(self, predictions, timestamp):
        """发送webhook通知"""
        try:
            import requests
            
            config = notification_service.config
            webhook_type = config.get('webhook_type', 'dingtalk')
            webhook_url = config['webhook_url']
            
            # 格式化简洁的分析摘要
            summary = self._format_webhook_summary(predictions, timestamp)
            
            if webhook_type == 'dingtalk':
                return self._send_dingtalk(webhook_url, summary, timestamp)
            elif webhook_type == 'feishu':
                return self._send_feishu(webhook_url, summary, timestamp)
            else:
                print(f"[智策定时] ✗ 不支持的webhook类型: {webhook_type}")
                return False
        
        except Exception as e:
            print(f"[智策定时] ✗ Webhook发送失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _send_dingtalk(self, url, summary, timestamp):
        """发送钉钉消息"""
        try:
            import requests
            
            # 获取自定义关键词
            keyword = notification_service.config.get('webhook_keyword', '')
            title_prefix = f"{keyword} - " if keyword else ""
            
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": f"{title_prefix}智策板块分析报告",
                    "text": summary
                }
            }
            
            response = requests.post(url, json=data, headers={'Content-Type': 'application/json'}, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('errcode') == 0
            return False
        
        except Exception as e:
            print(f"[智策定时] 钉钉发送异常: {e}")
            return False
    
    def _send_feishu(self, url, summary, timestamp):
        """发送飞书消息"""
        try:
            import requests
            
            # 获取自定义关键词（飞书通常不需要关键词，但保持一致性）
            keyword = notification_service.config.get('webhook_keyword', '')
            title_prefix = f"【{keyword} - " if keyword else "【"
            
            data = {
                "msg_type": "text",
                "content": {
                    "text": f"{title_prefix}智策板块分析报告】\n分析时间: {timestamp}\n\n{summary}"
                }
            }
            
            response = requests.post(url, json=data, headers={'Content-Type': 'application/json'}, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('code') == 0
            return False
        
        except Exception as e:
            print(f"[智策定时] 飞书发送异常: {e}")
            return False
    
    def _format_webhook_summary(self, predictions, timestamp):
        """格式化webhook摘要（精简版）"""
        # 获取自定义关键词
        keyword = notification_service.config.get('webhook_keyword', '')
        title_prefix = f"{keyword} - " if keyword else ""
        
        lines = []
        lines.append(f"### {title_prefix}智策板块分析报告")
        lines.append(f"**分析时间**: {timestamp}")
        lines.append("")
        
        # 板块多空（只显示高信心度的）
        long_short = predictions.get("long_short", {})
        if long_short:
            bullish = [item for item in long_short.get("bullish", []) if item.get('confidence', 0) >= 7]
            bearish = [item for item in long_short.get("bearish", []) if item.get('confidence', 0) >= 7]
            
            if bullish or bearish:
                lines.append("#### 📊 板块多空")
                if bullish:
                    lines.append("**看多**: " + "、".join([f"{item.get('sector')}({item.get('confidence')}分)" for item in bullish[:3]]))
                if bearish:
                    lines.append("**看空**: " + "、".join([f"{item.get('sector')}({item.get('confidence')}分)" for item in bearish[:3]]))
                lines.append("")
        
        # 板块轮动（只显示潜力板块）
        rotation = predictions.get("rotation", {})
        if rotation:
            potential = rotation.get("potential", [])[:3]
            if potential:
                lines.append("#### 🔄 潜力接力板块")
                for item in potential:
                    lines.append(f"- {item.get('sector')}: {item.get('advice', 'N/A')}")
                lines.append("")
        
        # 板块热度TOP3
        heat = predictions.get("heat", {})
        if heat:
            hottest = heat.get("hottest", [])[:3]
            if hottest:
                lines.append("#### 🌡️ 热度TOP3")
                for idx, item in enumerate(hottest, 1):
                    lines.append(f"{idx}. {item.get('sector')} - {item.get('score', 0)}分")
                lines.append("")
        
        # 策略总结
        summary = predictions.get("summary", {})
        if summary and summary.get('key_opportunity'):
            lines.append("#### 💡 核心机会")
            lines.append(summary['key_opportunity'][:150] + "..." if len(summary.get('key_opportunity', '')) > 150 else summary.get('key_opportunity', ''))
            lines.append("")
        
        lines.append("---")
        lines.append("*由智策AI系统自动生成*")
        
        return "\n".join(lines)
    
    def _send_email_direct(self, subject, body):
        """直接发送邮件（参考notification_service的实现）"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            config = notification_service.config
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = config['email_from']
            msg['To'] = config['email_to']
            msg['Subject'] = subject
            
            # 添加正文（纯文本）
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            print(f"[智策定时] 📧 正在发送邮件...")
            print(f"[智策定时]   - 收件人: {config['email_to']}")
            print(f"[智策定时]   - 主题: {subject}")
            
            # 根据端口选择连接方式
            if config['smtp_port'] == 465:
                print(f"[智策定时]   - 使用 SMTP_SSL 连接 {config['smtp_server']}:{config['smtp_port']}")
                server = smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'], timeout=15)
            else:
                print(f"[智策定时]   - 使用 SMTP+TLS 连接 {config['smtp_server']}:{config['smtp_port']}")
                server = smtplib.SMTP(config['smtp_server'], config['smtp_port'], timeout=15)
                server.starttls()
            
            print(f"[智策定时]   - 正在登录...")
            server.login(config['email_from'], config['email_password'])
            print(f"[智策定时]   - 正在发送...")
            server.send_message(msg)
            server.quit()
            print(f"[智策定时] ✓ 邮件发送成功")
            return True
            
        except Exception as e:
            print(f"[智策定时] ✗ 邮件发送失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _format_email_body(self, predictions, timestamp):
        """格式化邮件正文"""
        
        if not predictions or predictions.get("prediction_text"):
            # 文本格式
            return f"""
智策板块策略分析报告
分析时间: {timestamp}

{predictions.get('prediction_text', '暂无预测')}

---
本邮件由智策系统自动发送
"""
        
        # JSON格式预测
        body_parts = []
        
        # 标题
        body_parts.append("="*60)
        body_parts.append("智策板块策略分析报告")
        body_parts.append("="*60)
        body_parts.append(f"分析时间: {timestamp}")
        body_parts.append(f"AI模型: DeepSeek Multi-Agent System")
        body_parts.append("")
        
        # 1. 板块多空
        long_short = predictions.get("long_short", {})
        
        if long_short:
            body_parts.append("="*60)
            body_parts.append("一、板块多空预测")
            body_parts.append("="*60)
            body_parts.append("")
            
            # 看多板块
            bullish = long_short.get("bullish", [])
            if bullish:
                body_parts.append("【看多板块】")
                body_parts.append("")
                for idx, item in enumerate(bullish, 1):
                    body_parts.append(f"{idx}. {item.get('sector', 'N/A')} (信心度: {item.get('confidence', 0)}/10)")
                    body_parts.append(f"   理由: {item.get('reason', 'N/A')}")
                    body_parts.append(f"   风险: {item.get('risk', 'N/A')}")
                    body_parts.append("")
            
            # 看空板块
            bearish = long_short.get("bearish", [])
            if bearish:
                body_parts.append("【看空板块】")
                body_parts.append("")
                for idx, item in enumerate(bearish, 1):
                    body_parts.append(f"{idx}. {item.get('sector', 'N/A')} (信心度: {item.get('confidence', 0)}/10)")
                    body_parts.append(f"   理由: {item.get('reason', 'N/A')}")
                    body_parts.append(f"   风险: {item.get('risk', 'N/A')}")
                    body_parts.append("")
        
        # 2. 板块轮动
        rotation = predictions.get("rotation", {})
        
        if rotation:
            body_parts.append("="*60)
            body_parts.append("二、板块轮动预测")
            body_parts.append("="*60)
            body_parts.append("")
            
            # 当前强势
            current_strong = rotation.get("current_strong", [])
            if current_strong:
                body_parts.append("【当前强势板块】")
                body_parts.append("")
                for item in current_strong:
                    body_parts.append(f"• {item.get('sector', 'N/A')}")
                    body_parts.append(f"  轮动逻辑: {item.get('logic', 'N/A')[:100]}...")
                    body_parts.append(f"  时间窗口: {item.get('time_window', 'N/A')}")
                    body_parts.append(f"  操作建议: {item.get('advice', 'N/A')}")
                    body_parts.append("")
            
            # 潜力接力
            potential = rotation.get("potential", [])
            if potential:
                body_parts.append("【潜力接力板块】⭐ 重点关注")
                body_parts.append("")
                for item in potential:
                    body_parts.append(f"• {item.get('sector', 'N/A')}")
                    body_parts.append(f"  轮动逻辑: {item.get('logic', 'N/A')[:100]}...")
                    body_parts.append(f"  时间窗口: {item.get('time_window', 'N/A')}")
                    body_parts.append(f"  操作建议: {item.get('advice', 'N/A')}")
                    body_parts.append("")
        
        # 3. 板块热度
        heat = predictions.get("heat", {})
        
        if heat:
            body_parts.append("="*60)
            body_parts.append("三、板块热度排行")
            body_parts.append("="*60)
            body_parts.append("")
            
            # 最热板块
            hottest = heat.get("hottest", [])
            if hottest:
                body_parts.append("【最热板块 TOP5】")
                body_parts.append("")
                for idx, item in enumerate(hottest, 1):
                    body_parts.append(f"{idx}. {item.get('sector', 'N/A')} - 热度: {item.get('score', 0)}分 ({item.get('trend', 'N/A')})")
                body_parts.append("")
            
            # 升温板块
            heating = heat.get("heating", [])
            if heating:
                body_parts.append("【升温板块】")
                body_parts.append("")
                for idx, item in enumerate(heating, 1):
                    body_parts.append(f"{idx}. {item.get('sector', 'N/A')} - 热度: {item.get('score', 0)}分 ↗")
                body_parts.append("")
        
        # 4. 策略总结
        summary = predictions.get("summary", {})
        
        if summary:
            body_parts.append("="*60)
            body_parts.append("四、策略总结")
            body_parts.append("="*60)
            body_parts.append("")
            
            if summary.get('market_view'):
                body_parts.append("【市场观点】")
                body_parts.append(summary['market_view'])
                body_parts.append("")
            
            if summary.get('key_opportunity'):
                body_parts.append("【核心机会】⭐")
                body_parts.append(summary['key_opportunity'])
                body_parts.append("")
            
            if summary.get('major_risk'):
                body_parts.append("【主要风险】⚠️")
                body_parts.append(summary['major_risk'])
                body_parts.append("")
            
            if summary.get('strategy'):
                body_parts.append("【整体策略】")
                body_parts.append(summary['strategy'])
                body_parts.append("")
        
        # 结束语
        body_parts.append("="*60)
        body_parts.append("本报告由智策AI系统自动生成并发送")
        body_parts.append("仅供参考，不构成投资建议")
        body_parts.append("="*60)
        
        return "\n".join(body_parts)
    
    def manual_run(self):
        """手动触发一次分析"""
        print("[智策定时] 手动触发分析...")
        self._run_analysis()
    
    def get_status(self):
        """获取调度器状态"""
        return {
            "running": self.running,
            "enabled": self.enabled,
            "schedule_time": self.schedule_time,
            "last_run_time": self.last_run_time,
            "next_run_time": self._get_next_run_time()
        }
    
    def _get_next_run_time(self):
        """获取下次运行时间"""
        if not self.running:
            return None
        
        try:
            jobs = schedule.get_jobs('sector_strategy')
            if jobs:
                next_run = jobs[0].next_run
                if next_run:
                    return next_run.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
        
        return None


# 创建全局实例
sector_strategy_scheduler = SectorStrategyScheduler()


# 测试函数
if __name__ == "__main__":
    print("智策定时分析服务测试")
    print("="*60)
    
    # 启动定时任务（测试用，设置为当前时间后1分钟）
    from datetime import datetime, timedelta
    test_time = (datetime.now() + timedelta(minutes=1)).strftime("%H:%M")
    
    print(f"设置测试时间: {test_time}")
    sector_strategy_scheduler.start(test_time)
    
    # 保持运行
    try:
        while True:
            status = sector_strategy_scheduler.get_status()
            print(f"\n状态: {status}")
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n停止测试...")
        sector_strategy_scheduler.stop()

