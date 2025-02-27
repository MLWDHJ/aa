from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from datetime import datetime
import pandas as pd
import jieba
from collections import Counter
import functools
import os
from mysql.connector import Error
import hashlib
import mysql.connector
from openai import OpenAI  # 添加 OpenAI 导入
from dotenv import load_dotenv

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # 用于session加密

# 修改数据库配置
app.config['MYSQL_HOST'] = 'localhost'      # 数据库主机名
app.config['MYSQL_USER'] = 'user'          # MySQL用户名
app.config['MYSQL_PASSWORD'] = '1234'       # MySQL密码
app.config['MYSQL_DB'] = 'education'        # 数据库名称
app.config['MYSQL_CHARSET'] = 'utf8mb4'     # 添加字符集设置
app.config['MYSQL_PORT'] = 3306            # 添加端口配置
app.config['MYSQL_AUTOCOMMIT'] = True      # 自动提交配置

load_dotenv()  # 加载 .env 文件

# 配置 DeepSeek API
client = OpenAI(
    base_url="https://api.deepseek.com/v1",
    api_key=os.getenv('DEEPSEEK_API_KEY')
)

# 错误处理装饰器
def handle_error(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            print(f"Error in {f.__name__}: {e}")
            flash('操作失败，请稍后重试', 'error')
            return redirect(url_for('index'))
    return decorated_function

def text_similarity(text1, text2):
    """计算两段文本的相似度"""
    words1 = set(jieba.cut(text1))
    words2 = set(jieba.cut(text2))
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union) if union else 0

