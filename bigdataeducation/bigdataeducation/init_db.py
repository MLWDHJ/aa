from database import Database
from mysql.connector import Error
import mysql.connector

def init_database():
    try:
        # 首先创建一个不指定数据库的连接
        conn = mysql.connector.connect(
            host='localhost',
            user='uesr',
            password='1234'
        )
        cursor = conn.cursor()
        
        # 创建数据库
        cursor.execute("CREATE DATABASE IF NOT EXISTS education")
        print("数据库创建成功！")
        
        # 使用新创建的数据库
        cursor.execute("USE education")
        
        # 创建用户表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(32) NOT NULL,
            email VARCHAR(100),
            role VARCHAR(20) DEFAULT 'student',
            student_number VARCHAR(20),
            department VARCHAR(50),
            major VARCHAR(50),
            gender VARCHAR(10),
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            status VARCHAR(20) DEFAULT 'active'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # 创建决策表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            decision_id INT PRIMARY KEY AUTO_INCREMENT,
            title VARCHAR(200) NOT NULL,
            content TEXT NOT NULL,
            create_user_id INT,
            category VARCHAR(50),
            priority VARCHAR(20) DEFAULT 'normal',
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            deadline DATETIME,
            status VARCHAR(20) DEFAULT '进行中',
            feedback TEXT,
            implementation_notes TEXT,
            completion_time DATETIME,
            views INT DEFAULT 0,
            FOREIGN KEY (create_user_id) REFERENCES users(user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # 创建投票表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            vote_id INT PRIMARY KEY AUTO_INCREMENT,
            decision_id INT,
            user_id INT,
            vote_type VARCHAR(10),
            reason TEXT,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (decision_id) REFERENCES decisions(decision_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE KEY unique_vote (decision_id, user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # 创建资讯表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS news (
            news_id INT PRIMARY KEY AUTO_INCREMENT,
            title VARCHAR(200) NOT NULL,
            content TEXT NOT NULL,
            author_id INT,
            category VARCHAR(50),
            tags VARCHAR(200),
            importance VARCHAR(20) DEFAULT 'normal',
            views INT DEFAULT 0,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'published',
            FOREIGN KEY (author_id) REFERENCES users(user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # 创建评论表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            comment_id INT PRIMARY KEY AUTO_INCREMENT,
            decision_id INT NOT NULL,
            user_id INT NOT NULL,
            content TEXT NOT NULL,
            parent_id INT,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'active',
            FOREIGN KEY (decision_id) REFERENCES decisions(decision_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (parent_id) REFERENCES comments(comment_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # 创建问题表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            question_id INT PRIMARY KEY AUTO_INCREMENT,
            news_id INT NOT NULL,
            user_id INT NOT NULL,
            title VARCHAR(200),
            content TEXT NOT NULL,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'pending',
            FOREIGN KEY (news_id) REFERENCES news(news_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # 创建回答表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            answer_id INT PRIMARY KEY AUTO_INCREMENT,
            question_id INT NOT NULL,
            user_id INT NOT NULL,
            content TEXT NOT NULL,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'active',
            FOREIGN KEY (question_id) REFERENCES questions(question_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # 创建系统设置表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            id INT PRIMARY KEY AUTO_INCREMENT,
            site_name VARCHAR(100) DEFAULT '教育决策支持系统',
            maintenance_mode BOOLEAN DEFAULT FALSE,
            announcement TEXT,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # 插入默认设置
        cursor.execute("""
        INSERT INTO system_settings (id, site_name)
        VALUES (1, '教育决策支持系统')
        ON DUPLICATE KEY UPDATE id=id
        """)
        
        print("所有表创建成功！")
        conn.commit()
        
    except Error as e:
        print(f"初始化数据库时出错：{e}")
        
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    init_database() 