# 数据库检查报告

## 📊 检查结果摘要

检查了 `data` 目录下的 9 个数据库文件，发现以下问题：

### ⚠️ 发现的问题

#### 1. **main_force_batch1.db** (6.8 MB) - 文件大但无数据

**问题描述**：
- 文件大小：6.8 MB
- `batch_analysis_history` 表：0 条记录
- `sqlite_sequence` 表：序列值 = 3（说明之前有3条记录被删除）

**原因分析**：
1. **文件名不匹配**：代码期望文件名是 `main_force_batch.db`，但实际存在的是 `main_force_batch1.db`
2. **数据被删除**：从 `sqlite_sequence` 可以看出之前有3条记录，但后来被删除了
3. **文件未收缩**：SQLite 在删除数据后不会自动收缩文件大小，所以文件仍然保持 6.8MB 的大小
4. **可能的数据迁移**：可能数据被迁移到了其他位置，或者被清理了

**影响**：
- 代码无法找到正确的数据库文件（代码查找 `main_force_batch.db`，但实际是 `main_force_batch1.db`）
- 浪费存储空间（6.8MB 的空文件）

**建议解决方案**：
1. 检查是否有数据需要恢复
2. 如果有 `main_force_batch.db` 文件，确认哪个是正确的
3. 如果 `main_force_batch1.db` 确实没有用，可以执行 `VACUUM` 收缩文件或删除
4. 确保代码使用的文件名与实际的数据库文件名一致

#### 2. **profit_growth_monitor.db** (20 KB) - 文件有大小但无数据

**问题描述**：
- 文件大小：20 KB
- 所有表：0 条记录（`monitored_stocks`, `sqlite_sequence`, `sell_alerts`）

**原因分析**：
- 这是正常的！表结构已创建，但还没有添加监控数据
- 20KB 是 SQLite 创建表和索引所需的最小空间

**影响**：
- 无影响，这是正常的初始化状态

**建议**：
- 无需处理，这是正常的空数据库状态

---

## 📋 所有数据库文件状态

| 文件名 | 大小 | 状态 | 总记录数 | 说明 |
|--------|------|------|----------|------|
| longhubang.db | 968 KB | ✅ 正常 | 1214 | 有数据 |
| low_price_bull_monitor.db | 20 KB | ✅ 正常 | 13 | 有数据 |
| **main_force_batch1.db** | **6.8 MB** | **⚠️ 文件大但无数据** | **1** | **只有 sqlite_sequence，主表为空** |
| portfolio_stocks.db | 28 KB | ✅ 正常 | 32 | 有数据 |
| **profit_growth_monitor.db** | **20 KB** | **⚠️ 文件存在但无数据** | **0** | **表已创建但无数据（正常）** |
| sector_strategy.db | 328 KB | ✅ 正常 | 544 | 有数据 |
| smart_monitor.db | 316 KB | ✅ 正常 | 158 | 有数据 |
| stock_analysis.db | 24.8 MB | ✅ 正常 | 299 | 有数据 |
| stock_monitor.db | 20 KB | ✅ 正常 | 21 | 有数据 |

---

## 🔧 建议的操作

### 对于 main_force_batch1.db

1. **检查是否有 `main_force_batch.db` 文件**：
   ```bash
   ls -lh data/main_force_batch*.db
   ```

2. **如果有 `main_force_batch.db`，检查其内容**：
   ```python
   import sqlite3
   conn = sqlite3.connect('data/main_force_batch.db')
   cursor = conn.cursor()
   cursor.execute('SELECT COUNT(*) FROM batch_analysis_history;')
   print(f'记录数: {cursor.fetchone()[0]}')
   conn.close()
   ```

3. **如果需要收缩 `main_force_batch1.db`**：
   ```sql
   VACUUM;
   ```
   这将把文件从 6.8MB 缩小到约 20KB

4. **如果需要删除空文件**：
   ```bash
   rm data/main_force_batch1.db
   ```
   ⚠️ 注意：删除前请确认没有重要数据

### 对于 profit_growth_monitor.db

- **无需处理**，这是正常的空数据库状态
- 当用户添加监控股票时，会自动添加数据

---

## 📝 详细检查脚本

检查脚本已保存为 `check_databases.py`，可以随时运行：

```bash
python3 check_databases.py
```
