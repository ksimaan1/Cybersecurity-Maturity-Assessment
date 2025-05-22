#!/usr/bin/env python3
"""
Script to create an admin user for the application
"""

import sys
import os
from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine, text

def create_admin_user():
    """Create an admin user"""
    
    # Database configuration
    DATABASE_URL = 'sqlite:///app.db'
    engine = create_engine(DATABASE_URL)
    
    # User details
    username = input("Enter admin username: ").strip()
    if not username:
        print("Username cannot be empty")
        return False
        
    email = input("Enter admin email: ").strip()
    if not email:
        print("Email cannot be empty")
        return False
        
    password = input("Enter admin password: ").strip()
    if not password:
        print("Password cannot be empty")
        return False
        
    first_name = input("Enter first name: ").strip() or "Admin"
    last_name = input("Enter last name: ").strip() or "User"
    
    try:
        with engine.connect() as conn:
            # Check if user already exists
            result = conn.execute(
                text("SELECT id FROM user WHERE username = :username OR email = :email"),
                {"username": username, "email": email}
            ).fetchone()
            
            if result:
                print("❌ User with this username or email already exists")
                return False
            
            # Create the user
            password_hash = generate_password_hash(password)
            conn.execute(
                text("""
                INSERT INTO user (username, email, password_hash, first_name, last_name, role, language)
                VALUES (:username, :email, :password_hash, :first_name, :last_name, :role, :language)
                """),
                {
                    "username": username,
                    "email": email, 
                    "password_hash": password_hash,
                    "first_name": first_name,
                    "last_name": last_name,
                    "role": "admin",
                    "language": "en"
                }
            )
            conn.commit()
            
        print(f"✅ Admin user '{username}' created successfully!")
        print(f"You can now login with:")
        print(f"Username: {username}")
        print(f"Password: {password}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False

if __name__ == "__main__":
    print("=== Create Admin User ===")
    success = create_admin_user()
    sys.exit(0 if success else 1)