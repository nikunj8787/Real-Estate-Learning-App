import streamlit as st
import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
import requests
from utils.auth import check_authentication, get_user_role
from utils.llm_integration import DeepSeekChat
from utils.content_research import ContentResearcher
from database.database import init_database, get_db_connection

# Page configuration
st.set_page_config(
    page_title="RealEstateGuru",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_database()

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'current_module' not in st.session_state:
    st.session_state.current_module = None

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
</style>
""", unsafe_allow_html=True)

def main():
    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-logo"><h2>🏠 RealEstateGuru</h2></div>', unsafe_allow_html=True)
        
        if not st.session_state.authenticated:
            show_login_form()
        else:
            show_navigation()

    # Main content
    if not st.session_state.authenticated:
        show_welcome_page()
    else:
        show_dashboard()

def show_login_form():
    st.subheader("Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if authenticate_user(username, password):
                st.session_state.authenticated = True
                st.session_state.user_role = get_user_role(username)
                st.session_state.user_id = get_user_id(username)
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")
    
    st.divider()
    
    if st.button("Register New Account"):
        show_registration_form()

def show_registration_form():
    st.subheader("Register")
    
    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        user_type = st.selectbox("User Type", ["student", "professional", "admin"])
        submitted = st.form_submit_button("Register")
        
        if submitted:
            if password != confirm_password:
                st.error("Passwords don't match")
            elif register_user(username, email, password, user_type):
                st.success("Registration successful! Please login.")
                st.rerun()
            else:
                st.error("Registration failed")

def show_navigation():
    st.subheader(f"Welcome, {st.session_state.get('username', 'User')}!")
    
    if st.session_state.user_role == 'admin':
        st.subheader("Admin Panel")
        admin_options = [
            "Dashboard",
            "Content Management",
            "User Management",
            "Analytics",
            "System Settings"
        ]
        choice = st.selectbox("Select Option", admin_options)
        
        if choice == "Dashboard":
            st.session_state.current_page = "admin_dashboard"
        elif choice == "Content Management":
            st.session_state.current_page = "content_management"
        elif choice == "User Management":
            st.session_state.current_page = "user_management"
        elif choice == "Analytics":
            st.session_state.current_page = "analytics"
        elif choice == "System Settings":
            st.session_state.current_page = "system_settings"
    else:
        st.subheader("Learning Modules")
        modules = get_available_modules()
        
        for module in modules:
            if st.button(f"📚 {module['title']}", key=f"module_{module['id']}"):
                st.session_state.current_module = module['id']
                st.session_state.current_page = "module_content"
        
        st.divider()
        
        if st.button("📊 My Progress"):
            st.session_state.current_page = "progress"
        
        if st.button("🏆 Assessments"):
            st.session_state.current_page = "assessments"
        
        if st.button("🤖 AI Assistant"):
            st.session_state.current_page = "ai_assistant"
    
    st.divider()
    
    if st.button("Logout"):
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
    
    st.subheader("Key Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        - 📚 **Comprehensive Curriculum**: 11 detailed modules covering all aspects of Indian real estate
        - 🎮 **Gamified Learning**: Points, badges, and leaderboards to keep you engaged
        - 📱 **Multi-Platform Access**: Learn on desktop, tablet, or mobile
        - 🏅 **Certification**: LinkedIn-shareable certificates upon completion
        """)
    
    with col2:
        st.markdown("""
        - 🤖 **AI Assistant**: Get instant help with your queries using advanced AI
        - 📊 **Progress Tracking**: Monitor your learning journey with detailed analytics
        - 🎥 **Rich Media**: Videos, infographics, and interactive content
        - 👥 **Expert Support**: Access to real estate professionals and mentors
        """)

def show_dashboard():
    page = st.session_state.get('current_page', 'dashboard')
    
    if page == 'dashboard':
        show_user_dashboard()
    elif page == 'admin_dashboard':
        show_admin_dashboard()
    elif page == 'content_management':
        show_content_management()
    elif page == 'user_management':
        show_user_management()
    elif page == 'analytics':
        show_analytics()
    elif page == 'module_content':
        show_module_content()
    elif page == 'progress':
        show_progress_page()
    elif page == 'assessments':
        show_assessments()
    elif page == 'ai_assistant':
        show_ai_assistant()

