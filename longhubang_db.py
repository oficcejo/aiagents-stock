"""
智瞰龙虎数据库模块
用于存储龙虎榜历史数据和分析报告
"""

import sqlite3
from datetime import datetime
import json
import pandas as pd
import logging


class LonghubangDatabase:
    """龙虎榜数据库管理类"""
    
    def __init__(self, db_path='longhubang.db'):
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
        
        # 龙虎榜原始数据表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS longhubang_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            stock_code TEXT NOT NULL,
            stock_name TEXT,
            youzi_name TEXT,
            yingye_bu TEXT,
            list_type TEXT,
            buy_amount REAL,
            sell_amount REAL,
            net_inflow REAL,
            concepts TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, stock_code, youzi_name, yingye_bu)
        )
        ''')
        
        # 创建索引
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_date ON longhubang_records(date)
        ''')
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_stock_code ON longhubang_records(stock_code)
        ''')
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_youzi_name ON longhubang_records(youzi_name)
        ''')
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_net_inflow ON longhubang_records(net_inflow)
        ''')
        
        # AI分析报告表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS longhubang_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_date TEXT NOT NULL,
            data_date_range TEXT,
            analysis_content TEXT,
            recommended_stocks TEXT,
            summary TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 股票追踪表（记录推荐股票的后续表现）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER,
            stock_code TEXT NOT NULL,
            stock_name TEXT,
            recommended_date TEXT,
            recommended_price REAL,
            target_price REAL,
            stop_loss_price REAL,
            current_price REAL,
            profit_loss_pct REAL,
            status TEXT,
            notes TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(analysis_id) REFERENCES longhubang_analysis(id)
        )
        ''')
        
        conn.commit()
        conn.close()
        
        self.logger.info("[智瞰龙虎] 数据库初始化完成")
    
    def save_longhubang_data(self, data_list):
        """
        保存龙虎榜数据
        
        Args:
            data_list: 龙虎榜数据列表
            
        Returns:
            int: 成功保存的记录数
        """
        if not data_list:
            return 0
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        saved_count = 0
        
        for record in data_list:
            try:
                cursor.execute('''
                INSERT OR REPLACE INTO longhubang_records 
                (date, stock_code, stock_name, youzi_name, yingye_bu, list_type, 
                 buy_amount, sell_amount, net_inflow, concepts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record.get('rq') or record.get('日期'),
                    record.get('gpdm') or record.get('股票代码'),
                    record.get('gpmc') or record.get('股票名称'),
                    record.get('yzmc') or record.get('游资名称'),
                    record.get('yyb') or record.get('营业部'),
                    record.get('sblx') or record.get('榜单类型'),
                    float(record.get('mrje') or record.get('买入金额') or 0),
                    float(record.get('mcje') or record.get('卖出金额') or 0),
                    float(record.get('jlrje') or record.get('净流入金额') or 0),
                    record.get('gl') or record.get('概念')
                ))
                saved_count += 1
            except Exception as e:
                self.logger.exception(f"保存记录失败: {e}", exc_info=True)
                continue
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"[智瞰龙虎] 成功保存 {saved_count} 条龙虎榜记录")
        return saved_count
    
    def get_longhubang_data(self, start_date=None, end_date=None, stock_code=None):
        """
        查询龙虎榜数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            stock_code: 股票代码
            
        Returns:
            pd.DataFrame: 查询结果
        """
        conn = self.get_connection()
        
        query = "SELECT * FROM longhubang_records WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        if stock_code:
            query += " AND stock_code = ?"
            params.append(stock_code)
        
        query += " ORDER BY date DESC, net_inflow DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def get_top_youzi(self, start_date=None, end_date=None, limit=20):
        """
        获取活跃游资排名
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量
            
        Returns:
            pd.DataFrame: 游资排名
        """
        conn = self.get_connection()
        
        query = '''
        SELECT 
            youzi_name,
            COUNT(*) as trade_count,
            SUM(buy_amount) as total_buy,
            SUM(sell_amount) as total_sell,
            SUM(net_inflow) as total_net_inflow
        FROM longhubang_records
        WHERE 1=1
        '''
        
        params = []
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += '''
        GROUP BY youzi_name
        ORDER BY total_net_inflow DESC
        LIMIT ?
        '''
        params.append(limit)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def get_top_stocks(self, start_date=None, end_date=None, limit=20):
        """
        获取热门股票排名
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量
            
        Returns:
            pd.DataFrame: 股票排名
        """
        conn = self.get_connection()
        
        query = '''
        SELECT 
            stock_code,
            stock_name,
            COUNT(DISTINCT youzi_name) as youzi_count,
            SUM(buy_amount) as total_buy,
            SUM(sell_amount) as total_sell,
            SUM(net_inflow) as total_net_inflow,
            GROUP_CONCAT(DISTINCT concepts) as all_concepts
        FROM longhubang_records
        WHERE 1=1
        '''
        
        params = []
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += '''
        GROUP BY stock_code, stock_name
        ORDER BY total_net_inflow DESC
        LIMIT ?
        '''
        params.append(limit)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def save_analysis_report(self, data_date_range, analysis_content, 
                           recommended_stocks, summary, full_result=None):
        """
        保存AI分析报告（完整版）
        
        Args:
            data_date_range: 数据日期范围
            analysis_content: 分析内容（JSON字符串或字典）
            recommended_stocks: 推荐股票列表
            summary: 摘要
            full_result: 完整的分析结果字典（可选）
            
        Returns:
            int: 报告ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 如果传入的是字典，转换为JSON字符串
        if isinstance(analysis_content, dict):
            analysis_content = json.dumps(analysis_content, ensure_ascii=False, indent=2)
        
        cursor.execute('''
        INSERT INTO longhubang_analysis 
        (analysis_date, data_date_range, analysis_content, recommended_stocks, summary)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            data_date_range,
            analysis_content,
            json.dumps(recommended_stocks, ensure_ascii=False),
            summary
        ))
        
        report_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"[智瞰龙虎] 分析报告已保存 (ID: {report_id})")
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
        SELECT * FROM longhubang_analysis
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
        SELECT * FROM longhubang_analysis WHERE id = ?
        ''', (report_id,))
        
        row = cursor.fetchone()
        # 在关闭连接之前获取列名，避免关闭后访问游标属性报错
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        conn.close()
        
        if row:
            report = dict(zip(columns, row))
            
            # 解析JSON字段
            if report.get('recommended_stocks'):
                try:
                    report['recommended_stocks'] = json.loads(report['recommended_stocks'])
                except Exception as e:
                    self.logger.warning(f"推荐股票JSON解析失败: {e}")
            
            # 解析analysis_content字段
            if report.get('analysis_content'):
                try:
                    report['analysis_content_parsed'] = json.loads(report['analysis_content'])
                except json.JSONDecodeError as e:
                    # 如果不是JSON格式，保持原样
                    report['analysis_content_parsed'] = None
                    self.logger.debug(f"analysis_content字段不是有效JSON格式，将保持原始文本格式: {str(e)[:100]}")
                except Exception as e:
                    report['analysis_content_parsed'] = None
                    self.logger.warning(f"analysis_content字段解析时发生未知错误: {str(e)[:100]}")
            
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
            # 先删除相关的股票追踪记录
            cursor.execute('DELETE FROM stock_tracking WHERE analysis_id = ?', (report_id,))
            
            # 删除分析报告
            cursor.execute('DELETE FROM longhubang_analysis WHERE id = ?', (report_id,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                self.logger.info(f"[智瞰龙虎] 成功删除分析报告 (ID: {report_id})")
                return True
            else:
                self.logger.warning(f"[智瞰龙虎] 未找到要删除的分析报告 (ID: {report_id})")
                return False
                
        except Exception as e:
            self.logger.error(f"[智瞰龙虎] 删除分析报告失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def update_stock_tracking(self, analysis_id, stock_code, current_price, status, notes=None):
        """
        更新股票追踪信息
        
        Args:
            analysis_id: 分析报告ID
            stock_code: 股票代码
            current_price: 当前价格
            status: 状态
            notes: 备注
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE stock_tracking
        SET current_price = ?, status = ?, notes = ?, updated_at = ?
        WHERE analysis_id = ? AND stock_code = ?
        ''', (
            current_price,
            status,
            notes,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            analysis_id,
            stock_code
        ))
        
        conn.commit()
        conn.close()
    
    def get_statistics(self):
        """
        获取数据库统计信息
        
        Returns:
            dict: 统计信息
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # 总记录数
        cursor.execute('SELECT COUNT(*) FROM longhubang_records')
        stats['total_records'] = cursor.fetchone()[0]
        
        # 涉及股票数
        cursor.execute('SELECT COUNT(DISTINCT stock_code) FROM longhubang_records')
        stats['total_stocks'] = cursor.fetchone()[0]
        
        # 涉及游资数
        cursor.execute('SELECT COUNT(DISTINCT youzi_name) FROM longhubang_records')
        stats['total_youzi'] = cursor.fetchone()[0]
        
        # 分析报告数
        cursor.execute('SELECT COUNT(*) FROM longhubang_analysis')
        stats['total_reports'] = cursor.fetchone()[0]
        
        # 日期范围
        cursor.execute('SELECT MIN(date), MAX(date) FROM longhubang_records')
        date_range = cursor.fetchone()
        stats['date_range'] = {
            'start': date_range[0],
            'end': date_range[1]
        }
        
        conn.close()
        
        return stats


# 测试函数
if __name__ == "__main__":
    print("=" * 60)
    print("测试智瞰龙虎数据库模块")
    print("=" * 60)
    
    db = LonghubangDatabase('test_longhubang.db')
    
    # 测试数据
    test_data = [
        {
            'rq': '2023-03-22',
            'gpdm': '001337',
            'gpmc': '四川黄金',
            'yzmc': '92科比',
            'yyb': '兴业证券股份有限公司南京天元东路证券营业部',
            'sblx': '1',
            'mrje': 14470401,
            'mcje': 15080,
            'jlrje': 14455321,
            'gl': '贵金属,四川板块,昨日连板_含一字,昨日涨停_含一字,黄金概念,次新股'
        }
    ]
    
    # 测试保存
    db.save_longhubang_data(test_data)
    
    # 测试查询
    df = db.get_longhubang_data()
    print(f"\n查询到 {len(df)} 条记录")
    
    # 获取统计信息
    stats = db.get_statistics()
    print(f"\n数据库统计: {stats}")

