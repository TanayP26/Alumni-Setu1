# -*- coding: utf-8 -*-
"""
Created on Thu Sep 11 17:05:22 2025

@author: Admin
"""

# init_db.py

from app import create_app, db
from models import User, UserRole
from werkzeug.security import generate_password_hash

def init_database():
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()

        # Create default admin user if not exists
        admin_user = User.query.filter_by(email='admin@alumni.com').first()
        if not admin_user:
            admin_user = User(
                email='admin@alumni.com',
                first_name='Admin',
                last_name='User',
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
                graduation_year=2020,
                course='Computer Science',
                department='Engineering'
            )
            # Hash and set password
            admin_user.password_hash = generate_password_hash('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user created:")
            print("  Email: admin@alumni.com")
            print("  Password: admin123")
        else:
            print("Admin user already exists")

        print("Database initialized successfully!")

if __name__ == '__main__':
    init_database()
