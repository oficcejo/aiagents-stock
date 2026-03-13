#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主力选股批量分析历史记录数据库模块
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import pandas as pd

class MainForceBatchDatabase:
    """主力选股批量分析历史数据库管理类"""
    
    def __init__(self, db_path: str = "data/main_force_batch.db"):
        """初始化数据库连接"""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 批量分析历史记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS batch_analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_date TEXT NOT NULL,
                batch_count INTEGER NOT NULL,
                analysis_mode TEXT NOT NULL,
                success_count INTEGER NOT NULL,
                failed_count INTEGER NOT NULL,
                total_time REAL NOT NULL,
                results_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_analysis_date 
            ON batch_analysis_history(analysis_date)
        ''')
        
        conn.commit()
        conn.close()
    
    def _clean_results_for_json(self, results: List[Dict]) -> List[Dict]:
        """
        清理结果数据，确保可以JSON序列化
        
        Args:
            results: 原始结果列表
            
        Returns:
            清理后的结果列表
        """
        def clean_value(value):
            """递归清理值"""
            # 处理None
            if value is None:
                return None
            # 处理DataFrame - 只保留前100行避免数据过大
            elif isinstance(value, pd.DataFrame):
                if len(value) > 100:
                    return value.head(100).to_dict('records')
                return value.to_dict('records')
            # 处理Series
            elif isinstance(value, pd.Series):
                return value.to_dict()
            # 处理字典 - 递归清理
            elif isinstance(value, dict):
                return {k: clean_value(v) for k, v in value.items()}
            # 处理列表 - 递归清理
            elif isinstance(value, (list, tuple)):
                return [clean_value(v) for v in value]
            # 处理基本类型
            elif isinstance(value, (str, int, float, bool)):
                return value
            # 其他对象转为字符串
            else:
                try:
                    return str(value)
                except:
                    return "无法序列化"
        
        cleaned = []
        for result in results:
            try:
                cleaned_result = {}
                for key, value in result.items():
                    cleaned_result[key] = clean_value(value)
                cleaned.append(cleaned_result)
            except Exception as e:
                # 如果单个结果清理失败，记录错误
                cleaned.append({
                    "error": f"清理失败: {str(e)}",
                    "original_keys": list(result.keys()) if isinstance(result, dict) else []
                })
        return cleaned
    
    def save_batch_analysis(
        self,
        batch_count: int,
        analysis_mode: str,
        success_count: int,
        failed_count: int,
        total_time: float,
        results: List[Dict]
    ) -> int:
        """
        保存批量分析结果
        
        Args:
            batch_count: 分析股票数量
            analysis_mode: 分析模式（sequential/parallel）
            success_count: 成功数量
            failed_count: 失败数量
            total_time: 总耗时（秒）
            results: 分析结果列表
            
        Returns:
            记录ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        analysis_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 清理结果数据，确保可以JSON序列化
        cleaned_results = self._clean_results_for_json(results)
        results_json = json.dumps(cleaned_results, ensure_ascii=False, default=str)
        
        cursor.execute('''
            INSERT INTO batch_analysis_history 
            (analysis_date, batch_count, analysis_mode, success_count, failed_count, total_time, results_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (analysis_date, batch_count, analysis_mode, success_count, failed_count, total_time, results_json))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return record_id
    
    def get_all_history(self, limit: int = 50) -> List[Dict]:
        """
        获取所有历史记录
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            历史记录列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, analysis_date, batch_count, analysis_mode, 
                   success_count, failed_count, total_time, results_json, created_at
            FROM batch_analysis_history
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            try:
                results = json.loads(row[7])
            except:
                results = []
            
            history.append({
                'id': row[0],
                'analysis_date': row[1],
                'batch_count': row[2],
                'analysis_mode': row[3],
                'success_count': row[4],
                'failed_count': row[5],
                'total_time': row[6],
                'results': results,
                'created_at': row[8]
            })
        
        return history
    
    def get_record_by_id(self, record_id: int) -> Optional[Dict]:
        """
        根据ID获取单条记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            记录详情
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, analysis_date, batch_count, analysis_mode, 
                   success_count, failed_count, total_time, results_json, created_at
            FROM batch_analysis_history
            WHERE id = ?
        ''', (record_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        try:
            results = json.loads(row[7])
        except:
            results = []
        
        return {
            'id': row[0],
            'analysis_date': row[1],
            'batch_count': row[2],
            'analysis_mode': row[3],
            'success_count': row[4],
            'failed_count': row[5],
            'total_time': row[6],
            'results': results,
            'created_at': row[8]
        }
    
    def delete_record(self, record_id: int) -> bool:
        """
        删除记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            是否删除成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM batch_analysis_history WHERE id = ?', (record_id,))
        
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected_rows > 0
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            统计数据
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 总记录数
        cursor.execute('SELECT COUNT(*) FROM batch_analysis_history')
        total_records = cursor.fetchone()[0]
        
        # 总分析股票数
        cursor.execute('SELECT SUM(batch_count) FROM batch_analysis_history')
        total_stocks = cursor.fetchone()[0] or 0
        
        # 总成功数
        cursor.execute('SELECT SUM(success_count) FROM batch_analysis_history')
        total_success = cursor.fetchone()[0] or 0
        
        # 总失败数
        cursor.execute('SELECT SUM(failed_count) FROM batch_analysis_history')
        total_failed = cursor.fetchone()[0] or 0
        
        # 平均耗时
        cursor.execute('SELECT AVG(total_time) FROM batch_analysis_history')
        avg_time = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_records': total_records,
            'total_stocks_analyzed': total_stocks,
            'total_success': total_success,
            'total_failed': total_failed,
            'average_time': round(avg_time, 2),
            'success_rate': round(total_success / total_stocks * 100, 2) if total_stocks > 0 else 0
        }


# 全局数据库实例
batch_db = MainForceBatchDatabase()

