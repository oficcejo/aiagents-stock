import sqlite3
import json
from datetime import datetime
import os

class StockAnalysisDatabase:
    def __init__(self, db_path="data/stock_analysis.db"):
        """初始化数据库连接"""
        self.db_path = db_path
        # 确保数据库所在目录存在
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建分析记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                stock_name TEXT,
                analysis_date TEXT NOT NULL,
                period TEXT NOT NULL,
                stock_info TEXT,
                agents_results TEXT,
                discussion_result TEXT,
                final_decision TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_analysis(self, symbol, stock_name, period, stock_info, agents_results, discussion_result, final_decision):
        """保存分析记录到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 准备数据
        analysis_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        created_at = datetime.now().isoformat()
        
        # 将复杂对象转换为JSON字符串
        stock_info_json = json.dumps(stock_info, ensure_ascii=False, default=str)
        agents_results_json = json.dumps(agents_results, ensure_ascii=False, default=str)
        discussion_result_json = json.dumps(discussion_result, ensure_ascii=False, default=str)
        final_decision_json = json.dumps(final_decision, ensure_ascii=False, default=str)
        
        cursor.execute('''
            INSERT INTO analysis_records 
            (symbol, stock_name, analysis_date, period, stock_info, agents_results, discussion_result, final_decision, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (symbol, stock_name, analysis_date, period, stock_info_json, agents_results_json, discussion_result_json, final_decision_json, created_at))
        
        conn.commit()
        conn.close()
        
        return cursor.lastrowid
    
    def get_all_records(self):
        """获取所有分析记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, symbol, stock_name, analysis_date, period, final_decision, created_at
            FROM analysis_records 
            ORDER BY created_at DESC
        ''')
        
        records = cursor.fetchall()
        conn.close()
        
        result = []
        for record in records:
            # 解析final_decision获取评级
            final_decision = json.loads(record[5]) if record[5] else {}
            rating = final_decision.get('rating', '未知') if isinstance(final_decision, dict) else '未知'
            
            result.append({
                'id': record[0],
                'symbol': record[1],
                'stock_name': record[2],
                'analysis_date': record[3],
                'period': record[4],
                'rating': rating,
                'created_at': record[6]
            })
        
        return result
    
    def get_record_count(self):
        """获取记录总数"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM analysis_records')
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def get_record_by_id(self, record_id):
        """根据ID获取详细分析记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM analysis_records WHERE id = ?
        ''', (record_id,))
        
        record = cursor.fetchone()
        conn.close()
        
        if not record:
            return None
        
        # 解析JSON数据
        return {
            'id': record[0],
            'symbol': record[1],
            'stock_name': record[2],
            'analysis_date': record[3],
            'period': record[4],
            'stock_info': json.loads(record[5]) if record[5] else {},
            'agents_results': json.loads(record[6]) if record[6] else {},
            'discussion_result': json.loads(record[7]) if record[7] else {},
            'final_decision': json.loads(record[8]) if record[8] else {},
            'created_at': record[9]
        }
    
    def delete_record(self, record_id):
        """删除指定记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM analysis_records WHERE id = ?', (record_id,))
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0
    
    def get_record_count(self):
        """获取记录总数"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM analysis_records')
        count = cursor.fetchone()[0]
        conn.close()
        
        return count

# 全局数据库实例
db = StockAnalysisDatabase()