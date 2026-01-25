"""
新闻流量数据库模块
用于存储和管理新闻流量监测数据
包含：快照、新闻、情绪、预警、AI分析、定时任务日志
"""
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsFlowDatabase:
    """新闻流量数据库管理类"""
    
    def __init__(self, db_path: str = "news_flow.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """初始化数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 1. 新闻流量快照表（记录每次监测的整体情况）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS flow_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fetch_time TEXT NOT NULL,
            total_platforms INTEGER NOT NULL,
            success_count INTEGER NOT NULL,
            total_score INTEGER NOT NULL,
            flow_level TEXT NOT NULL,
            social_score INTEGER,
            news_score INTEGER,
            finance_score INTEGER,
            tech_score INTEGER,
            analysis TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 2. 平台新闻表（存储各平台的新闻数据）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS platform_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            platform_name TEXT NOT NULL,
            category TEXT NOT NULL,
            weight INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            url TEXT,
            source TEXT,
            publish_time TEXT,
            rank INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (snapshot_id) REFERENCES flow_snapshots(id)
        )
        ''')
        
        # 3. 股票相关新闻表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_related_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            platform_name TEXT NOT NULL,
            category TEXT NOT NULL,
            weight INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            url TEXT,
            source TEXT,
            publish_time TEXT,
            matched_keywords TEXT,
            keyword_count INTEGER,
            score INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (snapshot_id) REFERENCES flow_snapshots(id)
        )
        ''')
        
        # 4. 热门话题表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS hot_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            count INTEGER NOT NULL,
            heat INTEGER NOT NULL,
            cross_platform INTEGER,
            sources TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (snapshot_id) REFERENCES flow_snapshots(id)
        )
        ''')
        
        # 5. 监测历史统计表（按天汇总）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS flow_statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            avg_score INTEGER,
            max_score INTEGER,
            min_score INTEGER,
            snapshot_count INTEGER,
            top_topics TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 6. 情绪指标记录表【新增】
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sentiment_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER,
            sentiment_index INTEGER NOT NULL,
            sentiment_class TEXT NOT NULL,
            flow_stage TEXT NOT NULL,
            momentum REAL,
            viral_k REAL,
            flow_type TEXT,
            stage_analysis TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (snapshot_id) REFERENCES flow_snapshots(id)
        )
        ''')
        
        # 7. 预警记录表【新增】
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS flow_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type TEXT NOT NULL,
            alert_level TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            related_topics TEXT,
            trigger_value TEXT,
            threshold_value TEXT,
            is_notified INTEGER DEFAULT 0,
            snapshot_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (snapshot_id) REFERENCES flow_snapshots(id)
        )
        ''')
        
        # 8. AI分析记录表【新增】
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER,
            affected_sectors TEXT,
            recommended_stocks TEXT,
            risk_level TEXT,
            risk_factors TEXT,
            advice TEXT,
            confidence INTEGER,
            summary TEXT,
            raw_response TEXT,
            model_used TEXT,
            analysis_time REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (snapshot_id) REFERENCES flow_snapshots(id)
        )
        ''')
        
        # 9. 定时任务日志表【新增】
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduler_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            task_type TEXT,
            status TEXT NOT NULL,
            message TEXT,
            duration REAL,
            snapshot_id INTEGER,
            executed_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 10. 预警配置表【新增】
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alert_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT NOT NULL UNIQUE,
            config_value TEXT NOT NULL,
            description TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 初始化预警配置默认值
        default_configs = [
            ('heat_threshold', '800', '热度飙升阈值'),
            ('rank_change_threshold', '10', '排名变化阈值'),
            ('sentiment_high_threshold', '90', '情绪高位阈值'),
            ('sentiment_low_threshold', '20', '情绪低位阈值'),
            ('viral_k_threshold', '1.5', 'K值阈值'),
            ('alert_enabled', 'true', '预警开关'),
            ('notification_enabled', 'true', '通知开关'),
        ]
        
        for key, value, desc in default_configs:
            cursor.execute('''
            INSERT OR IGNORE INTO alert_config (config_key, config_value, description)
            VALUES (?, ?, ?)
            ''', (key, value, desc))
        
        # 数据库迁移：添加缺失的列
        self._migrate_database(cursor)
        
        conn.commit()
        conn.close()
        logger.info("✅ 新闻流量数据库初始化完成")
    
    def _migrate_database(self, cursor):
        """数据库迁移：添加缺失的列"""
        # 定义需要迁移的列
        migrations = [
            # (表名, 列名, 列定义)
            ('stock_related_news', 'score', 'INTEGER DEFAULT 0'),
            ('stock_related_news', 'rank', 'INTEGER'),
            ('platform_news', 'rank', 'INTEGER'),
            ('hot_topics', 'cross_platform', 'INTEGER'),
            ('hot_topics', 'sources', 'TEXT'),
        ]
        
        for table, column, column_def in migrations:
            try:
                # 检查列是否存在
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                
                if column not in columns:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_def}")
                    logger.info(f"✅ 迁移: 向 {table} 添加列 {column}")
            except Exception as e:
                logger.warning(f"迁移列 {table}.{column} 时出错: {e}")
    
    # ==================== 快照相关方法 ====================
    
    def save_flow_snapshot(self, flow_data: Dict, platforms_data: List[Dict], 
                           stock_news: List[Dict], hot_topics: List[Dict]) -> int:
        """
        保存完整的流量快照
        
        Args:
            flow_data: 流量得分数据
            platforms_data: 平台新闻数据
            stock_news: 股票相关新闻
            hot_topics: 热门话题
            
        Returns:
            snapshot_id: 快照ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. 保存快照主表
            cursor.execute('''
            INSERT INTO flow_snapshots 
            (fetch_time, total_platforms, success_count, total_score, flow_level,
             social_score, news_score, finance_score, tech_score, analysis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                len(platforms_data),
                sum(1 for p in platforms_data if p.get('success')),
                flow_data['total_score'],
                flow_data['level'],
                flow_data.get('social_score', 0),
                flow_data.get('news_score', 0),
                flow_data.get('finance_score', 0),
                flow_data.get('tech_score', 0),
                flow_data.get('analysis', '')
            ))
            
            snapshot_id = cursor.lastrowid
            
            # 2. 保存平台新闻
            for platform_data in platforms_data:
                if not platform_data.get('success'):
                    continue
                
                for news in platform_data.get('data', []):
                    cursor.execute('''
                    INSERT INTO platform_news
                    (snapshot_id, platform, platform_name, category, weight,
                     title, content, url, source, publish_time, rank)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        snapshot_id,
                        platform_data['platform'],
                        platform_data['platform_name'],
                        platform_data['category'],
                        platform_data['weight'],
                        news.get('title') or '',
                        news.get('content') or '',
                        news.get('url') or '',
                        news.get('source') or '',
                        news.get('publish_time') or '',
                        news.get('rank', 0)
                    ))
            
            # 3. 保存股票相关新闻
            for news in stock_news:
                cursor.execute('''
                INSERT INTO stock_related_news
                (snapshot_id, platform, platform_name, category, weight,
                 title, content, url, source, publish_time, matched_keywords, keyword_count, score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    snapshot_id,
                    news['platform'],
                    news['platform_name'],
                    news['category'],
                    news['weight'],
                    news['title'],
                    news.get('content') or '',
                    news.get('url') or '',
                    news.get('source') or '',
                    news.get('publish_time') or '',
                    json.dumps(news.get('matched_keywords', []), ensure_ascii=False),
                    news.get('keyword_count', 0),
                    news.get('score', 0)
                ))
            
            # 4. 保存热门话题
            for topic in hot_topics:
                cursor.execute('''
                INSERT INTO hot_topics
                (snapshot_id, topic, count, heat, cross_platform, sources)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    snapshot_id,
                    topic['topic'],
                    topic['count'],
                    topic['heat'],
                    topic.get('cross_platform', 0),
                    json.dumps(topic.get('sources', []), ensure_ascii=False)
                ))
            
            # 5. 更新每日统计
            self._update_daily_statistics(cursor, flow_data['total_score'], hot_topics)
            
            conn.commit()
            logger.info(f"✅ 保存流量快照成功，ID: {snapshot_id}")
            return snapshot_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ 保存流量快照失败: {e}")
            raise
        finally:
            conn.close()
    
    def _update_daily_statistics(self, cursor, score: int, hot_topics: List[Dict]):
        """更新每日统计"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
        SELECT avg_score, max_score, min_score, snapshot_count, top_topics
        FROM flow_statistics WHERE date = ?
        ''', (today,))
        
        row = cursor.fetchone()
        
        if row:
            old_avg = row['avg_score'] or 0
            old_count = row['snapshot_count'] or 0
            new_avg = int((old_avg * old_count + score) / (old_count + 1))
            new_max = max(row['max_score'] or 0, score)
            new_min = min(row['min_score'] or 999999, score)
            
            old_topics = json.loads(row['top_topics']) if row['top_topics'] else []
            new_topics = old_topics + [t['topic'] for t in hot_topics[:10]]
            topic_counter = Counter(new_topics)
            top_topics = [topic for topic, _ in topic_counter.most_common(20)]
            
            cursor.execute('''
            UPDATE flow_statistics
            SET avg_score = ?, max_score = ?, min_score = ?, 
                snapshot_count = ?, top_topics = ?
            WHERE date = ?
            ''', (new_avg, new_max, new_min, old_count + 1,
                  json.dumps(top_topics, ensure_ascii=False), today))
        else:
            top_topics = [t['topic'] for t in hot_topics[:20]]
            cursor.execute('''
            INSERT INTO flow_statistics
            (date, avg_score, max_score, min_score, snapshot_count, top_topics)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (today, score, score, score, 1,
                  json.dumps(top_topics, ensure_ascii=False)))
    
    def get_latest_snapshot(self) -> Optional[Dict]:
        """获取最新的流量快照"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM flow_snapshots
        ORDER BY created_at DESC LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_recent_snapshots(self, limit: int = 10) -> List[Dict]:
        """获取最近的流量快照列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM flow_snapshots
        ORDER BY created_at DESC LIMIT ?
        ''', (limit,))
        
        snapshots = []
        for row in cursor.fetchall():
            snapshots.append(dict(row))
        
        conn.close()
        return snapshots
    
    def get_snapshot_detail(self, snapshot_id: int) -> Dict:
        """获取快照详细信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM flow_snapshots WHERE id = ?', (snapshot_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return {}
        
        snapshot = dict(row)
        
        cursor.execute('''
        SELECT * FROM stock_related_news
        WHERE snapshot_id = ?
        ORDER BY COALESCE(score, 0) DESC, weight DESC
        ''', (snapshot_id,))
        
        stock_news = []
        for row in cursor.fetchall():
            news = dict(row)
            news['matched_keywords'] = json.loads(news['matched_keywords']) if news['matched_keywords'] else []
            stock_news.append(news)
        
        cursor.execute('''
        SELECT * FROM hot_topics
        WHERE snapshot_id = ?
        ORDER BY heat DESC
        ''', (snapshot_id,))
        
        hot_topics = []
        for row in cursor.fetchall():
            topic = dict(row)
            topic['sources'] = json.loads(topic['sources']) if topic['sources'] else []
            hot_topics.append(topic)
        
        # 获取情绪记录
        cursor.execute('''
        SELECT * FROM sentiment_records
        WHERE snapshot_id = ?
        ORDER BY created_at DESC LIMIT 1
        ''', (snapshot_id,))
        sentiment_row = cursor.fetchone()
        sentiment = dict(sentiment_row) if sentiment_row else None
        
        # 获取AI分析
        cursor.execute('''
        SELECT * FROM ai_analysis
        WHERE snapshot_id = ?
        ORDER BY created_at DESC LIMIT 1
        ''', (snapshot_id,))
        ai_row = cursor.fetchone()
        ai_analysis = None
        if ai_row:
            ai_analysis = dict(ai_row)
            ai_analysis['affected_sectors'] = json.loads(ai_analysis['affected_sectors']) if ai_analysis['affected_sectors'] else []
            ai_analysis['recommended_stocks'] = json.loads(ai_analysis['recommended_stocks']) if ai_analysis['recommended_stocks'] else []
            ai_analysis['risk_factors'] = json.loads(ai_analysis['risk_factors']) if ai_analysis['risk_factors'] else []
        
        conn.close()
        
        return {
            'snapshot': snapshot,
            'stock_news': stock_news,
            'hot_topics': hot_topics,
            'sentiment': sentiment,
            'ai_analysis': ai_analysis,
        }
    
    def get_history_snapshots(self, limit: int = 50) -> List[Dict]:
        """获取历史快照列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, fetch_time, total_score, flow_level, 
               success_count, total_platforms, analysis
        FROM flow_snapshots
        ORDER BY created_at DESC
        LIMIT ?
        ''', (limit,))
        
        snapshots = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return snapshots
    
    def get_daily_statistics(self, days: int = 7) -> List[Dict]:
        """获取每日统计数据"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM flow_statistics
        ORDER BY date DESC
        LIMIT ?
        ''', (days,))
        
        stats = []
        for row in cursor.fetchall():
            stat = dict(row)
            stat['top_topics'] = json.loads(stat['top_topics']) if stat['top_topics'] else []
            stats.append(stat)
        
        conn.close()
        return stats
    
    def get_recent_scores(self, hours: int = 24) -> List[Dict]:
        """获取最近N小时的得分记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
        SELECT id, fetch_time, total_score, flow_level
        FROM flow_snapshots
        WHERE fetch_time >= ?
        ORDER BY fetch_time ASC
        ''', (since,))
        
        scores = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return scores
    
    def search_stock_news(self, keyword: str, limit: int = 50) -> List[Dict]:
        """搜索股票相关新闻"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT srn.*, fs.fetch_time, fs.flow_level
        FROM stock_related_news srn
        JOIN flow_snapshots fs ON srn.snapshot_id = fs.id
        WHERE srn.title LIKE ? OR srn.content LIKE ?
        ORDER BY srn.created_at DESC
        LIMIT ?
        ''', (f'%{keyword}%', f'%{keyword}%', limit))
        
        results = []
        for row in cursor.fetchall():
            news = dict(row)
            news['matched_keywords'] = json.loads(news['matched_keywords']) if news['matched_keywords'] else []
            results.append(news)
        
        conn.close()
        return results
    
    # ==================== 情绪记录相关方法 ====================
    
    def save_sentiment_record(self, snapshot_id: int, sentiment_data: Dict) -> int:
        """保存情绪记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO sentiment_records
        (snapshot_id, sentiment_index, sentiment_class, flow_stage, 
         momentum, viral_k, flow_type, stage_analysis)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            snapshot_id,
            sentiment_data.get('sentiment_index', 50),
            sentiment_data.get('sentiment_class', '中性'),
            sentiment_data.get('flow_stage', '未知'),
            sentiment_data.get('momentum', 0),
            sentiment_data.get('viral_k', 1.0),
            sentiment_data.get('flow_type', '未知'),
            sentiment_data.get('stage_analysis', '')
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return record_id
    
    def get_sentiment_history(self, limit: int = 50) -> List[Dict]:
        """获取情绪历史记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT sr.*, fs.fetch_time, fs.total_score
        FROM sentiment_records sr
        LEFT JOIN flow_snapshots fs ON sr.snapshot_id = fs.id
        ORDER BY sr.created_at DESC
        LIMIT ?
        ''', (limit,))
        
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return records
    
    def get_latest_sentiment(self) -> Optional[Dict]:
        """获取最新情绪记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT sr.*, fs.fetch_time, fs.total_score, fs.flow_level
        FROM sentiment_records sr
        LEFT JOIN flow_snapshots fs ON sr.snapshot_id = fs.id
        ORDER BY sr.created_at DESC
        LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    # ==================== 预警相关方法 ====================
    
    def save_alert(self, alert_data: Dict) -> int:
        """保存预警记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO flow_alerts
        (alert_type, alert_level, title, content, related_topics,
         trigger_value, threshold_value, is_notified, snapshot_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            alert_data['alert_type'],
            alert_data.get('alert_level', 'info'),
            alert_data['title'],
            alert_data.get('content', ''),
            json.dumps(alert_data.get('related_topics', []), ensure_ascii=False),
            str(alert_data.get('trigger_value', '')),
            str(alert_data.get('threshold_value', '')),
            1 if alert_data.get('is_notified') else 0,
            alert_data.get('snapshot_id')
        ))
        
        alert_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return alert_id
    
    def get_alerts(self, days: int = 7, alert_type: str = None) -> List[Dict]:
        """获取预警记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        if alert_type:
            cursor.execute('''
            SELECT * FROM flow_alerts
            WHERE created_at >= ? AND alert_type = ?
            ORDER BY created_at DESC
            ''', (since, alert_type))
        else:
            cursor.execute('''
            SELECT * FROM flow_alerts
            WHERE created_at >= ?
            ORDER BY created_at DESC
            ''', (since,))
        
        alerts = []
        for row in cursor.fetchall():
            alert = dict(row)
            alert['related_topics'] = json.loads(alert['related_topics']) if alert['related_topics'] else []
            alerts.append(alert)
        
        conn.close()
        return alerts
    
    def get_unnotified_alerts(self) -> List[Dict]:
        """获取未通知的预警"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM flow_alerts
        WHERE is_notified = 0
        ORDER BY created_at DESC
        ''')
        
        alerts = []
        for row in cursor.fetchall():
            alert = dict(row)
            alert['related_topics'] = json.loads(alert['related_topics']) if alert['related_topics'] else []
            alerts.append(alert)
        
        conn.close()
        return alerts
    
    def mark_alert_notified(self, alert_id: int):
        """标记预警为已通知"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE flow_alerts SET is_notified = 1 WHERE id = ?
        ''', (alert_id,))
        
        conn.commit()
        conn.close()
    
    # ==================== AI分析相关方法 ====================
    
    def save_ai_analysis(self, snapshot_id: int, analysis_data: Dict) -> int:
        """保存AI分析结果"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO ai_analysis
        (snapshot_id, affected_sectors, recommended_stocks, risk_level,
         risk_factors, advice, confidence, summary, raw_response, model_used, analysis_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            snapshot_id,
            json.dumps(analysis_data.get('affected_sectors', []), ensure_ascii=False),
            json.dumps(analysis_data.get('recommended_stocks', []), ensure_ascii=False),
            analysis_data.get('risk_level', '未知'),
            json.dumps(analysis_data.get('risk_factors', []), ensure_ascii=False),
            analysis_data.get('advice', '观望'),
            analysis_data.get('confidence', 50),
            analysis_data.get('summary', ''),
            analysis_data.get('raw_response', ''),
            analysis_data.get('model_used', 'deepseek-chat'),
            analysis_data.get('analysis_time', 0)
        ))
        
        analysis_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return analysis_id
    
    def get_latest_ai_analysis(self) -> Optional[Dict]:
        """获取最新AI分析结果"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT aa.*, fs.fetch_time, fs.total_score, fs.flow_level
        FROM ai_analysis aa
        LEFT JOIN flow_snapshots fs ON aa.snapshot_id = fs.id
        ORDER BY aa.created_at DESC
        LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            analysis = dict(row)
            analysis['affected_sectors'] = json.loads(analysis['affected_sectors']) if analysis['affected_sectors'] else []
            analysis['recommended_stocks'] = json.loads(analysis['recommended_stocks']) if analysis['recommended_stocks'] else []
            analysis['risk_factors'] = json.loads(analysis['risk_factors']) if analysis['risk_factors'] else []
            return analysis
        return None
    
    def get_ai_analysis_history(self, limit: int = 20) -> List[Dict]:
        """获取AI分析历史"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT aa.*, fs.fetch_time, fs.total_score, fs.flow_level
        FROM ai_analysis aa
        LEFT JOIN flow_snapshots fs ON aa.snapshot_id = fs.id
        ORDER BY aa.created_at DESC
        LIMIT ?
        ''', (limit,))
        
        results = []
        for row in cursor.fetchall():
            analysis = dict(row)
            analysis['affected_sectors'] = json.loads(analysis['affected_sectors']) if analysis['affected_sectors'] else []
            analysis['recommended_stocks'] = json.loads(analysis['recommended_stocks']) if analysis['recommended_stocks'] else []
            analysis['risk_factors'] = json.loads(analysis['risk_factors']) if analysis['risk_factors'] else []
            results.append(analysis)
        
        conn.close()
        return results
    
    # ==================== 定时任务日志相关方法 ====================
    
    def save_scheduler_log(self, task_name: str, task_type: str, 
                           status: str, message: str = '', 
                           duration: float = 0, snapshot_id: int = None) -> int:
        """保存定时任务日志"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO scheduler_logs
        (task_name, task_type, status, message, duration, snapshot_id)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (task_name, task_type, status, message, duration, snapshot_id))
        
        log_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return log_id
    
    def get_scheduler_logs(self, days: int = 7, task_type: str = None) -> List[Dict]:
        """获取定时任务日志"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        if task_type:
            cursor.execute('''
            SELECT * FROM scheduler_logs
            WHERE executed_at >= ? AND task_type = ?
            ORDER BY executed_at DESC
            ''', (since, task_type))
        else:
            cursor.execute('''
            SELECT * FROM scheduler_logs
            WHERE executed_at >= ?
            ORDER BY executed_at DESC
            ''', (since,))
        
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return logs
    
    # ==================== 预警配置相关方法 ====================
    
    def get_alert_config(self, key: str) -> Optional[str]:
        """获取预警配置"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT config_value FROM alert_config WHERE config_key = ?
        ''', (key,))
        
        row = cursor.fetchone()
        conn.close()
        
        return row['config_value'] if row else None
    
    def set_alert_config(self, key: str, value: str, description: str = None):
        """设置预警配置"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO alert_config (config_key, config_value, description, updated_at)
        VALUES (?, ?, ?, ?)
        ''', (key, value, description, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        conn.commit()
        conn.close()
    
    def get_all_alert_configs(self) -> Dict[str, str]:
        """获取所有预警配置"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT config_key, config_value FROM alert_config')
        
        configs = {row['config_key']: row['config_value'] for row in cursor.fetchall()}
        conn.close()
        return configs