# 添加登录装饰器
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'error')
            session['next'] = request.url
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 添加管理员装饰器
def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash('需要管理员权限', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# 修改Database类的初始化
class Database:
    def __init__(self):
        try:
            # 添加更多连接参数
            self.conn = mysql.connector.connect(
                host=app.config['MYSQL_HOST'],
                user=app.config['MYSQL_USER'],
                password=app.config['MYSQL_PASSWORD'],
                database=app.config['MYSQL_DB'],
                port=app.config['MYSQL_PORT'],
                charset=app.config['MYSQL_CHARSET'],
                autocommit=app.config['MYSQL_AUTOCOMMIT'],
                use_pure=True,  # 使用纯Python实现
                connection_timeout=5,  # 连接超时时间
                auth_plugin='mysql_native_password'  # 认证插件
            )
            self.cursor = self.conn.cursor(dictionary=True, buffered=True)
            print("数据库连接成功！")
        except Error as e:
            print(f"数据库连接错误：{e}")
            print(f"连接参数：")
            print(f"  Host: {app.config['MYSQL_HOST']}")
            print(f"  User: {app.config['MYSQL_USER']}")
            print(f"  Database: {app.config['MYSQL_DB']}")
            print(f"  Port: {app.config['MYSQL_PORT']}")
            raise e

    def __del__(self):
        try:
            if hasattr(self, 'cursor') and self.cursor:
                self.cursor.close()
            if hasattr(self, 'conn') and self.conn and self.conn.is_connected():
                self.conn.close()
                print("数据库连接已关闭")
        except Error as e:
            print(f"关闭数据库连接时出错：{e}")

    def execute_query(self, query, params=None):
        try:
            if not self.conn.is_connected():
                self.__init__()  # 重新连接
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except Error as e:
            print(f"查询执行错误: {e}")
            print(f"SQL语句: {query}")
            print(f"参数: {params}")
            raise e

    def execute_update(self, query, params=None):
        try:
            if not self.conn.is_connected():
                self.__init__()  # 重新连接
            self.cursor.execute(query, params or ())
            self.conn.commit()
            return True
        except Error as e:
            print(f"更新执行错误: {e}")
            print(f"SQL语句: {query}")
            print(f"参数: {params}")
            self.conn.rollback()
            raise e

def hash_password(password):
    """密码哈希函数"""
    return hashlib.sha256(password.encode()).hexdigest()

# 路由处理函数
@app.route('/')
def index():
    """首页路由"""
    db = Database()
    try:
        # 获取统计数据
        stats = db.execute_query("""
            SELECT 
                (SELECT COUNT(*) FROM users) as total_users,
                (SELECT COUNT(*) FROM decisions) as total_decisions,
                (SELECT COUNT(*) FROM news) as total_news,
                (SELECT COUNT(*) FROM comments) as total_comments
        """)[0]
        
        # 获取最新的决策列表
        decisions = db.execute_query("""
            SELECT 
                d.decision_id,
                d.title,
                d.content,
                d.create_time,
                d.status,
                u.username as creator_name,
                (SELECT COUNT(*) FROM votes WHERE decision_id = d.decision_id AND vote_type = 'support') as support_count,
                (SELECT COUNT(*) FROM votes WHERE decision_id = d.decision_id AND vote_type = 'oppose') as oppose_count
            FROM decisions d
            LEFT JOIN users u ON d.create_user_id = u.user_id
            ORDER BY d.create_time DESC
            LIMIT 5
        """)
        
        # 获取最新的资讯列表
        latest_news = db.execute_query("""
            SELECT 
                n.news_id,
                n.title,
                n.create_time,
                u.username as author_name,
                (SELECT COUNT(*) FROM questions WHERE news_id = n.news_id) as question_count
            FROM news n
            LEFT JOIN users u ON n.author_id = u.user_id
            ORDER BY n.create_time DESC
            LIMIT 5
        """)
        
        return render_template('index.html', 
                             stats=stats,
                             decisions=decisions or [], 
                             latest_news=latest_news or [])
        
    except Error as e:
        print(f"数据库错误：{e}")
        return render_template('index.html', 
                             stats={'total_users': 0, 'total_decisions': 0, 'total_news': 0, 'total_comments': 0},
                             decisions=[], 
                             latest_news=[])

@app.route('/decisions')
def decision_list():
    """决策列表页面"""
    db = Database()
    try:
        # 获取所有决策
        decisions = db.execute_query("""
            SELECT d.*, u.username as creator_name,
                (SELECT COUNT(*) FROM votes WHERE decision_id = d.decision_id AND vote_type = 'support') as support_count,
                (SELECT COUNT(*) FROM votes WHERE decision_id = d.decision_id AND vote_type = 'oppose') as oppose_count
            FROM decisions d
            LEFT JOIN users u ON d.create_user_id = u.user_id
            ORDER BY d.create_time DESC
        """)
        
        return render_template('decision_list.html', decisions=decisions)
    except Error as e:
        flash('获取决策列表失败', 'error')
        print(f"Error getting decisions: {e}")
        return redirect(url_for('index'))

@app.route('/decision/<int:decision_id>')
def decision_detail(decision_id):
    """决策详情页面"""
    db = Database()
    try:
        # 获取决策信息
        decisions = db.execute_query("""
            SELECT d.*, u.username as creator_name
            FROM decisions d
            LEFT JOIN users u ON d.create_user_id = u.user_id
            WHERE d.decision_id = %s
        """, (decision_id,))
        
        if not decisions:
            flash('决策不存在', 'error')
            return redirect(url_for('index'))
            
        decision = decisions[0]
        
        # 获取投票统计
        vote_stats = db.execute_query("""
            SELECT vote_type, COUNT(*) as count
            FROM votes
            WHERE decision_id = %s
            GROUP BY vote_type
        """, (decision_id,))
        
        # 处理投票数据
        support_count = 0
        oppose_count = 0
        for stat in vote_stats:
            if stat['vote_type'] == 'support':
                support_count = stat['count']
            elif stat['vote_type'] == 'oppose':
                oppose_count = stat['count']
        
        # 获取当前用户的投票
        current_vote = None
        if 'user_id' in session:
            votes = db.execute_query("""
                SELECT vote_type
                FROM votes
                WHERE decision_id = %s AND user_id = %s
            """, (decision_id, session['user_id']))
            if votes:
                current_vote = votes[0]['vote_type']
        
        # 构建决策数据
        decision_data = {
            'id': decision['decision_id'],
            'title': decision['title'],
            'content': decision['content'],
            'creator': decision['creator_name'],
            'create_time': decision['create_time'],
            'status': decision['status'],
            'support_count': support_count,
            'oppose_count': oppose_count,
            'current_vote': current_vote
        }
        
        # 获取评论列表（如果评论表存在）
        try:
            comments = db.execute_query("""
                SELECT c.*, u.username
                FROM comments c
                LEFT JOIN users u ON c.user_id = u.user_id
                WHERE c.decision_id = %s
                ORDER BY c.create_time DESC
            """, (decision_id,))
        except Error:
            comments = []
        
        return render_template('decision_detail.html', 
                             decision=decision_data,
                             comments=comments)
        
    except Error as e:
        flash('获取决策详情失败', 'error')
        print(f"Error getting decision detail: {e}")
        return redirect(url_for('index'))

@app.route('/vote/<int:decision_id>/<vote_type>')
@login_required
def vote(decision_id, vote_type):
    """处理投票"""
    if vote_type not in ['support', 'oppose']:
        flash('无效的投票类型', 'error')
        return redirect(url_for('decision_detail', decision_id=decision_id))
    
    db = Database()
    try:
        # 检查是否已经投票
        existing_vote = db.execute_query("""
            SELECT vote_id, vote_type 
            FROM votes 
            WHERE decision_id = %s AND user_id = %s
        """, (decision_id, session['user_id']))
        
        if existing_vote:
            if existing_vote[0]['vote_type'] == vote_type:
                # 取消投票
                success = db.execute_update("""
                    DELETE FROM votes 
                    WHERE vote_id = %s
                """, (existing_vote[0]['vote_id'],))
                if success:
                    flash('已取消投票', 'success')
            else:
                # 更新投票
                success = db.execute_update("""
                    UPDATE votes 
                    SET vote_type = %s 
                    WHERE vote_id = %s
                """, (vote_type, existing_vote[0]['vote_id']))
                if success:
                    flash('投票已更新', 'success')
        else:
            # 新增投票
            success = db.execute_update("""
                INSERT INTO votes (decision_id, user_id, vote_type)
                VALUES (%s, %s, %s)
            """, (decision_id, session['user_id'], vote_type))
            if success:
                flash('投票成功', 'success')
        
        if not success:
            flash('投票操作失败', 'error')
            
    except Error as e:
        flash('投票失败', 'error')
        print(f"Error during voting: {e}")
    
    return redirect(url_for('decision_detail', decision_id=decision_id))

@app.route('/comment', methods=['POST'])
def comment():
    """处理评论提交"""
    decision_id = request.form.get('decision_id')
    content = request.form.get('content')
    
    # 创建新评论
    comment = Comment(decision_id=decision_id, content=content)
    db.session.add(comment)
    db.session.commit()
    
    return redirect(url_for('decision_detail', decision_id=decision_id))

@app.route('/analytics')
@admin_required
def analytics():
    """数据分析页面：展示决策统计和参与情况"""
    # 获取基础统计数据
    total_decisions = Decision.query.count()
    total_votes = Vote.query.count()
    total_comments = Comment.query.count()
    
    # 计算参与率
    unique_voters = db.session.query(Vote.student_id).distinct().count()
    total_students = 1000  # 总学生数（示例值）
    participation_rate = round((unique_voters / total_students) * 100, 1) if total_students > 0 else 0
    
    # 获取每个决策的投票统计
    decisions = Decision.query.all()
    vote_stats = []
    for decision in decisions:
        votes = Vote.query.filter_by(decision_id=decision.id).all()
        support_count = len([v for v in votes if v.vote_type == '支持'])
        oppose_count = len([v for v in votes if v.vote_type == '反对'])
        vote_stats.append({
            'title': decision.title[:20] + '...' if len(decision.title) > 20 else decision.title,
            'support': support_count,
            'oppose': oppose_count
        })
    
    # 评论词频分析
    comments = Comment.query.all()
    comment_texts = [comment.content for comment in comments]
    words = []
    for text in comment_texts:
        words.extend(jieba.cut(text))  # 使用结巴分词
    filtered_words = [w for w in words if len(w) > 1]  # 过滤单字词
    word_counts = Counter(filtered_words).most_common(10)  # 获取前10个高频词
    
    return render_template('analytics.html',
                         total_decisions=total_decisions,
                         total_votes=total_votes,
                         total_comments=total_comments,
                         participation_rate=participation_rate,
                         vote_stats=vote_stats,
                         word_counts=word_counts)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """管理员登录处理"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            return redirect(url_for('admin_dashboard'))
        flash('用户名或密码错误')
    
    return render_template('admin_login.html')  # 使用英文文件名

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """管理员仪表板"""
    db = Database()
    try:
        # 获取统计数据
        stats = {}
        
        # 用户统计
        users = db.execute_query("SELECT COUNT(*) as count FROM users")[0]
        stats['total_users'] = users['count']
        
        # 决策统计
        decisions = db.execute_query("SELECT COUNT(*) as count FROM decisions")[0]
        stats['total_decisions'] = decisions['count']
        
        # 资讯统计
        news = db.execute_query("SELECT COUNT(*) as count FROM news")[0]
        stats['total_news'] = news['count']
        
        # 评论统计
        comments = db.execute_query("SELECT COUNT(*) as count FROM comments")[0]
        stats['total_comments'] = comments['count']
        
        # 获取最新用户
        latest_users = db.execute_query("""
            SELECT * FROM users 
            ORDER BY create_time DESC 
            LIMIT 5
        """)
        
        # 获取最新决策
        latest_decisions = db.execute_query("""
            SELECT d.*, u.username as creator_name
            FROM decisions d
            LEFT JOIN users u ON d.create_user_id = u.user_id
            ORDER BY d.create_time DESC
            LIMIT 5
        """)
        
        # 获取最新资讯（添加问题数统计）
        latest_news = db.execute_query("""
            SELECT 
                n.*,
                u.username as author_name,
                (SELECT COUNT(*) FROM questions WHERE news_id = n.news_id) as question_count
            FROM news n
            LEFT JOIN users u ON n.author_id = u.user_id
            ORDER BY n.create_time DESC
            LIMIT 5
        """)
        
        # 获取系统设置
        settings = db.execute_query("""
            SELECT * FROM system_settings
            WHERE id = 1
        """)[0]
        
        return render_template('admin_dashboard.html',
                             stats=stats,
                             latest_users=latest_users,
                             latest_decisions=latest_decisions,
                             latest_news=latest_news,
                             settings=settings)
                             
    except Error as e:
        flash('获取数据失败', 'error')
        print(f"Error in admin dashboard: {e}")
        return redirect(url_for('index'))

@app.route('/admin/decision/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_decision():
    """发布新决策"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        if not title or not content:
            flash('标题和内容不能为空', 'error')
            return render_template('new_decision.html')
        
        db = Database()
        try:
            success = db.execute_update("""
                INSERT INTO decisions (title, content, create_user_id, status)
                VALUES (%s, %s, %s, '进行中')
            """, (title, content, session['user_id']))
            
            if success:
                flash('决策发布成功', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('决策发布失败', 'error')
        except Error as e:
            flash('决策发布失败', 'error')
            print(f"Error creating decision: {e}")
    
    return render_template('new_decision.html')

@app.route('/news')
def news_list():
    """资讯列表页面"""
    db = Database()
    try:
        # 修改查询，添加错误处理和分页
        news = db.execute_query("""
            SELECT n.*, u.username as author_name,
                   (SELECT COUNT(*) FROM questions WHERE news_id = n.news_id) as question_count
            FROM news n
            LEFT JOIN users u ON n.author_id = u.user_id
            ORDER BY n.create_time DESC
        """)
        
        if news is None:
            news = []
            
        # 添加调试信息
        print(f"获取到 {len(news)} 条资讯")
        
        return render_template('news_list.html', news=news)
    except Error as e:
        print(f"获取资讯列表错误: {e}")
        flash('获取资讯列表失败', 'error')
        return render_template('news_list.html', news=[])

@app.route('/news/<int:news_id>')
def news_detail(news_id):
    """资讯详情页面"""
    db = Database()
    try:
        # 获取资讯信息
        news_list = db.execute_query("""
            SELECT n.*, u.username as author_name
            FROM news n
            LEFT JOIN users u ON n.author_id = u.user_id
            WHERE n.news_id = %s
        """, (news_id,))
        
        if not news_list:
            flash('资讯不存在', 'error')
            return redirect(url_for('news_list'))
            
        news = news_list[0]
        
        # 更新浏览量
        db.execute_update("""
            UPDATE news 
            SET views = views + 1
            WHERE news_id = %s
        """, (news_id,))
        
        # 获取该资讯的问题列表
        try:
            questions = db.execute_query("""
                SELECT q.*, u.username,
                       a.content as answer_content,
                       a.answered_by,
                       a.create_time as answer_time
                FROM questions q
                LEFT JOIN users u ON q.user_id = u.user_id
                LEFT JOIN answers a ON q.question_id = a.question_id
                WHERE q.news_id = %s
                ORDER BY q.create_time DESC
            """, (news_id,))
            
            # 处理问题和回答数据
            for question in questions:
                if question['answer_content']:
                    question['answer'] = {
                        'content': question['answer_content'],
                        'answered_by': question['answered_by'],
                        'create_time': question['answer_time']
                    }
                else:
                    question['answer'] = None
                    
        except Error:
            questions = []
        
        return render_template('news_detail.html', 
                             news=news,
                             questions=questions)
                             
    except Error as e:
        flash('获取资讯详情失败', 'error')
        print(f"Error in news detail: {e}")
        return redirect(url_for('news_list'))

@app.route('/news/<int:news_id>/ask', methods=['POST'])
def ask_question(news_id):
    try:
        content = request.form.get('content')
        if not content:
            flash('问题内容不能为空')
            return redirect(url_for('news_detail', news_id=news_id))
            
        question = Question(news_id=news_id, content=content)
        db.session.add(question)
        db.session.commit()
        flash('问题提交成功')
    except Exception as e:
        flash('提交问题失败')
        db.session.rollback()
    
    return redirect(url_for('news_detail', news_id=news_id))

@app.route('/admin/news/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_news():
    """发布新资讯"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        
        if not title or not content:
            flash('标题和内容不能为空', 'error')
            return render_template('new_news.html')
        
        db = Database()
        try:
            success = db.execute_update("""
                INSERT INTO news (title, content, author_id, category)
                VALUES (%s, %s, %s, %s)
            """, (title, content, session['user_id'], category))
            
            if success:
                flash('资讯发布成功', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('资讯发布失败', 'error')
        except Error as e:
            flash('资讯发布失败', 'error')
            print(f"Error creating news: {e}")
    
    return render_template('new_news.html')

@app.route('/admin/decision/<int:decision_id>/status', methods=['POST'])
@admin_required
def update_decision_status(decision_id):
    """更新决策状态"""
    decision = Decision.query.get_or_404(decision_id)
    status = request.form.get('status')
    
    # 验证状态值的合法性
    if status in ['进行中', '已结束']:
        decision.status = status
        db.session.commit()
        flash('决策状态更新成功')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/questions')
@login_required
@admin_required
def admin_questions():
    """管理员查看所有问题"""
    db = Database()
    try:
        # 获取URL参数中的资讯ID
        news_id = request.args.get('news_id', type=int)
        
        # 构建基础查询
        query = """
            SELECT 
                q.*,
                u.username as user_name,
                n.title as news_title,
                a.content as answer_content,
                a.create_time as answer_time,
                a.answered_by
            FROM questions q
            LEFT JOIN users u ON q.user_id = u.user_id
            LEFT JOIN news n ON q.news_id = n.news_id
            LEFT JOIN answers a ON q.question_id = a.question_id
        """
        
        params = []
        # 如果指定了资讯ID，添加过滤条件
        if news_id:
            query += " WHERE q.news_id = %s"
            params.append(news_id)
            
            # 获取资讯信息
            news = db.execute_query("""
                SELECT title FROM news WHERE news_id = %s
            """, (news_id,))
            if news:
                news_title = news[0]['title']
            else:
                news_title = None
        else:
            news_title = None
            
        query += " ORDER BY q.create_time DESC"
        
        # 执行查询
        questions = db.execute_query(query, params if params else None)
        
        return render_template('admin_questions.html', 
                             questions=questions,
                             news_id=news_id,
                             news_title=news_title)
    except Error as e:
        flash('获取问题列表失败', 'error')
        print(f"Error getting questions: {e}")
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/question/<int:question_id>/answer', methods=['GET', 'POST'])
@login_required
@admin_required
def answer_question_page(question_id):
    """回答问题页面"""
    db = Database()
    try:
        # 获取问题详情
        question = db.execute_query("""
            SELECT 
                q.*,
                u.username as user_name,
                n.title as news_title,
                n.news_id,
                a.content as answer_content,
                a.answered_by,
                a.create_time as answer_time
            FROM questions q
            LEFT JOIN users u ON q.user_id = u.user_id
            LEFT JOIN news n ON q.news_id = n.news_id
            LEFT JOIN answers a ON q.question_id = a.question_id
            WHERE q.question_id = %s
        """, (question_id,))

        if not question:
            flash('问题不存在', 'error')
            return redirect(url_for('admin_questions'))

        if request.method == 'POST':
            answer_content = request.form.get('answer')
            if not answer_content:
                flash('回答内容不能为空', 'error')
                return redirect(url_for('answer_question_page', question_id=question_id))

            # 检查是否已有回答
            existing_answer = db.execute_query("""
                SELECT * FROM answers WHERE question_id = %s
            """, (question_id,))

            if existing_answer:
                # 更新已有回答
                success = db.execute_update("""
                    UPDATE answers 
                    SET content = %s, 
                        update_time = NOW(),
                        answered_by = %s
                    WHERE question_id = %s
                """, (answer_content, session['username'], question_id))
            else:
                # 创建新回答
                success = db.execute_update("""
                    INSERT INTO answers (
                        question_id, 
                        content, 
                        answered_by, 
                        create_time
                    ) VALUES (%s, %s, %s, NOW())
                """, (question_id, answer_content, session['username']))

            if success:
                flash('回答已提交', 'success')
                # 如果是从特定资讯的问题列表来的，返回那里
                news_id = question[0]['news_id']
                return redirect(url_for('admin_questions', news_id=news_id) if news_id else url_for('admin_questions'))
            else:
                flash('回答提交失败', 'error')

        return render_template('answer_question.html', question=question[0])

    except Error as e:
        flash('操作失败', 'error')
        print(f"Error in answer question page: {e}")
        return redirect(url_for('admin_questions'))

@app.route('/api/search', methods=['POST'])
def search():
    """智能搜索接口"""
    query = request.json.get('query', '')
    search_type = request.json.get('type', 'all')
    
    results = []
    if search_type in ['decision', 'all']:
        # 搜索决策
        decisions = Decision.query.all()
        for decision in decisions:
            text = f"{decision.title} {decision.content}"
            similarity = text_similarity(query, text)
            if similarity > 0.1:  # 降低相似度阈值
                results.append({
                    'type': 'decision',
                    'title': decision.title,
                    'content': decision.content[:200],
                    'url': url_for('decision_detail', decision_id=decision.id),
                    'similarity': similarity
                })
    
    if search_type in ['news', 'all']:
        # 搜索资讯
        news_items = News.query.all()
        for news in news_items:
            text = f"{news.title} {news.content}"
            similarity = text_similarity(query, text)
            if similarity > 0.1:
                results.append({
                    'type': 'news',
                    'title': news.title,
                    'content': news.content[:200],
                    'url': url_for('news_detail', news_id=news.id),
                    'similarity': similarity
                })
    
    # 按相似度排序
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return jsonify(results)

@app.route('/analytics/learning')
@admin_required
def learning_analytics():
    """学习行为分析页面"""
    return render_template('learning_analytics.html')

@app.route('/api/learning_stats')
def learning_stats():
    """获取学习行为统计数据"""
    # 获取所有学习记录
    records = LearningRecord.query.all()
    
    # 转换为DataFrame进行分析
    data = pd.DataFrame([{
        'student_id': r.student_id,
        'activity_type': r.activity_type,
        'duration': r.duration,
        'target_type': r.target_type,
        'create_time': r.create_time
    } for r in records])
    
    # 计算统计数据
    stats = {
        'total_students': len(data['student_id'].unique()),
        'total_duration': int(data['duration'].sum()),
        'activity_distribution': data.groupby('activity_type')['duration'].sum().to_dict(),
        'daily_activity': data.groupby(data['create_time'].dt.date)['duration'].sum().to_dict(),
        'target_type_distribution': data.groupby('target_type')['duration'].sum().to_dict()
    }
    
    return jsonify(stats)

@app.route('/library_reading_month')
def library_reading_month():
    """图书馆读书月活动页面"""
    return render_template('library_reading_month.html')

# 添加用户资料相关路由
@app.route('/profile')
@login_required
@handle_error
def profile():
    """用户资料页面"""
    db = Database()
    try:
        # 获取更详细的用户信息
        user = db.execute_query("""
            SELECT 
                u.*,
                (SELECT COUNT(*) FROM comments WHERE user_id = u.user_id) as comment_count,
                (SELECT COUNT(*) FROM votes WHERE user_id = u.user_id) as vote_count,
                (SELECT COUNT(*) FROM questions WHERE user_id = u.user_id) as question_count,
                (SELECT MAX(create_time) FROM comments WHERE user_id = u.user_id) as last_comment_time,
                (SELECT MAX(create_time) FROM votes WHERE user_id = u.user_id) as last_vote_time,
                (SELECT MAX(create_time) FROM questions WHERE user_id = u.user_id) as last_question_time
            FROM users u 
            WHERE u.user_id = %s
        """, (session['user_id'],))

        if not user:
            flash('获取用户信息失败', 'error')
            return redirect(url_for('index'))

        # 获取用户最近的活动
        recent_activities = []
        
        # 获取最近的评论
        comments = db.execute_query("""
            SELECT c.*, d.title as decision_title
            FROM comments c
            LEFT JOIN decisions d ON c.decision_id = d.decision_id
            WHERE c.user_id = %s
            ORDER BY c.create_time DESC
            LIMIT 5
        """, (session['user_id'],))
        
        # 获取最近的投票
        votes = db.execute_query("""
            SELECT v.*, d.title as decision_title
            FROM votes v
            LEFT JOIN decisions d ON v.decision_id = d.decision_id
            WHERE v.user_id = %s
            ORDER BY v.create_time DESC
            LIMIT 5
        """, (session['user_id'],))
        
        # 获取最近的问题
        questions = db.execute_query("""
            SELECT q.*, n.title as news_title
            FROM questions q
            LEFT JOIN news n ON q.news_id = n.news_id
            WHERE q.user_id = %s
            ORDER BY q.create_time DESC
            LIMIT 5
        """, (session['user_id'],))

        return render_template('profile.html', 
                             user=user[0],
                             comments=comments,
                             votes=votes,
                             questions=questions)
                             
    except Error as e:
        flash('获取用户信息失败', 'error')
        print(f"Error getting user profile: {e}")
        return redirect(url_for('index'))

@app.route('/update_profile', methods=['POST'])
@login_required
@handle_error
def update_profile():
    """更新用户资料"""
    email = request.form.get('email')
    
    if not email:
        flash('邮箱不能为空', 'error')
        return redirect(url_for('profile'))
    
    db = Database()
    try:
        success = db.execute_update("""
            UPDATE users SET email = %s
            WHERE user_id = %s
        """, (email, session['user_id']))
        
        if success:
            flash('资料更新成功', 'success')
        else:
            flash('资料更新失败', 'error')
    except Error as e:
        flash('资料更新失败', 'error')
        print(f"Error updating profile: {e}")
    
    return redirect(url_for('profile'))

@app.route('/change_password', methods=['POST'])
@login_required
@handle_error
def change_password():
    """修改密码"""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if new_password != confirm_password:
        flash('新密码两次输入不一致', 'error')
        return redirect(url_for('profile'))
    
    db = Database()
    try:
        # 验证当前密码
        user = db.execute_query("""
            SELECT password FROM users WHERE user_id = %s
        """, (session['user_id'],))[0]
        
        if not verify_password(user['password'], current_password):
            flash('当前密码错误', 'error')
            return redirect(url_for('profile'))
        
        # 更新密码
        hashed_password = hash_password(new_password)
        success = db.execute_update("""
            UPDATE users SET password = %s
            WHERE user_id = %s
        """, (hashed_password, session['user_id']))
        
        if success:
            flash('密码修改成功', 'success')
        else:
            flash('密码修改失败', 'error')
    except Error as e:
        flash('密码修改失败', 'error')
        print(f"Error changing password: {e}")
    
    return redirect(url_for('profile'))

# 添加密码重置功能
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    """密码重置"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        
        db = Database()
        try:
            # 验证用户名和邮箱是否匹配
            user = db.execute_query("""
                SELECT * FROM users 
                WHERE username = %s AND email = %s
            """, (username, email))
            
            if user:
                # 生成新密码（这里简单示例，实际应该生成随机密码）
                new_password = '123456'
                hashed_password = hash_password(new_password)
                
                # 更新密码
                success = db.execute_update("""
                    UPDATE users SET password = %s
                    WHERE username = %s
                """, (hashed_password, username))
                
                if success:
                    # 这里应该发送邮件通知用户新密码
                    flash(f'密码已重置为：{new_password}，请尽快登录并修改密码', 'success')
                    return redirect(url_for('login'))
            
            flash('用户名或邮箱错误', 'error')
        except Error as e:
            flash('密码重置失败', 'error')
            print(f"Error resetting password: {e}")
    
    return render_template('reset_password.html')

# 修改评论路由
@app.route('/comment/<int:decision_id>', methods=['POST'])
@login_required
def add_comment(decision_id):
    """添加评论"""
    content = request.form.get('content')
    if not content:
        flash('评论内容不能为空', 'error')
        return redirect(url_for('decision_detail', decision_id=decision_id))
    
    db = Database()
    try:
        # 先检查决策是否存在
        decisions = db.execute_query("""
            SELECT decision_id FROM decisions 
            WHERE decision_id = %s
        """, (decision_id,))
        
        if not decisions:
            flash('决策不存在', 'error')
            return redirect(url_for('index'))
        
        # 添加评论
        success = db.execute_update("""
            INSERT INTO comments (decision_id, user_id, content)
            VALUES (%s, %s, %s)
        """, (decision_id, session['user_id'], content))
        
        if success:
            flash('评论发表成功', 'success')
        else:
            flash('评论发表失败', 'error')
    except Error as e:
        flash('评论发表失败', 'error')
        print(f"Error adding comment: {e}")
    
    return redirect(url_for('decision_detail', decision_id=decision_id))

@app.route('/admin/users')
@login_required
@admin_required
def user_management():
    """用户管理页面"""
    db = Database()
    try:
        users = db.execute_query("""
            SELECT * FROM users 
            ORDER BY create_time DESC
        """)
        return render_template('user_management.html', users=users)
    except Error as e:
        flash('获取用户列表失败', 'error')
        print(f"Error getting users: {e}")
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/user/<int:user_id>/update', methods=['POST'])
@login_required
@admin_required
def update_user_role(user_id):
    """更新用户角色"""
    new_role = request.form.get('role')
    new_status = request.form.get('status')
    
    if not new_role or not new_status:
        flash('参数错误', 'error')
        return redirect(url_for('user_management'))
    
    db = Database()
    try:
        success = db.execute_update("""
            UPDATE users 
            SET role = %s, status = %s
            WHERE user_id = %s
        """, (new_role, new_status, user_id))
        
        if success:
            flash('用户信息更新成功', 'success')
        else:
            flash('用户信息更新失败', 'error')
    except Error as e:
        flash('更新失败', 'error')
        print(f"Error updating user: {e}")
    
    return redirect(url_for('user_management'))

@app.route('/admin/settings')
@login_required
@admin_required
def system_settings():
    """系统设置页面"""
    db = Database()
    try:
        # 获取系统配置
        settings = db.execute_query("""
            SELECT * FROM system_settings
            WHERE id = 1
        """)
        
        return render_template('system_settings.html', 
                             settings=settings[0] if settings else {})
    except Error as e:
        flash('获取系统设置失败', 'error')
        print(f"Error getting system settings: {e}")
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/settings/update', methods=['POST'])
@login_required
@admin_required
def update_settings():
    """更新系统设置"""
    site_name = request.form.get('site_name')
    maintenance_mode = request.form.get('maintenance_mode', '0')
    
    db = Database()
    try:
        success = db.execute_update("""
            UPDATE system_settings
            SET site_name = %s,
                maintenance_mode = %s,
                update_time = CURRENT_TIMESTAMP
            WHERE id = 1
        """, (site_name, maintenance_mode))
        
        if success:
            flash('系统设置更新成功', 'success')
        else:
            flash('系统设置更新失败', 'error')
    except Error as e:
        flash('更新失败', 'error')
        print(f"Error updating settings: {e}")
    
    return redirect(url_for('system_settings'))

@app.route('/admin/decision/<int:decision_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_decision(decision_id):
    """编辑决策"""
    db = Database()
    try:
        if request.method == 'POST':
            title = request.form.get('title')
            content = request.form.get('content')
            status = request.form.get('status')
            
            if not title or not content:
                flash('标题和内容不能为空', 'error')
                return redirect(url_for('edit_decision', decision_id=decision_id))
            
            success = db.execute_update("""
                UPDATE decisions 
                SET title = %s, content = %s, status = %s
                WHERE decision_id = %s
            """, (title, content, status, decision_id))
            
            if success:
                flash('决策更新成功', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('决策更新失败', 'error')
        
        # GET请求，获取决策信息
        decisions = db.execute_query("""
            SELECT * FROM decisions WHERE decision_id = %s
        """, (decision_id,))
        
        if not decisions:
            flash('决策不存在', 'error')
            return redirect(url_for('admin_dashboard'))
            
        return render_template('edit_decision.html', decision=decisions[0])
        
    except Error as e:
        flash('操作失败', 'error')
        print(f"Error editing decision: {e}")
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/news/<int:news_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_news(news_id):
    """编辑资讯"""
    db = Database()
    try:
        if request.method == 'POST':
            title = request.form.get('title')
            content = request.form.get('content')
            category = request.form.get('category')
            
            if not title or not content:
                flash('标题和内容不能为空', 'error')
                return redirect(url_for('edit_news', news_id=news_id))
            
            success = db.execute_update("""
                UPDATE news 
                SET title = %s, content = %s, category = %s
                WHERE news_id = %s
            """, (title, content, category, news_id))
            
            if success:
                flash('资讯更新成功', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('资讯更新失败', 'error')
        
        # GET请求，获取资讯信息
        news_list = db.execute_query("""
            SELECT * FROM news WHERE news_id = %s
        """, (news_id,))
        
        if not news_list:
            flash('资讯不存在', 'error')
            return redirect(url_for('admin_dashboard'))
            
        return render_template('edit_news.html', news=news_list[0])
        
    except Error as e:
        flash('操作失败', 'error')
        print(f"Error editing news: {e}")
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/decision/analysis/<int:decision_id>')
@login_required
@admin_required
def decision_analysis(decision_id):
    db = Database()
    try:
        # 获取决策信息
        decision = db.execute_query("""
            SELECT d.*, u.username as creator_name
            FROM decisions d
            JOIN users u ON d.create_user_id = u.user_id
            WHERE d.decision_id = %s
        """, (decision_id,))

        if not decision:
            flash('决策不存在', 'error')
            return redirect(url_for('admin_dashboard'))

        # 获取投票统计（包括加权）
        votes = db.execute_query("""
            SELECT 
                v.vote_type,
                v.user_id,
                u.role,
                COALESCE(uba.vote_weight, 1.0) as vote_weight
            FROM votes v
            JOIN users u ON v.user_id = u.user_id
            LEFT JOIN user_behavior_analysis uba ON v.user_id = uba.user_id
            WHERE v.decision_id = %s
        """, (decision_id,))

        # 统计各类数据
        stats = {
            'total_votes': len(votes),
            'vote_distribution': {'support': 0, 'oppose': 0},
            'weighted_support': 0,
            'weighted_oppose': 0,
            'weighted_total': 0,
            'vote_by_role': {},
            'total_comments': 0,
            'comment_by_role': {}
        }

        # 计算投票统计
        for vote in votes:
            vote_type = vote['vote_type']
            role = vote['role']
            weight = float(vote['vote_weight'])

            # 原始投票统计
            stats['vote_distribution'][vote_type] = stats['vote_distribution'].get(vote_type, 0) + 1

            # 加权投票统计
            if vote_type == 'support':
                stats['weighted_support'] += weight
            else:
                stats['weighted_oppose'] += weight

            # 按角色统计
            if role not in stats['vote_by_role']:
                stats['vote_by_role'][role] = {'support': 0, 'oppose': 0}
            stats['vote_by_role'][role][vote_type] += 1

        stats['weighted_total'] = stats['weighted_support'] + stats['weighted_oppose']

        # 获取评论统计
        comments = db.execute_query("""
            SELECT DISTINCT 
                c.*, 
                u.username, 
                u.role
            FROM comments c
            JOIN users u ON c.user_id = u.user_id
            WHERE c.decision_id = %s
            ORDER BY c.create_time DESC
        """, (decision_id,))

        # 统计评论
        stats['total_comments'] = len(comments)
        for comment in comments:
            role = comment['role']
            stats['comment_by_role'][role] = stats['comment_by_role'].get(role, 0) + 1

        return render_template('decision_analysis.html',
                             decision=decision[0],
                             stats=stats,
                             comments=comments,
                             support_count=stats['vote_distribution']['support'],
                             oppose_count=stats['vote_distribution']['oppose'],
                             weighted_support=stats['weighted_support'],
                             weighted_oppose=stats['weighted_oppose'])

    except Error as e:
        flash('获取分析数据失败', 'error')
        print(f"Error in decision analysis: {e}")
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/user/analysis/<int:user_id>')
@login_required
@admin_required
def user_analysis(user_id):
    """用户行为分析页面"""
    db = Database()
    try:
        # 获取用户基本信息
        users = db.execute_query("""
            SELECT * FROM users WHERE user_id = %s
        """, (user_id,))
        
        if not users:
            flash('用户不存在', 'error')
            return redirect(url_for('admin_dashboard'))
            
        user = users[0]
        
        # 获取用户投票统计
        vote_stats = db.execute_query("""
            SELECT 
                d.title,
                v.vote_type,
                v.create_time
            FROM votes v
            JOIN decisions d ON v.decision_id = d.decision_id
            WHERE v.user_id = %s
            ORDER BY v.create_time DESC
        """, (user_id,))
        
        # 获取用户评论统计
        comment_stats = db.execute_query("""
            SELECT 
                d.title,
                c.content,
                c.create_time
            FROM comments c
            JOIN decisions d ON c.decision_id = d.decision_id
            WHERE c.user_id = %s
            ORDER BY c.create_time DESC
        """, (user_id,))
        
        # 获取用户提问统计
        question_stats = db.execute_query("""
            SELECT 
                n.title,
                q.content,
                q.create_time
            FROM questions q
            JOIN news n ON q.news_id = n.news_id
            WHERE q.user_id = %s
            ORDER BY q.create_time DESC
        """, (user_id,))
        
        # 处理统计数据
        stats = {
            'total_votes': len(vote_stats),
            'total_comments': len(comment_stats),
            'total_questions': len(question_stats),
            'vote_distribution': {},
            'activity_timeline': []
        }
        
        # 统计投票分布
        for vote in vote_stats:
            stats['vote_distribution'][vote['vote_type']] = \
                stats['vote_distribution'].get(vote['vote_type'], 0) + 1
        
        # 生成活动时间线
        for vote in vote_stats:
            stats['activity_timeline'].append({
                'type': '投票',
                'target': vote['title'],
                'action': vote['vote_type'],
                'time': vote['create_time']
            })
        
        for comment in comment_stats:
            stats['activity_timeline'].append({
                'type': '评论',
                'target': comment['title'],
                'action': comment['content'],
                'time': comment['create_time']
            })
            
        for question in question_stats:
            stats['activity_timeline'].append({
                'type': '提问',
                'target': question['title'],
                'action': question['content'],
                'time': question['create_time']
            })
        
        # 按时间排序
        stats['activity_timeline'].sort(key=lambda x: x['time'], reverse=True)
        
        return render_template('user_analysis.html',
                             user=user,
                             stats=stats,
                             vote_stats=vote_stats,
                             comment_stats=comment_stats,
                             question_stats=question_stats)
                             
    except Error as e:
        flash('获取分析数据失败', 'error')
        print(f"Error in user analysis: {e}")
        return redirect(url_for('admin_dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])  # 使用SHA256哈希
        
        db = Database()
        try:
            # 验证用户
            user = db.execute_query("""
                SELECT * FROM users 
                WHERE username = %s AND password = %s
            """, (username, password))
            
            if user:
                user = user[0]
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                session['role'] = user['role']
                flash('登录成功', 'success')
                return redirect(url_for('index'))
            else:
                flash('用户名或密码错误', 'error')
        except Error as e:
            flash('登录失败，请稍后重试', 'error')
            print(f"登录错误: {e}")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """用户注销"""
    session.clear()
    flash('已退出登录', 'success')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        role = request.form.get('role', 'student')
        
        if not all([username, password, email]):
            flash('请填写所有必填字段', 'error')
            return render_template('register.html')
            
        db = Database()
        try:
            # 检查用户名是否已存在
            existing_user = db.execute_query("""
                SELECT * FROM users WHERE username = %s
            """, (username,))
            
            if existing_user:
                flash('用户名已存在', 'error')
                return render_template('register.html')
            
            # 创建新用户
            password_md5 = hash_password(password)
            success = db.execute_update("""
                INSERT INTO users (username, password, email, role, status)
                VALUES (%s, %s, %s, %s, 'active')
            """, (username, password_md5, email, role))
            
            if success:
                flash('注册成功，请登录', 'success')
                return redirect(url_for('login'))
            else:
                flash('注册失败，请稍后重试', 'error')
                
        except Error as e:
            flash('注册失败，请稍后重试', 'error')
            print(f"Error in register: {e}")
            
    return render_template('register.html')

@app.route('/admin/behavior_analysis')
@login_required
@admin_required
def behavior_analysis():
    """用户行为分析页面"""
    db = Database()
    try:
        # 获取异常行为用户（使用子查询避免重复）
        abnormal_users = db.execute_query("""
            SELECT 
                u.username,
                u.role,
                uba.vote_pattern,
                uba.comment_ratio,
                uba.activity_score,
                uba.vote_weight,
                (
                    SELECT COUNT(*) 
                    FROM votes 
                    WHERE user_id = u.user_id
                ) as vote_count,
                (
                    SELECT COUNT(*) 
                    FROM comments 
                    WHERE user_id = u.user_id
                ) as comment_count
            FROM users u
            JOIN (
                SELECT DISTINCT user_id, vote_pattern, comment_ratio, activity_score, vote_weight
                FROM user_behavior_analysis
                WHERE vote_weight != 1.0
            ) uba ON u.user_id = uba.user_id
            ORDER BY uba.activity_score DESC
        """)
        
        # 获取投票统计（考虑权重）
        weighted_votes = db.execute_query("""
            SELECT 
                d.title,
                SUM(CASE WHEN v.vote_type = 'support' THEN COALESCE(uba.vote_weight, 1.0) ELSE 0 END) as weighted_support,
                SUM(CASE WHEN v.vote_type = 'oppose' THEN COALESCE(uba.vote_weight, 1.0) ELSE 0 END) as weighted_oppose,
                COUNT(DISTINCT v.user_id) as total_votes
            FROM votes v
            JOIN decisions d ON v.decision_id = d.decision_id
            LEFT JOIN user_behavior_analysis uba ON v.user_id = uba.user_id
            GROUP BY d.decision_id, d.title
            ORDER BY total_votes DESC
        """)
        
        return render_template('behavior_analysis.html',
                             abnormal_users=abnormal_users,
                             weighted_votes=weighted_votes)
                             
    except Error as e:
        flash('获取分析数据失败', 'error')
        print(f"Error in behavior analysis: {e}")
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/decision/analysis/report/<int:decision_id>')
@login_required
@admin_required
def generate_analysis_report(decision_id):
    """生成决策分析报告"""
    db = Database()
    try:
        # 获取决策信息
        decision = db.execute_query("""
            SELECT d.*, u.username as creator_name
            FROM decisions d
            JOIN users u ON d.create_user_id = u.user_id
            WHERE d.decision_id = %s
        """, (decision_id,))

        if not decision:
            flash('决策不存在', 'error')
            return redirect(url_for('admin_dashboard'))

        decision = decision[0]  # 获取第一条记录

        # 获取投票统计
        votes = db.execute_query("""
            SELECT 
                v.vote_type,
                v.user_id,
                u.role,
                u.username,
                COALESCE(uba.vote_weight, 1.0) as vote_weight
            FROM votes v
            JOIN users u ON v.user_id = u.user_id
            LEFT JOIN user_behavior_analysis uba ON v.user_id = uba.user_id
            WHERE v.decision_id = %s
        """, (decision_id,))

        # 获取评论
        comments = db.execute_query("""
            SELECT 
                c.*,
                u.username,
                u.role
            FROM comments c
            JOIN users u ON c.user_id = u.user_id
            WHERE c.decision_id = %s
            ORDER BY c.create_time DESC
        """, (decision_id,))

        # 计算投票统计数据
        total_votes = len(votes)
        support_votes = sum(1 for v in votes if v['vote_type'] == 'support')
        oppose_votes = total_votes - support_votes
        
        weighted_support = sum(float(v['vote_weight']) for v in votes if v['vote_type'] == 'support')
        weighted_oppose = sum(float(v['vote_weight']) for v in votes if v['vote_type'] == 'oppose')

        # 按角色统计投票
        role_votes = {}
        for vote in votes:
            role = vote['role']
            if role not in role_votes:
                role_votes[role] = {'support': 0, 'oppose': 0}
            role_votes[role][vote['vote_type']] += 1

        # 准备提示信息
        prompt = f"""
请根据以下决策信息生成一份详细的分析报告：

决策标题：{decision['title']}
决策内容：{decision['content']}

投票情况：
- 总投票数：{total_votes}
- 支持票数：{support_votes} ({support_votes/total_votes*100:.1f}%)
- 反对票数：{oppose_votes} ({oppose_votes/total_votes*100:.1f}%)

加权投票情况：
- 支持权重：{weighted_support:.1f}
- 反对权重：{weighted_oppose:.1f}
- 加权支持率：{(weighted_support/(weighted_support+weighted_oppose)*100):.1f}%

各角色投票分布：
{chr(10).join([f"- {role}: 支持 {votes['support']}票，反对 {votes['oppose']}票" for role, votes in role_votes.items()])}

评论摘要：
{chr(10).join([f"- {c['username']}({c['role']}): {c['content']}" for c in comments])}

请从以下几个方面进行分析：
1. 总体投票趋势分析
2. 不同角色的投票倾向及其可能的原因
3. 评论内容的关键观点归纳
4. 存在的问题和改进建议
5. 最终决策建议（是否通过、附加条件等）

请用markdown格式输出，保持客观专业的语气。
"""

        try:
            # 调用 DeepSeek API 生成报告
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的教育决策分析师，擅长分析投票数据和评论内容，生成客观公正的分析报告。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            # 获取生成的报告
            report = response.choices[0].message.content

            return render_template('decision_report.html',
                                decision=decision,
                                report=report,
                                now=datetime.now)

        except Exception as e:
            print(f"API调用错误: {e}")
            flash('生成报告失败：API调用错误', 'error')
            return redirect(url_for('decision_analysis', decision_id=decision_id))

    except Exception as e:
        flash('生成报告失败：数据获取错误', 'error')
        print(f"Error generating report: {e}")
        return redirect(url_for('decision_analysis', decision_id=decision_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
