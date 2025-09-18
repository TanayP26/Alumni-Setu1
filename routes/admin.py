# -*- coding: utf-8 -*-
"""
Created on Thu Sep 11 17:04:28 2025

@author: Admin
"""


from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, UserRole, db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user.role != UserRole.ADMIN:
        return jsonify({'error': 'Permission denied'}), 403

    users = User.query.all()
    return jsonify({'users': [u.to_dict() for u in users]}), 200

@admin_bp.route('/users/<int:user_id>/activate', methods=['POST'])
@jwt_required()
def activate_user(user_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user.role != UserRole.ADMIN:
        return jsonify({'error': 'Permission denied'}), 403

    target = User.query.get(user_id)
    if not target:
        return jsonify({'error': 'User not found'}), 404
    target.is_active = True
    db.session.commit()
    return jsonify({'message': 'User activated'}), 200

@admin_bp.route('/users/<int:user_id>/deactivate', methods=['POST'])
@jwt_required()
def deactivate_user(user_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user.role != UserRole.ADMIN:
        return jsonify({'error': 'Permission denied'}), 403

    target = User.query.get(user_id)
    if not target:
        return jsonify({'error': 'User not found'}), 404
    target.is_active = False
    db.session.commit()
    return jsonify({'message': 'User deactivated'}), 200
