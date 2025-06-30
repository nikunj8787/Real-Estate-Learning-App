import streamlit as st
import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
import requests
import os

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

# Database setup
DATABASE_PATH = "realestate_guru.db"

def init_database():
    """Initialize database with tables and default data"""
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
            active INTEGER DEFAULT 1
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
            order_index INTEGER DEFAULT 0,
            created_date TEXT NOT NULL,
            updated_date TEXT,
            active INTEGER DEFAULT 1
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
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (module_id) REFERENCES modules (id)
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
    
    # Insert default admin user if doesn't exist
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    admin_count = cursor.fetchone()[0]
    
    if admin_count == 0:
        admin_password = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute("""
            INSERT INTO users (username, email, password, role, created_date)
            VALUES (?, ?, ?, ?, ?)
        """, ("admin", "admin@realestateguruapp.com", admin_password, "admin", datetime.now().isoformat()))
    
    # Insert default modules if they don't exist
    cursor.execute("SELECT COUNT(*) FROM modules")
    module_count = cursor.fetchone()[0]
    
    if module_count == 0:
        default_modules = [
            ('Real Estate Fundamentals', 'Introduction to real estate basics, stakeholders, and market overview', 'Beginner', 'Fundamentals', 'Complete introduction to real estate industry in India...', 1),
            ('Legal Framework & RERA', 'Comprehensive guide to RERA, legal compliance, and regulatory framework', 'Intermediate', 'Legal Framework', 'Understanding RERA Act 2016 and its implications...', 2),
            ('Property Measurements', 'Carpet area vs built-up area, BIS standards, and floor plan reading', 'Beginner', 'Measurements', 'Learn about different property measurement standards...', 3),
            ('Valuation & Finance', 'Property valuation methods, home loans, and taxation', 'Intermediate', 'Finance', 'Master property valuation techniques and financing options...', 4),
            ('Land & Development Laws', 'GDCR, municipal bylaws, FSI/TDR calculations, and zoning', 'Advanced', 'Legal Framework', 'Deep dive into land development regulations...', 5)
        ]
        
        for module in default_modules:
            cursor.execute("""
                INSERT INTO modules (title, description, difficulty, category, content, order_index, created_date, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (*module, datetime.now().isoformat()))
    
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

.chat-container {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 1rem;
    margin: 1rem 0;
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
</style>
""", unsafe_allow_html=True)

