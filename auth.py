import hashlib
import streamlit as st
from datetime import datetime, timedelta
import jwt
from database.database import get_db_connection

class AuthManager:
    def __init__(self):
        self.secret_key = "your-secret-key-here"  # Change this in production
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password, hashed_password):
        """Verify password against hash"""
        return self.hash_password(password) == hashed_password
    
    def create_jwt_token(self, user_id, username, role):
        """Create JWT token for user session"""
        
        payload = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_jwt_token(self, token):
        """Verify JWT token"""
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def login_user(self, username, password):
        """Authenticate user and create session"""
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user from database
        cursor.execute("""
            SELECT id, username, password, role, active 
            FROM users 
            WHERE username = ?
        """, (username,))
        
        user = cursor.fetchone()
        
        if user and user[4] == 1:  # Check if user is active
            if self.verify_password(password, user[2]):
                # Update last login
                cursor.execute("""
                    UPDATE users 
                    SET last_login = ? 
                    WHERE id = ?
                """, (datetime.now().isoformat(), user[0]))
                
                conn.commit()
                conn.close()
                
                # Create session
                token = self.create_jwt_token(user[0], user[1], user[3])
                
                return {
                    'success': True,
                    'user_id': user[0],
                    'username': user[1],
                    'role': user[3],
                    'token': token
                }
        
        conn.close()
        return {'success': False, 'message': 'Invalid credentials'}
    
    def register_user(self, username, email, password, role='student'):
        """Register new user"""
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Check if username or email already exists
            cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE username = ? OR email = ?
            """, (username, email))
            
            if cursor.fetchone()[0] > 0:
                conn.close()
                return {'success': False, 'message': 'Username or email already exists'}
            
            # Hash password
            hashed_password = self.hash_password(password)
            
            # Insert new user
            cursor.execute("""
                INSERT INTO users (username, email, password, role, created_date, active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (username, email, hashed_password, role, datetime.now().isoformat()))
            
            user_id = cursor.lastrowid
            
            # Initialize user points
            cursor.execute("""
                INSERT INTO user_points (user_id, points, badges, streak_days, last_activity)
                VALUES (?, 0, '[]', 0, ?)
            """, (user_id, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'user_id': user_id, 'message': 'Registration successful'}
            
        except Exception as e:
            conn.close()
            return {'success': False, 'message': f'Registration failed: {str(e)}'}
    
    def change_password(self, user_id, old_password, new_password):
        """Change user password"""
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify old password
        cursor.execute("SELECT password FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        
        if result and self.verify_password(old_password, result[0]):
            # Update password
            new_hashed = self.hash_password(new_password)
            cursor.execute("""
                UPDATE users 
                SET password = ? 
                WHERE id = ?
            """, (new_hashed, user_id))
            
            conn.commit()
            conn.close()
            return {'success': True, 'message': 'Password changed successfully'}
        
        conn.close()
        return {'success': False, 'message': 'Invalid old password'}
    
    def get_user_profile(self, user_id):
        """Get user profile information"""
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.id, u.username, u.email, u.role, u.created_date, u.last_login,
                   up.points, up.badges, up.streak_days
            FROM users u
            LEFT JOIN user_points up ON u.id = up.user_id
            WHERE u.id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'username': result[1],
                'email': result[2],
                'role': result[3],
                'created_date': result[4],
                'last_login': result[5],
                'points': result[6] or 0,
                'badges': result[7] or '[]',
                'streak_days': result[8] or 0
            }
        
        return None
    
    def update_user_activity(self, user_id):
        """Update user's last activity"""
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update last activity
        cursor.execute("""
            UPDATE user_points 
            SET last_activity = ? 
            WHERE user_id = ?
        """, (datetime.now().isoformat(), user_id))
        
        # Check and update streak
        cursor.execute("""
            SELECT last_activity, streak_days 
            FROM user_points 
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        
        if result and result[0]:
            last_activity = datetime.fromisoformat(result[0])
            current_streak = result[1] or 0
            
            # If last activity was yesterday, increment streak
            if (datetime.now() - last_activity).days == 1:
                current_streak += 1
                cursor.execute("""
                    UPDATE user_points 
                    SET streak_days = ? 
                    WHERE user_id = ?
                """, (current_streak, user_id))
            # If more than 1 day, reset streak
            elif (datetime.now() - last_activity).days > 1:
                cursor.execute("""
                    UPDATE user_points 
                    SET streak_days = 1 
                    WHERE user_id = ?
                """, (user_id,))
        
        conn.commit()
        conn.close()

# Convenience functions for backward compatibility
def check_authentication():
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def get_user_role(username):
    """Get user role (deprecated - use AuthManager instead)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT role FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

# Initialize auth manager
auth_manager = AuthManager()