def show_user_dashboard():
    st.markdown('<div class="main-header"><h1>Your Learning Dashboard</h1></div>', unsafe_allow_html=True)
    
    # Progress Overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Modules Completed", "3/11", "2 this week")
    
    with col2:
        st.metric("Total Points", "1,250", "+150")
    
    with col3:
        st.metric("Current Streak", "7 days", "+1")
    
    with col4:
        st.metric("Certificates Earned", "1", "+1")
    
    st.markdown("---")
    
    # Learning Path Progress
    st.subheader("📈 Your Learning Progress")
    
    modules_progress = get_user_progress(st.session_state.user_id)
    
    for module in modules_progress:
        st.markdown(f"""
        <div class="module-card">
            <h4>{module['title']}</h4>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {module['progress']}%"></div>
            </div>
            <p>{module['progress']}% Complete • {module['lessons_completed']}/{module['total_lessons']} Lessons</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Recent Activity
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Recommended Next Steps")
        st.markdown("""
        - Complete Module 4: Property Valuation & Finance
        - Take Assessment: RERA Compliance Quiz
        - Watch: Understanding FSI/TDR Calculations
        - Practice: Property Measurement Exercise
        """)
    
    with col2:
        st.subheader("🏆 Recent Achievements")
        st.markdown("""
        - 🥇 Completed "Real Estate Fundamentals" Module
        - 🎖️ Earned "Quick Learner" Badge
        - 📈 Reached 1000+ Points Milestone
        - 🔥 Maintained 7-day Learning Streak
        """)

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
    
    # Quick Actions
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 Add New Module", use_container_width=True):
            st.session_state.current_page = "add_module"
    
    with col2:
        if st.button("🔍 Research Content", use_container_width=True):
            st.session_state.current_page = "content_research"
    
    with col3:
        if st.button("📊 Generate Report", use_container_width=True):
            st.session_state.current_page = "generate_report"
    
    st.markdown("---")
    
    # Recent Activity
    st.subheader("📋 Recent System Activity")
    
    activity_data = get_recent_activity()
    
    for activity in activity_data:
        st.markdown(f"""
        <div class="module-card">
            <strong>{activity['timestamp']}</strong> - {activity['action']} by {activity['user']}
            <br><small>{activity['details']}</small>
        </div>
        """, unsafe_allow_html=True)

def show_content_management():
    st.markdown('<div class="main-header"><h1>Content Management</h1></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📚 Modules", "🎥 Videos", "📊 Research", "⚙️ Settings"])
    
    with tab1:
        show_module_management()
    
    with tab2:
        show_video_management()
    
    with tab3:
        show_content_research()
    
    with tab4:
        show_content_settings()

def show_module_management():
    st.subheader("Module Management")
    
    # Add new module
    with st.expander("➕ Add New Module"):
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
            
            if submitted:
                if add_module(title, description, difficulty, category):
                    st.success("Module added successfully!")
                    st.rerun()
                else:
                    st.error("Failed to add module")
    
    # Existing modules
    st.subheader("Existing Modules")
    
    modules = get_all_modules()
    
    for module in modules:
        with st.expander(f"{module['title']} ({module['difficulty']})"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Description:** {module['description']}")
                st.write(f"**Category:** {module['category']}")
                st.write(f"**Created:** {module['created_date']}")
                st.write(f"**Last Updated:** {module['updated_date']}")
            
            with col2:
                if st.button("✏️ Edit", key=f"edit_{module['id']}"):
                    st.session_state.editing_module = module['id']
                
                if st.button("🗑️ Delete", key=f"delete_{module['id']}"):
                    if delete_module(module['id']):
                        st.success("Module deleted!")
                        st.rerun()

def show_video_management():
    st.subheader("Video Content Management")
    
    # YouTube integration
    with st.expander("🔍 Search YouTube Videos"):
        search_query = st.text_input("Search Query", placeholder="e.g., real estate valuation India")
        
        if st.button("Search Videos"):
            videos = search_youtube_videos(search_query)
            
            for video in videos:
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.image(video['thumbnail'], width=120)
                
                with col2:
                    st.write(f"**{video['title']}**")
                    st.write(f"Channel: {video['channel']}")
                    st.write(f"Duration: {video['duration']}")
                    st.write(f"Views: {video['views']}")
                    
                    if st.button("Add to Module", key=f"add_video_{video['id']}"):
                        module_id = st.selectbox("Select Module", get_module_options())
                        if add_video_to_module(video['id'], module_id):
                            st.success("Video added to module!")

def show_content_research():
    st.subheader("Automated Content Research")
    
    researcher = ContentResearcher()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Research Topics:**")
        topics = [
            "RERA compliance latest updates",
            "Property valuation methods India",
            "Real estate investment strategies",
            "Construction technology trends",
            "Green building certifications",
            "Property documentation process",
            "Real estate market analysis",
            "Legal framework updates",
            "Taxation in real estate",
            "Digital transformation real estate"
        ]
        
        selected_topics = st.multiselect("Select Topics to Research", topics)
        
        if st.button("Start Research"):
            with st.spinner("Researching content..."):
                results = researcher.research_topics(selected_topics)
                st.session_state.research_results = results
    
    with col2:
        if 'research_results' in st.session_state:
            st.write("**Research Results:**")
            
            for topic, content in st.session_state.research_results.items():
                with st.expander(f"📋 {topic}"):
                    st.write("**Key Points:**")
                    for point in content['key_points']:
                        st.write(f"• {point}")
                    
                    st.write("**Sources:**")
                    for source in content['sources']:
                        st.write(f"• [{source['title']}]({source['url']})")
                    
                    if st.button(f"Add to Module", key=f"research_{topic}"):
                        if add_research_to_module(topic, content):
                            st.success("Content added to module!")

def show_ai_assistant():
    st.markdown('<div class="main-header"><h1>🤖 AI Assistant</h1></div>', unsafe_allow_html=True)
    
    # Initialize chat
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Initialize DeepSeek chat
    deepseek_chat = DeepSeekChat(api_key="sk-54bd3323c4d14bf08b941f0bff7a47d5")
    
    # Chat interface
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            st.markdown(f"**You:** {message['content']}")
        else:
            st.markdown(f"**AI Assistant:** {message['content']}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input
    user_input = st.text_input("Ask me anything about real estate:", key="chat_input")
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if st.button("Send", key="send_message"):
            if user_input:
                # Add user message to history
                st.session_state.chat_history.append({
                    'role': 'user',
                    'content': user_input
                })
                
                # Get AI response
                with st.spinner("Thinking..."):
                    response = deepseek_chat.get_response(user_input, context="real estate education")
                    
                    # Add AI response to history
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': response
                    })
                
                st.rerun()
    
    with col2:
        if st.button("Clear Chat", key="clear_chat"):
            st.session_state.chat_history = []
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
                    response = deepseek_chat.get_response(question, context="real estate education")
                    
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': response
                    })
                
                st.rerun()

# Database helper functions
def authenticate_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    cursor.execute("""
        SELECT id, username, role FROM users 
        WHERE username = ? AND password = ?
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

def get_user_role(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT role FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

def get_user_id(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

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

def get_user_progress(user_id):
    # Mock data for demonstration
    return [
        {
            'title': 'Real Estate Fundamentals',
            'progress': 100,
            'lessons_completed': 8,
            'total_lessons': 8
        },
        {
            'title': 'Legal Framework & RERA',
            'progress': 75,
            'lessons_completed': 6,
            'total_lessons': 8
        },
        {
            'title': 'Property Measurements',
            'progress': 50,
            'lessons_completed': 4,
            'total_lessons': 8
        },
        {
            'title': 'Valuation & Finance',
            'progress': 25,
            'lessons_completed': 2,
            'total_lessons': 8
        }
    ]

def get_all_modules():
    # Mock data for demonstration
    return [
        {
            'id': 1,
            'title': 'Real Estate Fundamentals',
            'description': 'Introduction to real estate basics, stakeholders, and market overview',
            'difficulty': 'Beginner',
            'category': 'Fundamentals',
            'created_date': '2024-01-15',
            'updated_date': '2024-02-01'
        },
        {
            'id': 2,
            'title': 'Legal Framework & RERA',
            'description': 'Comprehensive guide to RERA, legal compliance, and regulatory framework',
            'difficulty': 'Intermediate',
            'category': 'Legal Framework',
            'created_date': '2024-01-20',
            'updated_date': '2024-02-05'
        }
    ]

def get_recent_activity():
    # Mock data for demonstration
    return [
        {
            'timestamp': '2024-06-30 14:30',
            'action': 'Module Updated',
            'user': 'admin',
            'details': 'Updated "Property Valuation" module with new video content'
        },
        {
            'timestamp': '2024-06-30 12:15',
            'action': 'User Registered',
            'user': 'system',
            'details': 'New user "john_doe" registered as professional'
        },
        {
            'timestamp': '2024-06-30 10:45',
            'action': 'Content Research',
            'user': 'admin',
            'details': 'Automated research completed for "RERA compliance updates"'
        }
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

def search_youtube_videos(query):
    # Mock YouTube API response
    return [
        {
            'id': 'video_1',
            'title': 'Understanding RERA Compliance in Real Estate',
            'channel': 'Real Estate Expert',
            'duration': '12:34',
            'views': '15,000',
            'thumbnail': 'https://via.placeholder.com/120x90'
        },
        {
            'id': 'video_2',
            'title': 'Property Valuation Methods Explained',
            'channel': 'Property Guru',
            'duration': '18:22',
            'views': '28,500',
            'thumbnail': 'https://via.placeholder.com/120x90'
        }
    ]

def get_module_options():
    modules = get_available_modules()
    return [(module['id'], module['title']) for module in modules]

def add_video_to_module(video_id, module_id):
    # Implementation for adding video to module
    return True

def add_research_to_module(topic, content):
    # Implementation for adding research content to module
    return True

if __name__ == "__main__":
    main()
