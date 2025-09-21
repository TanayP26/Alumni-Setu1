# -*- coding: utf-8 -*-
"""
Created on Thu Sep 11 17:02:00 2025
@author: Admin
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User, UserRole
from datetime import datetime
import re, hashlib

auth_bp = Blueprint('auth', __name__)


def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
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
    try:
        if stored_hash == password:
            return True
        if stored_hash == hashlib.md5(password.encode()).hexdigest():
            return True
        if stored_hash == hashlib.sha1(password.encode()).hexdigest():
            return True
        if stored_hash == hashlib.sha256(password.encode()).hexdigest():
            return True
        return False
    except:
        return False


@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        required_fields = [
            'email', 'password', 'first_name', 'last_name',
            'graduation_year', 'course', 'department'
        ]
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400

        if User.query.filter_by(email=data['email'].lower()).first():
            return jsonify({'error': 'Email already registered'}), 400

        is_valid, msg = validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': msg}), 400

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

        password_valid = False
        needs_update = False

        if user.password_hash and check_password_hash(user.password_hash, data['password']):
            password_valid = True
        elif user.password_hash and check_legacy_password(user.password_hash, data['password']):
            password_valid = True
            needs_update = True

        if not password_valid:
            return jsonify({'error': 'Invalid credentials'}), 401

        if needs_update:
            user.password_hash = generate_password_hash(data['password'])
        user.last_login = datetime.utcnow()
        db.session.commit()

        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict(include_sensitive=True)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/alumni-list', methods=['GET'])
@jwt_required()
def alumni_list():
    current_id = get_jwt_identity()
    users = User.query.filter(User.is_active.is_(True), User.id != current_id).all()
    return jsonify([
        {'id': u.id, 'first_name': u.first_name, 'last_name': u.last_name}
        for u in users
    ]), 200


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        uid = get_jwt_identity()
        user = User.query.get(uid)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'user': user.to_dict(include_sensitive=True)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        uid = get_jwt_identity()
        user = User.query.get(uid)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()
        allowed = [
            'first_name', 'last_name', 'phone', 'bio',
            'current_company', 'current_position', 'industry',
            'experience_years', 'skills', 'linkedin_url',
            'city', 'state', 'country'
        ]
        for field in allowed:
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
        uid = get_jwt_identity()
        user = User.query.get(uid)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Current and new passwords are required'}), 400

        valid = False
        if check_password_hash(user.password_hash, data['current_password']):
            valid = True
        elif check_legacy_password(user.password_hash, data['current_password']):
            valid = True

        if not valid:
            return jsonify({'error': 'Current password is incorrect'}), 400

        is_valid, msg = validate_password(data['new_password'])
        if not is_valid:
            return jsonify({'error': msg}), 400

        user.set_password(data['new_password'])
        db.session.commit()
        return jsonify({'message': 'Password changed successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Debug endpoint—remove in production
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
                'hash_len': len(user.password_hash) if user.password_hash else 0
            }), 200
        return jsonify({'found': False}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
