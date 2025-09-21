from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import User, Message
from datetime import datetime

messaging_bp = Blueprint('messaging', __name__)

@messaging_bp.route('/send', methods=['POST'])
@jwt_required()
def send_message():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not all(key in data for key in ['recipient_id', 'subject', 'content']):
            return jsonify({'error': 'Recipient ID, subject, and content are required'}), 400
        
        # Check if recipient exists
        recipient = User.query.get(data['recipient_id'])
        if not recipient:
            return jsonify({'error': 'Recipient not found'}), 404
        
        # Don't allow sending to self
        if int(current_user_id) == int(data['recipient_id']):
            return jsonify({'error': 'Cannot send message to yourself'}), 400
        
        # Create message
        message = Message(
            sender_id=int(current_user_id),
            recipient_id=int(data['recipient_id']),
            subject=data['subject'],
            content=data['content']
        )
        
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'message': 'Message sent successfully',
            'data': message.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@messaging_bp.route('/inbox', methods=['GET'])
@jwt_required()
def get_inbox():
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        messages = Message.query.filter_by(recipient_id=current_user_id)\
                               .order_by(Message.timestamp.desc())\
                               .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'messages': [msg.to_dict() for msg in messages.items],
            'total': messages.total,
            'page': page,
            'per_page': per_page,
            'pages': messages.pages
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messaging_bp.route('/sent', methods=['GET'])
@jwt_required()
def get_sent():
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        messages = Message.query.filter_by(sender_id=current_user_id)\
                               .order_by(Message.timestamp.desc())\
                               .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'messages': [msg.to_dict() for msg in messages.items],
            'total': messages.total,
            'page': page,
            'per_page': per_page,
            'pages': messages.pages
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messaging_bp.route('/<int:message_id>', methods=['GET'])
@jwt_required()
def get_message(message_id):
    try:
        current_user_id = get_jwt_identity()
        message = Message.query.get(message_id)
        
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # Only sender or recipient can view message
        if message.sender_id != int(current_user_id) and message.recipient_id != int(current_user_id):
            return jsonify({'error': 'Access denied'}), 403
        
        # Mark as read if recipient is viewing
        if message.recipient_id == int(current_user_id) and not message.is_read:
            message.is_read = True
            db.session.commit()
        
        return jsonify({'message': message.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messaging_bp.route('/<int:message_id>/read', methods=['PUT'])
@jwt_required()
def mark_as_read(message_id):
    try:
        current_user_id = get_jwt_identity()
        message = Message.query.get(message_id)
        
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # Only recipient can mark as read
        if message.recipient_id != int(current_user_id):
            return jsonify({'error': 'Access denied'}), 403
        
        message.is_read = True
        db.session.commit()
        
        return jsonify({'message': 'Message marked as read'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@messaging_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    try:
        current_user_id = get_jwt_identity()
        count = Message.query.filter_by(recipient_id=current_user_id, is_read=False).count()
        return jsonify({'unread_count': count}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messaging_bp.route('/<int:message_id>', methods=['DELETE'])
@jwt_required()
def delete_message(message_id):
    try:
        current_user_id = get_jwt_identity()
        message = Message.query.get(message_id)
        
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # Only sender or recipient can delete message
        if message.sender_id != int(current_user_id) and message.recipient_id != int(current_user_id):
            return jsonify({'error': 'Access denied'}), 403
        
        db.session.delete(message)
        db.session.commit()
        
        return jsonify({'message': 'Message deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
