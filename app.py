import streamlit as st
import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
import requests
import os
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import re
from urllib.parse import urlparse, parse_qs

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

def init_database():
    """Initialize database with comprehensive tables and content"""
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
    
    # Insert default admin user if doesn't exist
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    admin_count = cursor.fetchone()[0]
    
    if admin_count == 0:
        admin_password = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute("""
            INSERT INTO users (username, email, password, role, created_date, points, badges)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("admin", "admin@realestateguruapp.com", admin_password, "admin", datetime.now().isoformat(), 1000, '["Admin Master", "System Creator"]'))
    
    # Insert comprehensive modules with rich content if they don't exist
    cursor.execute("SELECT COUNT(*) FROM modules")
    module_count = cursor.fetchone()[0]
    
    if module_count == 0:
        # Module contents (same as before but with YouTube URLs)
        modules_data = [
            {
                'title': 'Real Estate Fundamentals',
                'description': 'Introduction to real estate basics, stakeholders, and market overview',
                'difficulty': 'Beginner',
                'category': 'Fundamentals',
                'youtube_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'content': """
# Real Estate Fundamentals

## 1. Introduction to Real Estate

Real estate encompasses **land and any permanent structures** attached to it, including buildings, homes, and other improvements. In India, real estate is governed by various central and state laws.

### Key Definitions:
- **Immovable Property**: Land, buildings, and anything attached to the earth
- **Movable Property**: Furniture, fixtures that can be removed
- **Freehold**: Absolute ownership of land and building
- **Leasehold**: Right to use property for specified period

## 2. Market Stakeholders

### Primary Stakeholders:
- **Developers**: Create new properties
- **Buyers/Investors**: Purchase for residence or investment
- **Brokers/Agents**: Facilitate transactions
- **Financial Institutions**: Provide funding
- **Government Bodies**: Regulate and approve

### Regulatory Bodies:
- **RERA**: Real Estate Regulatory Authority
- **Municipal Corporations**: Local approvals
- **State Housing Boards**: Affordable housing
- **SEBI**: REITs regulation

## 3. Property Types

### Residential:
- Apartments/Flats
- Independent Houses/Villas
- Row Houses/Townhouses
- Studio Apartments

### Commercial:
- Office Spaces
- Retail Outlets
- Warehouses
- Mixed-Use Developments

### Industrial:
- Manufacturing Units
- IT Parks
- Special Economic Zones (SEZ)

## 4. Market Dynamics

The Indian real estate market is valued at over **$200 billion** and growing at 6-8% annually. Key growth drivers include urbanization, rising incomes, and government initiatives like Housing for All.

### Current Trends:
- **Affordable Housing**: Government focus on sub-₹30 lakh homes
- **Smart Cities**: 100 smart cities mission
- **Green Buildings**: IGBC and GRIHA certifications
- **PropTech**: Digital platforms transforming transactions
""",
                'order_index': 1
            },
            {
                'title': 'Legal Framework & RERA',
                'description': 'Comprehensive guide to RERA, legal compliance, and regulatory framework',
                'difficulty': 'Intermediate',
                'category': 'Legal Framework',
                'youtube_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'content': """
# Legal Framework & RERA

## 1. Real Estate (Regulation and Development) Act, 2016

RERA was enacted to protect homebuyer interests and promote transparency in real estate transactions.

### Key Objectives:
- **Protect Homebuyer Rights**: Timely delivery and quality construction
- **Increase Transparency**: Mandatory project disclosures
- **Establish Accountability**: Developer penalties for non-compliance
- **Boost Investor Confidence**: Structured regulatory framework

## 2. RERA Registration Requirements

### For Developers:
- Projects with **8+ units or 500+ sq.m** must register
- Deposit **70% of receivables** in escrow account
- Submit quarterly progress reports
- Provide 5-year structural warranty

### For Real Estate Agents:
- Mandatory registration with state RERA
- Professional conduct standards
- Commission structure transparency

## 3. Homebuyer Rights Under RERA

### Delivery Rights:
- **Compensation** for delayed possession
- **Interest** on advance payments if project delayed
- **Refund** option with interest if developer fails

### Quality Rights:
- **5-year warranty** on structural defects
- **Right to inspect** during construction
- **Defect liability** for common areas

### Information Rights:
- **Project details** on RERA website
- **Financial information** including approvals
- **Timeline updates** through quarterly reports
""",
                'order_index': 2
            }
        ]
        
        for module in modules_data:
            cursor.execute("""
                INSERT INTO modules (title, description, difficulty, category, content, youtube_url, order_index, created_date, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                module['title'],
                module['description'],
                module['difficulty'],
                module['category'],
                module['content'],
                module['youtube_url'],
                module['order_index'],
                datetime.now().isoformat()
            ))
    
    # Insert sample quiz questions if they don't exist
    cursor.execute("SELECT COUNT(*) FROM quizzes")
    quiz_count = cursor.fetchone()[0]
    
    if quiz_count == 0:
        sample_questions = [
            # Real Estate Fundamentals Quiz (Module ID 1)
            (1, "What does real estate primarily encompass?", "Only land", "Land and permanent structures", "Only buildings", "Movable property", "B", "Real estate includes both land and any permanent structures attached to it."),
            (1, "Which regulatory body primarily governs real estate in India?", "SEBI", "RBI", "RERA", "IRDA", "C", "RERA (Real Estate Regulatory Authority) is the primary regulatory body for real estate in India."),
            (1, "What is a freehold property?", "Temporary ownership", "Absolute ownership", "Rental property", "Shared ownership", "B", "Freehold means absolute ownership of both land and building."),
            (1, "Which type of property is NOT mentioned as residential?", "Apartments", "Warehouses", "Villas", "Studio Apartments", "B", "Warehouses are commercial/industrial properties, not residential."),
            (1, "What is the approximate value of the Indian real estate market?", "$100 billion", "$200 billion", "$300 billion", "$400 billion", "B", "The Indian real estate market is valued at over $200 billion."),
            # Legal Framework & RERA Quiz (Module ID 2)
            (2, "In which year was RERA enacted?", "2015", "2016", "2017", "2018", "B", "RERA (Real Estate Regulation and Development Act) was enacted in 2016."),
            (2, "What percentage of receivables must developers deposit in escrow account?", "50%", "60%", "70%", "80%", "C", "Developers must deposit 70% of receivables in escrow account under RERA."),
            (2, "How many years of structural warranty must developers provide?", "3 years", "5 years", "7 years", "10 years", "B", "Developers must provide 5-year structural warranty under RERA."),
            (2, "Projects with how many units must register under RERA?", "5+ units", "6+ units", "7+ units", "8+ units", "D", "Projects with 8 or more units or 500+ sq.m must register under RERA."),
            (2, "What is the minimum area threshold for RERA registration?", "300 sq.m", "400 sq.m", "500 sq.m", "600 sq.m", "C", "Projects with 500 sq.m or more must register under RERA.")
        ]
        
        for question in sample_questions:
            cursor.execute("""
                INSERT INTO quizzes (module_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (*question, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DATABASE_PATH)

# Enhanced CSS Styling with Gamification
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
    max-height: 400px;
    overflow-y: auto;
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
    padding-bottom: 56.25%; /* 16:9 aspect ratio */
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

# Enhanced DeepSeek Chat Integration
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
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except requests.exceptions.Timeout:
            return "Sorry, the request timed out. Please try again."
        except requests.exceptions.RequestException as e:
            return f"Sorry, I'm having trouble connecting to the AI service. Please try again later."
        except Exception as e:
            return "Sorry, something went wrong. Please try again."
    
    def generate_quiz_questions(self, module_title, difficulty, count=5):
        """Generate quiz questions using AI"""
        prompt = f"""
        Generate {count} multiple-choice questions for the module "{module_title}" with difficulty level "{difficulty}".
        
        Each question should:
        1. Be relevant to Indian real estate context
        2. Have 4 options (A, B, C, D)
        3. Have one correct answer
        4. Include a brief explanation
        
        Format the response as JSON:
        {{
            "questions": [
                {{
                    "question": "Question text here",
                    "option_a": "First option",
                    "option_b": "Second option", 
                    "option_c": "Third option",
                    "option_d": "Fourth option",
                    "correct_answer": "B",
                    "explanation": "Brief explanation"
                }}
            ]
        }}
        """
        
        response = self.get_response(prompt, context="quiz generation")
        
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"questions": []}
        except:
            return {"questions": []}
    
    def improve_content(self, current_content, improvement_request):
        """Use AI to improve module content"""
        prompt = f"""
        Current content:
        {current_content[:1000]}...
        
        Improvement request: {improvement_request}
        
        Please provide improved content that:
        1. Maintains the educational structure
        2. Includes the requested improvements
        3. Stays relevant to Indian real estate context
        4. Uses proper markdown formatting
        
        Return only the improved content.
        """
        
        return self.get_response(prompt, context="content improvement")

# Enhanced Content Research Module
class ContentResearcher:
    def __init__(self):
        self.available_topics = [
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
        
        # Mock knowledge base with detailed content
        self._knowledge_base = {
            "RERA compliance updates": {
                "key_points": [
                    "RERA Amendment Act 2023 introduces stricter penalties for non-compliance",
                    "New online dispute resolution mechanism launched in Maharashtra and Karnataka",
                    "Mandatory quarterly progress reports now required on state RERA portals",
                    "Enhanced buyer protection measures in case of project delays and quality issues",
                    "Digital approval processes implemented for faster project registrations"
                ],
                "sources": [
                    {"title": "RERA Amendment Act 2023 - Key Changes", "url": "https://mohua.gov.in/rera-updates", "date": "2023-12-15"},
                    {"title": "MoHUA Guidelines on RERA Implementation", "url": "https://rera.karnataka.gov.in", "date": "2023-11-20"}
                ]
            },
            "Property valuation methods": {
                "key_points": [
                    "Comparative Market Analysis (CMA) remains the most widely used method in India",
                    "Income approach gaining popularity for rental property investments",
                    "Cost approach essential for new construction and insurance valuations",
                    "Automated Valuation Models (AVMs) being adopted by major banks",
                    "Location intelligence and GIS data improving valuation accuracy"
                ],
                "sources": [
                    {"title": "Property Valuation Standards in India", "url": "https://rbi.org.in/valuation-guidelines", "date": "2023-10-30"},
                    {"title": "Bank Valuation Norms Update", "url": "https://housing.com/valuation-guide", "date": "2023-09-15"}
                ]
            }
        }
    
    def run_research(self, selected_topics):
        """Research selected topics and return structured content"""
        results = {}
        
        for topic in selected_topics:
            if topic in self._knowledge_base:
                results[topic] = self._knowledge_base[topic].copy()
            else:
                # Generate generic content for topics not in knowledge base
                results[topic] = {
                    "key_points": [
                        f"Latest developments in {topic} show significant impact on Indian real estate",
                        f"Regulatory changes in {topic} affecting property transactions",
                        f"Market trends indicate growing importance of {topic}",
                        f"Industry experts recommend staying updated on {topic}",
                        f"Future outlook for {topic} remains positive with new initiatives"
                    ],
                    "sources": [
                        {"title": f"Industry Report on {topic}", "url": "https://realestate-india.com/reports", "date": datetime.now().strftime("%Y-%m-%d")},
                        {"title": f"Expert Analysis - {topic}", "url": "https://propertyguide.in/analysis", "date": datetime.now().strftime("%Y-%m-%d")}
                    ]
                }
            
            results[topic]["last_updated"] = datetime.now().isoformat()
        
        return results

# Gamification Functions
def award_points(user_id, points, reason):
    """Award points to user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Update user points
    cursor.execute("UPDATE users SET points = points + ? WHERE id = ?", (points, user_id))
    
    # Record achievement
    cursor.execute("""
        INSERT INTO user_achievements (user_id, achievement_type, achievement_name, points_earned, earned_date)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, "points", reason, points, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

def award_badge(user_id, badge_name):
    """Award badge to user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current badges
    cursor.execute("SELECT badges FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    
    if result:
        badges = json.loads(result[0]) if result[0] else []
        if badge_name not in badges:
            badges.append(badge_name)
            
            # Update badges
            cursor.execute("UPDATE users SET badges = ? WHERE id = ?", (json.dumps(badges), user_id))
            
            # Record achievement
            cursor.execute("""
                INSERT INTO user_achievements (user_id, achievement_type, achievement_name, points_earned, earned_date)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, "badge", badge_name, 0, datetime.now().isoformat()))
            
            conn.commit()
    
    conn.close()

def get_user_stats(user_id):
    """Get user statistics for gamification"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT points, badges, streak_days FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    
    if result:
        return {
            'points': result[0] or 0,
            'badges': json.loads(result[1]) if result[1] else [],
            'streak_days': result[2] or 0
        }
    
    conn.close()
    return {'points': 0, 'badges': [], 'streak_days': 0}

# YouTube Functions
def extract_youtube_id(url):
    """Extract YouTube video ID from URL"""
    if not url:
        return None
    
    # Handle various YouTube URL formats
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
        r'youtube\.com/watch\?.*v=([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def embed_youtube_video(video_url):
    """Embed YouTube video in Streamlit"""
    video_id = extract_youtube_id(video_url)
    if video_id:
        embed_url = f"https://www.youtube.com/embed/{video_id}"
        st.markdown(f"""
        <div class="youtube-container">
            <iframe src="{embed_url}" frameborder="0" allowfullscreen></iframe>
        </div>
        """, unsafe_allow_html=True)
        return True
    return False

# Authentication functions
def authenticate_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    cursor.execute("""
        SELECT id, username, role, points, badges FROM users 
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
        # Check if username or email already exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ? OR email = ?", (username, email))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return False
            
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute("""
            INSERT INTO users (username, email, password, role, created_date, points, badges)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username, email, hashed_password, user_type, datetime.now().isoformat(), 100, '["Welcome Learner"]'))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False

def create_user_by_admin(username, email, password, role):
    """Admin function to create new users"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if username or email already exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ? OR email = ?", (username, email))
        if cursor.fetchone()[0] > 0:
            return False, "Username or email already exists"
            
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute("""
            INSERT INTO users (username, email, password, role, created_date, points, badges)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username, email, hashed_password, role, datetime.now().isoformat(), 100, '["New Member"]'))
        
        conn.commit()
        conn.close()
        return True, "User created successfully"
    except Exception as e:
        conn.close()
        return False, f"Error creating user: {str(e)}"

# Module and Content Functions
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
    """Get full content of a specific module"""
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

def update_module_content(module_id, title, description, content, youtube_url):
    """Update module content"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE modules 
            SET title = ?, description = ?, content = ?, youtube_url = ?, updated_date = ?
            WHERE id = ?
        """, (title, description, content, youtube_url, datetime.now().isoformat(), module_id))
        
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def add_module(title, description, difficulty, category, content="", youtube_url=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO modules (title, description, difficulty, category, content, youtube_url, created_date, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (title, description, difficulty, category, content, youtube_url, datetime.now().isoformat()))
        
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

# Quiz Functions
def get_quiz_questions(module_id):
    """Get quiz questions for a module"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, question, option_a, option_b, option_c, option_d, correct_answer, explanation
        FROM quizzes
        WHERE module_id = ?
        ORDER BY id
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
    """Add a new quiz question"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO quizzes (module_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (module_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def save_quiz_result(user_id, module_id, score, total_questions):
    """Save quiz result and award points/badges"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    percentage = (score / total_questions) * 100
    
    # Update or insert progress
    cursor.execute("""
        INSERT OR REPLACE INTO user_progress 
        (user_id, module_id, quiz_score, quiz_attempts, started_date)
        VALUES (?, ?, ?, 
                COALESCE((SELECT quiz_attempts FROM user_progress WHERE user_id = ? AND module_id = ?), 0) + 1,
                ?)
    """, (user_id, module_id, percentage, user_id, module_id, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    # Award points based on performance
    if percentage >= 90:
        award_points(user_id, 100, f"Excellent Quiz Performance ({percentage:.1f}%)")
        if percentage == 100:
            award_badge(user_id, "Perfect Score")
    elif percentage >= 80:
        award_points(user_id, 75, f"Good Quiz Performance ({percentage:.1f}%)")
    elif percentage >= 70:
        award_points(user_id, 50, f"Passing Quiz Score ({percentage:.1f}%)")
    
    # Award completion badge
    award_badge(user_id, "Quiz Taker")

# Data Visualization Functions
def create_user_progress_chart(user_id):
    """Create user progress visualization"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT m.title, COALESCE(p.quiz_score, 0) as score
        FROM modules m
        LEFT JOIN user_progress p ON m.id = p.module_id AND p.user_id = ?
        WHERE m.active = 1
        ORDER BY m.order_index
    """, (user_id,))
    
    data = cursor.fetchall()
    conn.close()
    
    if data:
        df = pd.DataFrame(data, columns=['Module', 'Score'])
        
        fig = px.bar(
            df, 
            x='Module', 
            y='Score',
            title='Your Module Progress',
            color='Score',
            color_continuous_scale='viridis'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

def create_admin_analytics_charts():
    """Create admin analytics visualizations"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # User registration over time
    cursor.execute("""
        SELECT DATE(created_date) as date, COUNT(*) as registrations
        FROM users
        WHERE role != 'admin'
        GROUP BY DATE(created_date)
        ORDER BY date
    """)
    
    reg_data = cursor.fetchall()
    
    if reg_data:
        df_reg = pd.DataFrame(reg_data, columns=['Date', 'Registrations'])
        df_reg['Date'] = pd.to_datetime(df_reg['Date'])
        
        fig1 = px.line(
            df_reg,
            x='Date',
            y='Registrations',
            title='User Registrations Over Time',
            markers=True
        )
        
        st.plotly_chart(fig1, use_container_width=True)
    
    # Module completion rates
    cursor.execute("""
        SELECT m.title, COUNT(p.user_id) as completions
        FROM modules m
        LEFT JOIN user_progress p ON m.id = p.module_id AND p.quiz_score >= 70
        WHERE m.active = 1
        GROUP BY m.id, m.title
        ORDER BY completions DESC
    """)
    
    completion_data = cursor.fetchall()
    
    if completion_data:
        df_comp = pd.DataFrame(completion_data, columns=['Module', 'Completions'])
        
        fig2 = px.pie(
            df_comp,
            values='Completions',
            names='Module',
            title='Module Completion Distribution'
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    conn.close()

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
            if not username or not email or not password:
                st.error("Please fill all fields")
            elif password != confirm_password:
                st.error("Passwords don't match")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters")
            elif register_user(username, email, password, user_type):
                st.success("Registration successful! You've earned 100 points and your first badge! Please login.")
                st.session_state.show_register = False
                st.rerun()
            else:
                st.error("Registration failed - Username or email already exists")
    
    if st.button("Back to Login"):
        st.session_state.show_register = False
        st.rerun()

def show_navigation():
    st.markdown('<div class="sidebar-logo"><h3>🏠 RealEstateGuru</h3></div>', unsafe_allow_html=True)
    
    # User info with gamification
    st.write(f"Welcome, **{st.session_state.username}**!")
    st.write(f"Role: *{st.session_state.user_role.title()}*")
    
    # Show points and badges
    if st.session_state.user_role != 'admin':
        user_stats = get_user_stats(st.session_state.user_id)
        st.markdown(f'<div class="points-display">🏆 {user_stats["points"]} Points</div>', unsafe_allow_html=True)
        
        if user_stats['badges']:
            st.write("**Badges:**")
            for badge in user_stats['badges']:
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
        
        if st.button("🔍 Content Research", use_container_width=True):
            st.session_state.current_page = "content_research"
            st.rerun()
        
        if st.button("📈 Analytics", use_container_width=True):
            st.session_state.current_page = "analytics"
            st.rerun()
    else:
        st.subheader("Learning Modules")
        modules = get_available_modules()
        
        for module in modules:
            difficulty_emoji = {"Beginner": "🟢", "Intermediate": "🟡", "Advanced": "🔴"}
            emoji = difficulty_emoji.get(module['difficulty'], "📚")
            
            if st.button(f"{emoji} {module['title']}", key=f"module_{module['id']}", use_container_width=True):
                st.session_state.current_module = module['id']
                st.session_state.current_page = "module_content"
                st.rerun()
        
        st.divider()
        
        if st.button("📊 My Progress", use_container_width=True):
            st.session_state.current_page = "progress"
            st.rerun()
        
        if st.button("🏆 Take Quiz", use_container_width=True):
            st.session_state.current_page = "quiz"
            st.rerun()
        
        if st.button("🎖️ Achievements", use_container_width=True):
            st.session_state.current_page = "achievements"
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
    st.markdown('<div class="main-header"><h1>Welcome to RealEstateGuru</h1><p>Your Complete Real Estate Education Platform with Gamification</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="module-card">
            <h3>🎯 Learn & Earn Points</h3>
            <p>Complete modules, take quizzes, and earn points and badges while mastering real estate concepts.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="module-card">
            <h3>🎥 Video Learning</h3>
            <p>Watch curated YouTube videos embedded in each module for enhanced learning experience.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="module-card">
            <h3>🤖 AI-Powered</h3>
            <p>Get AI assistance, auto-generated quizzes, and content improvements using advanced AI technology.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Key Features")
        st.markdown("""
        - 📚 **Rich Content**: Comprehensive modules with videos and interactive content
        - 🎮 **Gamification**: Points, badges, and achievements to keep you motivated
        - 📱 **Responsive Design**: Learn on any device with optimized interface
        - 🏅 **Certification Ready**: Prepare for real estate certifications
        """)
    
    with col2:
        st.subheader("🚀 Advanced Features")
        st.markdown("""
        - 🤖 **AI Assistant**: Get instant help and generate custom content
        - 📊 **Progress Analytics**: Detailed charts and progress tracking
        - 🎥 **Video Integration**: YouTube videos embedded in modules
        - 👥 **Admin Tools**: Complete content and user management system
        """)
    
    st.markdown("---")
    st.info("💡 **Get Started**: Register as a student to start earning points and badges, or login as admin (`admin`/`admin123`) to manage content and users.")

def show_user_dashboard():
    st.markdown('<div class="main-header"><h1>Your Learning Dashboard</h1></div>', unsafe_allow_html=True)
    
    # Gamification metrics
    user_stats = get_user_stats(st.session_state.user_id)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("🏆 Points", user_stats['points'], "Keep learning!")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("🏅 Badges", len(user_stats['badges']), "Achievements unlocked")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("🔥 Streak", user_stats['streak_days'], "Days in a row")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("📚 Modules", "5", "Available to learn")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Progress chart
    st.subheader("📈 Your Progress Analytics")
    create_user_progress_chart(st.session_state.user_id)
    
    st.markdown("---")
    
    # Available Modules
    st.subheader("📚 Available Learning Modules")
    
    modules = get_available_modules()
    
    for module in modules:
        difficulty_color = {"Beginner": "🟢", "Intermediate": "🟡", "Advanced": "🔴"}
        color = difficulty_color.get(module['difficulty'], "📚")
        
        with st.expander(f"{color} {module['title']} ({module['difficulty']})"):
            st.write(f"**Category:** {module['category']}")
            st.write(f"**Description:** {module['description']}")
            
            if module['youtube_url']:
                st.write("📹 **Video Available**")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"📖 Study", key=f"study_{module['id']}"):
                    st.session_state.current_module = module['id']
                    st.session_state.current_page = "module_content"
                    st.rerun()
            
            with col2:
                if st.button(f"🏆 Quiz", key=f"quiz_{module['id']}"):
                    st.session_state.current_module = module['id']
                    st.session_state.current_page = "quiz"
                    st.rerun()
            
            with col3:
                st.info("Earn points & badges!")

def show_module_content():
    """Display detailed content of a specific module with video"""
    module_id = st.session_state.get('current_module')
    if not module_id:
        st.error("No module selected")
        return
    
    module = get_module_content(module_id)
    if not module:
        st.error("Module not found")
        return
    
    # Module header
    st.markdown(f'<div class="main-header"><h1>{module["title"]}</h1><p>{module["description"]}</p></div>', unsafe_allow_html=True)
    
    # Module info and navigation
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.info(f"**Difficulty:** {module['difficulty']}")
    with col2:
        st.info(f"**Category:** {module['category']}")
    with col3:
        if st.button("🏆 Take Quiz"):
            st.session_state.current_page = "quiz"
            st.rerun()
    with col4:
        if st.button("← Back"):
            st.session_state.current_page = "dashboard"
            st.session_state.current_module = None
            st.rerun()
    
    st.markdown("---")
    
    # YouTube video if available
    if module['youtube_url']:
        st.subheader("📹 Module Video")
        if embed_youtube_video(module['youtube_url']):
            # Award points for watching video
            award_points(st.session_state.user_id, 10, f"Watched video: {module['title']}")
        else:
            st.error("Invalid YouTube URL")
    
    # Module content
    if module['content']:
        st.subheader("📖 Module Content")
        st.markdown('<div class="content-viewer">', unsafe_allow_html=True)
        st.markdown(module['content'])
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Award points for reading content
        if st.button("✅ Mark as Read (+20 points)", use_container_width=True):
            award_points(st.session_state.user_id, 20, f"Completed reading: {module['title']}")
            award_badge(st.session_state.user_id, "Content Reader")
            st.success("Great! You've earned 20 points for reading this module!")
            st.rerun()
    else:
        st.warning("No content available for this module yet.")

def show_quiz():
    """Enhanced quiz system with gamification"""
    module_id = st.session_state.get('current_module')
    if not module_id:
        st.error("No module selected")
        return
    
    # Get module info
    module = get_module_content(module_id)
    if not module:
        st.error("Module not found")
        return
    
    st.markdown(f'<div class="main-header"><h1>🏆 Quiz: {module["title"]}</h1></div>', unsafe_allow_html=True)
    
    # Get quiz questions
    questions = get_quiz_questions(module_id)
    
    if not questions:
        st.warning("No quiz questions available for this module yet.")
        if st.button("← Back to Module"):
            st.session_state.current_page = "module_content"
            st.rerun()
        return
    
    # Quiz logic
    if not st.session_state.quiz_started:
        # Quiz start screen
        st.subheader(f"📋 Quiz Information")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Questions", len(questions))
        with col2:
            st.metric("Points per Question", "10")
        with col3:
            st.metric("Passing Score", "70%")
        
        st.markdown("---")
        st.write("**Instructions:**")
        st.write("- Answer all questions to the best of your ability")
        st.write("- You can review your answers before submitting")
        st.write("- Minimum 70% required to pass")
        st.write("- Earn bonus points for high scores!")
        
        if st.button("🚀 Start Quiz", use_container_width=True):
            st.session_state.quiz_started = True
            st.session_state.current_question = 0
            st.session_state.quiz_answers = {}
            st.session_state.quiz_score = 0
            st.rerun()
    
    else:
        # Quiz questions
        total_questions = len(questions)
        current_q = st.session_state.current_question
        
        if current_q < total_questions:
            question = questions[current_q]
            
            st.subheader(f"Question {current_q + 1} of {total_questions}")
            st.progress((current_q + 1) / total_questions)
            
            st.markdown(f'<div class="quiz-question"><h4>{question["question"]}</h4></div>', unsafe_allow_html=True)
            
            # Answer options
            selected_answer = st.radio(
                "Choose your answer:",
                options=list(question['options'].keys()),
                format_func=lambda x: f"{x}. {question['options'][x]}",
                key=f"q_{current_q}"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if current_q > 0:
                    if st.button("← Previous"):
                        st.session_state.current_question -= 1
                        st.rerun()
            
            with col2:
                if st.button("Next →" if current_q < total_questions - 1 else "Submit Quiz"):
                    # Save answer
                    st.session_state.quiz_answers[current_q] = selected_answer
                    
                    if current_q < total_questions - 1:
                        st.session_state.current_question += 1
                        st.rerun()
                    else:
                        # Calculate score and finish quiz
                        correct_answers = 0
                        for i, question in enumerate(questions):
                            if st.session_state.quiz_answers.get(i) == question['correct_answer']:
                                correct_answers += 1
                        
                        st.session_state.quiz_score = correct_answers
                        st.session_state.current_question = total_questions
                        st.rerun()
        
        else:
            # Quiz results
            correct_answers = st.session_state.quiz_score
            percentage = (correct_answers / total_questions) * 100
            
            st.subheader("🎉 Quiz Completed!")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Score", f"{correct_answers}/{total_questions}")
            with col2:
                st.metric("Percentage", f"{percentage:.1f}%")
            with col3:
                if percentage >= 70:
                    st.success("PASSED! 🎉")
                else:
                    st.error("Try Again")
            
            # Save results and award points
            save_quiz_result(st.session_state.user_id, module_id, correct_answers, total_questions)
            
            # Points calculation
            base_points = correct_answers * 10
            bonus_points = 0
            
            if percentage >= 90:
                bonus_points = 50
            elif percentage >= 80:
                bonus_points = 25
            
            total_points = base_points + bonus_points
            
            st.success(f"🏆 You earned {total_points} points! ({base_points} base + {bonus_points} bonus)")
            
            # Review answers
            st.subheader("📋 Answer Review")
            
            for i, question in enumerate(questions):
                user_answer = st.session_state.quiz_answers.get(i, 'Not answered')
                correct = user_answer == question['correct_answer']
                
                with st.expander(f"Question {i+1} - {'✅ Correct' if correct else '❌ Incorrect'}"):
                    st.write(f"**Question:** {question['question']}")
                    st.write(f"**Your Answer:** {user_answer}. {question['options'].get(user_answer, 'Not selected')}")
                    st.write(f"**Correct Answer:** {question['correct_answer']}. {question['options'][question['correct_answer']]}")
                    if question['explanation']:
                        st.write(f"**Explanation:** {question['explanation']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Retake Quiz"):
                    st.session_state.quiz_started = False
                    st.session_state.current_question = 0
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_score = 0
                    st.rerun()
            
            with col2:
                if st.button("← Back to Module"):
                    st.session_state.quiz_started = False
                    st.session_state.current_page = "module_content"
                    st.rerun()

def show_achievements():
    """Show user achievements and gamification elements"""
    st.markdown('<div class="main-header"><h1>🎖️ Your Achievements</h1></div>', unsafe_allow_html=True)
    
    user_stats = get_user_stats(st.session_state.user_id)
    
    # Overall stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h2>🏆 {user_stats['points']}</h2>
            <p>Total Points</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h2>🏅 {len(user_stats['badges'])}</h2>
            <p>Badges Earned</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h2>🔥 {user_stats['streak_days']}</h2>
            <p>Day Streak</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Badges
    st.subheader("🏅 Your Badges")
    
    if user_stats['badges']:
        cols = st.columns(3)
        for i, badge in enumerate(user_stats['badges']):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="module-card">
                    <center>
                        <h2>🏅</h2>
                        <h4>{badge}</h4>
                    </center>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No badges earned yet. Complete modules and quizzes to earn badges!")
    
    st.markdown("---")
    
    # Recent achievements
    st.subheader("📈 Recent Activity")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT achievement_name, points_earned, earned_date
        FROM user_achievements
        WHERE user_id = ?
        ORDER BY earned_date DESC
        LIMIT 10
    """, (st.session_state.user_id,))
    
    achievements = cursor.fetchall()
    conn.close()
    
    if achievements:
        for achievement in achievements:
            points_text = f"(+{achievement[1]} points)" if achievement[1] > 0 else ""
            st.markdown(f"""
            <div class="module-card">
                <strong>{achievement[0]}</strong> {points_text}
                <br><small>{achievement[2]}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent activity. Start learning to see your progress here!")

def show_admin_dashboard():
    st.markdown('<div class="main-header"><h1>Admin Dashboard</h1></div>', unsafe_allow_html=True)
    
    # System Overview with real data
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE active = 1")
    user_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM modules WHERE active = 1")
    module_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM quizzes")
    quiz_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(points) FROM users WHERE role != 'admin'")
    total_points = cursor.fetchone()[0] or 0
    
    conn.close()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", user_count, "Active users")
    
    with col2:
        st.metric("Modules", module_count, "Published")
    
    with col3:
        st.metric("Quiz Questions", quiz_count, "Available")
    
    with col4:
        st.metric("Total Points Earned", total_points, "By all users")
    
    st.markdown("---")
    
    # Analytics charts
    st.subheader("📊 System Analytics")
    create_admin_analytics_charts()
    
    st.markdown("---")
    
    # Quick Actions
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📚 Manage Content", use_container_width=True):
            st.session_state.current_page = "content_management"
            st.rerun()
    
    with col2:
        if st.button("👥 Add User", use_container_width=True):
            st.session_state.current_page = "add_user"
            st.rerun()
    
    with col3:
        if st.button("❓ Add Quiz", use_container_width=True):
            st.session_state.current_page = "quiz_management"
            st.rerun()

def show_content_management():
    st.markdown('<div class="main-header"><h1>Content Management</h1></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📚 Edit Modules", "➕ Add Module", "🤖 AI Content Tools"])
    
    with tab1:
        st.subheader("Edit Existing Modules")
        
        modules = get_available_modules()
        
        for module in modules:
            difficulty_color = {"Beginner": "🟢", "Intermediate": "🟡", "Advanced": "🔴"}
            color = difficulty_color.get(module['difficulty'], "📚")
            
            with st.expander(f"{color} {module['title']} ({module['difficulty']})"):
                # Get full module data
                full_module = get_module_content(module['id'])
                
                with st.form(f"edit_module_{module['id']}"):
                    title = st.text_input("Title", value=full_module['title'])
                    description = st.text_area("Description", value=full_module['description'], height=100)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"], 
                                                index=["Beginner", "Intermediate", "Advanced"].index(full_module['difficulty']))
                    with col2:
                        category = st.selectbox("Category", [
                            "Fundamentals", "Legal Framework", "Property Measurements",
                            "Valuation & Finance", "Technical & Construction", "Transactions & Documentation",
                            "Property Management", "Brokerage & Agency", "Digital Tools", "Case Studies", "Sustainability"
                        ])
                    
                    youtube_url = st.text_input("YouTube URL", value=full_module['youtube_url'] or "", 
                                              help="Enter YouTube video URL for this module")
                    
                    content = st.text_area("Module Content (Markdown)", value=full_module['content'] or "", 
                                         height=300, help="Use Markdown formatting for better presentation")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.form_submit_button("💾 Update Module"):
                            if update_module_content(module['id'], title, description, content, youtube_url):
                                st.success("Module updated successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to update module")
                    
                    with col2:
                        if st.form_submit_button("🗑️ Delete Module"):
                            if delete_module(module['id']):
                                st.success("Module deleted!")
                                st.rerun()
                            else:
                                st.error("Failed to delete module")
    
    with tab2:
        st.subheader("Add New Module")
        
        with st.form("add_module_form"):
            title = st.text_input("Module Title")
            description = st.text_area("Description", height=100)
            
            col1, col2 = st.columns(2)
            with col1:
                difficulty = st.selectbox("Difficulty Level", ["Beginner", "Intermediate", "Advanced"])
            with col2:
                category = st.selectbox("Category", [
                    "Fundamentals", "Legal Framework", "Property Measurements",
                    "Valuation & Finance", "Technical & Construction", "Transactions & Documentation",
                    "Property Management", "Brokerage & Agency", "Digital Tools", "Case Studies", "Sustainability"
                ])
            
            youtube_url = st.text_input("YouTube URL", help="Enter YouTube video URL for this module")
            content = st.text_area("Module Content (Markdown)", height=300, 
                                 placeholder="Enter detailed content for this module. You can use Markdown formatting.")
            
            if st.form_submit_button("➕ Add Module"):
                if title and description:
                    if add_module(title, description, difficulty, category, content, youtube_url):
                        st.success("Module added successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to add module")
                else:
                    st.error("Please fill in at least title and description")
    
    with tab3:
        st.subheader("🤖 AI Content Enhancement Tools")
        
        # Get DeepSeek API key
        try:
            api_key = st.secrets.get("DEEPSEEK_API_KEY", "sk-54bd3323c4d14bf08b941f0bff7a47d5")
        except:
            api_key = "sk-54bd3323c4d14bf08b941f0bff7a47d5"
        
        deepseek_chat = DeepSeekChat(api_key)
        
        st.write("**Improve Existing Content with AI:**")
        
        modules = get_available_modules()
        selected_module = st.selectbox("Select Module to Improve", 
                                     [f"{m['id']}: {m['title']}" for m in modules])
        
        if selected_module:
            module_id = int(selected_module.split(':')[0])
            improvement_request = st.text_area("What improvements would you like?", 
                                             placeholder="e.g., Add more examples, simplify language, include recent updates...")
            
            if st.button("✨ Improve Content with AI"):
                if improvement_request:
                    with st.spinner("AI is improving the content..."):
                        current_module = get_module_content(module_id)
                        improved_content = deepseek_chat.improve_content(
                            current_module['content'], 
                            improvement_request
                        )
                        
                        st.subheader("🎯 AI-Improved Content:")
                        st.markdown(improved_content)
                        
                        if st.button("✅ Apply Improvements"):
                            if update_module_content(module_id, current_module['title'], 
                                                   current_module['description'], improved_content, 
                                                   current_module['youtube_url']):
                                st.success("Content updated with AI improvements!")
                                st.rerun()

def show_user_management():
    st.markdown('<div class="main-header"><h1>User Management</h1></div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["👥 Manage Users", "➕ Add New User"])
    
    with tab1:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, role, created_date, last_login, active, points, badges
            FROM users
            ORDER BY created_date DESC
        """)
        
        users = cursor.fetchall()
        conn.close()
        
        # User statistics
        col1, col2, col3 = st.columns(3)
        
        total_users = len(users)
        active_users = len([u for u in users if u[6] == 1])
        admin_users = len([u for u in users if u[3] == 'admin'])
        
        with col1:
            st.metric("Total Users", total_users)
        with col2:
            st.metric("Active Users", active_users)
        with col3:
            st.metric("Admin Users", admin_users)
        
        st.markdown("---")
        
        st.subheader(f"All Users ({total_users})")
        
        for user in users:
            role_emoji = {"admin": "👑", "student": "📚", "professional": "💼"}
            emoji = role_emoji.get(user[3], "👤")
            status = "🟢 Active" if user[6] else "🔴 Inactive"
            
            badges = json.loads(user[8]) if user[8] else []
            
            with st.expander(f"{emoji} {user[1]} ({user[3]}) - {status} - 🏆 {user[7] or 0} points"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Email:** {user[2]}")
                    st.write(f"**Role:** {user[3].title()}")
                    st.write(f"**Joined:** {user[4]}")
                    st.write(f"**Points:** {user[7] or 0}")
                
                with col2:
                    st.write(f"**Last Login:** {user[5] or 'Never'}")
                    st.write(f"**Status:** {'Active' if user[6] else 'Inactive'}")
                    st.write(f"**Badges:** {len(badges)}")
                    
                    if badges:
                        for badge in badges[:3]:  # Show first 3 badges
                            st.markdown(f'<span class="badge">🏅 {badge}</span>', unsafe_allow_html=True)
                
                # Admin actions
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if user[3] != 'admin':  # Don't allow deactivating admin users
                        if st.button(f"{'Deactivate' if user[6] else 'Activate'}", key=f"toggle_{user[0]}"):
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("UPDATE users SET active = ? WHERE id = ?", (0 if user[6] else 1, user[0]))
                            conn.commit()
                            conn.close()
                            st.success(f"User {'deactivated' if user[6] else 'activated'} successfully!")
                            st.rerun()
                    else:
                        st.info("Admin user")
                
                with col2:
                    points_to_award = st.number_input(f"Award Points", min_value=0, max_value=1000, value=50, key=f"points_{user[0]}")
                    if st.button("🏆 Award", key=f"award_{user[0]}"):
                        award_points(user[0], points_to_award, "Admin Awarded Points")
                        st.success(f"Awarded {points_to_award} points!")
                        st.rerun()
                
                with col3:
                    badge_options = ["Excellence", "Top Performer", "Quick Learner", "Dedicated Student", "Expert Level"]
                    selected_badge = st.selectbox("Award Badge", badge_options, key=f"badge_{user[0]}")
                    if st.button("🏅 Badge", key=f"badge_btn_{user[0]}"):
                        award_badge(user[0], selected_badge)
                        st.success(f"Badge '{selected_badge}' awarded!")
                        st.rerun()
    
    with tab2:
        st.subheader("Add New User")
        
        with st.form("add_user_form"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["student", "professional", "admin"])
            
            if st.form_submit_button("➕ Create User"):
                if username and email and password:
                    success, message = create_user_by_admin(username, email, password, role)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please fill all fields")

def show_quiz_management():
    st.markdown('<div class="main-header"><h1>❓ Quiz Management</h1></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📝 Manage Questions", "➕ Add Questions", "🤖 AI Generate"])
    
    with tab1:
        st.subheader("Existing Quiz Questions")
        
        modules = get_available_modules()
        
        for module in modules:
            questions = get_quiz_questions(module['id'])
            
            with st.expander(f"📚 {module['title']} ({len(questions)} questions)"):
                if questions:
                    for i, question in enumerate(questions, 1):
                        st.write(f"**Q{i}:** {question['question']}")
                        st.write(f"**Options:** A) {question['options']['A']}, B) {question['options']['B']}, C) {question['options']['C']}, D) {question['options']['D']}")
                        st.write(f"**Correct:** {question['correct_answer']}")
                        if question['explanation']:
                            st.write(f"**Explanation:** {question['explanation']}")
                        st.markdown("---")
                else:
                    st.info("No questions available for this module")
    
    with tab2:
        st.subheader("Add New Quiz Question")
        
        modules = get_available_modules()
        selected_module = st.selectbox("Select Module", 
                                     [(m['id'], m['title']) for m in modules],
                                     format_func=lambda x: x[1])
        
        if selected_module:
            with st.form("add_question_form"):
                question = st.text_area("Question", height=100)
                
                col1, col2 = st.columns(2)
                with col1:
                    option_a = st.text_input("Option A")
                    option_c = st.text_input("Option C")
                with col2:
                    option_b = st.text_input("Option B")
                    option_d = st.text_input("Option D")
                
                correct_answer = st.selectbox("Correct Answer", ["A", "B", "C", "D"])
                explanation = st.text_area("Explanation (Optional)", height=80)
                
                if st.form_submit_button("➕ Add Question"):
                    if question and option_a and option_b and option_c and option_d:
                        if add_quiz_question(selected_module[0], question, option_a, option_b, 
                                           option_c, option_d, correct_answer, explanation):
                            st.success("Question added successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to add question")
                    else:
                        st.error("Please fill all required fields")
    
    with tab3:
        st.subheader("🤖 AI Question Generator")
        
        # Get DeepSeek API key
        try:
            api_key = st.secrets.get("DEEPSEEK_API_KEY", "sk-54bd3323c4d14bf08b941f0bff7a47d5")
        except:
            api_key = "sk-54bd3323c4d14bf08b941f0bff7a47d5"
        
        deepseek_chat = DeepSeekChat(api_key)
        
        modules = get_available_modules()
        selected_module = st.selectbox("Select Module for AI Generation", 
                                     [(m['id'], m['title']) for m in modules],
                                     format_func=lambda x: x[1])
        
        if selected_module:
            module_data = next(m for m in modules if m['id'] == selected_module[0])
            
            col1, col2 = st.columns(2)
            with col1:
                difficulty = st.selectbox("Question Difficulty", ["Beginner", "Intermediate", "Advanced"])
            with col2:
                question_count = st.number_input("Number of Questions", min_value=1, max_value=10, value=5)
            
            if st.button("🤖 Generate Questions with AI"):
                with st.spinner("AI is generating quiz questions..."):
                    result = deepseek_chat.generate_quiz_questions(
                        module_data['title'], 
                        difficulty, 
                        question_count
                    )
                    
                    if result and 'questions' in result:
                        st.subheader(f"🎯 Generated {len(result['questions'])} Questions:")
                        
                        for i, q in enumerate(result['questions'], 1):
                            with st.expander(f"Question {i}"):
                                st.write(f"**Question:** {q['question']}")
                                st.write(f"**A)** {q['option_a']}")
                                st.write(f"**B)** {q['option_b']}")
                                st.write(f"**C)** {q['option_c']}")
                                st.write(f"**D)** {q['option_d']}")
                                st.write(f"**Correct Answer:** {q['correct_answer']}")
                                st.write(f"**Explanation:** {q['explanation']}")
                                
                                if st.button(f"✅ Add Question {i}", key=f"add_ai_q_{i}"):
                                    if add_quiz_question(
                                        selected_module[0],
                                        q['question'],
                                        q['option_a'],
                                        q['option_b'],
                                        q['option_c'],
                                        q['option_d'],
                                        q['correct_answer'],
                                        q['explanation']
                                    ):
                                        st.success(f"Question {i} added successfully!")
                                        st.rerun()
                        
                        if st.button("✅ Add All Generated Questions"):
                            added_count = 0
                            for q in result['questions']:
                                if add_quiz_question(
                                    selected_module[0],
                                    q['question'],
                                    q['option_a'],
                                    q['option_b'],
                                    q['option_c'],
                                    q['option_d'],
                                    q['correct_answer'],
                                    q['explanation']
                                ):
                                    added_count += 1
                            
                            st.success(f"Added {added_count} questions successfully!")
                            st.rerun()
                    else:
                        st.error("Failed to generate questions. Please try again.")

def show_content_research():
    st.markdown('<div class="main-header"><h1>🔍 Content Research</h1></div>', unsafe_allow_html=True)
    
    researcher = ContentResearcher()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Research Topics")
        selected_topics = st.multiselect(
            "Select Topics to Research", 
            researcher.available_topics,
            help="Select one or more topics to research for content creation"
        )
        
        if st.button("🔍 Start Research", use_container_width=True):
            if selected_topics:
                with st.spinner("Researching content..."):
                    results = researcher.run_research(selected_topics)
                    st.session_state.research_results = results
                    st.success(f"Research completed for {len(selected_topics)} topics!")
            else:
                st.warning("Please select at least one topic to research")
    
    with col2:
        st.subheader("Research Results")
        
        if 'research_results' in st.session_state and st.session_state.research_results:
            for topic, content in st.session_state.research_results.items():
                with st.expander(f"📋 {topic}"):
                    st.write("**Key Points:**")
                    for i, point in enumerate(content['key_points'], 1):
                        st.write(f"{i}. {point}")
                    
                    st.write("**Sources:**")
                    for source in content['sources']:
                        st.write(f"• [{source['title']}]({source['url']}) - {source['date']}")
                    
                    st.write(f"**Last Updated:** {content.get('last_updated', 'N/A')}")
                    
                    if st.button(f"💾 Save Research", key=f"research_{topic}"):
                        # Save research to database
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            INSERT INTO content_research (topic, content, sources, created_date, status)
                            VALUES (?, ?, ?, ?, 'completed')
                        """, (
                            topic,
                            json.dumps(content['key_points']),
                            json.dumps(content['sources']),
                            datetime.now().isoformat()
                        ))
                        
                        conn.commit()
                        conn.close()
                        
                        st.success(f"Research for '{topic}' saved to database!")
        else:
            st.info("No research results yet. Select topics and click 'Start Research' to begin.")

def show_analytics():
    """Enhanced analytics page with comprehensive charts"""
    st.markdown('<div class="main-header"><h1>📈 System Analytics</h1></div>', unsafe_allow_html=True)
    
    create_admin_analytics_charts()
    
    # Additional analytics
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # User points distribution
    cursor.execute("""
        SELECT username, points 
        FROM users 
        WHERE role != 'admin' AND points > 0
        ORDER BY points DESC
        LIMIT 10
    """)
    
    top_users = cursor.fetchall()
    
    if top_users:
        st.subheader("🏆 Top Performers")
        
        df_top = pd.DataFrame(top_users, columns=['Username', 'Points'])
        
        fig3 = px.bar(
            df_top,
            x='Username',
            y='Points',
            title='Top 10 Users by Points',
            color='Points',
            color_continuous_scale='viridis'
        )
        
        st.plotly_chart(fig3, use_container_width=True)
    
    # Quiz performance by module
    cursor.execute("""
        SELECT m.title, AVG(p.quiz_score) as avg_score, COUNT(p.user_id) as attempts
        FROM modules m
        LEFT JOIN user_progress p ON m.id = p.module_id AND p.quiz_score > 0
        WHERE m.active = 1
        GROUP BY m.id, m.title
    """)
    
    quiz_performance = cursor.fetchall()
    
    if quiz_performance:
        st.subheader("📊 Quiz Performance by Module")
        
        df_quiz = pd.DataFrame(quiz_performance, columns=['Module', 'Average Score', 'Attempts'])
        df_quiz['Average Score'] = df_quiz['Average Score'].fillna(0)
        
        fig4 = px.scatter(
            df_quiz,
            x='Attempts',
            y='Average Score',
            size='Attempts',
            hover_name='Module',
            title='Quiz Performance vs Attempts'
        )
        
        st.plotly_chart(fig4, use_container_width=True)
    
    conn.close()

def show_ai_assistant():
    st.markdown('<div class="main-header"><h1>🤖 AI Assistant</h1></div>', unsafe_allow_html=True)
    
    st.info("💡 Ask me anything about real estate! I can help with RERA compliance, property valuation, legal frameworks, and more. I can also help generate content and quiz questions!")
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Get DeepSeek API key
    try:
        api_key = st.secrets.get("DEEPSEEK_API_KEY", "sk-54bd3323c4d14bf08b941f0bff7a47d5")
    except:
        api_key = "sk-54bd3323c4d14bf08b941f0bff7a47d5"
    
    deepseek_chat = DeepSeekChat(api_key)
    
    # Chat interface
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            st.markdown(f"**You:** {message['content']}")
            st.markdown("---")
        else:
            st.markdown(f"**🤖 AI Assistant:** {message['content']}")
            st.markdown("---")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "Ask me anything about real estate:", 
            key="chat_input", 
            placeholder="e.g., Generate 5 quiz questions about RERA compliance"
        )
    
    with col2:
        send_clicked = st.button("Send", use_container_width=True)
    
    if (send_clicked or user_input) and user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })
        
        # Get AI response
        with st.spinner("🤔 Thinking..."):
            response = deepseek_chat.get_response(user_input)
            
            # Add AI response to history
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response
            })
        
        # Clear input and rerun
        st.session_state.chat_input = ""
        st.rerun()
    
    # Quick questions with gamification focus
    st.markdown("---")
    st.subheader("💡 Quick Questions")
    
    quick_questions = [
        "What is RERA and how does it protect homebuyers?",
        "Generate 5 quiz questions about property valuation methods",
        "How do I calculate EMI for home loans?",
        "What are the latest FSI regulations in Mumbai?",
        "Create content outline for real estate investment module",
        "What are the tax benefits of buying property in India?",
        "How do I conduct due diligence before buying property?",
        "Generate assessment questions for RERA compliance"
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
                
                # Award points for using AI assistant
                award_points(st.session_state.user_id, 5, "Used AI Assistant")
                st.rerun()

def show_progress_page():
    st.markdown('<div class="main-header"><h1>📊 Your Learning Progress</h1></div>', unsafe_allow_html=True)
    
    # User stats with gamification
    user_stats = get_user_stats(st.session_state.user_id)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🏆 Total Points", user_stats['points'])
    
    with col2:
        st.metric("🏅 Badges Earned", len(user_stats['badges']))
    
    with col3:
        st.metric("🔥 Learning Streak", f"{user_stats['streak_days']} days")
    
    st.markdown("---")
    
    # Progress chart
    st.subheader("📈 Your Module Progress")
    create_user_progress_chart(st.session_state.user_id)
    
    st.markdown("---")
    
    # Module progress details
    st.subheader("📚 Detailed Progress")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT m.title, m.difficulty, COALESCE(p.quiz_score, 0) as score, p.quiz_attempts
        FROM modules m
        LEFT JOIN user_progress p ON m.id = p.module_id AND p.user_id = ?
        WHERE m.active = 1
        ORDER BY m.order_index
    """, (st.session_state.user_id,))
    
    progress_data = cursor.fetchall()
    conn.close()
    
    for module in progress_data:
        difficulty_color = {"Beginner": "🟢", "Intermediate": "🟡", "Advanced": "🔴"}
        color = difficulty_color.get(module[1], "📚")
        
        score = module[2] or 0
        attempts = module[3] or 0
        
        status = "✅ Completed" if score >= 70 else "📖 In Progress" if score > 0 else "⚪ Not Started"
        
        st.markdown(f"""
        <div class="module-card">
            <h4>{color} {module[0]}</h4>
            <p><strong>Difficulty:</strong> {module[1]} | <strong>Status:</strong> {status}</p>
            <p><strong>Best Score:</strong> {score:.1f}% | <strong>Attempts:</strong> {attempts}</p>
        </div>
        """, unsafe_allow_html=True)

def main():
    # Initialize database
    try:
        init_database()
    except Exception as e:
        st.error(f"Database initialization error: {str(e)}")
        st.stop()
    
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
        
        try:
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
            elif page == 'quiz_management':
                show_quiz_management()
            elif page == 'content_research':
                show_content_research()
            elif page == 'analytics':
                show_analytics()
            elif page == 'module_content':
                show_module_content()
            elif page == 'progress':
                show_progress_page()
            elif page == 'quiz':
                show_quiz()
            elif page == 'achievements':
                show_achievements()
            elif page == 'ai_assistant':
                show_ai_assistant()
            else:
                show_user_dashboard()
        except Exception as e:
            st.error(f"Page error: {str(e)}")
            st.info("Redirecting to dashboard...")
            st.session_state.current_page = 'dashboard'
            st.rerun()

if __name__ == "__main__":
    main()
