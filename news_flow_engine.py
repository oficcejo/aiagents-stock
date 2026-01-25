"""
新闻流量分析引擎
基于"流量为王"理念的短线炒股指导系统
整合数据获取、流量模型、情绪分析、AI分析、预警系统
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsFlowEngine:
    """新闻流量分析引擎"""
    
    def __init__(self):
        """初始化引擎"""
        # 核心模块
        self.fetcher = None
        self.model = None
        self.sentiment = None
        self.agents = None
        self.alerts = None
        self.db = None
        
        self._init_modules()
        logger.info("✅ 新闻流量引擎初始化完成")
    
    def _init_modules(self):
        """初始化所有模块"""
        try:
            from news_flow_data import NewsFlowDataFetcher
            self.fetcher = NewsFlowDataFetcher()
        except Exception as e:
            logger.error(f"数据获取模块初始化失败: {e}")
        
        try:
            from news_flow_model import NewsFlowModel
            self.model = NewsFlowModel()
        except Exception as e:
            logger.error(f"流量模型模块初始化失败: {e}")
        
        try:
            from news_flow_sentiment import SentimentAnalyzer
            self.sentiment = SentimentAnalyzer()
        except Exception as e:
            logger.error(f"情绪分析模块初始化失败: {e}")
        
        try:
            from news_flow_agents import NewsFlowAgents
            self.agents = NewsFlowAgents()
        except Exception as e:
            logger.error(f"AI分析模块初始化失败: {e}")
        
        try:
            from news_flow_alert import NewsFlowAlertSystem
            self.alerts = NewsFlowAlertSystem()
        except Exception as e:
            logger.error(f"预警系统模块初始化失败: {e}")
        
        try:
            from news_flow_db import news_flow_db
            self.db = news_flow_db
        except Exception as e:
            logger.error(f"数据库模块初始化失败: {e}")
    
    def run_quick_analysis(self, platforms: List[str] = None, 
                           category: str = None) -> Dict:
        """
        运行快速分析（不含AI）
        
        用于定时同步和快速查看
        
        Returns:
            {
                'success': bool,
                'snapshot_id': int,
                'flow_data': Dict,
                'model_data': Dict,
                'sentiment_data': Dict,
                'stock_news': List,
                'hot_topics': List,
                'fetch_time': str,
            }
        """
        try:
            logger.info("🚀 开始快速分析...")
            start_time = time.time()
            
            # 1. 获取多平台新闻数据
            logger.info("📊 获取新闻数据...")
            if not self.fetcher:
                return {'success': False, 'error': '数据获取模块不可用'}
            
            multi_result = self.fetcher.get_multi_platform_news(
                platforms=platforms, category=category
            )
            
            if not multi_result['success']:
                return {'success': False, 'error': '获取新闻数据失败'}
            
            platforms_data = multi_result['platforms_data']
            success_count = multi_result['success_count']
            
            # 2. 提取股票相关新闻
            logger.info("🔍 提取股票相关新闻...")
            stock_news = self.fetcher.extract_stock_related_news(platforms_data)
            
            # 3. 获取热门话题
            logger.info("🔥 分析热门话题...")
            hot_topics = self.fetcher.get_hot_topics(platforms_data, top_n=20)
            
            # 4. 计算流量得分（基础）
            logger.info("📈 计算流量得分...")
            flow_data = self.fetcher.calculate_flow_score(platforms_data)
            
            # 5. 运行流量模型
            logger.info("🔬 运行流量模型...")
            history_scores = self._get_history_scores(hours=24)
            model_data = None
            if self.model:
                model_data = self.model.run_full_model(
                    platforms_data, hot_topics, history_scores
                )
            
            # 6. 情绪分析
            logger.info("💭 分析市场情绪...")
            sentiment_data = None
            if self.sentiment:
                history_sentiments = self._get_history_sentiments(limit=10)
                sentiment_data = self.sentiment.run_full_sentiment_analysis(
                    platforms_data, stock_news, history_scores,
                    flow_data['total_score'], history_sentiments
                )
            
            # 7. 保存到数据库
            logger.info("💾 保存分析结果...")
            snapshot_id = None
            if self.db:
                snapshot_id = self.db.save_flow_snapshot(
                    flow_data, platforms_data, stock_news, hot_topics
                )
                
                # 保存情绪记录
                if sentiment_data and snapshot_id:
                    sentiment_record = {
                        'sentiment_index': sentiment_data.get('sentiment', {}).get('sentiment_index', 50),
                        'sentiment_class': sentiment_data.get('sentiment', {}).get('sentiment_class', '中性'),
                        'flow_stage': sentiment_data.get('flow_stage', {}).get('stage_name', '未知'),
                        'momentum': sentiment_data.get('momentum', {}).get('momentum', 1.0),
                        'viral_k': model_data.get('viral_k', {}).get('k_value', 1.0) if model_data else 1.0,
                        'flow_type': model_data.get('flow_type', {}).get('flow_type', '未知') if model_data else '未知',
                        'stage_analysis': sentiment_data.get('flow_stage', {}).get('analysis', ''),
                    }
                    self.db.save_sentiment_record(snapshot_id, sentiment_record)
            
            duration = time.time() - start_time
            logger.info(f"✅ 快速分析完成，耗时 {duration:.2f} 秒")
            
            return {
                'success': True,
                'snapshot_id': snapshot_id,
                'success_count': success_count,
                'flow_data': flow_data,
                'model_data': model_data,
                'sentiment_data': sentiment_data,
                'stock_news': stock_news,
                'hot_topics': hot_topics,
                'platforms_data': platforms_data,
                'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'duration': round(duration, 2),
            }
            
        except Exception as e:
            logger.error(f"❌ 快速分析失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_full_analysis(self, platforms: List[str] = None, 
                          category: str = None,
                          include_ai: bool = True) -> Dict:
        """
        运行完整分析（含AI）
        
        Returns:
            {
                'success': bool,
                'snapshot_id': int,
                'flow_data': Dict,
                'model_data': Dict,
                'sentiment_data': Dict,
                'ai_analysis': Dict,
                'trading_signals': Dict,
                'stock_news': List,
                'hot_topics': List,
            }
        """
        try:
            logger.info("🚀 开始完整分析...")
            start_time = time.time()
            
            # 1. 先运行快速分析
            quick_result = self.run_quick_analysis(platforms, category)
            
            if not quick_result['success']:
                return quick_result
            
            # 2. AI智能分析
            ai_analysis = None
            if include_ai:
                if not self.agents:
                    logger.warning("⚠️ AI代理模块未初始化")
                elif not self.agents.is_available():
                    logger.warning("⚠️ DeepSeek API不可用，请检查API密钥配置")
                else:
                    logger.info("🤖 运行AI分析...")
                    
                    model_data = quick_result.get('model_data', {})
                    sentiment_data = quick_result.get('sentiment_data', {})
                    
                    # 基础AI分析
                    ai_analysis = self.agents.run_full_analysis(
                        quick_result['hot_topics'],
                        quick_result['stock_news'],
                        quick_result['flow_data'],
                        sentiment_data,
                        viral_k=model_data.get('viral_k', {}).get('k_value', 1.0) if model_data else 1.0,
                        flow_type=model_data.get('flow_type', {}).get('flow_type', '未知') if model_data else '未知',
                    )
                    
                    # 多板块深度分析（多次调用DeepSeek）
                    logger.info("🔍 开始多板块深度分析...")
                    multi_sector_analysis = self.agents.run_multi_sector_analysis(
                        quick_result['hot_topics'],
                        quick_result['stock_news']
                    )
                    
                    # 合并多板块分析结果
                    if ai_analysis and multi_sector_analysis.get('success'):
                        ai_analysis['multi_sector'] = multi_sector_analysis
                    
                    # 保存AI分析结果
                    if ai_analysis and self.db and quick_result.get('snapshot_id'):
                        ai_record = {
                            'affected_sectors': ai_analysis.get('sector_analysis', {}).get('benefited_sectors', []),
                            'recommended_stocks': ai_analysis.get('stock_recommend', {}).get('recommended_stocks', []),
                            'risk_level': ai_analysis.get('risk_assess', {}).get('risk_level', '未知'),
                            'risk_factors': ai_analysis.get('risk_assess', {}).get('risk_factors', []),
                            'advice': ai_analysis.get('investment_advice', {}).get('advice', '观望'),
                            'confidence': ai_analysis.get('investment_advice', {}).get('confidence', 50),
                            'summary': ai_analysis.get('investment_advice', {}).get('summary', ''),
                            'model_used': 'deepseek-chat',
                            'analysis_time': ai_analysis.get('analysis_time', 0),
                        }
                        self.db.save_ai_analysis(quick_result['snapshot_id'], ai_record)
            
            # 3. 生成交易信号
            trading_signals = self._generate_trading_signals(
                quick_result.get('flow_data', {}),
                quick_result.get('model_data', {}),
                quick_result.get('sentiment_data', {}),
                ai_analysis
            )
            
            duration = time.time() - start_time
            logger.info(f"✅ 完整分析完成，耗时 {duration:.2f} 秒")
            
            return {
                'success': True,
                'snapshot_id': quick_result.get('snapshot_id'),
                'flow_data': quick_result.get('flow_data'),
                'model_data': quick_result.get('model_data'),
                'sentiment_data': quick_result.get('sentiment_data'),
                'ai_analysis': ai_analysis,
                'trading_signals': trading_signals,
                'stock_news': quick_result.get('stock_news'),
                'hot_topics': quick_result.get('hot_topics'),
                'platforms_data': quick_result.get('platforms_data'),
                'fetch_time': quick_result.get('fetch_time'),
                'duration': round(duration, 2),
            }
            
        except Exception as e:
            logger.error(f"❌ 完整分析失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_alert_check(self) -> Dict:
        """
        运行预警检查
        
        Returns:
            {
                'success': bool,
                'alerts': List[Dict],
            }
        """
        try:
            logger.info("⚠️ 开始预警检查...")
            
            if not self.alerts:
                return {'success': False, 'error': '预警系统不可用'}
            
            # 获取当前数据
            quick_result = self.run_quick_analysis()
            
            if not quick_result['success']:
                return {'success': False, 'error': quick_result.get('error')}
            
            # 获取历史数据
            history_data = self._get_previous_snapshot()
            
            # 构建检查数据
            current_data = {
                'flow_data': quick_result.get('flow_data', {}),
                'hot_topics': quick_result.get('hot_topics', []),
                'viral_k': quick_result.get('model_data', {}).get('viral_k', {}),
                'flow_stage': quick_result.get('sentiment_data', {}).get('flow_stage', {}),
            }
            
            # 检查预警
            alerts = self.alerts.check_alerts(
                current_data,
                history_data,
                quick_result.get('sentiment_data'),
                quick_result.get('snapshot_id')
            )
            
            logger.info(f"✅ 预警检查完成，触发 {len(alerts)} 个预警")
            
            return {
                'success': True,
                'alerts': alerts,
                'snapshot_id': quick_result.get('snapshot_id'),
            }
            
        except Exception as e:
            logger.error(f"❌ 预警检查失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_dashboard_data(self) -> Dict:
        """
        获取仪表盘数据
        
        Returns:
            {
                'latest_snapshot': Dict,
                'latest_sentiment': Dict,
                'latest_ai_analysis': Dict,
                'recent_alerts': List,
                'flow_trend': Dict,
                'scheduler_status': Dict,
            }
        """
        try:
            data = {}
            
            if self.db:
                # 最新快照
                data['latest_snapshot'] = self.db.get_latest_snapshot()
                
                # 最新情绪
                data['latest_sentiment'] = self.db.get_latest_sentiment()
                
                # 最新AI分析
                data['latest_ai_analysis'] = self.db.get_latest_ai_analysis()
                
                # 最近预警
                data['recent_alerts'] = self.db.get_alerts(days=1)
                
                # 流量趋势（7天）
                data['flow_trend'] = self.get_flow_trend(days=7)
            
            # 调度器状态
            try:
                from news_flow_scheduler import news_flow_scheduler
                data['scheduler_status'] = news_flow_scheduler.get_status()
            except:
                data['scheduler_status'] = None
            
            return data
            
        except Exception as e:
            logger.error(f"获取仪表盘数据失败: {e}")
            return {}
    
    def get_flow_trend(self, days: int = 7) -> Dict:
        """获取流量趋势"""
        if not self.db:
            return {'dates': [], 'scores': [], 'trend': '无数据'}
        
        stats = self.db.get_daily_statistics(days)
        
        if not stats:
            return {'dates': [], 'scores': [], 'trend': '无数据', 'analysis': '暂无历史数据'}
        
        # 反转（从旧到新）
        stats.reverse()
        
        dates = [s['date'] for s in stats]
        avg_scores = [s['avg_score'] for s in stats]
        max_scores = [s['max_score'] for s in stats]
        min_scores = [s['min_score'] for s in stats]
        
        # 判断趋势
        if len(avg_scores) >= 3:
            recent_avg = sum(avg_scores[-3:]) / 3
            earlier_avg = sum(avg_scores[:3]) / 3
            
            if recent_avg > earlier_avg * 1.2:
                trend = '上升'
                analysis = f"近期流量持续上升（近3日均值{recent_avg:.0f} > 前3日均值{earlier_avg:.0f}），市场热度升温。"
            elif recent_avg < earlier_avg * 0.8:
                trend = '下降'
                analysis = f"近期流量持续下降（近3日均值{recent_avg:.0f} < 前3日均值{earlier_avg:.0f}），市场热度降温。"
            else:
                trend = '平稳'
                analysis = f"近期流量波动不大（近3日均值{recent_avg:.0f} ≈ 前3日均值{earlier_avg:.0f}），市场处于平衡状态。"
        else:
            trend = '数据不足'
            analysis = '历史数据不足，无法判断趋势'
        
        return {
            'dates': dates,
            'avg_scores': avg_scores,
            'max_scores': max_scores,
            'min_scores': min_scores,
            'trend': trend,
            'analysis': analysis,
        }
    
    def _generate_trading_signals(self, flow_data: Dict, 
                                   model_data: Dict,
                                   sentiment_data: Dict,
                                   ai_analysis: Dict = None) -> Dict:
        """生成交易信号"""
        signals = {
            'overall_signal': '观望',
            'confidence': 50,
            'risk_level': '中等',
            'hot_sectors': [],
            'operation_advice': '',
            'key_message': '',
        }
        
        # 获取各项指标
        total_score = flow_data.get('total_score', 0)
        flow_level = flow_data.get('level', '中')
        
        sentiment_index = 50
        flow_stage = '未知'
        if sentiment_data:
            sentiment_index = sentiment_data.get('sentiment', {}).get('sentiment_index', 50)
            flow_stage = sentiment_data.get('flow_stage', {}).get('stage_name', '未知')
        
        viral_k = 1.0
        if model_data:
            viral_k = model_data.get('viral_k', {}).get('k_value', 1.0)
        
        # 核心判断逻辑
        if flow_stage in ['一致', 'consensus']:
            # 流量高潮 = 逃命时刻
            signals['overall_signal'] = '卖出'
            signals['confidence'] = 90
            signals['risk_level'] = '极高'
            signals['key_message'] = '⚠️ 流量高潮 = 价格高潮 = 逃命时刻！立即减仓或清仓！'
            signals['operation_advice'] = '立即减仓或清仓，锁定利润。不要贪婪，不要犹豫。'
            
        elif flow_stage in ['退潮', 'decline']:
            signals['overall_signal'] = '观望'
            signals['confidence'] = 80
            signals['risk_level'] = '高'
            signals['key_message'] = '流量退潮，及时止盈止损'
            signals['operation_advice'] = '持仓者及时止盈止损，空仓者继续观望。'
            
        elif flow_stage in ['加速', 'acceleration'] and viral_k > 1.2:
            signals['overall_signal'] = '买入'
            signals['confidence'] = 75
            signals['risk_level'] = '中等'
            signals['key_message'] = '流量加速期，可参与龙头'
            signals['operation_advice'] = '关注龙头股，轻仓试探。设置止损位（-5%），止盈位（+15%）。'
            
        elif flow_stage in ['启动', 'startup']:
            signals['overall_signal'] = '关注'
            signals['confidence'] = 65
            signals['risk_level'] = '低'
            signals['key_message'] = '流量启动期，可以关注'
            signals['operation_advice'] = '密切关注，等待确认后介入。'
            
        elif flow_level == "极高" and sentiment_index > 85:
            signals['overall_signal'] = '观望'
            signals['confidence'] = 70
            signals['risk_level'] = '高'
            signals['key_message'] = '流量极高+情绪过热，追高风险大'
            signals['operation_advice'] = '不建议追高，等待回调机会。'
            
        else:
            signals['overall_signal'] = '观望'
            signals['confidence'] = 50
            signals['risk_level'] = '中等'
            signals['key_message'] = '市场无明确方向，保持观望'
            signals['operation_advice'] = '保持观望，等待流量信号明确。'
        
        # 整合AI分析结果
        if ai_analysis:
            advice = ai_analysis.get('investment_advice', {})
            if advice.get('advice'):
                signals['ai_advice'] = advice.get('advice')
                signals['ai_confidence'] = advice.get('confidence', 50)
                signals['ai_summary'] = advice.get('summary', '')
            
            sectors = ai_analysis.get('sector_analysis', {}).get('benefited_sectors', [])
            signals['hot_sectors'] = sectors[:3]
        
        return signals
    
    def _get_history_scores(self, hours: int = 24) -> List[int]:
        """获取历史流量得分"""
        if not self.db:
            return []
        
        scores = self.db.get_recent_scores(hours)
        return [s['total_score'] for s in scores]
    
    def _get_history_sentiments(self, limit: int = 10) -> List[Dict]:
        """获取历史情绪记录"""
        if not self.db:
            return []
        
        return self.db.get_sentiment_history(limit)
    
    def _get_previous_snapshot(self) -> Optional[Dict]:
        """获取上一次快照"""
        if not self.db:
            return None
        
        snapshots = self.db.get_history_snapshots(limit=2)
        if len(snapshots) >= 2:
            detail = self.db.get_snapshot_detail(snapshots[1]['id'])
            return {
                'hot_topics': detail.get('hot_topics', []),
                'snapshot': detail.get('snapshot', {}),
            }
        return None
    
    def compare_with_history(self, current_score: int) -> Dict:
        """与历史数据对比"""
        if not self.db:
            return {
                'percentile': 50,
                'level_description': '无历史对比',
                'comparison': '暂无足够的历史数据进行对比'
            }
        
        stats = self.db.get_daily_statistics(30)
        
        if not stats:
            return {
                'percentile': 50,
                'level_description': '无历史对比',
                'comparison': '暂无足够的历史数据进行对比'
            }
        
        all_scores = []
        for stat in stats:
            all_scores.extend([stat['avg_score'], stat['max_score'], stat['min_score']])
        
        all_scores.sort()
        
        lower_count = sum(1 for s in all_scores if s < current_score)
        percentile = int(lower_count / len(all_scores) * 100) if all_scores else 50
        
        if percentile >= 90:
            level_description = "极高水平"
            comparison = f"当前流量得分{current_score}处于历史极高水平（超过{percentile}%的历史记录），流量极度爆发！"
        elif percentile >= 70:
            level_description = "较高水平"
            comparison = f"当前流量得分{current_score}处于历史较高水平（超过{percentile}%的历史记录），流量活跃。"
        elif percentile >= 30:
            level_description = "正常水平"
            comparison = f"当前流量得分{current_score}处于历史正常水平（超过{percentile}%的历史记录）。"
        else:
            level_description = "较低水平"
            comparison = f"当前流量得分{current_score}处于历史较低水平（仅超过{percentile}%的历史记录），流量低迷。"
        
        return {
            'percentile': percentile,
            'level_description': level_description,
            'comparison': comparison
        }


# 全局引擎实例
news_flow_engine = NewsFlowEngine()


# 测试代码
if __name__ == "__main__":
    print("=== 测试新闻流量分析引擎 ===")
    
    # 运行快速分析
    print("\n--- 快速分析 ---")
    result = news_flow_engine.run_quick_analysis(category='finance')
    
    if result['success']:
        print(f"✅ 分析成功！快照ID: {result.get('snapshot_id')}")
        print(f"\n流量得分: {result['flow_data']['total_score']}")
        print(f"流量等级: {result['flow_data']['level']}")
        print(f"股票相关新闻: {len(result['stock_news'])} 条")
        print(f"热门话题: {len(result['hot_topics'])} 个")
        
        if result.get('sentiment_data'):
            sentiment = result['sentiment_data'].get('sentiment', {})
            print(f"\n情绪指数: {sentiment.get('sentiment_index', 'N/A')}")
            print(f"情绪分类: {sentiment.get('sentiment_class', 'N/A')}")
            
            flow_stage = result['sentiment_data'].get('flow_stage', {})
            print(f"流量阶段: {flow_stage.get('stage_name', 'N/A')}")
    else:
        print(f"❌ 分析失败: {result.get('error')}")
