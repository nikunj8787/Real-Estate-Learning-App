import streamlit as st
import sqlite3
import hashlib
import json
from datetime import datetime
import requests
import pandas as pd
import re

# Page configuration
st.set_page_config(
    page_title="RealEstateGuru",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'dashboard'
if 'current_module' not in st.session_state:
    st.session_state.current_module = None
if 'show_register' not in st.session_state:
    st.session_state.show_register = False
if 'user_points' not in st.session_state:
    st.session_state.user_points = 0
if 'user_badges' not in st.session_state:
    st.session_state.user_badges = []
if 'quiz_score' not in st.session_state:
    st.session_state.quiz_score = 0
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'quiz_answers' not in st.session_state:
    st.session_state.quiz_answers = {}
if 'quiz_started' not in st.session_state:
    st.session_state.quiz_started = False

# Database setup
DATABASE_PATH = "realestate_guru.db"

def migrate_database():
    """Migrate database to add missing columns"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        # Add columns to users table
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'points' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0")
        if 'badges' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN badges TEXT DEFAULT '[]'")
        if 'streak_days' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN streak_days INTEGER DEFAULT 0")
        
        # Add columns to modules table
        cursor.execute("PRAGMA table_info(modules)")
        module_columns = [col[1] for col in cursor.fetchall()]
        if 'youtube_url' not in module_columns:
            cursor.execute("ALTER TABLE modules ADD COLUMN youtube_url TEXT")
        
        conn.commit()
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        conn.close()

def init_database():
    """Initialize database with tables and content"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            created_date TEXT NOT NULL,
            last_login TEXT,
            active INTEGER DEFAULT 1,
            points INTEGER DEFAULT 0,
            badges TEXT DEFAULT '[]',
            streak_days INTEGER DEFAULT 0
        )
    """)
    
    # Create modules table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            difficulty TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT,
            youtube_url TEXT,
            order_index INTEGER DEFAULT 0,
            created_date TEXT NOT NULL,
            updated_date TEXT,
            active INTEGER DEFAULT 1
        )
    """)
    
    # Create quizzes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            explanation TEXT,
            created_date TEXT NOT NULL,
            FOREIGN KEY (module_id) REFERENCES modules (id)
        )
    """)
    
    # Create user progress table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            module_id INTEGER NOT NULL,
            progress_percentage REAL DEFAULT 0,
            completed INTEGER DEFAULT 0,
            started_date TEXT,
            completed_date TEXT,
            quiz_score REAL DEFAULT 0,
            quiz_attempts INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (module_id) REFERENCES modules (id)
        )
    """)
    
    # Create user achievements table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_type TEXT NOT NULL,
            achievement_name TEXT NOT NULL,
            points_earned INTEGER DEFAULT 0,
            earned_date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Create content research table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content_research (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            content TEXT NOT NULL,
            sources TEXT NOT NULL,
            created_date TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    """)
    
    # Insert default admin user
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    admin_count = cursor.fetchone()[0]
    if admin_count == 0:
        admin_password = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute("""
            INSERT INTO users (username, email, password, role, created_date, points, badges, streak_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("admin", "admin@realestateguruapp.com", admin_password, "admin", datetime.now().isoformat(), 1000, '["Admin Master", "System Creator"]', 1))
    
    # Insert sample modules
    cursor.execute("SELECT COUNT(*) FROM modules")
    module_count = cursor.fetchone()[0]
    if module_count == 0:
        modules_data = [
            ('Real Estate Fundamentals', 'Introduction to real estate basics', 'Beginner', 'Fundamentals', 'Learn about property types, market dynamics...', 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 1),
            ('Legal Framework & RERA', 'Understanding real estate regulations', 'Intermediate', 'Legal', 'Learn about RERA compliance...', 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 2)
        ]
        for module in modules_data:
            cursor.execute("""
                INSERT INTO modules (title, description, difficulty, category, content, youtube_url, order_index, created_date, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (*module, datetime.now().isoformat()))
    
    # Insert sample quiz questions
    cursor.execute("SELECT COUNT(*) FROM quizzes")
    quiz_count = cursor.fetchone()[0]
    if quiz_count == 0:
        quiz_questions = [
            (1, "What is the primary focus of real estate?", "Land only", "Land and structures", "Buildings only", "Financial aspects", "B", "Real estate includes land and permanent structures", datetime.now().isoformat()),
            (1, "Which year was RERA enacted?", "2015", "2016", "2017", "2018", "B", "RERA was enacted in 2016", datetime.now().isoformat()),
            (2, "What does RERA stand for?", "Real Estate Regulation Act", "Real Estate Regulatory Authority", "Real Estate Registration Act", "Real Estate Rights Act", "A", "Real Estate Regulation Act", datetime.now().isoformat()),
            (2, "What percentage must developers deposit in escrow?", "50%", "60%", "70%", "80%", "C", "70% must be deposited", datetime.now().isoformat())
        ]
        for question in quiz_questions:
            cursor.execute("""
                INSERT INTO quizzes (module_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, question)
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DATABASE_PATH)

# CSS Styling
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
}