# 全局数据库实例
news_flow_db = NewsFlowDatabase()


# 测试代码
if __name__ == "__main__":
    print("=== 测试新闻流量数据库 ===")
    
    # 测试保存快照
    flow_data = {
        'total_score': 650,
        'social_score': 200,
        'news_score': 180,
        'finance_score': 220,
        'tech_score': 50,
        'level': '高',
        'analysis': '流量较高，市场活跃'
    }
    
    platforms_data = [{
        'success': True,
        'platform': 'weibo',
        'platform_name': '微博热搜',
        'category': 'social',
        'weight': 10,
        'data': [
            {'title': '某某股票大涨', 'content': '今日涨停', 'url': 'http://example.com', 
             'source': '微博', 'publish_time': '2026-01-25 10:00:00', 'rank': 1}
        ]
    }]
    
    stock_news = [{
        'platform': 'weibo',
        'platform_name': '微博热搜',
        'category': 'social',
        'weight': 10,
        'title': '某某股票大涨',
        'content': '今日涨停',
        'url': 'http://example.com',
        'source': '微博',
        'publish_time': '2026-01-25 10:00:00',
        'matched_keywords': ['股票', '涨停'],
        'keyword_count': 2,
        'score': 100
    }]
    
    hot_topics = [
        {'topic': 'AI', 'count': 50, 'heat': 95, 'cross_platform': 5, 'sources': ['微博', '抖音']},
        {'topic': '新能源', 'count': 30, 'heat': 80, 'cross_platform': 3, 'sources': ['微博']}
    ]
    
    snapshot_id = news_flow_db.save_flow_snapshot(flow_data, platforms_data, stock_news, hot_topics)
    print(f"✅ 保存快照成功，ID: {snapshot_id}")
    
    # 测试保存情绪记录
    sentiment_data = {
        'sentiment_index': 75,
        'sentiment_class': '乐观',
        'flow_stage': '加速',
        'momentum': 1.5,
        'viral_k': 1.2,
        'flow_type': '增量流量型',
        'stage_analysis': '流量正在快速上升'
    }
    sentiment_id = news_flow_db.save_sentiment_record(snapshot_id, sentiment_data)
    print(f"✅ 保存情绪记录成功，ID: {sentiment_id}")
    
    # 测试保存预警
    alert_data = {
        'alert_type': 'heat_surge',
        'alert_level': 'warning',
        'title': '热度飙升预警',
        'content': '当前流量得分650，超过阈值500',
        'related_topics': ['AI', '新能源'],
        'trigger_value': 650,
        'threshold_value': 500,
        'snapshot_id': snapshot_id
    }
    alert_id = news_flow_db.save_alert(alert_data)
    print(f"✅ 保存预警成功，ID: {alert_id}")
    
    # 测试保存AI分析
    ai_data = {
        'affected_sectors': [{'name': 'AI', 'impact': '利好', 'reason': '政策支持'}],
        'recommended_stocks': [{'code': '000001', 'name': '平安银行', 'reason': '龙头'}],
        'risk_level': '中等',
        'risk_factors': ['追高风险', '流动性风险'],
        'advice': '观望',
        'confidence': 75,
        'summary': '当前市场热度较高，建议观望',
        'model_used': 'deepseek-chat',
        'analysis_time': 2.5
    }
    ai_id = news_flow_db.save_ai_analysis(snapshot_id, ai_data)
    print(f"✅ 保存AI分析成功，ID: {ai_id}")
    
    # 测试保存任务日志
    log_id = news_flow_db.save_scheduler_log(
        '热点同步', 'sync_hotspots', 'success', 
        '成功同步22个平台', 5.2, snapshot_id
    )
    print(f"✅ 保存任务日志成功，ID: {log_id}")
    
    # 测试获取详情
    detail = news_flow_db.get_snapshot_detail(snapshot_id)
    print(f"\n快照详情:")
    print(f"  流量得分: {detail['snapshot']['total_score']}")
    print(f"  情绪指数: {detail['sentiment']['sentiment_index'] if detail['sentiment'] else 'N/A'}")
    print(f"  AI建议: {detail['ai_analysis']['advice'] if detail['ai_analysis'] else 'N/A'}")
