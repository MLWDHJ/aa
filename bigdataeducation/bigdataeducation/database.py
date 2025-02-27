import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import time
import random

load_dotenv()

class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.connection = None
        return cls._instance

    def __init__(self):
        self.config = {
            'host': 'localhost',
            'user': 'uesr',
            'password': '1234',
            'database': 'education',
            'port': 3306,
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
            'raise_on_warnings': True
        }
        self.connection = None
        self.max_retries = 3
        self.connect()

    def connect(self):
        """建立数据库连接，包含重试机制"""
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                if self.connection is None or not self.connection.is_connected():
                    self.connection = mysql.connector.connect(**self.config)
                    print("数据库连接成功")
                    return True
            except Error as e:
                retry_count += 1
                print(f"连接尝试 {retry_count}/{self.max_retries} 失败: {e}")
                if retry_count < self.max_retries:
                    time.sleep(2)  # 等待2秒后重试
                else:
                    print("数据库连接失败，已达到最大重试次数")
                    raise
        return False

    def get_connection(self):
        """获取数据库连接"""
        try:
            if not self.connection or not self.connection.is_connected():
                if not self.connect():
                    raise Error("Could not establish database connection")
            return self.connection
        except Error as e:
            print(f"Error getting connection: {e}")
            raise

    def close(self):
        """关闭数据库连接"""
        try:
            if hasattr(self, 'connection') and self.connection:
                if self.connection.is_connected():
                    self.connection.close()
                    print("数据库连接已关闭")
        except Exception as e:
            print(f"关闭数据库连接时出错: {e}")
            # 忽略错误继续执行

    def execute_query(self, query, params=None):
        """执行SQL查询，包含重试和重连机制"""
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                if not self.connection or not self.connection.is_connected():
                    self.connect()
                
                cursor = self.connection.cursor(dictionary=True)
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                    self.connection.commit()
                    result = cursor.rowcount
                else:
                    result = cursor.fetchall()
                
                cursor.close()
                return result

            except Error as e:
                retry_count += 1
                print(f"查询执行尝试 {retry_count}/{self.max_retries} 失败: {e}")
                if retry_count < self.max_retries:
                    time.sleep(2)  # 等待2秒后重试
                    self.connect()  # 尝试重新连接
                else:
                    print("查询执行失败，已达到最大重试次数")
                    raise

    def execute_update(self, query, params=None):
        """执行更新操作"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            return True
        except Error as e:
            if conn:
                try:
                    conn.rollback()
                except Error:
                    pass
            print(f"Error executing update: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    def execute_transaction(self, queries):
        """执行事务"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            for query, params in queries:
                cursor.execute(query, params or ())
            conn.commit()
            return True
        except Error as e:
            if conn:
                try:
                    conn.rollback()
                except Error:
                    pass
            print(f"Error executing transaction: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    def random(self):
        """生成随机数"""
        return random.random()

    def __del__(self):
        """析构函数"""
        try:
            self.close()
        except:
            # 忽略析构时的错误
            pass 