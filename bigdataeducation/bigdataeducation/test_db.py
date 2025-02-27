from database import Database

def test_connection():
    try:
        # 获取数据库连接
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 测试查询
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print("数据库中的表：")
        for table in tables:
            print(table)
            
        # 关闭连接
        cursor.close()
        db.close()
        print("数据库连接测试成功！")
        
    except Exception as e:
        print(f"数据库连接测试失败：{e}")

if __name__ == "__main__":
    test_connection() 