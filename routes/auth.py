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
        required = ['email','password','first_name','last_name','graduation_year','course','department']
        for f in required:
            if not data.get(f):
                return jsonify(error=f"{f} is required"), 400

        if not validate_email(data['email']):
            return jsonify(error="Invalid email format"), 400
        if User.query.filter_by(email=data['email'].lower()).first():
            return jsonify(error="Email already registered"), 400

        valid, msg = validate_password(data['password'])
        if not valid:
            return jsonify(error=msg), 400

        user = User(
            email=data['email'].lower(),
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=UserRole(data.get('role','alumni')),
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

        token = create_access_token(identity=str(user.id))
        return jsonify(message="User registered", access_token=token, user=user.to_dict(include_sensitive=True)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data.get('email') or not data.get('password'):
            return jsonify(error="Email and password required"), 400

        user = User.query.filter_by(email=data['email'].lower()).first()
        if not user or not user.is_active:
            return jsonify(error="Invalid credentials"), 401

        valid = False
        update_hash = False
        if check_password_hash(user.password_hash, data['password']):
            valid = True
        elif check_legacy_password(user.password_hash, data['password']):
            valid = True
            update_hash = True

        if not valid:
            return jsonify(error="Invalid credentials"), 401

        if update_hash:
            user.password_hash = generate_password_hash(data['password'])
        user.last_login = datetime.utcnow()
        db.session.commit()

        token = create_access_token(identity=str(user.id))
        return jsonify(message="Login successful", access_token=token, user=user.to_dict(include_sensitive=True)), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@auth_bp.route('/alumni-list', methods=['GET'])
@jwt_required()
def alumni_list():
    current_id = get_jwt_identity()
    users = User.query.filter(User.is_active.is_(True), User.id!=current_id).all()
    return jsonify([{'id':u.id,'first_name':u.first_name,'last_name':u.last_name} for u in users]), 200

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        uid = get_jwt_identity()
        user = User.query.get(uid)
        if not user:
            return jsonify(error="User not found"), 404
        return jsonify(user=user.to_dict(include_sensitive=True)), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        uid = get_jwt_identity()
        user = User.query.get(uid)
        if not user:
            return jsonify(error="User not found"), 404

        data = request.get_json()
        fields = ['first_name','last_name','phone','bio','current_company','current_position','industry','experience_years','skills','linkedin_url','city','state','country']
        for f in fields:
            if f in data:
                setattr(user, f, data[f])

        db.session.commit()
        return jsonify(message="Profile updated", user=user.to_dict(include_sensitive=True)), 200
    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        uid = get_jwt_identity()
        user = User.query.get(uid)
        if not user:
            return jsonify(error="User not found"), 404

        data = request.get_json()
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify(error="Both current and new passwords required"), 400

        valid = False
        if check_password_hash(user.password_hash, data['current_password']):
            valid = True
        elif check_legacy_password(user.password_hash, data['current_password']):
            valid = True

        if not valid:
            return jsonify(error="Current password incorrect"), 400

        valid_new, msg = validate_password(data['new_password'])
        if not valid_new:
            return jsonify(error=msg), 400

        user.set_password(data['new_password'])
        db.session.commit()
        return jsonify(message="Password changed"), 200
    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

# Debug endpoint (remove in production)
@auth_bp.route('/debug-user/<email>')
def debug_user(email):
    try:
        user = User.query.filter_by(email=email.lower()).first()
        if user:
            return jsonify(found=True, id=user.id, email=user.email, is_active=user.is_active,
                           hash_len=len(user.password_hash)), 200
        return jsonify(found=False), 404
    except Exception as e:
        return jsonify(error=str(e)), 500
