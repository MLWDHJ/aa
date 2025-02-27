from database import Database
from mysql.connector import Error
import random
from datetime import datetime, timedelta
import hashlib

def hash_password(password):
    """密码哈希函数"""
    return hashlib.sha256(password.encode()).hexdigest()

def random_status():
    """随机生成决策状态"""
    return random.choice(['pending', 'approved', 'rejected', 'draft'])

def insert_test_data():
    db = Database()
    
    try:
        # 清空现有数据
        db.execute_query("DELETE FROM comments")
        db.execute_query("DELETE FROM votes")
        db.execute_query("DELETE FROM questions")
        db.execute_query("DELETE FROM news")
        db.execute_query("DELETE FROM decisions")
        db.execute_query("DELETE FROM users")
        
        # 插入测试用户
        users = [
            ('admin', hash_password('admin123'), 'admin', '20230001', '男', 'admin@edu.com'),
            ('teacher1', hash_password('123456'), 'teacher', '20230002', '女', 'teacher1@edu.com'),
            ('teacher2', hash_password('123456'), 'teacher', '20230003', '男', 'teacher2@edu.com'),
            ('student1', hash_password('123456'), 'student', '20230004', '女', 'student1@edu.com'),
            ('student2', hash_password('123456'), 'student', '20230005', '男', 'student2@edu.com'),
            ('student3', hash_password('123456'), 'student', '20230006', '女', 'student3@edu.com'),
            ('guest1', hash_password('12345'), 'guest', '20230007', '女', 'guest1@edu.com'),  # 新增用户角色
            ('staff1', hash_password('staff123'), 'staff', '20230008', '男', 'staff1@edu.com')  # 新增用户角色
        ]
        
        for user in users:
            db.execute_query("""
                INSERT INTO users (username, password, role, student_id, gender, email, status, create_time)
                VALUES (%s, %s, %s, %s, %s, %s, 'active', NOW())
            """, user)
        
        # 获取用户ID
        user_ids = db.execute_query("SELECT user_id, username FROM users")
        user_id_map = {user['username']: user['user_id'] for user in user_ids}
        
        # 插入测试决策
        decisions = [
            ('关于调整教学计划的决策', '为提高教学质量，建议调整现有教学计划...', user_id_map['teacher1'], 'pending'),
            ('教师培训计划决策', '为提升教师专业素养，拟定教师培训计划...', user_id_map['admin'], 'approved'),
            ('学生活动场地改造决策', '针对学生活动场地不足的问题，提议改造...', user_id_map['teacher2'], 'rejected'),  # 新增状态
            ('教学设备更新决策', '建议更新教学楼多媒体设备，提升教学效果...', user_id_map['teacher1'], 'approved'),
            ('校园网络升级决策', '为满足师生需求，建议升级校园网络设施...', user_id_map['admin'], 'pending'),
            ('图书馆资源扩充决策', '针对图书馆资源不足问题，建议增加投入...', user_id_map['teacher2'], 'draft'),  # 新增状态
            ('教学评价体系改革决策', '建议改革现有教学评价体系，促进教学发展...', user_id_map['teacher1'], 'pending'),
            ('实验室建设规划决策', '为加强实践教学，制定实验室建设规划...', user_id_map['admin'], 'approved'),
            ('关于新增专业课程的决策', '为满足社会需求，提议新增相关专业课程...', user_id_map['teacher2'], 'pending')  # 新增决策
        ]
        
        for title, content, creator_id, status in decisions:
            db.execute_query("""
                INSERT INTO decisions (title, content, create_user_id, status, create_time)
                VALUES (%s, %s, %s, %s, NOW() - INTERVAL FLOOR(RAND() * 30) DAY)
            """, (title, content, creator_id, status))
        
        # 插入测试资讯
        news = [
            ('教育部发布新政策', '教育部近日发布关于深化教育改革的新政策...', user_id_map['admin']),
            ('我校教学成果获奖', '我校在全国教学成果评选中获得特等奖...', user_id_map['teacher1']),
            ('校园信息化建设进展', '我校信息化建设项目取得重要进展...', user_id_map['teacher2']),
            ('教师发展中心成立', '为促进教师专业发展，我校成立教师发展中心...', user_id_map['admin']),
            ('学生创新项目展示', '2023年度学生创新项目成果展示会圆满结束...', user_id_map['teacher1']),
            ('国际交流项目启动', '我校与多所国际知名高校建立合作关系...', user_id_map['teacher2']),
            ('教学质量评估报告', '2023年度教学质量评估报告显示...', user_id_map['admin']),
            ('校园文化建设成果', '我校校园文化建设取得显著成效...', user_id_map['teacher1']),
            ('学术讲座通知', '本周六将举办诺贝尔奖获得者学术讲座...', user_id_map['teacher2'])
        ]
        
        for title, content, author_id in news:
            db.execute_query("""
                INSERT INTO news (title, content, author_id, create_time)
                VALUES (%s, %s, %s, NOW() - INTERVAL FLOOR(RAND() * 30) DAY)
            """, (title, content, author_id))
        
        # 插入测试评论
        decisions_ids = db.execute_query("SELECT decision_id FROM decisions")
        
        # 获取资讯ID（修改这部分）
        news_items = db.execute_query("""
            SELECT n.news_id, n.title 
            FROM news n 
            ORDER BY n.create_time DESC
        """)
        
        comments = [
            '这个提议很有建设性，支持！',
            '建议可以进一步细化实施方案',
            '期待这个决策能够尽快落实',
            '这个想法不错，但是执行可能有难度',
            '完全同意这个观点',
            '希望能听取更多师生意见',
            '这个决策对学校发展很有帮助',
            '建议考虑更多实际情况',
            '我对这个决策有疑问，希望能得到解答',
            '这个主意很有趣，值得尝试'
        ]
        
        # 为决策添加评论
        for decision in decisions_ids:
            decision_id = decision['decision_id']
            # 添加多条评论，覆盖更多用户
            for user_id in [user_id_map['student1'], user_id_map['student2'], user_id_map['teacher1'], user_id_map['guest1']]:
                comment_content = random.choice(comments)
                db.execute_query("""
                    INSERT INTO comments (content, user_id, decision_id, create_time)
                    VALUES (%s, %s, %s, NOW() - INTERVAL FLOOR(RAND() * 30) DAY)
                """, (comment_content, user_id, decision_id))
        
        # 为资讯添加问题（修改这部分）
        questions = [
            '这个政策具体什么时候实施？',
            '如何参与这个项目？',
            '能否详细说明具体内容？',
            '这个变化会带来哪些影响？',
            '是否会举办相关说明会？',
            '具体实施细则是什么？',
            '如何保证政策的有效执行？',
            '学生可以如何参与其中？',
            '这个活动的具体时间是什么时候？',
            '这个计划的预算有多少？'
        ]
        
        # 为每条资讯添加问题
        for news in news_items:
            news_id = news['news_id']
            # 添加多个问题，覆盖更多用户
            for user_id in [user_id_map['student1'], user_id_map['student2'], user_id_map['staff1']]:
                question_content = random.choice(questions)
                db.execute_query("""
                    INSERT INTO questions (content, user_id, news_id, create_time)
                    VALUES (%s, %s, %s, NOW() - INTERVAL FLOOR(RAND() * 30) DAY)
                """, (question_content, user_id, news_id))
        
        # 添加投票数据
        for decision in decisions_ids:
            decision_id = decision['decision_id']
            # 添加更多投票，覆盖更多用户
            for user_id in [user_id_map['student1'], user_id_map['student2'], user_id_map['teacher1'], user_id_map['guest1']]:
                vote_type = 'support' if random.random() > 0.3 else 'oppose'
                # 检查是否已投票，确保唯一性
                existing_vote = db.execute_query("""
                    SELECT * FROM votes WHERE user_id = %s AND decision_id = %s
                """, (user_id, decision_id))
                if not existing_vote:
                    db.execute_query("""
                        INSERT INTO votes (user_id, decision_id, vote_type, create_time)
                        VALUES (%s, %s, %s, NOW() - INTERVAL FLOOR(RAND() * 30) DAY)
                    """, (user_id, decision_id, vote_type))
    except Error as e:
        print(f"数据插入失败: {e}")
    finally:
        # 在这里关闭数据库连接
        try:
            db.close()
        except:
            pass

if __name__ == '__main__':
    try:
        insert_test_data()
        print("测试数据插入完成！")
    except Exception as e:
        print(f"执行失败: {e}")