# -*- coding: utf-8 -*-
"""
Created on Thu Sep 11 17:04:50 2025

@author: Admin
"""


from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, Message, db
from datetime import datetime

messages_bp = Blueprint('messages', __name__)

@messages_bp.route('/', methods=['GET'])
@jwt_required()
def get_messages():
    try:
        current_user_id = get_jwt_identity()

        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        message_type = request.args.get('type', 'received')  # received, sent, all

        # Build query based on type
        if message_type == 'sent':
            query = Message.query.filter_by(sender_id=current_user_id)
        elif message_type == 'all':
            query = Message.query.filter(
                (Message.sender_id == current_user_id) | 
                (Message.receiver_id == current_user_id)
            )
        else:  # received (default)
            query = Message.query.filter_by(receiver_id=current_user_id)

        # Order by latest first
        query = query.order_by(Message.created_at.desc())

        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        messages = pagination.items

        return jsonify({
            'messages': [message.to_dict() for message in messages],
            'pagination': {
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/<int:message_id>', methods=['GET'])
@jwt_required()
def get_message(message_id):
    try:
        current_user_id = get_jwt_identity()

        message = Message.query.get(message_id)

        if not message:
            return jsonify({'error': 'Message not found'}), 404

        # Check if user has access to this message
        if message.sender_id != current_user_id and message.receiver_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403

        # Mark as read if receiver is viewing
        if message.receiver_id == current_user_id and not message.is_read:
            message.is_read = True
            db.session.commit()

        return jsonify({
            'message': message.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/', methods=['POST'])
@jwt_required()
def send_message():
    try:
        current_user_id = get_jwt_identity()

        data = request.get_json()

        # Validate required fields
        if not data.get('receiver_id') or not data.get('content'):
            return jsonify({'error': 'Receiver ID and content are required'}), 400

        # Check if receiver exists
        receiver = User.query.get(data['receiver_id'])
        if not receiver or not receiver.is_active:
            return jsonify({'error': 'Receiver not found'}), 404

        # Create message
        message = Message(
            sender_id=current_user_id,
            receiver_id=data['receiver_id'],
            subject=data.get('subject'),
            content=data['content']
        )

        db.session.add(message)
        db.session.commit()

        return jsonify({
            'message': 'Message sent successfully',
            'message_data': message.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/<int:message_id>/read', methods=['POST'])
@jwt_required()
def mark_as_read(message_id):
    try:
        current_user_id = get_jwt_identity()

        message = Message.query.get(message_id)

        if not message:
            return jsonify({'error': 'Message not found'}), 404

        # Check if user is the receiver
        if message.receiver_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403

        message.is_read = True
        db.session.commit()

        return jsonify({
            'message': 'Message marked as read'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    try:
        current_user_id = get_jwt_identity()

        # Get unique conversation partners
        sent_to = db.session.query(Message.receiver_id.label('user_id')).filter_by(sender_id=current_user_id).distinct()
        received_from = db.session.query(Message.sender_id.label('user_id')).filter_by(receiver_id=current_user_id).distinct()

        # Combine and get user details
        conversation_user_ids = [row.user_id for row in sent_to.union(received_from).all()]

        conversations = []
        for user_id in conversation_user_ids:
            user = User.query.get(user_id)
            if not user:
                continue

            # Get last message in conversation
            last_message = Message.query.filter(
                ((Message.sender_id == current_user_id) & (Message.receiver_id == user_id)) |
                ((Message.sender_id == user_id) & (Message.receiver_id == current_user_id))
            ).order_by(Message.created_at.desc()).first()

            # Count unread messages from this user
            unread_count = Message.query.filter_by(
                sender_id=user_id,
                receiver_id=current_user_id,
                is_read=False
            ).count()

            conversations.append({
                'user': user.to_dict(),
                'last_message': last_message.to_dict() if last_message else None,
                'unread_count': unread_count
            })

        # Sort by last message time
        conversations.sort(key=lambda x: x['last_message']['created_at'] if x['last_message'] else '', reverse=True)

        return jsonify({
            'conversations': conversations
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/conversation/<int:user_id>', methods=['GET'])
@jwt_required()
def get_conversation_with_user(user_id):
    try:
        current_user_id = get_jwt_identity()

        # Check if other user exists
        other_user = User.query.get(user_id)
        if not other_user:
            return jsonify({'error': 'User not found'}), 404

        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # Get messages between users
        query = Message.query.filter(
            ((Message.sender_id == current_user_id) & (Message.receiver_id == user_id)) |
            ((Message.sender_id == user_id) & (Message.receiver_id == current_user_id))
        ).order_by(Message.created_at.desc())

        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        messages = pagination.items

        # Mark messages from other user as read
        unread_messages = Message.query.filter_by(
            sender_id=user_id,
            receiver_id=current_user_id,
            is_read=False
        ).all()

        for message in unread_messages:
            message.is_read = True

        db.session.commit()

        return jsonify({
            'messages': [message.to_dict() for message in messages],
            'other_user': other_user.to_dict(),
            'pagination': {
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    try:
        current_user_id = get_jwt_identity()

        unread_count = Message.query.filter_by(
            receiver_id=current_user_id,
            is_read=False
        ).count()

        return jsonify({
            'unread_count': unread_count
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
