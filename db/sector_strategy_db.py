"""
智策板块数据库模块
用于存储板块策略历史数据和分析报告
"""

import sqlite3
from datetime import datetime
import json
import pandas as pd
import logging


class SectorStrategyDatabase:
    """智策板块数据库管理类"""
    
    def __init__(self, db_path='data/sector_strategy.db'):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        # 初始化日志
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(name)s: %(message)s')
        self.init_database()
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """初始化数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 板块原始数据表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sector_raw_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_date TEXT NOT NULL,
            sector_code TEXT NOT NULL,
            sector_name TEXT,
            price REAL,
            change_pct REAL,
            volume REAL,
            turnover REAL,
            market_cap REAL,
            pe_ratio REAL,
            pb_ratio REAL,
            data_type TEXT,
            data_version INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(data_date, sector_code, data_type)
        )
        ''')
        
        # 创建索引
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_sector_data_date ON sector_raw_data(data_date)
        ''')
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_sector_code ON sector_raw_data(sector_code)
        ''')
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_data_type ON sector_raw_data(data_type)
        ''')
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_data_version ON sector_raw_data(data_version)
        ''')
        
        # 板块新闻数据表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sector_news_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_date TEXT NOT NULL,
            title TEXT,
            content TEXT,
            source TEXT,
            url TEXT,
            related_sectors TEXT,
            sentiment_score REAL,
            importance_score REAL,
            data_version INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # AI分析报告表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sector_analysis_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_date TEXT NOT NULL,
            data_date_range TEXT,
            analysis_content TEXT,
            recommended_sectors TEXT,
            summary TEXT,
            confidence_score REAL,
            risk_level TEXT,
            investment_horizon TEXT,
            market_outlook TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 板块追踪表（记录推荐板块的后续表现）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sector_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER,
            sector_code TEXT NOT NULL,
            sector_name TEXT,
            recommended_date TEXT,
            recommended_price REAL,
            target_price REAL,
            stop_loss_price REAL,
            current_price REAL,
            profit_loss_pct REAL,
            status TEXT,
            notes TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (analysis_id) REFERENCES sector_analysis_reports (id)
        )
        ''')
        
        # 数据版本管理表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_type TEXT NOT NULL,
            data_date TEXT NOT NULL,
            version INTEGER NOT NULL,
            status TEXT DEFAULT 'active',
            fetch_success BOOLEAN DEFAULT 1,
            error_message TEXT,
            record_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(data_type, data_date, version)
        )
        ''')
        
        conn.commit()
        conn.close()
        
        self.logger.info("[智策板块] 数据库初始化完成")
    
    def save_raw_data(self, data_date, data_type, data_df, version=None):
        """
        保存原始数据
        
        Args:
            data_date: 数据日期
            data_type: 数据类型 (sector_data, news_data等)
            data_df: 数据DataFrame
            version: 数据版本号，如果为None则自动生成
            
        Returns:
            int: 数据版本号
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 获取或生成版本号
            if version is None:
                cursor.execute('''
                SELECT COALESCE(MAX(version), 0) + 1 
                FROM data_versions 
                WHERE data_type = ? AND data_date = ?
                ''', (data_type, data_date))
                version = cursor.fetchone()[0]
            
            # 保存数据
            if data_type == 'sector_data':
                self._save_sector_data(cursor, data_date, data_df, version)
            elif data_type == 'news_data':
                self._save_news_data(cursor, data_date, data_df, version)
            
            # 记录版本信息
            cursor.execute('''
            INSERT OR REPLACE INTO data_versions 
            (data_type, data_date, version, status, fetch_success, record_count)
            VALUES (?, ?, ?, 'active', 1, ?)
            ''', (data_type, data_date, version, len(data_df)))
            
            conn.commit()
            self.logger.info(f"[智策板块] 保存{data_type}数据成功 (日期: {data_date}, 版本: {version}, 记录数: {len(data_df)})")
            return version
            
        except Exception as e:
            conn.rollback()
            # 记录失败版本
            cursor.execute('''
            INSERT OR REPLACE INTO data_versions 
            (data_type, data_date, version, status, fetch_success, error_message, record_count)
            VALUES (?, ?, ?, 'failed', 0, ?, 0)
            ''', (data_type, data_date, version or 1, str(e)))
            conn.commit()
            self.logger.error(f"[智策板块] 保存{data_type}数据失败: {e}")
            raise
        finally:
            conn.close()
    
    def _save_sector_data(self, cursor, data_date, data_df, version):
        """保存板块数据"""
        for _, row in data_df.iterrows():
            cursor.execute('''
            INSERT OR REPLACE INTO sector_raw_data 
            (data_date, sector_code, sector_name, price, change_pct, volume, 
             turnover, market_cap, pe_ratio, pb_ratio, data_type, data_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'sector_data', ?)
            ''', (
                data_date,
                row.get('sector_code', ''),
                row.get('sector_name', ''),
                row.get('price', 0),
                row.get('change_pct', 0),
                row.get('volume', 0),
                row.get('turnover', 0),
                row.get('market_cap', 0),
                row.get('pe_ratio', 0),
                row.get('pb_ratio', 0),
                version
            ))
    
    def _save_news_data(self, cursor, data_date, data_df, version):
        """保存新闻数据"""
        for _, row in data_df.iterrows():
            cursor.execute('''
            INSERT OR REPLACE INTO sector_news_data 
            (news_date, title, content, source, url, related_sectors, 
             sentiment_score, importance_score, data_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data_date,
                row.get('title', ''),
                row.get('content', ''),
                row.get('source', ''),
                row.get('url', ''),
                json.dumps(row.get('related_sectors', []), ensure_ascii=False),
                row.get('sentiment_score', 0),
                row.get('importance_score', 0),
                version
            ))
    
    def get_latest_data(self, data_type, data_date=None):
        """
        获取最新的成功数据
        
        Args:
            data_type: 数据类型
            data_date: 指定日期，如果为None则获取最新日期的数据
            
        Returns:
            pd.DataFrame: 数据DataFrame
        """
        conn = self.get_connection()
        
        try:
            # 获取最新成功的数据版本
            if data_date:
                query = '''
                SELECT version FROM data_versions 
                WHERE data_type = ? AND data_date = ? AND fetch_success = 1
                ORDER BY version DESC LIMIT 1
                '''
                params = [data_type, data_date]
            else:
                query = '''
                SELECT data_date, version FROM data_versions 
                WHERE data_type = ? AND fetch_success = 1
                ORDER BY data_date DESC, version DESC LIMIT 1
                '''
                params = [data_type]
            
            version_df = pd.read_sql_query(query, conn, params=params)
            
            if version_df.empty:
                self.logger.warning(f"[智策板块] 未找到{data_type}的成功数据")
                return pd.DataFrame()
            
            if data_date is None:
                data_date = version_df.iloc[0]['data_date']
            version = version_df.iloc[0]['version']
            
            # 获取具体数据
            if data_type == 'sector_data':
                data_query = '''
                SELECT * FROM sector_raw_data 
                WHERE data_date = ? AND data_version = ?
                ORDER BY sector_code
                '''
            elif data_type == 'news_data':
                data_query = '''
                SELECT * FROM sector_news_data 
                WHERE news_date = ? AND data_version = ?
                ORDER BY importance_score DESC
                '''
            else:
                return pd.DataFrame()
            
            data_df = pd.read_sql_query(data_query, conn, params=[data_date, version])
            self.logger.info(f"[智策板块] 获取{data_type}数据成功 (日期: {data_date}, 版本: {version}, 记录数: {len(data_df)})")
            return data_df
            
        except Exception as e:
            self.logger.error(f"[智策板块] 获取{data_type}数据失败: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def save_analysis_report(self, data_date_range, analysis_content, 
                           recommended_sectors, summary, confidence_score=None,
                           risk_level=None, investment_horizon=None, market_outlook=None):
        """
        保存AI分析报告
        
        Args:
            data_date_range: 数据日期范围
            analysis_content: 分析内容（JSON字符串或字典）
            recommended_sectors: 推荐板块列表
            summary: 摘要
            confidence_score: 置信度分数
            risk_level: 风险等级
            investment_horizon: 投资周期
            market_outlook: 市场展望
            
        Returns:
            int: 报告ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 如果传入的是字典，转换为JSON字符串
        if isinstance(analysis_content, dict):
            analysis_content = json.dumps(analysis_content, ensure_ascii=False, indent=2)
        
        cursor.execute('''
        INSERT INTO sector_analysis_reports 
        (analysis_date, data_date_range, analysis_content, recommended_sectors, 
         summary, confidence_score, risk_level, investment_horizon, market_outlook)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            data_date_range,
            analysis_content,
            json.dumps(recommended_sectors, ensure_ascii=False),
            summary,
            confidence_score,
            risk_level,
            investment_horizon,
            market_outlook
        ))
        
        report_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"[智策板块] 分析报告已保存 (ID: {report_id})")
        return report_id
    
    def get_analysis_reports(self, limit=10):
        """
        获取历史分析报告
        
        Args:
            limit: 返回数量
            
        Returns:
            pd.DataFrame: 报告列表
        """
        conn = self.get_connection()
        
        query = '''
        SELECT * FROM sector_analysis_reports
        ORDER BY created_at DESC
        LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=[limit])
        conn.close()
        
        return df
    
    def get_analysis_report(self, report_id):
        """
        获取单个分析报告详情
        
        Args:
            report_id: 报告ID
            
        Returns:
            dict: 报告详情
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM sector_analysis_reports WHERE id = ?
        ''', (report_id,))
        
        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        conn.close()
        
        if row:
            report = dict(zip(columns, row))
            
            # 解析JSON字段
            try:
                if report.get('analysis_content'):
                    report['analysis_content_parsed'] = json.loads(report['analysis_content'])
                if report.get('recommended_sectors'):
                    report['recommended_sectors_parsed'] = json.loads(report['recommended_sectors'])
            except json.JSONDecodeError as e:
                self.logger.warning(f"[智策板块] JSON解析失败: {e}")
            
            return report
        
        return None
    
    def delete_analysis_report(self, report_id):
        """
        删除分析报告
        
        Args:
            report_id: 报告ID
            
        Returns:
            bool: 删除是否成功
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 删除相关的追踪记录
            cursor.execute('DELETE FROM sector_tracking WHERE analysis_id = ?', (report_id,))
            
            # 删除报告
            cursor.execute('DELETE FROM sector_analysis_reports WHERE id = ?', (report_id,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                self.logger.info(f"[智策板块] 报告删除成功 (ID: {report_id})")
                return True
            else:
                self.logger.warning(f"[智策板块] 未找到要删除的报告 (ID: {report_id})")
                return False
                
        except Exception as e:
            conn.rollback()
            self.logger.error(f"[智策板块] 删除报告失败: {e}")
            return False
        finally:
            conn.close()
    
    def get_data_versions(self, data_type, limit=10):
        """
        获取数据版本历史
        
        Args:
            data_type: 数据类型
            limit: 返回数量
            
        Returns:
            pd.DataFrame: 版本历史
        """
        conn = self.get_connection()
        
        query = '''
        SELECT * FROM data_versions 
        WHERE data_type = ?
        ORDER BY data_date DESC, version DESC
        LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=[data_type, limit])
        conn.close()
        
        return df
    
    def save_sector_raw_data(self, data_date, data_type, data_df):
        """
        保存板块原始数据
        
        Args:
            data_date: 数据日期
            data_type: 数据类型 ('industry', 'concept', 'fund_flow', 'market_overview', 'north_fund', 'news')
            data_df: 数据DataFrame
        """
        # 兼容不同数据结构的空值判断
        is_empty = False
        if data_df is None:
            is_empty = True
        elif hasattr(data_df, 'empty'):
            is_empty = data_df.empty
        elif isinstance(data_df, (list, tuple, set, dict)):
            is_empty = len(data_df) == 0
        if is_empty:
            self.logger.warning(f"[智策板块] {data_type}数据为空，跳过保存")
            return
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 获取下一个版本号
            version = self._get_next_version(data_date, data_type)
            
            # 根据数据类型保存数据
            if data_type in ['industry', 'concept']:
                self._save_sector_data_raw(cursor, data_date, data_df, data_type, version)
            elif data_type == 'fund_flow':
                self._save_fund_flow_data(cursor, data_date, data_df, version)
            elif data_type == 'market_overview':
                self._save_market_overview_data(cursor, data_date, data_df, version)
            elif data_type == 'north_fund':
                self._save_north_fund_data(cursor, data_date, data_df, version)
            elif data_type == 'news':
                self._save_news_data_raw(cursor, data_date, data_df, version)
            
            # 记录版本信息
            cursor.execute('''
            INSERT OR REPLACE INTO data_versions 
            (data_date, data_type, version, fetch_success, record_count)
            VALUES (?, ?, ?, 1, ?)
            ''', (data_date, data_type, version, len(data_df)))
            
            conn.commit()
            self.logger.info(f"[智策板块] {data_type}数据保存成功 (日期: {data_date}, 版本: {version}, 记录数: {len(data_df)})")
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"[智策板块] 保存{data_type}数据失败: {e}")
            raise
        finally:
            conn.close()
    
    def _save_sector_data_raw(self, cursor, data_date, data_df, data_type, version):
        """保存板块原始数据"""
        for _, row in data_df.iterrows():
            cursor.execute('''
            INSERT OR REPLACE INTO sector_raw_data 
            (data_date, sector_code, sector_name, price, change_pct, volume, 
             turnover, market_cap, pe_ratio, pb_ratio, data_type, data_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data_date,
                str(row.get('板块代码', row.get('sector_code', ''))),
                str(row.get('板块名称', row.get('sector_name', ''))),
                float(row.get('最新价', row.get('price', 0))) if pd.notna(row.get('最新价', row.get('price', 0))) else 0,
                float(row.get('涨跌幅', row.get('change_pct', 0))) if pd.notna(row.get('涨跌幅', row.get('change_pct', 0))) else 0,
                float(row.get('成交量', row.get('volume', 0))) if pd.notna(row.get('成交量', row.get('volume', 0))) else 0,
                float(row.get('成交额', row.get('turnover', 0))) if pd.notna(row.get('成交额', row.get('turnover', 0))) else 0,
                float(row.get('总市值', row.get('market_cap', 0))) if pd.notna(row.get('总市值', row.get('market_cap', 0))) else 0,
                float(row.get('市盈率', row.get('pe_ratio', 0))) if pd.notna(row.get('市盈率', row.get('pe_ratio', 0))) else 0,
                float(row.get('市净率', row.get('pb_ratio', 0))) if pd.notna(row.get('市净率', row.get('pb_ratio', 0))) else 0,
                data_type,
                version
            ))
    
    def _save_fund_flow_data(self, cursor, data_date, data_df, version):
        """保存资金流向数据"""
        for _, row in data_df.iterrows():
            cursor.execute('''
            INSERT OR REPLACE INTO sector_raw_data 
            (data_date, sector_code, sector_name, price, change_pct, volume, 
             turnover, market_cap, pe_ratio, pb_ratio, data_type, data_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'fund_flow', ?)
            ''', (
                data_date,
                str(row.get('行业', '')),
                str(row.get('行业', '')),
                float(row.get('主力净流入-净额', 0)) if pd.notna(row.get('主力净流入-净额', 0)) else 0,
                float(row.get('主力净流入-净占比', 0)) if pd.notna(row.get('主力净流入-净占比', 0)) else 0,
                float(row.get('超大单净流入-净额', 0)) if pd.notna(row.get('超大单净流入-净额', 0)) else 0,
                float(row.get('超大单净流入-净占比', 0)) if pd.notna(row.get('超大单净流入-净占比', 0)) else 0,
                float(row.get('大单净流入-净额', 0)) if pd.notna(row.get('大单净流入-净额', 0)) else 0,
                float(row.get('大单净流入-净占比', 0)) if pd.notna(row.get('大单净流入-净占比', 0)) else 0,
                0,
                version
            ))
    
    def _save_market_overview_data(self, cursor, data_date, data_df, version):
        """保存市场概况数据"""
        for _, row in data_df.iterrows():
            cursor.execute('''
            INSERT OR REPLACE INTO sector_raw_data 
            (data_date, sector_code, sector_name, price, change_pct, volume, 
             turnover, market_cap, pe_ratio, pb_ratio, data_type, data_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'market_overview', ?)
            ''', (
                data_date,
                str(row.get('名称', '')),
                str(row.get('名称', '')),
                float(row.get('最新价', 0)) if pd.notna(row.get('最新价', 0)) else 0,
                float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅', 0)) else 0,
                float(row.get('成交量', 0)) if pd.notna(row.get('成交量', 0)) else 0,
                float(row.get('成交额', 0)) if pd.notna(row.get('成交额', 0)) else 0,
                0, 0, 0,
                version
            ))
    
    def _save_north_fund_data(self, cursor, data_date, data_df, version):
        """保存北向资金数据"""
        for _, row in data_df.iterrows():
            cursor.execute('''
            INSERT OR REPLACE INTO sector_raw_data 
            (data_date, sector_code, sector_name, price, change_pct, volume, 
             turnover, market_cap, pe_ratio, pb_ratio, data_type, data_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'north_fund', ?)
            ''', (
                data_date,
                str(row.get('代码', '')),
                str(row.get('名称', '')),
                float(row.get('收盘价', 0)) if pd.notna(row.get('收盘价', 0)) else 0,
                float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅', 0)) else 0,
                float(row.get('持股数量', 0)) if pd.notna(row.get('持股数量', 0)) else 0,
                float(row.get('持股市值', 0)) if pd.notna(row.get('持股市值', 0)) else 0,
                float(row.get('持股变化', 0)) if pd.notna(row.get('持股变化', 0)) else 0,
                0, 0,
                version
            ))
    
    def _save_news_data_raw(self, cursor, data_date, data_df, version):
        """保存新闻数据"""
        for _, row in data_df.iterrows():
            cursor.execute('''
            INSERT OR REPLACE INTO sector_news_data 
            (news_date, title, content, source, url, related_sectors, 
             sentiment_score, importance_score, data_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data_date,
                str(row.get('新闻标题', row.get('title', ''))),
                str(row.get('新闻内容', row.get('content', ''))),
                str(row.get('新闻来源', row.get('source', ''))),
                str(row.get('新闻链接', row.get('url', ''))),
                json.dumps([], ensure_ascii=False),  # 暂时为空
                0,  # 暂时为0
                0,  # 暂时为0
                version
            ))

    def cleanup_old_data(self, data_type, keep_days=30):
        """
        清理旧数据，保留指定天数的数据
        
        Args:
            data_type: 数据类型
            keep_days: 保留天数
            
        Returns:
            int: 删除的记录数
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cutoff_date = (datetime.now() - pd.Timedelta(days=keep_days)).strftime('%Y-%m-%d')
            
            if data_type == 'sector_data':
                cursor.execute('''
                DELETE FROM sector_raw_data 
                WHERE data_date < ?
                ''', (cutoff_date,))
            elif data_type == 'news_data':
                cursor.execute('''
                DELETE FROM sector_news_data 
                WHERE news_date < ?
                ''', (cutoff_date,))
            
            deleted_count = cursor.rowcount
            
            # 同时清理版本记录
            cursor.execute('''
            DELETE FROM data_versions 
            WHERE data_type = ? AND data_date < ?
            ''', (data_type, cutoff_date))
            
            conn.commit()
            self.logger.info(f"[智策板块] 清理{data_type}旧数据完成，删除{deleted_count}条记录")
            return deleted_count
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"[智策板块] 清理{data_type}旧数据失败: {e}")
            return 0
        finally:
            conn.close()

    # =====================
    # 缓存与最近数据读取接口
    # =====================
    def save_news_data(self, news_list, news_date, source="akshare"):
        """
        保存新闻列表（字典列表）到数据库，用于非DataFrame场景
        Args:
            news_list: [{title, content, url, related_sectors, sentiment_score, importance_score}]
            news_date: 新闻日期字符串
            source: 新闻来源
        """
        if not news_list:
            self.logger.warning("[智策板块] 新闻列表为空，跳过保存")
            return 0

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 版本号按日期累加
            version = self._get_next_version(news_date, 'news')
            inserted = 0
            for item in news_list:
                cursor.execute('''
                INSERT OR REPLACE INTO sector_news_data 
                (news_date, title, content, source, url, related_sectors, 
                 sentiment_score, importance_score, data_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(news_date),
                    str(item.get('title', '')),
                    str(item.get('content', '')),
                    str(item.get('source', source)),
                    str(item.get('url', '')),
                    json.dumps(item.get('related_sectors', []), ensure_ascii=False),
                    float(item.get('sentiment_score', 0) or 0),
                    float(item.get('importance_score', 0) or 0),
                    version
                ))
                inserted += 1

            # 记录版本信息
            cursor.execute('''
            INSERT OR REPLACE INTO data_versions 
            (data_date, data_type, version, fetch_success, record_count)
            VALUES (?, ?, ?, 1, ?)
            ''', (str(news_date), 'news', version, inserted))

            conn.commit()
            self.logger.info(f"[智策板块] 保存新闻数据成功 (日期: {news_date}, 版本: {version}, 记录数: {inserted})")
            return inserted
        except Exception as e:
            conn.rollback()
            self.logger.error(f"[智策板块] 保存新闻数据失败: {e}")
            return 0
        finally:
            conn.close()

    def _get_next_version(self, data_date: str, data_type: str) -> int:
        """获取指定日期与类型的下一个版本号"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
            SELECT COALESCE(MAX(version), 0) + 1 FROM data_versions 
            WHERE data_type = ? AND data_date = ?
            ''', (data_type, data_date))
            next_version = cursor.fetchone()[0] or 1
            return int(next_version)
        finally:
            conn.close()

    def get_latest_raw_data(self, key: str, within_hours: int = 24):
        """
        获取最近within_hours小时内的原始数据并组装为分析所需结构
        Args:
            key: 'sectors' | 'concepts' | 'fund_flow' | 'market_overview' | 'north_flow'
            within_hours: 有效缓存时长（小时）
        Returns:
            dict 或 None
        """
        # 将key映射到内部data_type
        key_map = {
            'sectors': 'industry',
            'concepts': 'concept',
            'fund_flow': 'fund_flow',
            'market_overview': 'market_overview',
            'north_flow': 'north_fund'
        }
        data_type = key_map.get(key)
        if not data_type:
            return None

        conn = self.get_connection()
        try:
            cutoff = (pd.Timestamp.now() - pd.Timedelta(hours=within_hours)).strftime('%Y-%m-%d %H:%M:%S')
            # 选取最近版本的数据（同一天可能有多版本）
            # 先查最近有效版本记录
            version_df = pd.read_sql_query('''
                SELECT data_date, version FROM data_versions
                WHERE data_type = ? AND fetch_success = 1 
                AND datetime(created_at) >= datetime(?)
                ORDER BY data_date DESC, version DESC LIMIT 1
            ''', conn, params=[data_type, cutoff])

            if version_df.empty:
                return None

            data_date = version_df.iloc[0]['data_date']
            version = int(version_df.iloc[0]['version'])

            # 读取具体行
            raw_df = pd.read_sql_query('''
                SELECT * FROM sector_raw_data 
                WHERE data_type = ? AND data_date = ? AND data_version = ?
            ''', conn, params=[data_type, data_date, version])

            if raw_df.empty:
                return None

            # 组装成预期结构
            if key in ['sectors', 'concepts']:
                result = {}
                for _, row in raw_df.iterrows():
                    name = str(row.get('sector_name', ''))
                    result[name] = {
                        'name': name,
                        'change_pct': float(row.get('change_pct', 0) or 0),
                        'price': float(row.get('price', 0) or 0),
                        'volume': float(row.get('volume', 0) or 0),
                        'turnover': float(row.get('turnover', 0) or 0),
                        'market_cap': float(row.get('market_cap', 0) or 0),
                        'pe_ratio': float(row.get('pe_ratio', 0) or 0),
                        'pb_ratio': float(row.get('pb_ratio', 0) or 0),
                    }
                return {
                    'data_date': data_date,
                    'data_content': result
                }

            if key == 'fund_flow':
                today = []
                for _, row in raw_df.iterrows():
                    name = str(row.get('sector_name', ''))
                    today.append({
                        'sector': name,
                        'main_net_inflow': float(row.get('price', 0) or 0),  # 映射自主力净额
                        'main_net_inflow_pct': float(row.get('change_pct', 0) or 0),
                        'super_large_net_inflow': float(row.get('volume', 0) or 0),
                        'super_large_net_inflow_pct': float(row.get('turnover', 0) or 0),
                        'large_net_inflow': float(row.get('market_cap', 0) or 0),
                        'large_net_inflow_pct': float(row.get('pe_ratio', 0) or 0),
                        'medium_net_inflow': 0,
                        'small_net_inflow': 0
                    })
                return {
                    'data_date': data_date,
                    'data_content': {
                        'today': today
                    }
                }

            if key == 'market_overview':
                overview = {}
                for _, row in raw_df.iterrows():
                    name = str(row.get('sector_name', ''))
                    entry = {
                        'price': float(row.get('price', 0) or 0),
                        'change_pct': float(row.get('change_pct', 0) or 0),
                        'turnover': float(row.get('turnover', 0) or 0),
                        'volume': float(row.get('volume', 0) or 0)
                    }
                    # 简单映射：名称包含上证/深证/创业板
                    if '上证' in name or '沪指' in name or 'SH' in name:
                        overview['sh_index'] = entry
                    elif '深证' in name or 'SZ' in name:
                        overview['sz_index'] = entry
                    elif '创业' in name or 'CYB' in name:
                        overview['cyb_index'] = entry
                return {
                    'data_date': data_date,
                    'data_content': overview
                }

            if key == 'north_flow':
                # 北向资金结构差异较大，返回最简结构用于提示
                total_value = float(raw_df['turnover'].sum()) if not raw_df.empty else 0
                return {
                    'data_date': data_date,
                    'data_content': {
                        'north_total_amount': total_value,
                        'history': []
                    }
                }

            return None
        except Exception as e:
            self.logger.error(f"[智策板块] 获取最近原始数据失败: {e}")
            return None
        finally:
            conn.close()

    def get_latest_news_data(self, within_hours: int = 24):
        """获取最近within_hours小时的新闻列表"""
        conn = self.get_connection()
        try:
            cutoff = (pd.Timestamp.now() - pd.Timedelta(hours=within_hours)).strftime('%Y-%m-%d %H:%M:%S')
            df = pd.read_sql_query('''
                SELECT * FROM sector_news_data 
                WHERE datetime(created_at) >= datetime(?)
                ORDER BY importance_score DESC, created_at DESC
            ''', conn, params=[cutoff])
            if df.empty:
                return None
            news = []
            for _, row in df.iterrows():
                try:
                    related = json.loads(row.get('related_sectors', '[]'))
                except Exception:
                    related = []
                news.append({
                    'title': row.get('title', ''),
                    'content': row.get('content', ''),
                    'source': row.get('source', ''),
                    'url': row.get('url', ''),
                    'related_sectors': related,
                    'sentiment_score': float(row.get('sentiment_score', 0) or 0),
                    'importance_score': float(row.get('importance_score', 0) or 0),
                    'news_date': row.get('news_date', '')
                })
            return {
                'data_date': df.iloc[0]['news_date'] if not df.empty else None,
                'data_content': news
            }
        except Exception as e:
            self.logger.error(f"[智策板块] 获取最近新闻数据失败: {e}")
            return None
        finally:
            conn.close()