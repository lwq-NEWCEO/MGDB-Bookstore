import sqlite3
import os
import sys

# --- 配置路径 ---
# 假设此脚本运行在项目的根目录 (例如，在 'bookstore.MongoDB-main' 目录下)
# 原始大 book.db 文件的相对路径
original_db_relative_path = 'fe/data/book.db'
# 新创建的测试数据库的相对路径和名称
test_db_relative_path = 'fe/data/test_book.db'

script_current_dir = os.getcwd()
original_db_path = os.path.join(script_current_dir, original_db_relative_path)
test_db_path = os.path.join(script_current_dir, test_db_relative_path)
test_db_dir = os.path.dirname(test_db_path)

# --- 配置抽样大小 ---
ROWS_PER_TABLE = 100

print(f"当前脚本运行目录: {script_current_dir}")
print(f"预期原始数据库路径: {original_db_path}")
print(f"预期测试数据库路径: {test_db_path}")

os.makedirs(test_db_dir, exist_ok=True)

# !!! 新增：如果 test_book.db 存在，则先删除它 !!!
if os.path.exists(test_db_path):
    print(f"\n检测到旧的测试数据库文件 '{test_db_path}'，正在删除...")
    os.remove(test_db_path)
    print("旧文件已删除。")

if not os.path.exists(original_db_path):
    print(f"\n错误: 原始数据库文件 '{original_db_path}' 不存在。")
    print("请确认：")
    print("  1. 您已将原始的 3.6GB book.db 文件放置在正确的路径。")
    print("  2. 此脚本正在项目的根目录运行，以便正确解析相对路径。")
    sys.exit(1)

try:
    print(f"\n正在连接到原始数据库: '{original_db_path}'...")
    conn_orig = sqlite3.connect(original_db_path)
    cursor_orig = conn_orig.cursor()
    print("成功连接到原始数据库。")

    print(f"正在连接到/创建测试数据库: '{test_db_path}'...")
    conn_test = sqlite3.connect(test_db_path)
    cursor_test = conn_test.cursor()
    print("成功连接到/创建测试数据库。")

    print(f"\n开始从 '{original_db_path}' 提取数据到 '{test_db_path}'...")

    cursor_orig.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor_orig.fetchall()

    if not tables:
        print("警告: 原始数据库中没有找到任何表。请检查数据库文件是否为空或损坏。")

    for table_name_tuple in tables:
        table_name = table_name_tuple[0]
        print(f"\n--- 处理表: {table_name} ---")

        cursor_orig.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
        create_table_sql_result = cursor_orig.fetchone()
        if create_table_sql_result:
            create_table_sql = create_table_sql_result[0]
            # 在测试数据库中创建相同的表
            cursor_test.execute(create_table_sql) # 此处现在不会报错，因为旧文件已被删除
            print(f"  - 在测试数据库中创建了表 '{table_name}'。")
        else:
            print(f"  - 无法获取表 '{table_name}' 的 CREATE TABLE 语句，跳过创建。")
            continue

        cursor_orig.execute(f"SELECT * FROM '{table_name}' LIMIT {ROWS_PER_TABLE};")
        rows = cursor_orig.fetchall()

        if rows:
            cursor_orig.execute(f"PRAGMA table_info('{table_name}');")
            column_names = [col[1] for col in cursor_orig.fetchall()]
            placeholders = ', '.join(['?' for _ in column_names])

            insert_sql = f"INSERT INTO '{table_name}' VALUES ({placeholders});"
            cursor_test.executemany(insert_sql, rows)
            print(f"  - 已从表 '{table_name}' 插入 {len(rows)} 行数据。")
        else:
            print(f"  - 表 '{table_name}' 为空或没有足够的数据可供抽样，跳过插入。")

    conn_test.commit()
    print("\n测试数据库创建完成并提交。")

except sqlite3.Error as e:
    print(f"\n数据库操作错误: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n发生其他错误: {e}")
    sys.exit(1)
finally:
    if 'conn_orig' in locals() and conn_orig:
        conn_orig.close()
        print("原始数据库连接已关闭。")
    if 'conn_test' in locals() and conn_test:
        conn_test.close()
        print("测试数据库连接已关闭。")

if os.path.exists(test_db_path):
    file_size_mb = os.path.getsize(test_db_path) / (1024 * 1024)
    print(f"\n--- 恭喜！新生成的测试数据库文件 '{test_db_path}' 大小: {file_size_mb:.2f} MB ---")
    if file_size_mb > 90:
        print("\n警告: 生成的测试数据库文件大小超过 90MB。")
        print("这可能仍然太大，无法直接推送到 GitHub。")
        print("请考虑减小脚本中 'ROWS_PER_TABLE' 参数的值，并重新运行脚本。")
    else:
        print("\n此文件现在大小合适，可以安全地提交到 Git 并推送到 GitHub。")
        print("请记住：")
        print("  1. 将 'fe/data/test_book.db' 添加到 Git。")
        print("  2. 确保您的 '.gitignore' 包含了 'fe/data/book.db'，以避免提交原始大文件。")
        print("  3. 在您的测试代码或 GitHub Actions 工作流中，将数据库连接路径更新为 'fe/data/test_book.db'。")
else:
    print("\n错误: 测试数据库文件未成功创建。请检查上面的错误信息。")
    sys.exit(1)

