# -*- coding: utf-8 -*-
"""
Created on Thu Sep 11 17:02:00 2025

@author: Admin
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User, UserRole
from datetime import datetime
import re
import hashlib

auth_bp = Blueprint('auth', __name__)
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    # ... other fields ...
    password_hash = db.Column(db.String(255), nullable=False)
    
    def set_password(self, password):
        """Set password using secure Werkzeug hashing"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password - this method is now handled in auth.py for legacy support"""
        return check_password_hash(self.password_hash, password)


def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    # At least 8 characters, one uppercase, one lowercase, one digit
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Valid password"


def check_legacy_password(stored_hash, password):
    """Check if password matches legacy format and return True if it does"""
    try:
        # Try common legacy formats
        
        # 1. Plain text (very insecure, but might exist)
        if stored_hash == password:
            return True
            
        # 2. MD5 hash
        if stored_hash == hashlib.md5(password.encode()).hexdigest():
            return True
            
        # 3. SHA1 hash  
        if stored_hash == hashlib.sha1(password.encode()).hexdigest():
            return True
            
        # 4. SHA256 hash
        if stored_hash == hashlib.sha256(password.encode()).hexdigest():
            return True
            
        # Add other legacy formats as needed
        return False
        
    except Exception:
        return False


@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name',
                           'graduation_year', 'course', 'department']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400

        # Validate email
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400

        # Check if user already exists
        if User.query.filter_by(email=data['email'].lower()).first():
            return jsonify({'error': 'Email already registered'}), 400

        # Validate password
        is_valid, message = validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': message}), 400

        # Create new user
        user = User(
            email=data['email'].lower(),
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=UserRole(data.get('role', 'alumni')),
            graduation_year=data['graduation_year'],
            course=data['course'],
            department=data['department'],
            phone=data.get('phone'),
            student_id=data.get('student_id'),
            bio=data.get('bio'),
            current_company=data.get('current_company'),
            current_position=data.get('current_position'),
            industry=data.get('industry'),
            experience_years=data.get('experience_years'),
            skills=data.get('skills'),
            linkedin_url=data.get('linkedin_url'),
            city=data.get('city'),
            state=data.get('state'),
            country=data.get('country')
        )
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()

        # Create access token with identity as string
        access_token = create_access_token(identity=str(user.id))

        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': user.to_dict(include_sensitive=True)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()

        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400

        user = User.query.filter_by(email=data['email'].lower()).first()

        if not user or not user.is_active:
            return jsonify({'error': 'Invalid credentials'}), 401

        # Check password with legacy support
        password_valid = False
        needs_hash_update = False

        # Try modern Werkzeug format first
        if user.password_hash and check_password_hash(user.password_hash, data['password']):
            password_valid = True
        
        # If modern format fails, try legacy formats
        elif user.password_hash and check_legacy_password(user.password_hash, data['password']):
            password_valid = True
            needs_hash_update = True

        if password_valid:
            # Update to modern hash format if using legacy
            if needs_hash_update:
                user.password_hash = generate_password_hash(data['password'])
                print(f"Updated legacy password for user {user.email}")

            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()

            # Create access token with identity as string
            access_token = create_access_token(identity=str(user.id))

            return jsonify({
                'message': 'Login successful',
                'access_token': access_token,
                'user': user.to_dict(include_sensitive=True)
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401

    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'user': user.to_dict(include_sensitive=True)}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()
        # Update allowed fields
        updatable_fields = [
            'first_name', 'last_name', 'phone', 'bio', 'current_company',
            'current_position', 'industry', 'experience_years', 'skills',
            'linkedin_url', 'city', 'state', 'country'
        ]
        for field in updatable_fields:
            if field in data:
                setattr(user, field, data[field])

        db.session.commit()
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict(include_sensitive=True)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()
        if not all(key in data for key in ['current_password', 'new_password']):
            return jsonify({'error': 'Current password and new password are required'}), 400

        # Check current password with legacy support
        password_valid = False
        if user.password_hash and check_password_hash(user.password_hash, data['current_password']):
            password_valid = True
        elif user.password_hash and check_legacy_password(user.password_hash, data['current_password']):
            password_valid = True

        if not password_valid:
            return jsonify({'error': 'Current password is incorrect'}), 400

        # Validate new password
        is_valid, message = validate_password(data['new_password'])
        if not is_valid:
            return jsonify({'error': message}), 400

        user.set_password(data['new_password'])
        db.session.commit()
        return jsonify({'message': 'Password changed successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Debug endpoint (remove in production)
@auth_bp.route('/debug-user/<email>')
def debug_user(email):
    try:
        user = User.query.filter_by(email=email.lower()).first()
        if user:
            return jsonify({
                'found': True,
                'id': user.id,
                'email': user.email,
                'is_active': user.is_active,
                'password_hash_length': len(user.password_hash) if user.password_hash else 0,
                'password_hash_starts_with': user.password_hash[:20] if user.password_hash else None
            })
        return jsonify({'found': False})
    except Exception as e:
        return jsonify({'error': str(e)})
