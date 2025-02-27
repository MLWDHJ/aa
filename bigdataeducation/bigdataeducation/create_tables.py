from database import Database

def create_tables():
    db = Database()
    try:
        # 按照依赖关系顺序删除表
        db.execute_query("DROP TABLE IF EXISTS answers")
        db.execute_query("DROP TABLE IF EXISTS questions")
        db.execute_query("DROP TABLE IF EXISTS news")
        db.execute_query("DROP TABLE IF EXISTS user_behavior_analysis")
        
        # 创建 news 表
        db.execute_query("""
            CREATE TABLE news (
                news_id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                author_id INT NOT NULL,
                create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (author_id) REFERENCES users(user_id)
            )
        """)
        print("news 表创建成功！")
        
        # 创建 questions 表
        db.execute_query("""
            CREATE TABLE questions (
                question_id INT AUTO_INCREMENT PRIMARY KEY,
                content TEXT NOT NULL,
                user_id INT NOT NULL,
                news_id INT NOT NULL,
                create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (news_id) REFERENCES news(news_id)
            )
        """)
        print("questions 表创建成功！")
        
        # 创建 answers 表
        db.execute_query("""
            CREATE TABLE answers (
                answer_id INT AUTO_INCREMENT PRIMARY KEY,
                question_id INT NOT NULL,
                content TEXT NOT NULL,
                answered_by VARCHAR(255) NOT NULL,
                create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (question_id) REFERENCES questions(question_id)
            )
        """)
        print("answers 表创建成功！")
        
        # 创建索引
        db.execute_query("""
            CREATE INDEX idx_news_author ON news(author_id);
            CREATE INDEX idx_news_create_time ON news(create_time);
            CREATE INDEX idx_questions_news ON questions(news_id);
            CREATE INDEX idx_questions_user ON questions(user_id);
            CREATE INDEX idx_answers_question ON answers(question_id);
        """)
        print("索引创建成功！")
        
        # 创建用户行为分析表
        db.execute_query("""
            CREATE TABLE user_behavior_analysis (
                analysis_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                vote_pattern FLOAT DEFAULT 0.0,  # 投票模式得分（0-1，0表示完全单一，1表示完全平衡）
                comment_ratio FLOAT DEFAULT 0.0,  # 评论参与度（评论数/投票数）
                activity_score FLOAT DEFAULT 0.0, # 总活跃度得分
                vote_weight FLOAT DEFAULT 1.0,    # 计算得出的投票权重
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        print("用户行为分析表创建成功！")
        
        # 创建存储过程用于更新用户行为分析
        db.execute_query("""
            CREATE PROCEDURE update_user_behavior()
            BEGIN
                INSERT INTO user_behavior_analysis (user_id, vote_pattern, comment_ratio, activity_score, vote_weight)
                SELECT 
                    u.user_id,
                    -- 计算投票模式得分
                    CASE 
                        WHEN total_votes = 0 THEN 0
                        ELSE 1 - ABS(support_votes/total_votes - 0.5)*2
                    END as vote_pattern,
                    -- 计算评论参与度
                    CASE 
                        WHEN total_votes = 0 THEN 0
                        ELSE comment_count/total_votes
                    END as comment_ratio,
                    -- 计算活跃度得分
                    (IFNULL(comment_count, 0) + IFNULL(total_votes, 0))/
                        (SELECT MAX(comment_count + total_votes) FROM users) as activity_score,
                    -- 计算最终投票权重
                    CASE 
                        WHEN u.role = 'teacher' THEN 3.0
                        WHEN vote_pattern < 0.3 AND comment_ratio < 0.2 THEN 0.5
                        ELSE 1.0
                    END as vote_weight
                FROM users u
                LEFT JOIN (
                    SELECT 
                        user_id,
                        COUNT(*) as total_votes,
                        SUM(CASE WHEN vote_type = 'support' THEN 1 ELSE 0 END) as support_votes
                    FROM votes
                    GROUP BY user_id
                ) v ON u.user_id = v.user_id
                LEFT JOIN (
                    SELECT user_id, COUNT(*) as comment_count
                    FROM comments
                    GROUP BY user_id
                ) c ON u.user_id = c.user_id
                ON DUPLICATE KEY UPDATE
                    vote_pattern = VALUES(vote_pattern),
                    comment_ratio = VALUES(comment_ratio),
                    activity_score = VALUES(activity_score),
                    vote_weight = VALUES(vote_weight);
            END
        """)
        print("用户行为分析存储过程创建成功！")

        # 创建定时事件每天更新用户行为分析
        db.execute_query("""
            CREATE EVENT IF NOT EXISTS daily_behavior_analysis
            ON SCHEDULE EVERY 1 DAY
            DO CALL update_user_behavior();
        """)
        print("定时分析事件创建成功！")
        
    except Exception as e:
        print(f"创建表时出错: {e}")

if __name__ == '__main__':
    create_tables() 