.module-card {
    background: white;
    padding: 1.5rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 1rem;
    border-left: 4px solid #2a5298;
}

.feature-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 15px;
    color: white;
    text-align: center;
    margin-bottom: 1rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
}

.progress-bar {
    background: #f0f0f0;
    border-radius: 10px;
    height: 20px;
    overflow: hidden;
}

.progress-fill {
    background: linear-gradient(90deg, #4CAF50, #45a049);
    height: 100%;
    transition: width 0.3s ease;
}

.sidebar-logo {
    text-align: center;
    padding: 1rem;
    background: #2a5298;
    color: white;
    border-radius: 10px;
    margin-bottom: 1rem;
}

.metric-card {
    background: white;
    padding: 1rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    text-align: center;
}

.content-viewer {
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin: 1rem 0;
}

.badge {
    background: linear-gradient(45deg, #FFD700, #FFA500);
    color: white;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.8rem;
    margin: 0.2rem;
    display: inline-block;
}

.points-display {
    background: linear-gradient(45deg, #4CAF50, #45a049);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 25px;
    font-weight: bold;
    text-align: center;
}

.quiz-question {
    background: #f8f9fa;
    padding: 1.5rem;
    border-radius: 10px;
    margin: 1rem 0;
    border-left: 4px solid #2a5298;
}

.quiz-option {
    background: white;
    padding: 0.8rem;
    margin: 0.5rem 0;
    border-radius: 8px;
    border: 2px solid #e0e0e0;
    cursor: pointer;
    transition: all 0.3s ease;
}

.quiz-option:hover {
    border-color: #2a5298;
    background: #f0f2f6;
}

.youtube-container {
    position: relative;
    width: 100%;
    height: 0;
    padding-bottom: 56.25%;
    margin: 1rem 0;
}

.youtube-container iframe {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# DeepSeek Chat Integration
class DeepSeekChat:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        
    def get_response(self, user_input):
        """Get response from DeepSeek API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": user_input}],
            "temperature": 0.7,
            "max_tokens": 1000,
            "stream": False
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except:
            return "Sorry, I'm having trouble connecting to the AI service."

# Authentication functions
def authenticate_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute("""
        SELECT id, username, role, points, badges 
        FROM users 
        WHERE username = ? AND password = ? AND active = 1
    """, (username, hashed_password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        st.session_state.user_id = user[0]
        st.session_state.username = user[1]
        st.session_state.user_role = user[2]
        st.session_state.user_points = user[3] or 0
        st.session_state.user_badges = json.loads(user[4]) if user[4] else []
        return True
    return False

def register_user(username, email, password, user_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ? OR email = ?", (username, email))
        if cursor.fetchone()[0] > 0:
            return False
            
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("""
            INSERT INTO users (username, email, password, role, created_date, points, badges)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username, email, hashed_password, user_type, datetime.now().isoformat(), 100, '["Welcome Learner"]'))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

# Module functions
def get_available_modules():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, description, difficulty, category, youtube_url
        FROM modules 
        WHERE active = 1
        ORDER BY order_index
    """)
    modules = cursor.fetchall()
    conn.close()
    return [
        {
            'id': module[0],
            'title': module[1],
            'description': module[2],
            'difficulty': module[3],
            'category': module[4],
            'youtube_url': module[5]
        }
        for module in modules
    ]

def get_module_content(module_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT title, description, content, difficulty, category, youtube_url
        FROM modules 
        WHERE id = ? AND active = 1
    """, (module_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            'title': result[0],
            'description': result[1],
            'content': result[2],
            'difficulty': result[3],
            'category': result[4],
            'youtube_url': result[5]
        }
    return None

# Quiz functions
def get_quiz_questions(module_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, question, option_a, option_b, option_c, option_d, correct_answer, explanation
        FROM quizzes
        WHERE module_id = ?
    """, (module_id,))
    questions = cursor.fetchall()
    conn.close()
    return [
        {
            'id': q[0],
            'question': q[1],
            'options': {'A': q[2], 'B': q[3], 'C': q[4], 'D': q[5]},
            'correct_answer': q[6],
            'explanation': q[7]
        }
        for q in questions
    ]

def add_quiz_question(module_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO quizzes (module_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (module_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation, datetime.now().isoformat()))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

# UI Components
def show_login_form():
    st.subheader("🔐 Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted and authenticate_user(username, password):
            st.session_state.authenticated = True
            st.success("Login successful!")
            st.rerun()
        elif submitted:
            st.error("Invalid credentials")
    
    if st.button("Register New Account"):
        st.session_state.show_register = True
        st.rerun()

def show_registration_form():
    st.subheader("📝 Register")
    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        user_type = st.selectbox("User Type", ["student", "professional"])
        submitted = st.form_submit_button("Register")
        
        if submitted:
            if password != confirm_password:
                st.error("Passwords don't match")
            elif register_user(username, email, password, user_type):
                st.success("Registration successful! Please login.")
                st.session_state.show_register = False
                st.rerun()
            else:
                st.error("Registration failed - Username or email already exists")
    
    if st.button("Back to Login"):
        st.session_state.show_register = False
        st.rerun()

def show_navigation():
    st.markdown('<div class="sidebar-logo"><h3>🏠 RealEstateGuru</h3></div>', unsafe_allow_html=True)
    st.write(f"Welcome, **{st.session_state.username}**!")
    st.write(f"Role: *{st.session_state.user_role.title()}*")
    
    if st.session_state.user_role != 'admin':
        st.markdown(f'<div class="points-display">🏆 {st.session_state.user_points} Points</div>', unsafe_allow_html=True)
        if st.session_state.user_badges:
            st.write("**Badges:**")
            for badge in st.session_state.user_badges:
                st.markdown(f'<span class="badge">🏅 {badge}</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.session_state.user_role == 'admin':
        st.subheader("Admin Panel")
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.current_page = "admin_dashboard"
            st.rerun()
        if st.button("📚 Content Management", use_container_width=True):
            st.session_state.current_page = "content_management"
            st.rerun()
        if st.button("👥 User Management", use_container_width=True):
            st.session_state.current_page = "user_management"
            st.rerun()
        if st.button("❓ Quiz Management", use_container_width=True):
            st.session_state.current_page = "quiz_management"
            st.rerun()
    else:
        st.subheader("Learning Modules")
        modules = get_available_modules()
        for module in modules:
            if st.button(f"{module['title']}", key=f"module_{module['id']}", use_container_width=True):
                st.session_state.current_module = module['id']
                st.session_state.current_page = "module_content"
                st.rerun()
        
        if st.button("📊 My Progress", use_container_width=True):
            st.session_state.current_page = "progress"
            st.rerun()
        if st.button("🏆 Take Quiz", use_container_width=True):
            st.session_state.current_page = "quiz"
            st.rerun()
    
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

def show_welcome_page():
    st.markdown('<div class="main-header"><h1>Welcome to RealEstateGuru</h1></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>🎯 Learn & Earn Points</h3>
            <p>Complete modules and quizzes to earn points and badges</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🎥 Video Learning</h3>
            <p>Watch embedded videos in each learning module</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 Progress Tracking</h3>
            <p>Track your learning progress with visual charts</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.info("💡 **Get Started**: Register as a student or login as admin (admin/admin123)")

def show_user_dashboard():
    st.markdown('<div class="main-header"><h1>Your Learning Dashboard</h1></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🏆 Points", st.session_state.user_points)
    with col2:
        st.metric("📚 Modules", "5")
    with col3:
        st.metric("🏅 Badges", len(st.session_state.user_badges))
    
    st.subheader("Available Learning Modules")
    modules = get_available_modules()
    for module in modules:
        with st.expander(module['title']):
            st.write(module['description'])
            if st.button("Study", key=f"study_{module['id']}"):
                st.session_state.current_module = module['id']
                st.session_state.current_page = "module_content"
                st.rerun()

def show_module_content():
    module_id = st.session_state.get('current_module')
    if not module_id:
        st.error("No module selected")
        return
    
    module = get_module_content(module_id)
    if not module:
        st.error("Module not found")
        return
    
    st.markdown(f'<div class="main-header"><h1>{module["title"]}</h1></div>', unsafe_allow_html=True)
    
    if module['youtube_url']:
        st.subheader("📹 Module Video")
        video_id = module['youtube_url'].split("v=")[-1]
        st.markdown(f"""
        <div class="youtube-container">
            <iframe src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe>
        </div>
        """, unsafe_allow_html=True)
    
    if module['content']:
        st.subheader("📖 Module Content")
        st.markdown(module['content'])
    
    if st.button("🏆 Take Quiz"):
        st.session_state.current_page = "quiz"
        st.rerun()
    if st.button("← Back to Dashboard"):
        st.session_state.current_page = "dashboard"
        st.rerun()

def show_quiz():
    module_id = st.session_state.get('current_module')
    if not module_id:
        st.error("No module selected")
        return
    
    module = get_module_content(module_id)
    if not module:
        st.error("Module not found")
        return
    
    st.markdown(f'<div class="main-header"><h1>🏆 Quiz: {module["title"]}</h1></div>', unsafe_allow_html=True)
    
    questions = get_quiz_questions(module_id)
    if not questions:
        st.warning("No questions available for this module")
        if st.button("← Back to Module"):
            st.session_state.current_page = "module_content"
            st.rerun()
        return
    
    if not st.session_state.quiz_started:
        st.subheader("📋 Quiz Information")
        st.write(f"**Questions:** {len(questions)}")
        st.write("**Instructions:** Answer all questions to the best of your ability")
        
        if st.button("🚀 Start Quiz", use_container_width=True):
            st.session_state.quiz_started = True
            st.session_state.current_question = 0
            st.session_state.quiz_answers = {}
            st.rerun()
    else:
        current_q = st.session_state.current_question
        if current_q < len(questions):
            question = questions[current_q]
            st.subheader(f"Question {current_q+1} of {len(questions)}")
            st.write(f"**{question['question']}**")
            
            selected_answer = st.radio(
                "Select your answer:",
                options=list(question['options'].keys()),
                format_func=lambda x: f"{x}. {question['options'][x]}",
                key=f"q_{current_q}"
            )
            
            if st.button("Next →"):
                st.session_state.quiz_answers[current_q] = selected_answer
                st.session_state.current_question += 1
                st.rerun()
        else:
            correct_answers = 0
            for i, question in enumerate(questions):
                if st.session_state.quiz_answers.get(i) == question['correct_answer']:
                    correct_answers += 1
            
            st.subheader("🎉 Quiz Completed!")
            st.metric("Your Score", f"{correct_answers}/{len(questions)}")
            
            if st.button("🔄 Retake Quiz"):
                st.session_state.quiz_started = False
                st.session_state.current_question = 0
                st.rerun()
            if st.button("← Back to Module"):
                st.session_state.quiz_started = False
                st.session_state.current_page = "module_content"
                st.rerun()

def show_quiz_management():
    st.markdown('<div class="main-header"><h1>❓ Quiz Management</h1></div>', unsafe_allow_html=True)
    
    modules = get_available_modules()
    selected_module = st.selectbox("Select Module", [f"{m['id']}: {m['title']}" for m in modules])
    
    if selected_module:
        module_id = int(selected_module.split(':')[0])
        module_title = next(m['title'] for m in modules if m['id'] == module_id)
        
        st.subheader(f"Add Question to: {module_title}")
        with st.form("add_question_form"):
            question = st.text_area("Question")
            col1, col2 = st.columns(2)
            with col1:
                option_a = st.text_input("Option A")
                option_c = st.text_input("Option C")
            with col2:
                option_b = st.text_input("Option B")
                option_d = st.text_input("Option D")
            correct_answer = st.selectbox("Correct Answer", ["A", "B", "C", "D"])
            explanation = st.text_area("Explanation")
            
            if st.form_submit_button("➕ Add Question"):
                if question and option_a and option_b and option_c and option_d:
                    if add_quiz_question(module_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation):
                        st.success("Question added successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to add question")
                else:
                    st.error("Please fill all fields")
        
        st.subheader("Existing Questions")
        questions = get_quiz_questions(module_id)
        if questions:
            for i, q in enumerate(questions):
                with st.expander(f"Question {i+1}"):
                    st.write(f"**{q['question']}**")
                    st.write(f"A) {q['options']['A']}")
                    st.write(f"B) {q['options']['B']}")
                    st.write(f"C) {q['options']['C']}")
                    st.write(f"D) {q['options']['D']}")
                    st.write(f"**Correct Answer:** {q['correct_answer']}")
                    st.write(f"**Explanation:** {q['explanation']}")
        else:
            st.info("No questions available for this module")

def main():
    # Run database setup
    migrate_database()
    init_database()
    
    # Sidebar
    with st.sidebar:
        if not st.session_state.authenticated:
            if st.session_state.get('show_register', False):
                show_registration_form()
            else:
                show_login_form()
        else:
            show_navigation()
    
    # Main content
    if not st.session_state.authenticated:
        show_welcome_page()
    else:
        page = st.session_state.get('current_page', 'dashboard')
        if page == 'dashboard':
            if st.session_state.user_role == 'admin':
                st.markdown('<div class="main-header"><h1>Admin Dashboard</h1></div>', unsafe_allow_html=True)
                st.write("Welcome to the admin dashboard")
            else:
                show_user_dashboard()
        elif page == 'module_content':
            show_module_content()
        elif page == 'quiz':
            show_quiz()
        elif page == 'quiz_management':
            show_quiz_management()
        elif page == 'content_management':
            st.markdown('<div class="main-header"><h1>Content Management</h1></div>', unsafe_allow_html=True)
            st.write("Module editing functionality")
        elif page == 'user_management':
            st.markdown('<div class="main-header"><h1>User Management</h1></div>', unsafe_allow_html=True)
            st.write("User management functionality")
        elif page == 'progress':
            st.markdown('<div class="main-header"><h1>Your Progress</h1></div>', unsafe_allow_html=True)
            st.write("Progress tracking charts")

if __name__ == "__main__":
    main()
