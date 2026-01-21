"""
智瞰龙虎综合分析引擎
整合数据获取、AI分析、结果生成的核心引擎
"""

from longhubang_data import LonghubangDataFetcher
from longhubang_db import LonghubangDatabase
from longhubang_agents import LonghubangAgents
from longhubang_scoring import LonghubangScoring
from typing import Dict, Any, List
from datetime import datetime, timedelta
import time
import logging


class LonghubangEngine:
    """龙虎榜综合分析引擎"""
    
    def __init__(self, model=None, db_path=None):
        """
        初始化分析引擎
        
        Args:
            model: AI模型名称（如果不传入，则使用配置文件中的默认模型）
            db_path: 数据库路径
        """
        import config
        # 强制使用配置文件中的默认模型
        # 如果传入的是 None、空字符串或旧的默认值 "deepseek-chat"，都使用配置文件的值
        if model is None or model == "" or model == "deepseek-chat":
            self.model = config.DEEPSEEK_MODEL_NAME
            if model == "deepseek-chat":
                print(f"[智瞰龙虎引擎] ⚠️ 检测到传入的模型是旧的默认值 'deepseek-chat'，强制使用配置文件中的模型: {self.model}")
        else:
            self.model = model
        self.data_fetcher = LonghubangDataFetcher()
        self.database = LonghubangDatabase(db_path)
        self.agents = LonghubangAgents(model=self.model)
        self.scoring = LonghubangScoring()
        # 初始化日志
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(name)s: %(message)s')
        self.logger.info("[智瞰龙虎] 分析引擎初始化完成")
    
    def run_comprehensive_analysis(self, date=None, days=1) -> Dict[str, Any]:
        """
        运行完整的龙虎榜分析流程
        
        Args:
            date: 指定日期，格式 YYYY-MM-DD，默认为昨日
            days: 分析最近几天的数据，默认1天
            
        Returns:
            完整的分析结果
        """
        self.logger.info("=" * 60)
        self.logger.info("🚀 智瞰龙虎综合分析系统启动")
        self.logger.info("=" * 60)
        
        results = {
            "success": False,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "data_info": {},
            "agents_analysis": {},
            "final_report": {},
            "recommended_stocks": []
        }
        
        try:
            # 阶段1: 获取龙虎榜数据
            self.logger.info("[阶段1] 获取龙虎榜数据...")
            self.logger.info("-" * 60)
            
            if date:
                data_list = [self.data_fetcher.get_longhubang_data(date)]
                data_list = data_list[0].get('data', []) if data_list[0] else []
            else:
                data_list = self.data_fetcher.get_recent_days_data(days)
            
            if not data_list:
                self.logger.error("未获取到龙虎榜数据")
                results["error"] = "未获取到龙虎榜数据"
                return results

            self.logger.info(f"成功获取 {len(data_list)} 条龙虎榜记录")
            
            # 阶段2: 保存数据到数据库
            self.logger.info("[阶段2] 保存数据到数据库...")
            self.logger.info("-" * 60)
            saved_count = self.database.save_longhubang_data(data_list)
            self.logger.info(f"保存 {saved_count} 条记录")
            
            # 阶段3: 数据分析和统计
            self.logger.info("[阶段3] 数据分析和统计...")
            self.logger.info("-" * 60)
            summary = self.data_fetcher.analyze_data_summary(data_list)
            formatted_data = self.data_fetcher.format_data_for_ai(data_list, summary)
            
            results["data_info"] = {
                "total_records": summary.get('total_records', 0),
                "total_stocks": summary.get('total_stocks', 0),
                "total_youzi": summary.get('total_youzi', 0),
                "summary": summary
            }
            self.logger.info("数据统计完成")
            
            # 阶段3.5: AI智能评分排名
            self.logger.info("[阶段3.5] AI智能评分排名...")
            self.logger.info("-" * 60)
            scoring_df = self.scoring.score_all_stocks(data_list)
            # 转换为可序列化格式以避免UI/存储类型问题
            scoring_ranking_data: List[Dict[str, Any]] = []
            try:
                if scoring_df is not None and hasattr(scoring_df, 'to_dict'):
                    scoring_ranking_data = scoring_df.to_dict('records')
                    self.logger.info(f"完成 {len(scoring_ranking_data)} 只股票的智能评分排名")
                else:
                    self.logger.warning("评分结果为空或格式不支持转换")
            except Exception as e:
                self.logger.exception(f"评分排名数据转换失败: {e}", exc_info=True)
                scoring_ranking_data = []
            results["scoring_ranking"] = scoring_ranking_data
            
            # 阶段4: AI分析师团队分析
            self.logger.info("[阶段4] AI分析师团队工作中...")
            self.logger.info("-" * 60)
            
            agents_results = {}
            
            # 1. 游资行为分析师
            self.logger.info("1/5 游资行为分析师...")
            youzi_result = self.agents.youzi_behavior_analyst(formatted_data, summary)
            agents_results["youzi"] = youzi_result
            
            # 2. 个股潜力分析师
            self.logger.info("2/5 个股潜力分析师...")
            stock_result = self.agents.stock_potential_analyst(formatted_data, summary)
            agents_results["stock"] = stock_result
            
            # 3. 题材追踪分析师
            self.logger.info("3/5 题材追踪分析师...")
            theme_result = self.agents.theme_tracker_analyst(formatted_data, summary)
            agents_results["theme"] = theme_result
            
            # 4. 风险控制专家
            self.logger.info("4/5 风险控制专家...")
            risk_result = self.agents.risk_control_specialist(formatted_data, summary)
            agents_results["risk"] = risk_result
            
            # 5. 首席策略师综合
            self.logger.info("5/5 首席策略师综合分析...")
            all_analyses = [youzi_result, stock_result, theme_result, risk_result]
            chief_result = self.agents.chief_strategist(all_analyses)
            agents_results["chief"] = chief_result
            
            results["agents_analysis"] = agents_results
            self.logger.info("所有AI分析师分析完成")
            
            # 阶段5: 提取推荐股票
            self.logger.info("[阶段5] 提取推荐股票...")
            self.logger.info("-" * 60)
            recommended_stocks = self._extract_recommended_stocks(
                chief_result.get('analysis', ''),
                stock_result.get('analysis', ''),
                summary
            )
            results["recommended_stocks"] = recommended_stocks
            self.logger.info(f"提取 {len(recommended_stocks)} 只推荐股票")
            
            # 阶段6: 生成最终报告
            self.logger.info("[阶段6] 生成最终报告...")
            self.logger.info("-" * 60)
            final_report = self._generate_final_report(agents_results, summary, recommended_stocks)
            results["final_report"] = final_report
            self.logger.info("最终报告生成完成")
            
            # 阶段7: 保存完整分析报告到数据库
            self.logger.info("[阶段7] 保存完整分析报告...")
            self.logger.info("-" * 60)
            data_date_range = self._get_date_range(data_list)
            
            # 转换评分排名数据为可序列化格式
            # 复用前面转换的评分数据
            # 若前面转换失败，此处不再重复转换，避免错误
            
            # 构建完整的分析内容（结构化）
            full_analysis_content = {
                "agents_analysis": agents_results,
                "data_info": results["data_info"],
                "scoring_ranking": scoring_ranking_data,
                "final_report": final_report,
                "timestamp": results["timestamp"]
            }
            
            report_id = self.database.save_analysis_report(
                data_date_range=data_date_range,
                analysis_content=full_analysis_content,  # 保存完整的结构化数据
                recommended_stocks=recommended_stocks,
                summary=final_report.get('summary', ''),
                full_result=results  # 传入完整结果
            )
            results["report_id"] = report_id
            self.logger.info(f"完整报告已保存 (ID: {report_id})")
            
            results["success"] = True
            
            self.logger.info("=" * 60)
            self.logger.info("✓ 智瞰龙虎综合分析完成！")
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.exception(f"分析过程出错: {e}", exc_info=True)
            results["error"] = str(e)

        return results
    
    def _extract_recommended_stocks(self, chief_analysis: str, stock_analysis: str, summary: Dict) -> List[Dict]:
        """
        从AI分析中提取推荐股票
        
        Args:
            chief_analysis: 首席策略师分析
            stock_analysis: 个股潜力分析师分析
            summary: 数据摘要
            
        Returns:
            推荐股票列表
        """
        recommended = []
        
        # 从摘要中获取TOP股票作为基础
        if summary.get('top_stocks'):
            for idx, stock in enumerate(summary['top_stocks'][:10], 1):
                recommended.append({
                    'rank': idx,
                    'code': stock['code'],
                    'name': stock['name'],
                    'net_inflow': stock['net_inflow'],
                    'reason': f"资金净流入 {stock['net_inflow']:,.2f} 元",
                    'confidence': '中',
                    'buy_price': '待定',
                    'target_price': '待定',
                    'stop_loss': '待定',
                    'hold_period': '短线'
                })
        
        return recommended
    
    def _generate_final_report(self, agents_results: Dict, summary: Dict, 
                               recommended_stocks: List[Dict]) -> Dict:
        """
        生成最终报告
        
        Args:
            agents_results: 所有分析师的分析结果
            summary: 数据摘要
            recommended_stocks: 推荐股票列表
            
        Returns:
            最终报告字典
        """
        report = {
            'title': '智瞰龙虎榜综合分析报告',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': '',
            'data_overview': {
                'total_records': summary.get('total_records', 0),
                'total_stocks': summary.get('total_stocks', 0),
                'total_youzi': summary.get('total_youzi', 0),
                'total_net_inflow': summary.get('total_net_inflow', 0)
            },
            'recommended_stocks_count': len(recommended_stocks),
            'agents_count': len(agents_results)
        }
        
        # 生成摘要
        summary_parts = []
        summary_parts.append(f"本次分析共涵盖 {summary.get('total_records', 0)} 条龙虎榜记录")
        summary_parts.append(f"涉及 {summary.get('total_stocks', 0)} 只股票")
        summary_parts.append(f"涉及 {summary.get('total_youzi', 0)} 个游资席位")
        summary_parts.append(f"共推荐 {len(recommended_stocks)} 只潜力股票")
        
        report['summary'] = "，".join(summary_parts) + "。"
        
        return report
    
    def _get_date_range(self, data_list: List[Dict]) -> str:
        """
        获取数据的日期范围
        
        Args:
            data_list: 数据列表
            
        Returns:
            日期范围字符串
        """
        if not data_list:
            return "未知"
        
        dates = []
        for record in data_list:
            date = record.get('rq') or record.get('日期')
            if date:
                dates.append(date)
        
        if not dates:
            return "未知"
        
        dates = sorted(set(dates))
        if len(dates) == 1:
            return dates[0]
        else:
            return f"{dates[0]} 至 {dates[-1]}"
    
    def get_historical_reports(self, limit=10):
        """
        获取历史分析报告
        
        Args:
            limit: 返回数量
            
        Returns:
            报告列表
        """
        return self.database.get_analysis_reports(limit)
    
    def get_report_detail(self, report_id):
        """
        获取报告详情
        
        Args:
            report_id: 报告ID
            
        Returns:
            报告详情
        """
        return self.database.get_analysis_report(report_id)
    
    def get_statistics(self):
        """
        获取数据库统计信息
        
        Returns:
            统计信息
        """
        return self.database.get_statistics()
    
    def get_top_youzi(self, start_date=None, end_date=None, limit=20):
        """
        获取活跃游资排名
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量
            
        Returns:
            游资排名
        """
        return self.database.get_top_youzi(start_date, end_date, limit)
    
    def get_top_stocks(self, start_date=None, end_date=None, limit=20):
        """
        获取热门股票排名
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量
            
        Returns:
            股票排名
        """
        return self.database.get_top_stocks(start_date, end_date, limit)


# 测试函数
if __name__ == "__main__":
    print("=" * 60)
    print("测试智瞰龙虎分析引擎")
    print("=" * 60)
    
    # 创建引擎实例
    engine = LonghubangEngine()
    
    # 运行综合分析（分析昨天的数据）
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    results = engine.run_comprehensive_analysis(date=yesterday)
    
    if results.get('success'):
        print("\n" + "=" * 60)
        print("分析成功！")
        print("=" * 60)
        print(f"数据记录: {results['data_info']['total_records']}")
        print(f"涉及股票: {results['data_info']['total_stocks']}")
        print(f"推荐股票: {len(results['recommended_stocks'])}")
    else:
        print(f"\n分析失败: {results.get('error', '未知错误')}")

