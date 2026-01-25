"""
新闻流量定时任务调度模块
实现三种定时任务：热点同步（30分钟）、预警生成（1小时）、深度分析（2小时）
"""
import schedule
import threading
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsFlowScheduler:
    """新闻流量定时任务调度器"""
    
    # 任务类型定义
    TASK_TYPES = {
        'sync_hotspots': {
            'name': '热点同步',
            'interval': 30,  # 分钟
            'description': '同步22个平台的热点数据',
        },
        'generate_alerts': {
            'name': '预警生成',
            'interval': 60,  # 分钟
            'description': '检查预警条件并生成预警',
        },
        'deep_analysis': {
            'name': '深度分析',
            'interval': 120,  # 分钟
            'description': '运行完整的AI分析',
        },
    }
    
    def __init__(self):
        """初始化调度器"""
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        
        # 任务配置
        self.task_enabled = {
            'sync_hotspots': True,
            'generate_alerts': True,
            'deep_analysis': True,
        }
        
        # 任务间隔（分钟）
        self.task_intervals = {
            'sync_hotspots': 30,
            'generate_alerts': 60,
            'deep_analysis': 120,
        }
        
        # 上次运行时间
        self.last_run_times = {}
        
        # 依赖模块
        self.engine = None
        self.db = None
        self.alert_system = None
        
        self._init_dependencies()
        logger.info("[新闻流量] 调度器初始化完成")
    
    def _init_dependencies(self):
        """初始化依赖模块"""
        try:
            from news_flow_db import news_flow_db
            self.db = news_flow_db
        except Exception as e:
            logger.warning(f"数据库模块初始化失败: {e}")
        
        try:
            from news_flow_alert import news_flow_alert_system
            self.alert_system = news_flow_alert_system
        except Exception as e:
            logger.warning(f"预警系统初始化失败: {e}")
    
    def _get_engine(self):
        """延迟加载引擎（避免循环导入）"""
        if self.engine is None:
            try:
                from news_flow_engine import news_flow_engine
                self.engine = news_flow_engine
            except Exception as e:
                logger.error(f"引擎模块初始化失败: {e}")
        return self.engine
    
    def start(self):
        """启动调度器"""
        if self.running:
            logger.warning("[新闻流量] 调度器已在运行")
            return
        
        with self.lock:
            # 清除旧任务
            self._clear_jobs()
            
            # 注册任务
            if self.task_enabled.get('sync_hotspots'):
                interval = self.task_intervals.get('sync_hotspots', 30)
                job = schedule.every(interval).minutes.do(self._run_sync_hotspots)
                job.tag('news_flow', 'sync_hotspots')
                logger.info(f"[新闻流量] 注册热点同步任务，间隔{interval}分钟")
            
            if self.task_enabled.get('generate_alerts'):
                interval = self.task_intervals.get('generate_alerts', 60)
                job = schedule.every(interval).minutes.do(self._run_generate_alerts)
                job.tag('news_flow', 'generate_alerts')
                logger.info(f"[新闻流量] 注册预警生成任务，间隔{interval}分钟")
            
            if self.task_enabled.get('deep_analysis'):
                interval = self.task_intervals.get('deep_analysis', 120)
                job = schedule.every(interval).minutes.do(self._run_deep_analysis)
                job.tag('news_flow', 'deep_analysis')
                logger.info(f"[新闻流量] 注册深度分析任务，间隔{interval}分钟")
            
            # 启动调度线程
            self.running = True
            self.thread = threading.Thread(target=self._schedule_loop, daemon=True)
            self.thread.start()
            
            logger.info("[新闻流量] 调度器已启动")
    
    def stop(self):
        """停止调度器"""
        with self.lock:
            self.running = False
            self._clear_jobs()
            logger.info("[新闻流量] 调度器已停止")
    
    def _clear_jobs(self):
        """清除本模块的任务"""
        jobs_to_remove = [job for job in schedule.jobs if 'news_flow' in job.tags]
        for job in jobs_to_remove:
            schedule.cancel_job(job)
    
    def _schedule_loop(self):
        """调度循环"""
        while self.running:
            try:
                schedule.run_pending()
            except Exception as e:
                logger.error(f"[新闻流量] 调度循环异常: {e}")
            time.sleep(30)  # 每30秒检查一次
    
    def _log_task(self, task_name: str, task_type: str, 
                  status: str, message: str = '', 
                  duration: float = 0, snapshot_id: int = None):
        """记录任务日志"""
        try:
            if self.db:
                self.db.save_scheduler_log(
                    task_name, task_type, status, message, duration, snapshot_id
                )
        except Exception as e:
            logger.error(f"记录任务日志失败: {e}")
    
    def _run_sync_hotspots(self):
        """运行热点同步任务"""
        task_type = 'sync_hotspots'
        task_name = self.TASK_TYPES[task_type]['name']
        
        logger.info(f"[新闻流量] 开始执行: {task_name}")
        start_time = time.time()
        
        try:
            engine = self._get_engine()
            if not engine:
                raise Exception("引擎模块不可用")
            
            # 运行快速分析（仅数据同步和基础计算）
            result = engine.run_quick_analysis()
            
            duration = time.time() - start_time
            
            if result.get('success'):
                snapshot_id = result.get('snapshot_id')
                message = f"成功同步{result.get('success_count', 0)}个平台数据"
                self._log_task(task_name, task_type, 'success', message, duration, snapshot_id)
                logger.info(f"[新闻流量] {task_name}完成: {message}")
            else:
                message = result.get('error', '未知错误')
                self._log_task(task_name, task_type, 'failed', message, duration)
                logger.error(f"[新闻流量] {task_name}失败: {message}")
            
            self.last_run_times[task_type] = datetime.now()
            
        except Exception as e:
            duration = time.time() - start_time
            message = str(e)
            self._log_task(task_name, task_type, 'error', message, duration)
            logger.error(f"[新闻流量] {task_name}异常: {e}")
    
    def _run_generate_alerts(self):
        """运行预警生成任务"""
        task_type = 'generate_alerts'
        task_name = self.TASK_TYPES[task_type]['name']
        
        logger.info(f"[新闻流量] 开始执行: {task_name}")
        start_time = time.time()
        
        try:
            engine = self._get_engine()
            if not engine:
                raise Exception("引擎模块不可用")
            
            # 运行预警检查
            result = engine.run_alert_check()
            
            duration = time.time() - start_time
            
            if result.get('success'):
                alert_count = len(result.get('alerts', []))
                message = f"生成{alert_count}个预警"
                self._log_task(task_name, task_type, 'success', message, duration)
                logger.info(f"[新闻流量] {task_name}完成: {message}")
                
                # 发送通知
                if alert_count > 0 and self.alert_system:
                    self.alert_system.send_notification(result['alerts'])
            else:
                message = result.get('error', '未知错误')
                self._log_task(task_name, task_type, 'failed', message, duration)
                logger.error(f"[新闻流量] {task_name}失败: {message}")
            
            self.last_run_times[task_type] = datetime.now()
            
        except Exception as e:
            duration = time.time() - start_time
            message = str(e)
            self._log_task(task_name, task_type, 'error', message, duration)
            logger.error(f"[新闻流量] {task_name}异常: {e}")
    
    def _run_deep_analysis(self):
        """运行深度分析任务"""
        task_type = 'deep_analysis'
        task_name = self.TASK_TYPES[task_type]['name']
        
        logger.info(f"[新闻流量] 开始执行: {task_name}")
        start_time = time.time()
        
        try:
            engine = self._get_engine()
            if not engine:
                raise Exception("引擎模块不可用")
            
            # 运行完整分析（包含AI）
            result = engine.run_full_analysis(include_ai=True)
            
            duration = time.time() - start_time
            
            if result.get('success'):
                snapshot_id = result.get('snapshot_id')
                advice = result.get('ai_analysis', {}).get('investment_advice', {}).get('advice', 'N/A')
                message = f"深度分析完成，建议：{advice}"
                self._log_task(task_name, task_type, 'success', message, duration, snapshot_id)
                logger.info(f"[新闻流量] {task_name}完成: {message}")
            else:
                message = result.get('error', '未知错误')
                self._log_task(task_name, task_type, 'failed', message, duration)
                logger.error(f"[新闻流量] {task_name}失败: {message}")
            
            self.last_run_times[task_type] = datetime.now()
            
        except Exception as e:
            duration = time.time() - start_time
            message = str(e)
            self._log_task(task_name, task_type, 'error', message, duration)
            logger.error(f"[新闻流量] {task_name}异常: {e}")
    
    # ==================== 手动触发方法 ====================
    
    def run_sync_now(self) -> Dict:
        """立即执行热点同步"""
        logger.info("[新闻流量] 手动触发热点同步")
        self._run_sync_hotspots()
        return {'success': True, 'message': '热点同步已执行'}
    
    def run_alerts_now(self) -> Dict:
        """立即执行预警生成"""
        logger.info("[新闻流量] 手动触发预警生成")
        self._run_generate_alerts()
        return {'success': True, 'message': '预警生成已执行'}
    
    def run_analysis_now(self) -> Dict:
        """立即执行深度分析"""
        logger.info("[新闻流量] 手动触发深度分析")
        self._run_deep_analysis()
        return {'success': True, 'message': '深度分析已执行'}
    
    # ==================== 配置方法 ====================
    
    def set_task_enabled(self, task_type: str, enabled: bool):
        """设置任务开关"""
        if task_type in self.task_enabled:
            self.task_enabled[task_type] = enabled
            logger.info(f"[新闻流量] 任务 {task_type} {'启用' if enabled else '禁用'}")
            
            # 如果调度器正在运行，重新注册任务
            if self.running:
                self.stop()
                self.start()
    
    def set_task_interval(self, task_type: str, interval: int):
        """设置任务间隔（分钟）"""
        if task_type in self.task_intervals:
            self.task_intervals[task_type] = interval
            logger.info(f"[新闻流量] 任务 {task_type} 间隔设置为 {interval} 分钟")
            
            # 如果调度器正在运行，重新注册任务
            if self.running:
                self.stop()
                self.start()
    
    def get_status(self) -> Dict:
        """获取调度器状态"""
        return {
            'running': self.running,
            'task_enabled': self.task_enabled.copy(),
            'task_intervals': self.task_intervals.copy(),
            'last_run_times': {
                k: v.strftime('%Y-%m-%d %H:%M:%S') if v else None 
                for k, v in self.last_run_times.items()
            },
            'next_run_times': self._get_next_run_times(),
        }
    
    def _get_next_run_times(self) -> Dict:
        """获取下次运行时间"""
        next_times = {}
        for job in schedule.jobs:
            if 'news_flow' in job.tags:
                for tag in job.tags:
                    if tag in self.TASK_TYPES:
                        next_times[tag] = str(job.next_run)
        return next_times
    
    def get_task_logs(self, days: int = 7, task_type: str = None) -> List[Dict]:
        """获取任务日志"""
        if self.db:
            return self.db.get_scheduler_logs(days, task_type)
        return []


# 全局实例
news_flow_scheduler = NewsFlowScheduler()


# 测试代码
if __name__ == "__main__":
    print("=== 测试新闻流量调度器 ===")
    
    # 获取状态
    status = news_flow_scheduler.get_status()
    print(f"\n调度器状态:")
    print(f"  运行中: {status['running']}")
    print(f"  任务配置: {status['task_enabled']}")
    print(f"  任务间隔: {status['task_intervals']}")
    
    # 启动调度器
    print("\n启动调度器...")
    news_flow_scheduler.start()
    
    # 再次获取状态
    status = news_flow_scheduler.get_status()
    print(f"\n调度器状态:")
    print(f"  运行中: {status['running']}")
    print(f"  下次运行: {status['next_run_times']}")
    
    # 等待一会儿
    print("\n等待5秒...")
    time.sleep(5)
    
    # 停止调度器
    print("\n停止调度器...")
    news_flow_scheduler.stop()
    
    print("\n测试完成")