# DeepSeek Chat Integration
class DeepSeekChat:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        
    def get_response(self, user_input, context="real estate education"):
        """Get response from DeepSeek API"""
        
        system_prompt = """You are an expert Real Estate Education Assistant specializing in Indian real estate laws, regulations, and practices. You provide accurate, helpful, and educational responses about:

- RERA (Real Estate Regulation and Development Act) compliance
- Property valuation methods and techniques
- Legal documentation and procedures
- Investment strategies and market analysis
- Construction and technical aspects
- Taxation and financial planning
- Property measurements and standards
- Dispute resolution and consumer rights

Always provide practical, actionable advice while mentioning relevant legal frameworks and current market conditions in India."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.7,
            "max_tokens": 1000,
            "stream": False
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            return f"Sorry, I'm having trouble connecting to the AI service. Error: {str(e)}"

# Content Research Module
class ContentResearcher:
    def __init__(self):
        self.research_topics = [
            "RERA compliance updates",
            "Property valuation methods",
            "Real estate market trends",
            "Legal framework changes",
            "Construction technology",
            "Green building standards",
            "Investment strategies",
            "Taxation updates",
            "Documentation processes",
            "Dispute resolution"
        ]
    
    def research_topics(self, selected_topics):
        """Research selected topics and return structured content"""
        results = {}
        
        for topic in selected_topics:
            # Mock research results
            results[topic] = {
                "key_points": [
                    f"Key insight 1 about {topic}",
                    f"Key insight 2 about {topic}",
                    f"Key insight 3 about {topic}",
                    f"Key insight 4 about {topic}",
                    f"Key insight 5 about {topic}"
                ],
                "sources": [
                    {
                        "title": f"Research Article on {topic}",
                        "url": "https://example.com/research",
                        "date": datetime.now().strftime("%Y-%m-%d")
                    }
                ],
                "last_updated": datetime.now().isoformat()
            }
            
        return results

# Authentication functions
def authenticate_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    cursor.execute("""
        SELECT id, username, role FROM users 
        WHERE username = ? AND password = ? AND active = 1
    """, (username, hashed_password))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        st.session_state.user_id = user[0]
        st.session_state.username = user[1]
        st.session_state.user_role = user[2]
        return True
    
    return False

def register_user(username, email, password, user_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute("""
            INSERT INTO users (username, email, password, role, created_date)
            VALUES (?, ?, ?, ?, ?)
        """, (username, email, hashed_password, user_type, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def get_available_modules():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, description, difficulty, category 
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
            'category': module[4]
        }
        for module in modules
    ]

def add_module(title, description, difficulty, category):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO modules (title, description, difficulty, category, created_date, active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (title, description, difficulty, category, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def delete_module(module_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE modules SET active = 0 WHERE id = ?", (module_id,))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

# Main UI Functions
def show_login_form():
    st.subheader("🔐 Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if authenticate_user(username, password):
                st.session_state.authenticated = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")
    
    st.divider()
    
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
                st.error("Registration failed")
    
    if st.button("Back to Login"):
        st.session_state.show_register = False
        st.rerun()

def show_navigation():
    st.markdown('<div class="sidebar-logo"><h3>🏠 RealEstateGuru</h3></div>', unsafe_allow_html=True)
    st.write(f"Welcome, **{st.session_state.username}**!")
    
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
        
        if st.button("🔍 Content Research", use_container_width=True):
            st.session_state.current_page = "content_research"
            st.rerun()
    else:
        st.subheader("Learning Modules")
        modules = get_available_modules()
        
        for module in modules:
            if st.button(f"📚 {module['title']}", key=f"module_{module['id']}", use_container_width=True):
                st.session_state.current_module = module['id']
                st.session_state.current_page = "module_content"
                st.rerun()
        
        st.divider()
        
        if st.button("📊 My Progress", use_container_width=True):
            st.session_state.current_page = "progress"
            st.rerun()
        
        if st.button("🏆 Assessments", use_container_width=True):
            st.session_state.current_page = "assessments"
            st.rerun()
    
    st.divider()
    
    if st.button("🤖 AI Assistant", use_container_width=True):
        st.session_state.current_page = "ai_assistant"
        st.rerun()
    
    if st.button("🚪 Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

def show_welcome_page():
    st.markdown('<div class="main-header"><h1>Welcome to RealEstateGuru</h1><p>Your Complete Real Estate Education Platform</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="module-card">
            <h3>🎯 Beginner Track</h3>
            <p>Start from basics with guided learning paths covering fundamentals of real estate, legal frameworks, and basic concepts.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="module-card">
            <h3>🚀 Intermediate Track</h3>
            <p>Deepen your knowledge with advanced topics including valuation methods, financial modeling, and regulatory compliance.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="module-card">
            <h3>🏆 Advanced Track</h3>
            <p>Master complex topics like dispute resolution, investment strategies, and become a real estate expert.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Key Features")
        st.markdown("""
        - 📚 **Comprehensive Curriculum**: 11 detailed modules covering all aspects of Indian real estate
        - 🎮 **Gamified Learning**: Points, badges, and leaderboards to keep you engaged
        - 📱 **Multi-Platform Access**: Learn on desktop, tablet, or mobile
        - 🏅 **Certification**: LinkedIn-shareable certificates upon completion
        """)
    
    with col2:
        st.subheader("🚀 Advanced Features")
        st.markdown("""
        - 🤖 **AI Assistant**: Get instant help with your queries using advanced AI
        - 📊 **Progress Tracking**: Monitor your learning journey with detailed analytics
        - 🎥 **Rich Media**: Videos, infographics, and interactive content
        - 👥 **Expert Support**: Access to real estate professionals and mentors
        """)

def show_user_dashboard():
    st.markdown('<div class="main-header"><h1>Your Learning Dashboard</h1></div>', unsafe_allow_html=True)
    
    # Progress Overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Modules Completed", "3/11", "2 this week")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Points", "1,250", "+150")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Current Streak", "7 days", "+1")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Certificates", "1", "+1")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Available Modules
    st.subheader("📚 Available Learning Modules")
    
    modules = get_available_modules()
    
    for module in modules:
        with st.expander(f"{module['title']} ({module['difficulty']})"):
            st.write(f"**Category:** {module['category']}")
            st.write(f"**Description:** {module['description']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Start Learning", key=f"start_{module['id']}"):
                    st.success(f"Starting {module['title']} module!")
            
            with col2:
                progress = 0  # Mock progress
                st.progress(progress, text=f"Progress: {progress}%")

def show_admin_dashboard():
    st.markdown('<div class="main-header"><h1>Admin Dashboard</h1></div>', unsafe_allow_html=True)
    
    # System Overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", "1,247", "+23 this week")
    
    with col2:
        st.metric("Active Modules", "11", "2 updated")
    
    with col3:
        st.metric("Completion Rate", "78%", "+5%")
    
    with col4:
        st.metric("System Health", "98.5%", "+0.5%")
    
    st.markdown("---")
    
    # Recent Activity
    st.subheader("📋 Recent System Activity")
    
    activities = [
        {"time": "2 hours ago", "action": "New user registered", "user": "john_doe"},
        {"time": "4 hours ago", "action": "Module completed", "user": "jane_smith"},
        {"time": "6 hours ago", "action": "Content updated", "user": "admin"},
        {"time": "1 day ago", "action": "New module added", "user": "admin"}
    ]
    
    for activity in activities:
        st.markdown(f"""
        <div class="module-card">
            <strong>{activity['time']}</strong> - {activity['action']} by {activity['user']}
        </div>
        """, unsafe_allow_html=True)

def show_content_management():
    st.markdown('<div class="main-header"><h1>Content Management</h1></div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📚 Manage Modules", "➕ Add New Module"])
    
    with tab1:
        st.subheader("Existing Modules")
        
        modules = get_available_modules()
        
        for module in modules:
            with st.expander(f"{module['title']} ({module['difficulty']})"):
                st.write(f"**Description:** {module['description']}")
                st.write(f"**Category:** {module['category']}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✏️ Edit", key=f"edit_{module['id']}"):
                        st.info("Edit functionality would be implemented here")
                
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{module['id']}"):
                        if delete_module(module['id']):
                            st.success("Module deleted!")
                            st.rerun()
    
    with tab2:
        st.subheader("Add New Module")
        
        with st.form("add_module_form"):
            title = st.text_input("Module Title")
            description = st.text_area("Description")
            difficulty = st.selectbox("Difficulty Level", ["Beginner", "Intermediate", "Advanced"])
            category = st.selectbox("Category", [
                "Fundamentals",
                "Legal Framework",
                "Property Measurements",
                "Valuation & Finance",
                "Technical & Construction",
                "Transactions & Documentation",
                "Property Management",
                "Brokerage & Agency",
                "Digital Tools",
                "Case Studies",
                "Sustainability"
            ])
            
            submitted = st.form_submit_button("Add Module")
            
            if submitted and title and description:
                if add_module(title, description, difficulty, category):
                    st.success("Module added successfully!")
                    st.rerun()
                else:
                    st.error("Failed to add module")

def show_user_management():
    st.markdown('<div class="main-header"><h1>User Management</h1></div>', unsafe_allow_html=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, username, email, role, created_date, last_login, active
        FROM users
        ORDER BY created_date DESC
    """)
    
    users = cursor.fetchall()
    conn.close()
    
    st.subheader(f"Total Users: {len(users)}")
    
    for user in users:
        with st.expander(f"{user[1]} ({user[3]})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Email:** {user[2]}")
                st.write(f"**Role:** {user[3]}")
                st.write(f"**Joined:** {user[4]}")
            
            with col2:
                st.write(f"**Last Login:** {user[5] or 'Never'}")
                st.write(f"**Status:** {'Active' if user[6] else 'Inactive'}")
                
                if st.button(f"{'Deactivate' if user[6] else 'Activate'}", key=f"toggle_{user[0]}"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET active = ? WHERE id = ?", (0 if user[6] else 1, user[0]))
                    conn.commit()
                    conn.close()
                    st.rerun()

def show_content_research():
    st.markdown('<div class="main-header"><h1>Content Research</h1></div>', unsafe_allow_html=True)
    
    researcher = ContentResearcher()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Research Topics")
        selected_topics = st.multiselect("Select Topics to Research", researcher.research_topics)
        
        if st.button("Start Research"):
            if selected_topics:
                with st.spinner("Researching content..."):
                    results = researcher.research_topics(selected_topics)
                    st.session_state.research_results = results
                    st.success("Research completed!")
            else:
                st.warning("Please select at least one topic")
    
    with col2:
        if 'research_results' in st.session_state:
            st.subheader("Research Results")
            
            for topic, content in st.session_state.research_results.items():
                with st.expander(f"📋 {topic}"):
                    st.write("**Key Points:**")
                    for point in content['key_points']:
                        st.write(f"• {point}")
                    
                    if st.button(f"Add to Module", key=f"research_{topic}"):
                        st.success("Content would be added to selected module!")

def show_ai_assistant():
    st.markdown('<div class="main-header"><h1>🤖 AI Assistant</h1></div>', unsafe_allow_html=True)
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Get DeepSeek API key from Streamlit secrets or environment
    try:
        api_key = st.secrets.get("DEEPSEEK_API_KEY", "sk-54bd3323c4d14bf08b941f0bff7a47d5")
    except:
        api_key = "sk-54bd3323c4d14bf08b941f0bff7a47d5"
    
    deepseek_chat = DeepSeekChat(api_key)
    
    # Display chat history
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            st.markdown(f"**You:** {message['content']}")
        else:
            st.markdown(f"**AI Assistant:** {message['content']}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input("Ask me anything about real estate:", key="chat_input", placeholder="e.g., What is RERA and how does it protect homebuyers?")
    
    with col2:
        send_clicked = st.button("Send", use_container_width=True)
    
    if send_clicked and user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })
        
        # Get AI response
        with st.spinner("Thinking..."):
            response = deepseek_chat.get_response(user_input)
            
            # Add AI response to history
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response
            })
        
        st.rerun()
    
    # Quick questions
    st.subheader("💡 Quick Questions")
    
    quick_questions = [
        "What is RERA and how does it protect homebuyers?",
        "How do I calculate property valuation?",
        "What are the different types of property documentation?",
        "What is FSI and TDR in real estate?",
        "How do I invest in REITs?",
        "What are the tax implications of property investment?",
        "How do I conduct due diligence before buying property?",
        "What are green building certifications in India?"
    ]
    
    cols = st.columns(2)
    
    for i, question in enumerate(quick_questions):
        with cols[i % 2]:
            if st.button(question, key=f"quick_{i}"):
                # Add question to chat
                st.session_state.chat_history.append({
                    'role': 'user',
                    'content': question
                })
                
                # Get AI response
                with st.spinner("Getting answer..."):
                    response = deepseek_chat.get_response(question)
                    
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': response
                    })
                
                st.rerun()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

