from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_socketio import emit, join_room
from extensions import db, socketio
from datetime import datetime

messaging_bp = Blueprint('messaging', __name__)

# Handle websocket connection and join room for receiving messages
@socketio.on('connect')
@jwt_required()
def handle_connect():
    user_id = get_jwt_identity()
    join_room(f"user_{user_id}")

# Send message API
@messaging_bp.route('/send', methods=['POST'])
@jwt_required()
def send_message():
    from models import User, Message
    try:
        sender_id = get_jwt_identity()
        data = request.get_json()
        recipient_id = data.get('recipient_id')
        subject = data.get('subject')
        content = data.get('content')

        if not recipient_id or not subject or not content:
            return jsonify(error='Recipient, subject, and content are required'), 400

        if sender_id == recipient_id:
            return jsonify(error='Cannot send message to self'), 400

        recipient = User.query.get(recipient_id)
        if not recipient:
            return jsonify(error='Recipient not found'), 404

        new_msg = Message(
            sender_id=sender_id,
            recipient_id=recipient_id,
            subject=subject,
            content=content,
            timestamp=datetime.utcnow()
        )

        db.session.add(new_msg)
        db.session.commit()

        payload = new_msg.to_dict()

        # Notify recipient in real-time via socket.io
        socketio.emit('new_message', payload, room=f"user_{recipient_id}")

        return jsonify(message='Message sent', data=payload), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

# Get user's inbox messages
@messaging_bp.route('/inbox', methods=['GET'])
@jwt_required()
def get_inbox():
    from models import Message, User
    try:
        user_id = get_jwt_identity()
        msgs = Message.query.filter_by(recipient_id=user_id).order_by(Message.timestamp.desc()).all()

        # Enrich with sender names
        messages = []
        for msg in msgs:
            sender = User.query.get(msg.sender_id)
            m = msg.to_dict()
            m['sender_name'] = f"{sender.first_name} {sender.last_name}" if sender else "Unknown"
            messages.append(m)

        return jsonify(messages=messages), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

# Get user's sent messages
@messaging_bp.route('/sent', methods=['GET'])
@jwt_required()
def get_sent():
    from models import Message, User
    try:
        user_id = get_jwt_identity()
        msgs = Message.query.filter_by(sender_id=user_id).order_by(Message.timestamp.desc()).all()

        # Enrich with recipient names
        messages = []
        for msg in msgs:
            recipient = User.query.get(msg.recipient_id)
            m = msg.to_dict()
            m['recipient_name'] = f"{recipient.first_name} {recipient.last_name}" if recipient else "Unknown"
            messages.append(m)

        return jsonify(messages=messages), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

# View a specific message
@messaging_bp.route('/<int:msg_id>', methods=['GET'])
@jwt_required()
def view_message(msg_id):
    from models import Message
    try:
        user_id = get_jwt_identity()
        msg = Message.query.get(msg_id)
        if not msg:
            return jsonify(error='Message not found'), 404
        if user_id not in [msg.sender_id, msg.recipient_id]:
            return jsonify(error='Access denied'), 403

        # Mark as read if recipient is caller
        if msg.recipient_id == user_id and not msg.is_read:
            msg.is_read = True
            db.session.commit()

        return jsonify(message=msg.to_dict()), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

# Delete a message
@messaging_bp.route('/<int:msg_id>', methods=['DELETE'])
@jwt_required()
def delete_message(msg_id):
    from models import Message
    try:
        user_id = get_jwt_identity()
        msg = Message.query.get(msg_id)
        if not msg:
            return jsonify(error='Message not found'), 404
        if user_id not in [msg.sender_id, msg.recipient_id]:
            return jsonify(error='Access denied'), 403

        db.session.delete(msg)
        db.session.commit()
        return jsonify(message='Message deleted'), 200
    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

# Mark message as read manually
@messaging_bp.route('/<int:msg_id>/read', methods=['PUT'])
@jwt_required()
def mark_read(msg_id):
    from models import Message
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

# Get unread message count
@messaging_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def unread_count():
    from models import Message
    try:
        user_id = get_jwt_identity()
        count = Message.query.filter_by(recipient_id=user_id, is_read=False).count()
        return jsonify(unread_count=count), 200
    except Exception as e:
        return jsonify(error=str(e)), 500
