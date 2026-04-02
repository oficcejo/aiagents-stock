"""
持仓定时分析调度器模块

提供定时任务调度功能，在设定时间自动执行持仓批量分析
"""

import schedule
import threading
import time
from datetime import datetime
from typing import Optional, Callable
import traceback

from portfolio_manager import portfolio_manager
from notification_service import NotificationService


class PortfolioScheduler:
    """持仓分析定时调度器"""
    
    def __init__(self):
        """初始化调度器"""
        self.schedule_times = ["09:30"]  # 支持多个定时时间点
        self.analysis_mode = "sequential"  # 默认顺序分析
        self._is_running = False  # 使用私有属性
        self.thread = None
        self.last_run_time = None
        self.next_run_time = None
        self.auto_monitor_sync = True  # 默认启用自动监测同步
        self.notification_enabled = True  # 默认启用通知
        self.selected_agents = None  # None表示全部分析师
        self.notification_service = NotificationService()
        self.max_workers = 3  # 并行模式的线程数
        self.task_lock = threading.Lock()  # 添加执行锁
    
    # 兼容旧代码的属性
    @property
    def schedule_time(self) -> str:
        """获取第一个定时时间（向后兼容）"""
        return self.schedule_times[0] if self.schedule_times else "09:30"
    
    def is_running(self) -> bool:
        """
        检查调度器是否正在运行
        
        Returns:
            bool: True表示运行中，False表示已停止
        """
        return self._is_running
    
    def set_schedule_time(self, time_str: str):
        """
        设置定时分析时间（向后兼容，设置为单个时间）
        
        Args:
            time_str: 时间字符串，格式"HH:MM"（如"08:00"）
        """
        try:
            # 验证时间格式
            datetime.strptime(time_str, "%H:%M")
            self.schedule_times = [time_str]
            print(f"[OK] 设置定时分析时间: {time_str}")
            
            # 如果调度器正在运行，重新调度
            if self._is_running:
                self._reschedule()
                
        except ValueError:
            print(f"[ERROR] 无效的时间格式: {time_str}，应为 HH:MM")
    
    def add_schedule_time(self, time_str: str) -> bool:
        """
        添加一个定时分析时间点
        
        Args:
            time_str: 时间字符串，格式"HH:MM"
            
        Returns:
            是否添加成功
        """
        try:
            # 验证时间格式
            datetime.strptime(time_str, "%H:%M")
            
            # 检查是否已存在
            if time_str in self.schedule_times:
                print(f"[WARN] 定时时间 {time_str} 已存在")
                return False
            
            self.schedule_times.append(time_str)
            self.schedule_times.sort()  # 保持时间顺序
            print(f"[OK] 添加定时时间: {time_str}")
            
            # 如果调度器正在运行，重新调度
            if self._is_running:
                self._reschedule()
            
            return True
            
        except ValueError:
            print(f"[ERROR] 无效的时间格式: {time_str}，应为 HH:MM")
            return False
    
    def remove_schedule_time(self, time_str: str) -> bool:
        """
        删除一个定时分析时间点
        
        Args:
            time_str: 时间字符串
            
        Returns:
            是否删除成功
        """
        if time_str in self.schedule_times:
            self.schedule_times.remove(time_str)
            print(f"[OK] 删除定时时间: {time_str}")
            
            # 如果调度器正在运行，重新调度
            if self._is_running:
                self._reschedule()
            
            return True
        else:
            print(f"[WARN] 定时时间 {time_str} 不存在")
            return False
    
    def get_schedule_times(self) -> list:
        """
        获取所有定时分析时间点
        
        Returns:
            时间列表
        """
        return self.schedule_times.copy()
    
    def set_schedule_times(self, times: list):
        """
        批量设置定时分析时间点
        
        Args:
            times: 时间字符串列表
        """
        valid_times = []
        for time_str in times:
            try:
                datetime.strptime(time_str, "%H:%M")
                valid_times.append(time_str)
            except ValueError:
                print(f"[WARN] 跳过无效时间: {time_str}")
        
        if valid_times:
            self.schedule_times = sorted(valid_times)
            print(f"[OK] 设置定时时间: {', '.join(self.schedule_times)}")
            
            # 如果调度器正在运行，重新调度
            if self._is_running:
                self._reschedule()
        else:
            print(f"[ERROR] 没有有效的时间配置")
    
    def set_analysis_mode(self, mode: str):
        """
        设置分析模式
        
        Args:
            mode: "sequential" 或 "parallel"
        """
        if mode in ["sequential", "parallel"]:
            self.analysis_mode = mode
            print(f"[OK] 设置分析模式: {mode}")
        else:
            print(f"[ERROR] 无效的分析模式: {mode}")
    
    def set_auto_monitor_sync(self, enabled: bool):
        """设置是否启用自动监测同步"""
        self.auto_monitor_sync = enabled
        print(f"[OK] 自动监测同步: {'启用' if enabled else '禁用'}")
    
    def set_notification_enabled(self, enabled: bool):
        """设置是否启用通知"""
        self.notification_enabled = enabled
        print(f"[OK] 通知推送: {'启用' if enabled else '禁用'}")
    
    def set_selected_agents(self, agents: Optional[list]):
        """设置参与分析的AI分析师"""
        self.selected_agents = agents
        if agents:
            print(f"[OK] 选择分析师: {', '.join(agents)}")
        else:
            print("[OK] 选择分析师: 全部")
    
    def _scheduled_job(self):
        # 尝试获取锁，若失败则跳过执行
        if not self.task_lock.acquire(blocking=False):
            print("⚠️ 任务正在执行中，跳过本次调度")
            return
        """定时任务执行的作业"""
        print("\n" + "="*60)
        print(f"定时分析开始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")
        
        try:
            # 1. 执行批量分析
            print("[1/4] 执行持仓批量分析...")
            analysis_results = portfolio_manager.batch_analyze_portfolio(
                mode=self.analysis_mode,
                max_workers=self.max_workers,
                selected_agents=self.selected_agents
            )
            
            if not analysis_results.get("success"):
                error_msg = analysis_results.get("error", "未知错误")
                print(f"[ERROR] 批量分析失败: {error_msg}")
                
                # 发送错误通知
                if self.notification_enabled:
                    self._send_error_notification(error_msg)
                
                self.last_run_time = datetime.now()
                return
            
            # 2. 保存分析结果
            print("\n[2/4] 保存分析结果...")
            saved_ids = portfolio_manager.save_analysis_results(analysis_results)
            print(f"[OK] 保存 {len(saved_ids)} 条分析记录")
            
            # 3. 自动监测同步
            sync_result = None
            if self.auto_monitor_sync:
                print("\n[3/4] 自动同步到监测列表...")
                sync_result = self._sync_to_monitor(analysis_results)
            else:
                print("\n[3/4] 跳过监测同步（已禁用）")
            
            # 4. 发送通知
            if self.notification_enabled:
                print("\n[4/4] 发送通知...")
                self._send_notification(analysis_results, sync_result)
            else:
                print("\n[4/4] 跳过通知发送（已禁用）")
            
            # 更新运行时间
            self.last_run_time = datetime.now()
            
            print("\n" + "="*60)
            print(f"定时分析完成: {self.last_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"\n[ERROR] 定时任务执行异常: {str(e)}")
            traceback.print_exc()
            
            # 发送错误通知
            if self.notification_enabled:
                self._send_error_notification(str(e))
            
            self.last_run_time = datetime.now()
        finally:
            self.task_lock.release()  # 释放锁
            self.last_run_time = datetime.now()
    
    def _sync_to_monitor(self, analysis_results: dict) -> dict:
        """
        同步分析结果到监测列表
        
        Args:
            analysis_results: 批量分析结果
            
        Returns:
            同步结果统计
        """
        try:
            from monitor_db import monitor_db
            
            # 准备批量监测数据
            monitors_data = []
            failed_count = 0
            
            for item in analysis_results.get("results", []):
                code = item.get("code")
                result = item.get("result", {})
                
                # 检查分析是否成功
                if not result.get("success"):
                    continue
                
                final_decision = result.get("final_decision", {})
                stock_info = result.get("stock_info", {})
                
                # 检查是否启用自动监测
                stock = portfolio_manager.db.get_stock_by_code(code)
                if not stock or not stock.get("auto_monitor"):
                    continue
                
                # 从final_decision中提取数据（使用正确的字段名）
                rating = final_decision.get("rating", "持有")
                entry_range = final_decision.get("entry_range", "")
                take_profit_str = final_decision.get("take_profit", "")
                stop_loss_str = final_decision.get("stop_loss", "")
                
                # 解析进场区间（格式如"10.5-12.3"）
                entry_min, entry_max = None, None
                if entry_range and isinstance(entry_range, str) and "-" in entry_range:
                    try:
                        parts = entry_range.split("-")
                        entry_min = float(parts[0].strip())
                        entry_max = float(parts[1].strip())
                    except:
                        pass
                
                # 解析止盈止损（提取数字）
                import re
                take_profit, stop_loss = None, None
                if take_profit_str:
                    try:
                        numbers = re.findall(r'\d+\.?\d*', str(take_profit_str))
                        if numbers:
                            take_profit = float(numbers[0])
                    except:
                        pass
                
                if stop_loss_str:
                    try:
                        numbers = re.findall(r'\d+\.?\d*', str(stop_loss_str))
                        if numbers:
                            stop_loss = float(numbers[0])
                    except:
                        pass
                
                # 检查参数有效性
                if not all([entry_min, entry_max, take_profit, stop_loss]):
                    print(f"[WARN] {code} 参数不完整，跳过同步")
                    failed_count += 1
                    continue
                
                # 构建监测数据
                monitor_data = {
                    "code": code,
                    "name": stock_info.get("name", stock.get("name", code)),
                    "rating": rating,
                    "entry_min": entry_min,
                    "entry_max": entry_max,
                    "take_profit": take_profit,
                    "stop_loss": stop_loss,
                    "check_interval": 60,
                    "notification_enabled": True
                }
                
                monitors_data.append(monitor_data)
            
            # 使用批量API同步
            if monitors_data:
                result = monitor_db.batch_add_or_update_monitors(monitors_data)
                return result
            else:
                print("[WARN] 没有需要同步的监测数据")
                return {"added": 0, "updated": 0, "failed": 0, "total": 0}
            
        except Exception as e:
            print(f"[ERROR] 监测同步异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"added": 0, "updated": 0, "failed": 0, "total": 0}
    
    def _send_notification(self, analysis_results: dict, sync_result: Optional[dict]):
        """
        发送分析完成通知（使用新的notification_service方法）
        
        Args:
            analysis_results: 批量分析结果
            sync_result: 监测同步结果
        """
        try:
            from notification_service import notification_service
            
            # 使用新的专用通知方法
            success = notification_service.send_portfolio_analysis_notification(
                analysis_results, sync_result
            )
            
            if success:
                print("[OK] 持仓分析通知发送成功")
            else:
                print("[WARN] 持仓分析通知发送失败（可能未配置通知服务）")
            
        except Exception as e:
            print(f"[ERROR] 发送通知失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _send_error_notification(self, error_msg: str):
        """发送错误通知"""
        try:
            content = f"""
持仓定时分析执行失败

错误信息：
{error_msg}

时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

请检查系统日志或手动运行分析。
"""
            
            if self.notification_service.email_enabled:
                self.notification_service.send_email("【持仓定时分析】执行失败", content)
            
            if self.notification_service.webhook_enabled:
                self.notification_service.send_webhook("【持仓定时分析】执行失败", content)
                
        except Exception as e:
            print(f"[ERROR] 发送错误通知失败: {str(e)}")
    
    def _generate_notification_content(self, analysis_results: dict, 
                                      sync_result: Optional[dict]) -> str:
        """
        生成通知内容
        
        Args:
            analysis_results: 批量分析结果
            sync_result: 监测同步结果
            
        Returns:
            通知内容文本
        """
        total = analysis_results.get("total", 0)
        succeeded = analysis_results.get("succeeded", 0)
        failed = analysis_results.get("failed", 0)
        mode = analysis_results.get("mode", "sequential")
        elapsed_time = analysis_results.get("elapsed_time", 0)
        
        # 统计评级分布
        rating_stats = {"买入": 0, "持有": 0, "卖出": 0}
        rating_changes = []
        
        for item in analysis_results.get("results", []):
            code = item.get("code")
            result = item.get("result", {})
            final_decision = result.get("final_decision", {})
            rating = final_decision.get("investment_rating", "持有")
            
            rating_stats[rating] = rating_stats.get(rating, 0) + 1
            
            # 检查评级变化
            stock = portfolio_manager.db.get_stock_by_code(code)
            if stock:
                history = portfolio_manager.db.get_analysis_history(stock['id'], limit=2)
                if len(history) >= 2:
                    old_rating = history[1]['rating']
                    new_rating = history[0]['rating']
                    if old_rating != new_rating:
                        stock_info = result.get("stock_info", {})
                        name = stock_info.get("name", stock.get("name", code))
                        rating_changes.append(f"{code} {name}: {old_rating} → {new_rating}")
        
        # 构建通知内容
        content = f"""
持仓定时分析报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}

📊 分析完成：{total}只持仓股票
✅ 成功：{succeeded}只
❌ 失败：{failed}只
⏱ 耗时：{elapsed_time:.1f}秒
🔄 模式：{'顺序分析' if mode == 'sequential' else '并行分析'}

📈 投资评级分布：
• 买入：{rating_stats.get('买入', 0)}只
• 持有：{rating_stats.get('持有', 0)}只
• 卖出：{rating_stats.get('卖出', 0)}只
"""
        
        # 添加评级变化
        if rating_changes:
            content += "\n🔔 评级变化：\n"
            for change in rating_changes[:5]:  # 最多显示5个
                content += f"• {change}\n"
        
        # 添加监测同步结果
        if sync_result:
            content += f"""
🎯 监测同步：
• 新增：{sync_result.get('added', 0)}只
• 更新：{sync_result.get('updated', 0)}只
• 失败：{sync_result.get('failed', 0)}只
"""
        
        # 添加失败股票
        if failed > 0:
            failed_stocks = analysis_results.get("failed_stocks", [])
            content += "\n⚠️ 失败股票：\n"
            for stock in failed_stocks[:3]:  # 最多显示3个
                content += f"• {stock.get('code')}: {stock.get('error')}\n"
        
        content += "\n详细报告请登录系统查看。"
        
        return content
    
    def _reschedule(self):
        """重新调度任务（支持多个时间点）"""
        # 只清除持仓定时分析的任务，不影响其他模块
        jobs_to_remove = [job for job in schedule.jobs if not any(tag in ['sector_strategy', 'monitor'] for tag in job.tags)]
        for job in jobs_to_remove:
            schedule.cancel_job(job)
        
        for time_str in self.schedule_times:
            job = schedule.every().day.at(time_str).do(self._scheduled_job)
            job.tag('portfolio_analysis')
        self._update_next_run_time()
        print(f"[OK] 重新调度任务: 每天 {', '.join(self.schedule_times)}")
    
    def _update_next_run_time(self):
        """更新下次运行时间"""
        jobs = schedule.jobs
        if jobs:
            self.next_run_time = jobs[0].next_run
        else:
            self.next_run_time = None
    
    def _run_schedule_loop(self):
        """调度循环（在后台线程中运行）"""
        print("[OK] 定时调度器线程启动")
        
        while self._is_running:
            schedule.run_pending()
            self._update_next_run_time()
            time.sleep(1)
        
        print("[OK] 定时调度器线程停止")
    
    def start(self) -> bool:
        """
        启动定时任务
        
        Returns:
            是否启动成功
        """
        if self._is_running:
            print("[WARN] 定时任务已在运行中")
            return False
        
        # 检查持仓数量
        stock_count = portfolio_manager.get_stock_count()
        if stock_count == 0:
            print("[ERROR] 没有持仓股票，无法启动定时任务")
            return False
        
        # 检查时间配置
        if not self.schedule_times:
            print("[ERROR] 没有配置定时时间")
            return False
        
        # 调度任务（为每个时间点创建任务）
        # 只清除持仓定时分析的任务，不影响智策和监测任务
        jobs_to_remove = [job for job in schedule.jobs if 'portfolio_analysis' in job.tags]
        for job in jobs_to_remove:
            schedule.cancel_job(job)
        print(f"[OK] 清除了 {len(jobs_to_remove)} 个旧的持仓任务")
        
        for time_str in self.schedule_times:
            job = schedule.every().day.at(time_str).do(self._scheduled_job)
            job.tag('portfolio_analysis')
            print(f"[OK] 添加调度任务: 每天 {time_str}")
        
        self._update_next_run_time()
        
        # 启动后台线程
        self._is_running = True
        self.thread = threading.Thread(target=self._run_schedule_loop, daemon=True)
        self.thread.start()
        
        print(f"\n[OK] 定时任务已启动")
        print(f"    调度时间: {', '.join(self.schedule_times)}")
        print(f"    分析模式: {self.analysis_mode}")
        print(f"    持仓数量: {stock_count}只")
        if self.next_run_time:
            print(f"    下次运行: {self.next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
    
    def stop(self) -> bool:
        """
        停止定时任务
        
        Returns:
            是否停止成功
        """
        if not self._is_running:
            print("[WARN] 定时任务未运行")
            return False
        
        self._is_running = False
        
        # 只清除持仓定时分析的任务，不影响其他模块（智策、监测）
        try:
            jobs_to_remove = [job for job in schedule.jobs if 'portfolio_analysis' in job.tags]
            for job in jobs_to_remove:
                schedule.cancel_job(job)
            print(f"[OK] 清除了 {len(jobs_to_remove)} 个持仓任务")
        except Exception as e:
            print(f"[WARN] 清除任务时出错: {e}")
        
        # 等待线程结束（最多等待2秒）
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        
        self.thread = None
        self.next_run_time = None
        
        print("[OK] 定时任务已停止")
        return True
    
    def run_once(self) -> bool:
        """
        立即执行一次分析（不影响定时计划）
        
        Returns:
            是否执行成功
        """
        # 检查持仓数量
        stock_count = portfolio_manager.get_stock_count()
        if stock_count == 0:
            print("[ERROR] 没有持仓股票")
            return False
        
        print("[OK] 立即执行持仓分析...")
        self._scheduled_job()
        return True
    
    def get_status(self) -> dict:
        """
        获取定时任务状态
        
        Returns:
            状态字典
        """
        return {
            "is_running": self._is_running,
            "schedule_time": self.schedule_time,
            "analysis_mode": self.analysis_mode,
            "auto_monitor_sync": self.auto_monitor_sync,
            "notification_enabled": self.notification_enabled,
            "last_run_time": self.last_run_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_run_time else None,
            "next_run_time": self.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if self.next_run_time else None,
            "portfolio_count": portfolio_manager.get_stock_count()
        }
    
    def get_next_run_time(self) -> Optional[str]:
        """
        获取下次运行时间
        
        Returns:
            下次运行时间字符串，格式"HH:MM"，如果未设置则返回None
        """
        if self.next_run_time:
            return self.next_run_time.strftime("%H:%M")
        return None
    
    def update_config(self, schedule_time: str = None, analysis_mode: str = None,
                     max_workers: int = None, auto_sync_monitor: bool = None,
                     send_notification: bool = None):
        """
        更新调度器配置
        
        Args:
            schedule_time: 定时分析时间（格式"HH:MM"，可选，用于向后兼容）
            analysis_mode: 分析模式（"sequential"或"parallel"）
            max_workers: 并行线程数（仅在parallel模式下有效）
            auto_sync_monitor: 是否自动同步到监测
            send_notification: 是否发送通知
        """
        if schedule_time is not None:
            self.set_schedule_time(schedule_time)
        
        if analysis_mode is not None:
            self.set_analysis_mode(analysis_mode)
        
        if max_workers is not None:
            self.max_workers = max_workers
            print(f"[OK] 设置并行线程数: {max_workers}")
        
        if auto_sync_monitor is not None:
            self.set_auto_monitor_sync(auto_sync_monitor)
        
        if send_notification is not None:
            self.set_notification_enabled(send_notification)
        
        print("[OK] 配置已更新")
    
    def start_scheduler(self) -> bool:
        """
        启动调度器（UI友好方法名）
        
        Returns:
            是否启动成功
        """
        return self.start()
    
    def stop_scheduler(self) -> bool:
        """
        停止调度器（UI友好方法名）
        
        Returns:
            是否停止成功
        """
        return self.stop()
    
    def run_analysis_now(self) -> bool:
        """
        立即执行一次分析（UI友好方法名）
        
        Returns:
            是否执行成功
        """
        return self.run_once()


# 创建全局实例
portfolio_scheduler = PortfolioScheduler()


if __name__ == "__main__":
    # 测试代码
    print("="*60)
    print("持仓定时调度器测试")
    print("="*60)
    
    scheduler = PortfolioScheduler()
    
    # 设置配置
    scheduler.set_schedule_time("09:00")
    scheduler.set_analysis_mode("sequential")
    scheduler.set_auto_monitor_sync(True)
    scheduler.set_notification_enabled(False)  # 测试时禁用通知
    
    # 获取状态
    status = scheduler.get_status()
    print("\n调度器状态:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print("\n[OK] 调度器测试完成")

