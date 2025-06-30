import sqlite3
import os
from database.models import DatabaseModels

DATABASE_PATH = "realestate_guru.db"

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database with tables and default data"""
    conn = get_db_connection()
    
    # Create tables
    DatabaseModels.create_tables(conn)
    
    # Insert default admin user if doesn't exist
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    admin_count = cursor.fetchone()[0]
    
    if admin_count == 0:
        import hashlib
        from datetime import datetime
        
        admin_password = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute("""
            INSERT INTO users (username, email, password, role, created_date)
            VALUES (?, ?, ?, ?, ?)
        """, ("admin", "admin@realestateguruapp.com", admin_password, "admin", datetime.now().isoformat()))
        
        conn.commit()
    
    # Insert default modules if they don't exist
    cursor.execute("SELECT COUNT(*) FROM modules")
    module_count = cursor.fetchone()[0]
    
    if module_count == 0:
        default_modules = [
            {
                'title': 'Real Estate Fundamentals',
                'description': 'Introduction to real estate basics, stakeholders, and market overview',
                'difficulty': 'Beginner',
                'category': 'Fundamentals',
                'content': 'Complete introduction to real estate industry in India...',
                'order_index': 1
            },
            {
                'title': 'Legal Framework & RERA',
                'description': 'Comprehensive guide to RERA, legal compliance, and regulatory framework',
                'difficulty': 'Intermediate',
                'category': 'Legal Framework',
                'content': 'Understanding RERA Act 2016 and its implications...',
                'order_index': 2
            },
            {
                'title': 'Property Measurements & Standards',
                'description': 'Carpet area vs built-up area, BIS standards, and floor plan reading',
                'difficulty': 'Beginner',
                'category': 'Measurements',
                'content': 'Learn about different property measurement standards...',
                'order_index': 3
            },
            {
                'title': 'Valuation & Finance',
                'description': 'Property valuation methods, home loans, and taxation',
                'difficulty': 'Intermediate',
                'category': 'Finance',
                'content': 'Master property valuation techniques and financing options...',
                'order_index': 4
            },
            {
                'title': 'Land & Development Laws',
                'description': 'GDCR, municipal bylaws, FSI/TDR calculations, and zoning',
                'difficulty': 'Advanced',
                'category': 'Legal Framework',
                'content': 'Deep dive into land development regulations...',
                'order_index': 5
            }
        ]
        
        from datetime import datetime
        for module in default_modules:
            cursor.execute("""
                INSERT INTO modules (title, description, difficulty, category, content, order_index, created_date, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                module['title'],
                module['description'],
                module['difficulty'],
                module['category'],
                module['content'],
                module['order_index'],
                datetime.now().isoformat()
            ))
        
        conn.commit()
    
    conn.close()

def seed_sample_data():
    """Seed database with sample data for testing"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Add sample lessons
    cursor.execute("SELECT id FROM modules LIMIT 1")
    module_id = cursor.fetchone()[0]
    
    sample_lessons = [
        {
            'module_id': module_id,
            'title': 'Introduction to Real Estate',
            'content': 'What is real estate and why is it important...',
            'order_index': 1
        },
        {
            'module_id': module_id,
            'title': 'Key Stakeholders',
            'content': 'Understanding the various players in real estate...',
            'order_index': 2
        },
        {
            'module_id': module_id,
            'title': 'Market Overview',
            'content': 'Current state of Indian real estate market...',
            'order_index': 3
        }
    ]
    
    from datetime import datetime
    for lesson in sample_lessons:
        cursor.execute("""
            INSERT INTO lessons (module_id, title, content, order_index, created_date, active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (
            lesson['module_id'],
            lesson['title'],
            lesson['content'],
            lesson['order_index'],
            datetime.now().isoformat()
        ))
    
    conn.commit()
    conn.close()