def show_progress_page():
    st.markdown('<div class="main-header"><h1>📊 Your Progress</h1></div>', unsafe_allow_html=True)
    
    # Mock progress data
    progress_data = [
        {'module': 'Real Estate Fundamentals', 'progress': 100, 'status': 'Completed'},
        {'module': 'Legal Framework & RERA', 'progress': 75, 'status': 'In Progress'},
        {'module': 'Property Measurements', 'progress': 50, 'status': 'In Progress'},
        {'module': 'Valuation & Finance', 'progress': 25, 'status': 'Started'},
        {'module': 'Land & Development Laws', 'progress': 0, 'status': 'Not Started'}
    ]
    
    for data in progress_data:
        st.markdown(f"""
        <div class="module-card">
            <h4>{data['module']}</h4>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {data['progress']}%"></div>
            </div>
            <p>{data['progress']}% Complete • Status: {data['status']}</p>
        </div>
        """, unsafe_allow_html=True)

def show_assessments():
    st.markdown('<div class="main-header"><h1>🏆 Assessments</h1></div>', unsafe_allow_html=True)
    
    st.subheader("Available Assessments")
    
    assessments = [
        {'title': 'Real Estate Fundamentals Quiz', 'questions': 10, 'duration': '15 min', 'status': 'Available'},
        {'title': 'RERA Compliance Test', 'questions': 15, 'duration': '20 min', 'status': 'Completed'},
        {'title': 'Property Valuation Assessment', 'questions': 12, 'duration': '18 min', 'status': 'Available'},
        {'title': 'Legal Framework Exam', 'questions': 20, 'duration': '30 min', 'status': 'Locked'}
    ]
    
    for assessment in assessments:
        with st.expander(f"{assessment['title']} ({assessment['status']})"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Questions:** {assessment['questions']}")
            
            with col2:
                st.write(f"**Duration:** {assessment['duration']}")
            
            with col3:
                if assessment['status'] == 'Available':
                    if st.button("Start Assessment", key=f"start_{assessment['title']}"):
                        st.success("Assessment would start here!")
                elif assessment['status'] == 'Completed':
                    st.success("✅ Completed")
                else:
                    st.info("🔒 Complete prerequisites first")

def main():
    # Initialize database
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
                show_admin_dashboard()
            else:
                show_user_dashboard()
        elif page == 'admin_dashboard':
            show_admin_dashboard()
        elif page == 'content_management':
            show_content_management()
        elif page == 'user_management':
            show_user_management()
        elif page == 'content_research':
            show_content_research()
        elif page == 'progress':
            show_progress_page()
        elif page == 'assessments':
            show_assessments()
        elif page == 'ai_assistant':
            show_ai_assistant()

if __name__ == "__main__":
    main()
