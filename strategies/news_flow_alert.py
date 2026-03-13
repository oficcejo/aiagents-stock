"""
新闻流量预警系统模块
实现6种预警类型和通知推送
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsFlowAlertSystem:
    """新闻流量预警系统"""
    
    # 预警类型定义
    ALERT_TYPES = {
        'heat_surge': {
            'name': '热度飙升',
            'level': 'warning',
            'description': '流量得分超过阈值，市场热度异常升高',
        },
        'rank_change': {
            'name': '排名变化',
            'level': 'info',
            'description': '热点排名快速变化',
        },
        'sentiment_extreme': {
            'name': '情绪极值',
            'level': 'warning',
            'description': '情绪指数处于极端状态（过高或过低）',
        },
        'flow_peak': {
            'name': '流量高潮',
            'level': 'danger',
            'description': '进入"一致"阶段，可能是逃命时刻',
        },
        'flow_decline': {
            'name': '流量退潮',
            'level': 'warning',
            'description': '进入"退潮"阶段，注意止盈止损',
        },
        'viral_spread': {
            'name': '病毒传播',
            'level': 'warning',
            'description': 'K值超过阈值，流量呈指数型增长',
        },
    }
    
    # 预警级别定义
    ALERT_LEVELS = {
        'info': {'name': '提示', 'color': 'blue', 'priority': 1},
        'warning': {'name': '警告', 'color': 'orange', 'priority': 2},
        'danger': {'name': '危险', 'color': 'red', 'priority': 3},
    }
    
    def __init__(self):
        """初始化预警系统"""
        self.db = None
        self.notification_service = None
        self._init_dependencies()
        
        # 默认阈值配置
        self.default_thresholds = {
            'heat_threshold': 800,
            'rank_change_threshold': 10,
            'sentiment_high_threshold': 90,
            'sentiment_low_threshold': 20,
            'viral_k_threshold': 1.5,
        }
    
    def _init_dependencies(self):
        """初始化依赖"""
        try:
            from db.news_flow_db import news_flow_db
            self.db = news_flow_db
        except Exception as e:
            logger.warning(f"数据库初始化失败: {e}")
        
        try:
            from services.notification_service import notification_service
            self.notification_service = notification_service
        except Exception as e:
            logger.warning(f"通知服务初始化失败: {e}")
    
    def get_threshold(self, key: str) -> float:
        """获取阈值配置"""
        if self.db:
            value = self.db.get_alert_config(key)
            if value:
                try:
                    return float(value)
                except ValueError:
                    pass
        return self.default_thresholds.get(key, 0)
    
    def set_threshold(self, key: str, value: float):
        """设置阈值配置"""
        if self.db:
            self.db.set_alert_config(key, str(value))
    
    def check_alerts(self, current_data: Dict, 
                     history_data: Dict = None,
                     sentiment_data: Dict = None,
                     snapshot_id: int = None) -> List[Dict]:
        """
        检查所有预警条件
        
        Args:
            current_data: 当前数据，包含flow_data, hot_topics等
            history_data: 历史数据，用于比较
            sentiment_data: 情绪数据
            snapshot_id: 快照ID
            
        Returns:
            List[Dict]: 触发的预警列表
        """
        alerts = []
        
        flow_data = current_data.get('flow_data', {})
        hot_topics = current_data.get('hot_topics', [])
        viral_k = current_data.get('viral_k', {})
        flow_stage = current_data.get('flow_stage', {})
        
        # 1. 检查热度飙升
        heat_alert = self._check_heat_surge(flow_data)
        if heat_alert:
            heat_alert['snapshot_id'] = snapshot_id
            alerts.append(heat_alert)
        
        # 2. 检查排名变化
        if history_data:
            rank_alert = self._check_rank_change(hot_topics, 
                                                  history_data.get('hot_topics', []))
            if rank_alert:
                rank_alert['snapshot_id'] = snapshot_id
                alerts.append(rank_alert)
        
        # 3. 检查情绪极值
        if sentiment_data:
            sentiment_alert = self._check_sentiment_extreme(sentiment_data)
            if sentiment_alert:
                sentiment_alert['snapshot_id'] = snapshot_id
                alerts.append(sentiment_alert)
        
        # 4. 检查流量高潮（一致阶段）
        peak_alert = self._check_flow_peak(flow_stage, sentiment_data)
        if peak_alert:
            peak_alert['snapshot_id'] = snapshot_id
            alerts.append(peak_alert)
        
        # 5. 检查流量退潮
        decline_alert = self._check_flow_decline(flow_stage)
        if decline_alert:
            decline_alert['snapshot_id'] = snapshot_id
            alerts.append(decline_alert)
        
        # 6. 检查病毒传播
        viral_alert = self._check_viral_spread(viral_k)
        if viral_alert:
            viral_alert['snapshot_id'] = snapshot_id
            alerts.append(viral_alert)
        
        # 按优先级排序
        alerts.sort(key=lambda x: self.ALERT_LEVELS.get(
            x.get('alert_level', 'info'), {}
        ).get('priority', 0), reverse=True)
        
        # 保存预警到数据库
        if self.db and alerts:
            for alert in alerts:
                self.db.save_alert(alert)
        
        return alerts
    
    def _check_heat_surge(self, flow_data: Dict) -> Optional[Dict]:
        """检查热度飙升"""
        threshold = self.get_threshold('heat_threshold')
        current_score = flow_data.get('total_score', 0)
        
        if current_score >= threshold:
            return {
                'alert_type': 'heat_surge',
                'alert_level': 'warning',
                'title': f'热度飙升预警：流量得分{current_score}',
                'content': f"当前流量得分{current_score}，超过阈值{threshold}。"
                           f"市场热度异常升高，可能存在短期机会，但也要注意追高风险。",
                'related_topics': [],
                'trigger_value': current_score,
                'threshold_value': threshold,
            }
        return None
    
    def _check_rank_change(self, current_topics: List[Dict], 
                           previous_topics: List[Dict]) -> Optional[Dict]:
        """检查排名变化"""
        threshold = int(self.get_threshold('rank_change_threshold'))
        
        if not previous_topics:
            return None
        
        # 建立之前的排名映射
        prev_ranks = {t.get('topic', ''): i for i, t in enumerate(previous_topics)}
        
        # 检查快速上升的话题
        rapid_rise_topics = []
        for i, topic in enumerate(current_topics[:20]):
            topic_name = topic.get('topic', '')
            if topic_name in prev_ranks:
                rank_change = prev_ranks[topic_name] - i
                if rank_change >= threshold:
                    rapid_rise_topics.append({
                        'topic': topic_name,
                        'current_rank': i + 1,
                        'previous_rank': prev_ranks[topic_name] + 1,
                        'change': rank_change,
                    })
        
        if rapid_rise_topics:
            topics_text = ', '.join([t['topic'] for t in rapid_rise_topics[:3]])
            return {
                'alert_type': 'rank_change',
                'alert_level': 'info',
                'title': f'排名变化提示：{topics_text}',
                'content': f"{len(rapid_rise_topics)}个话题排名快速上升（上升{threshold}名以上），"
                           f"可能是新热点正在发酵。",
                'related_topics': [t['topic'] for t in rapid_rise_topics],
                'trigger_value': len(rapid_rise_topics),
                'threshold_value': threshold,
            }
        return None
    
    def _check_sentiment_extreme(self, sentiment_data: Dict) -> Optional[Dict]:
        """检查情绪极值"""
        high_threshold = self.get_threshold('sentiment_high_threshold')
        low_threshold = self.get_threshold('sentiment_low_threshold')
        
        sentiment = sentiment_data.get('sentiment', {})
        sentiment_index = sentiment.get('sentiment_index', 50)
        sentiment_class = sentiment.get('sentiment_class', '中性')
        
        if sentiment_index >= high_threshold:
            return {
                'alert_type': 'sentiment_extreme',
                'alert_level': 'warning',
                'title': f'情绪极值警告：{sentiment_class}({sentiment_index}分)',
                'content': f"情绪指数{sentiment_index}分，处于极度乐观状态！"
                           f"根据'流量高潮=价格高潮'理论，市场可能接近顶部，注意及时止盈。",
                'related_topics': [],
                'trigger_value': sentiment_index,
                'threshold_value': high_threshold,
            }
        elif sentiment_index <= low_threshold:
            return {
                'alert_type': 'sentiment_extreme',
                'alert_level': 'warning',
                'title': f'情绪极值警告：{sentiment_class}({sentiment_index}分)',
                'content': f"情绪指数{sentiment_index}分，处于极度悲观状态！"
                           f"市场恐慌情绪蔓延，可能存在超跌反弹机会，但需谨慎左侧布局。",
                'related_topics': [],
                'trigger_value': sentiment_index,
                'threshold_value': low_threshold,
            }
        return None
    
    def _check_flow_peak(self, flow_stage: Dict, 
                          sentiment_data: Dict = None) -> Optional[Dict]:
        """
        检查流量高潮（逃命预警）
        
        当以下条件同时满足时触发：
        1. 流量阶段 = "一致"
        2. 情绪指数 > 85
        3. K值 > 1.5（可选）
        """
        stage = flow_stage.get('stage', '')
        stage_name = flow_stage.get('stage_name', '')
        
        # 主要触发条件：一致阶段
        if stage not in ['consensus', '一致']:
            return None
        
        # 增强条件检查
        sentiment_index = 50
        if sentiment_data:
            sentiment = sentiment_data.get('sentiment', {})
            sentiment_index = sentiment.get('sentiment_index', 50)
        
        # 一致阶段就触发危险预警
        return {
            'alert_type': 'flow_peak',
            'alert_level': 'danger',
            'title': '⚠️ 流量高潮预警：准备跑路！',
            'content': f"流量阶段进入【{stage_name}】！这是最危险的信号！\n\n"
                       f"根据'流量为王'理论：流量高潮 = 价格高潮 = 逃命时刻\n\n"
                       f"当热搜、媒体报道、KOL转发同时达到高潮时，就是出货时机。\n\n"
                       f"建议：立即减仓或清仓，锁定利润！",
            'related_topics': [],
            'trigger_value': stage_name,
            'threshold_value': '一致阶段',
        }
    
    def _check_flow_decline(self, flow_stage: Dict) -> Optional[Dict]:
        """检查流量退潮"""
        stage = flow_stage.get('stage', '')
        stage_name = flow_stage.get('stage_name', '')
        avg_growth = flow_stage.get('avg_growth', 0)
        
        if stage not in ['decline', '退潮']:
            return None
        
        return {
            'alert_type': 'flow_decline',
            'alert_level': 'warning',
            'title': f'流量退潮警告：及时止盈止损',
            'content': f"流量阶段进入【{stage_name}】，增速{avg_growth}%。\n\n"
                       f"题材热度正在消退，资金开始撤离。\n\n"
                       f"建议：持仓者及时止盈止损，不要恋战。空仓者不要抄底接飞刀。",
            'related_topics': [],
            'trigger_value': avg_growth,
            'threshold_value': '退潮阶段',
        }
    
    def _check_viral_spread(self, viral_k: Dict) -> Optional[Dict]:
        """检查病毒传播"""
        threshold = self.get_threshold('viral_k_threshold')
        k_value = viral_k.get('k_value', 1.0)
        trend = viral_k.get('trend', '')
        
        if k_value >= threshold:
            return {
                'alert_type': 'viral_spread',
                'alert_level': 'warning',
                'title': f'病毒传播预警：K值={k_value}',
                'content': f"K值={k_value}，趋势：{trend}\n\n"
                           f"流量正在指数型增长，这是病毒式传播的特征。\n\n"
                           f"题材可能进入加速期，但也要注意：\n"
                           f"- K值过高意味着接近顶部的风险增加\n"
                           f"- 指数型增长往往伴随着指数型下跌\n"
                           f"- 密切关注后续K值变化，一旦开始下降就是离场信号",
                'related_topics': [],
                'trigger_value': k_value,
                'threshold_value': threshold,
            }
        return None
    
    def send_notification(self, alerts: List[Dict]) -> bool:
        """
        发送通知
        
        Args:
            alerts: 预警列表
            
        Returns:
            bool: 是否发送成功
        """
        if not alerts:
            return True
        
        if not self.notification_service:
            logger.warning("通知服务不可用")
            return False
        
        try:
            # 按级别分组
            danger_alerts = [a for a in alerts if a.get('alert_level') == 'danger']
            warning_alerts = [a for a in alerts if a.get('alert_level') == 'warning']
            info_alerts = [a for a in alerts if a.get('alert_level') == 'info']
            
            # 构建通知内容
            lines = []
            lines.append("📊 新闻流量预警通知")
            lines.append(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("")
            
            if danger_alerts:
                lines.append("🔴 【危险预警】")
                for alert in danger_alerts:
                    lines.append(f"  • {alert['title']}")
                lines.append("")
            
            if warning_alerts:
                lines.append("🟠 【警告】")
                for alert in warning_alerts:
                    lines.append(f"  • {alert['title']}")
                lines.append("")
            
            if info_alerts:
                lines.append("🔵 【提示】")
                for alert in info_alerts:
                    lines.append(f"  • {alert['title']}")
            
            message = '\n'.join(lines)
            
            # 发送通知
            # 使用危险级别发送最高优先级预警
            if danger_alerts:
                subject = "⚠️ 新闻流量危险预警"
            else:
                subject = "📊 新闻流量预警通知"
            
            # 调用通知服务
            success = self.notification_service.send_analysis_result(
                subject=subject,
                content=message
            )
            
            # 标记为已通知
            if success and self.db:
                for alert in alerts:
                    if 'id' in alert:
                        self.db.mark_alert_notified(alert['id'])
            
            return success
            
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
            return False
    
    def get_alert_history(self, days: int = 7, 
                          alert_type: str = None) -> List[Dict]:
        """获取预警历史"""
        if self.db:
            return self.db.get_alerts(days, alert_type)
        return []
    
    def get_unnotified_alerts(self) -> List[Dict]:
        """获取未通知的预警"""
        if self.db:
            return self.db.get_unnotified_alerts()
        return []
    
    def get_alert_summary(self, days: int = 7) -> Dict:
        """获取预警统计摘要"""
        alerts = self.get_alert_history(days)
        
        # 按类型统计
        type_counts = {}
        for alert in alerts:
            alert_type = alert.get('alert_type', 'unknown')
            type_counts[alert_type] = type_counts.get(alert_type, 0) + 1
        
        # 按级别统计
        level_counts = {}
        for alert in alerts:
            level = alert.get('alert_level', 'info')
            level_counts[level] = level_counts.get(level, 0) + 1
        
        return {
            'total_count': len(alerts),
            'type_counts': type_counts,
            'level_counts': level_counts,
            'danger_count': level_counts.get('danger', 0),
            'warning_count': level_counts.get('warning', 0),
            'info_count': level_counts.get('info', 0),
        }
    
    def get_threshold_config(self) -> Dict:
        """获取所有阈值配置"""
        return {
            'heat_threshold': self.get_threshold('heat_threshold'),
            'rank_change_threshold': self.get_threshold('rank_change_threshold'),
            'sentiment_high_threshold': self.get_threshold('sentiment_high_threshold'),
            'sentiment_low_threshold': self.get_threshold('sentiment_low_threshold'),
            'viral_k_threshold': self.get_threshold('viral_k_threshold'),
        }


# 全局实例
news_flow_alert_system = NewsFlowAlertSystem()


# 测试代码
if __name__ == "__main__":
    print("=== 测试预警系统 ===")
    
    # 模拟数据
    current_data = {
        'flow_data': {'total_score': 850, 'level': '极高'},
        'hot_topics': [
            {'topic': 'AI芯片', 'heat': 95},
            {'topic': '新能源', 'heat': 80},
        ],
        'viral_k': {'k_value': 1.8, 'trend': '指数型爆发'},
        'flow_stage': {'stage': 'consensus', 'stage_name': '一致', 'avg_growth': 35},
    }
    
    sentiment_data = {
        'sentiment': {'sentiment_index': 92, 'sentiment_class': '极度乐观'},
    }
    
    history_data = {
        'hot_topics': [
            {'topic': '新能源', 'heat': 70},
            {'topic': 'AI芯片', 'heat': 60},
        ],
    }
    
    # 检查预警
    alerts = news_flow_alert_system.check_alerts(
        current_data, history_data, sentiment_data
    )
    
    print(f"\n触发 {len(alerts)} 个预警：")
    for alert in alerts:
        level_info = NewsFlowAlertSystem.ALERT_LEVELS.get(alert['alert_level'], {})
        print(f"\n[{level_info.get('name', alert['alert_level'])}] {alert['title']}")
        print(f"  {alert['content'][:100]}...")
    
    # 获取阈值配置
    print("\n当前阈值配置：")
    config = news_flow_alert_system.get_threshold_config()
    for key, value in config.items():
        print(f"  {key}: {value}")
