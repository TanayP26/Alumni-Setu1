# -*- coding: utf-8 -*-
"""
Created on Thu Sep 11 17:00:11 2025
@author: Admin
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_socketio import emit, join_room
from extensions import db, socketio
from models import User, Message
from datetime import datetime

messaging_bp = Blueprint('messaging', __name__)

@socketio.on('connect')
@jwt_required()
def handle_connect():
    user_id = get_jwt_identity()
    join_room(f"user_{user_id}")

@messaging_bp.route('/send', methods=['POST'])
@jwt_required()
def send_message():
    try:
        sender_id = get_jwt_identity()
        data = request.get_json()
        if not all(k in data for k in ('recipient_id','subject','content')):
            return jsonify(error='Recipient, subject, and content required'), 400

        recipient = User.query.get(data['recipient_id'])
        if not recipient or recipient.id == sender_id:
            return jsonify(error='Invalid recipient'), 400

        msg = Message(
            sender_id=sender_id,
            recipient_id=data['recipient_id'],
            subject=data['subject'],
            content=data['content']
        )
        db.session.add(msg)
        db.session.commit()

        payload = msg.to_dict()
        socketio.emit('new_message', payload, room=f"user_{msg.recipient_id}")
        return jsonify(message='Message sent', data=payload), 201

    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

@messaging_bp.route('/inbox', methods=['GET'])
@jwt_required()
def get_inbox():
    try:
        user_id = get_jwt_identity()
        msgs = Message.query.filter_by(recipient_id=user_id)\
                            .order_by(Message.timestamp.desc()).all()
        return jsonify(messages=[m.to_dict() for m in msgs]), 200

    except Exception as e:
        return jsonify(error=str(e)), 500

@messaging_bp.route('/sent', methods=['GET'])
@jwt_required()
def get_sent():
    try:
        user_id = get_jwt_identity()
        msgs = Message.query.filter_by(sender_id=user_id)\
                            .order_by(Message.timestamp.desc()).all()
        return jsonify(messages=[m.to_dict() for m in msgs]), 200

    except Exception as e:
        return jsonify(error=str(e)), 500

@messaging_bp.route('/<int:msg_id>', methods=['GET'])
@jwt_required()
def get_message(msg_id):
    try:
        user_id = get_jwt_identity()
        msg = Message.query.get(msg_id)
        if not msg:
            return jsonify(error='Message not found'), 404
        if msg.sender_id != user_id and msg.recipient_id != user_id:
            return jsonify(error='Access denied'), 403

        if msg.recipient_id == user_id and not msg.is_read:
            msg.is_read = True
            db.session.commit()

        return jsonify(message=msg.to_dict()), 200

    except Exception as e:
        return jsonify(error=str(e)), 500

@messaging_bp.route('/<int:msg_id>', methods=['DELETE'])
@jwt_required()
def delete_message(msg_id):
    try:
        user_id = get_jwt_identity()
        msg = Message.query.get(msg_id)
        if not msg:
            return jsonify(error='Message not found'), 404
        if msg.sender_id != user_id and msg.recipient_id != user_id:
            return jsonify(error='Access denied'), 403

        db.session.delete(msg)
        db.session.commit()
        return jsonify(message='Message deleted successfully'), 200

    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

@messaging_bp.route('/<int:msg_id>/read', methods=['PUT'])
@jwt_required()
def mark_as_read(msg_id):
    try:
        user_id = get_jwt_identity()
        msg = Message.query.get(msg_id)
        if not msg:
            return jsonify(error='Message not found'), 404
        if msg.recipient_id != user_id:
            return jsonify(error='Access denied'), 403

        msg.is_read = True
        db.session.commit()
        return jsonify(message='Message marked as read'), 200

    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

@messaging_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    try:
        user_id = get_jwt_identity()
        count = Message.query.filter_by(recipient_id=user_id, is_read=False).count()
        return jsonify(unread_count=count), 200

    except Exception as e:
        return jsonify(error=str(e)), 500
