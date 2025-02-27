# 导入系统模块，用于处理路径
import sys
import os
from datetime import datetime

# 获取当前文件所在目录的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from app import app, db, Decision, Vote, Comment, Admin, News, Question, Answer
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在正确的目录下运行此脚本")
    sys.exit(1)

def init_database():
    """初始化数据库"""
    try:
        with app.app_context():
            # 获取数据库文件的绝对路径
            db_path = os.path.join(current_dir, 'education_decision.db')
            print(f"数据库文件路径: {db_path}")
            
            # 删除现有的数据库文件（如果存在）
            if os.path.exists(db_path):
                os.remove(db_path)
                print("已删除旧的数据库文件")
            
            # 创建新的数据库表
            db.create_all()
            print("数据库表创建成功！")
            
            # 创建管理员账号
            create_admin()
            
            # 添加测试数据
            add_test_data()
            add_test_news()
            
            print("数据库初始化完成！")
            
            # 验证数据是否添加成功
            verify_data()
            
    except Exception as e:
        print(f"初始化数据库时出错: {e}")
        sys.exit(1)

def verify_data():
    """验证数据是否成功添加到数据库"""
    print("\n验证数据:")
    print(f"管理员数量: {Admin.query.count()}")
    print(f"决策数量: {Decision.query.count()}")
    print(f"资讯数量: {News.query.count()}")
    
    # 检查是否可以查询到具体数据
    decision = Decision.query.first()
    if decision:
        print(f"示例决策标题: {decision.title}")
    
    news = News.query.first()
    if news:
        print(f"示例资讯标题: {news.title}")

def create_admin():
    """创建管理员账号"""
    try:
        admin = Admin(username='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("管理员账号创建成功！")
    except Exception as e:
        print(f"创建管理员账号时出错: {e}")
        db.session.rollback()
        raise

def add_test_data():
    """添加测试决策数据"""
    try:
        decisions = [
            Decision(
                title='关于调整期末考试时间的提案',
                content='为了让学生有更充分的复习时间，建议将期末考试时间推迟一周。考虑到学生们的学习压力和课程安排，适当延后考试时间可以帮助学生更好地准备考试。',
                create_time=datetime.now()
            ),
            Decision(
                title='增设校园自习室的提案',
                content='考虑到学生对自习场所的需求，建议在图书馆增设24小时自习室。包括：1. 在图书馆二楼增设100个自习座位；2. 配备充足的照明和电源插座；3. 安装空调保证学习环境舒适。',
                create_time=datetime.now()
            ),
            Decision(
                title='改善食堂就餐环境的建议',
                content='针对学生反映的食堂就餐环境问题，建议：1. 增加取餐窗口数量；2. 扩大就餐区域；3. 增设自助打饭机器；4. 优化排队系统；5. 增加座位数量。',
                create_time=datetime.now()
            ),
            Decision(
                title='校园体育设施升级提案',
                content='为提升学生体育锻炼条件，建议：1. 翻新篮球场地面；2. 增设室内健身房；3. 更新田径场跑道；4. 添置新的体育器材；5. 延长体育场地开放时间。',
                create_time=datetime.now()
            )
        ]
        
        for decision in decisions:
            db.session.add(decision)
        db.session.commit()
        print("测试决策数据添加成功！")
        
    except Exception as e:
        print(f"添加决策数据时出错: {e}")
        db.session.rollback()
        raise

def add_test_news():
    """添加测试资讯数据"""
    try:
        news_items = [
            News(
                title='2024年校园创新创业大赛启动',
                content='为促进学生创新创业能力的培养，我校将于2024年3月举办校园创新创业大赛。比赛设置科技创新、商业计划、社会企业三个类别，总奖金池超过10万元。欢迎各院系学生组队参加，报名截止日期为2024年2月28日。',
                category='比赛',
                create_time=datetime.now()
            ),
            News(
                title='图书馆读书月活动公告',
                content='为培养学生的阅读兴趣，图书馆将在4月份举办读书月系列活动。活动包括：1. 经典名著导读讲座；2. 读书心得交流会；3. 优秀读者评选；4. 图书漂流活动。欢迎全校师生积极参与。',
                category='活动',
                create_time=datetime.now()
            ),
            News(
                title='2024春季运动会报名开始',
                content='2024年春季运动会将于4月15日至17日举行，比赛项目包括：田径、游泳、篮球、足球等。即日起开始报名，请各院系通过体育部网站提交报名表。本届运动会特设团体奖和个人全能奖。',
                category='比赛',
                create_time=datetime.now()
            ),
            News(
                title='校园网络升级通知',
                content='为提升校园网络服务质量，学校将于本周末进行网络设备升级。升级内容包括：1. 增加无线AP数量；2. 提升网络带宽；3. 优化网络架构。升级期间可能出现短暂网络中断，请师生提前做好准备。',
                category='通知',
                create_time=datetime.now()
            ),
            News(
                title='心理健康讲座系列活动',
                content='学生心理咨询中心将举办为期一个月的心理健康讲座系列活动。主题包括：压力管理、人际关系、学习规划、职业生涯等。每周三晚上7点在图书馆报告厅进行，欢迎同学们参加。',
                category='活动',
                create_time=datetime.now()
            )
        ]
        
        for news in news_items:
            db.session.add(news)
        db.session.commit()
        print("测试资讯数据添加成功！")
        
    except Exception as e:
        print(f"添加资讯数据时出错: {e}")
        db.session.rollback()
        raise

if __name__ == "__main__":
    print("开始初始化数据库...")
    init_database() 