import sqlite3
from datetime import datetime

class DatabaseModels:
    @staticmethod
    def create_tables(conn):
        cursor = conn.cursor()
        
        # Users table
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
        
        # Modules table
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
        
        # Lessons table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                video_url TEXT,
                order_index INTEGER DEFAULT 0,
                created_date TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                FOREIGN KEY (module_id) REFERENCES modules (id)
            )
        """)
        
        # User progress table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                module_id INTEGER NOT NULL,
                lesson_id INTEGER,
                progress_percentage REAL DEFAULT 0,
                completed INTEGER DEFAULT 0,
                started_date TEXT,
                completed_date TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (module_id) REFERENCES modules (id),
                FOREIGN KEY (lesson_id) REFERENCES lessons (id)
            )
        """)
        
        # Assessments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                questions TEXT NOT NULL,
                passing_score INTEGER DEFAULT 70,
                time_limit INTEGER DEFAULT 30,
                created_date TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                FOREIGN KEY (module_id) REFERENCES modules (id)
            )
        """)
        
        # User assessment results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assessment_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                assessment_id INTEGER NOT NULL,
                score REAL NOT NULL,
                answers TEXT,
                started_date TEXT NOT NULL,
                completed_date TEXT,
                passed INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (assessment_id) REFERENCES assessments (id)
            )
        """)
        
        # Gamification points
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                points INTEGER DEFAULT 0,
                badges TEXT,
                streak_days INTEGER DEFAULT 0,
                last_activity TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Content research table
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
        
        # Video content table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_id INTEGER,
                title TEXT NOT NULL,
                description TEXT,
                youtube_id TEXT,
                duration TEXT,
                thumbnail_url TEXT,
                created_date TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                FOREIGN KEY (module_id) REFERENCES modules (id)
            )
        """)
        
        conn.commit()
