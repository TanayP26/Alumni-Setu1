# -*- coding: utf-8 -*-
"""
Created on Thu Sep 11 17:02:55 2025

@author: Admin
"""


from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, UserRole, db
from sqlalchemy import or_

events_bp = Blueprint('events', __name__)

@events_bp.route('/', methods=['GET'])
@jwt_required()
def get_events():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', '')
        search = request.args.get('search', '')
        upcoming_only = request.args.get('upcoming_only', 'false').lower() == 'true'

        query = Event.query

        if status and status in [s.value for s in EventStatus]:
            query = query.filter(Event.status == EventStatus(status))

        if search:
            query = query.filter(Event.title.ilike(f'%{search}%'))

        if upcoming_only:
            query = query.filter(Event.start_datetime > datetime.utcnow())

        query = query.order_by(Event.start_datetime.asc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        events = pagination.items

        return jsonify({
            'events': [event.to_dict() for event in events],
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

@events_bp.route('/<int:event_id>', methods=['GET'])
@jwt_required()
def get_event(event_id):
    try:
        event = Event.query.get(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404

        current_user_id = get_jwt_identity()
        is_registered = db.session.query(event_attendees).filter_by(
            user_id=current_user_id,
            event_id=event_id
        ).first() is not None

        data = event.to_dict()
        data['is_registered'] = is_registered

        return jsonify({'event': data}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@events_bp.route('/', methods=['POST'])
@jwt_required()
def create_event():
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if current_user.role not in [UserRole.ADMIN, UserRole.FACULTY]:
            return jsonify({'error': 'Permission denied'}), 403

        data = request.get_json()
        required_fields = ['title', 'description', 'start_datetime']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        start_dt = datetime.fromisoformat(data['start_datetime'])
        end_dt = datetime.fromisoformat(data['end_datetime']) if data.get('end_datetime') else None
        reg_deadline = datetime.fromisoformat(data['registration_deadline']) if data.get('registration_deadline') else None

        event = Event(
            title=data['title'],
            description=data['description'],
            start_datetime=start_dt,
            end_datetime=end_dt,
            location=data.get('location'),
            is_virtual=data.get('is_virtual', False),
            virtual_link=data.get('virtual_link'),
            max_attendees=data.get('max_attendees'),
            registration_deadline=reg_deadline,
            creator_id=current_user_id
        )
        db.session.add(event)
        db.session.commit()

        return jsonify({'message': 'Event created successfully', 'event': event.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@events_bp.route('/<int:event_id>', methods=['PUT'])
@jwt_required()
def update_event(event_id):
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        event = Event.query.get(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        if current_user.role != UserRole.ADMIN and event.creator_id != current_user_id:
            return jsonify({'error': 'Permission denied'}), 403

        data = request.get_json()
        for field in ['title','description','location','is_virtual','virtual_link','max_attendees','status']:
            if field in data:
                setattr(event, field, data[field] if field!='status' else EventStatus(data[field]))
        if 'start_datetime' in data:
            event.start_datetime = datetime.fromisoformat(data['start_datetime'])
        if 'end_datetime' in data:
            event.end_datetime = datetime.fromisoformat(data['end_datetime'])
        if 'registration_deadline' in data:
            event.registration_deadline = datetime.fromisoformat(data['registration_deadline'])

        db.session.commit()
        return jsonify({'message': 'Event updated successfully', 'event': event.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@events_bp.route('/<int:event_id>/register', methods=['POST'])
@jwt_required()
def register_for_event(event_id):
    try:
        current_user_id = get_jwt_identity()
        event = Event.query.get(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        if event.registration_deadline and datetime.utcnow() > event.registration_deadline:
            return jsonify({'error': 'Registration deadline has passed'}), 400
        if event.max_attendees and event.attendee_count >= event.max_attendees:
            return jsonify({'error': 'Event is full'}), 400

        if db.session.query(event_attendees).filter_by(user_id=current_user_id, event_id=event_id).first():
            return jsonify({'error': 'Already registered'}), 400

        user = User.query.get(current_user_id)
        event.attendees.append(user)
        db.session.commit()
        return jsonify({'message': 'Successfully registered'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@events_bp.route('/<int:event_id>/unregister', methods=['POST'])
@jwt_required()
def unregister_from_event(event_id):
    try:
        current_user_id = get_jwt_identity()
        event = Event.query.get(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404

        registration = db.session.query(event_attendees).filter_by(user_id=current_user_id, event_id=event_id).first()
        if not registration:
            return jsonify({'error': 'Not registered'}), 400

        user = User.query.get(current_user_id)
        event.attendees.remove(user)
        db.session.commit()
        return jsonify({'message': 'Successfully unregistered'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@events_bp.route('/<int:event_id>/attendees', methods=['GET'])
@jwt_required()
def get_event_attendees(event_id):
    try:
        current_user_id = get_jwt_identity()
        event = Event.query.get(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        user = User.query.get(current_user_id)
        if user.role != UserRole.ADMIN and event.creator_id != current_user_id:
            return jsonify({'error': 'Permission denied'}), 403

        return jsonify({'attendees': [u.to_dict() for u in event.attendees], 'count': len(event.attendees)}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@events_bp.route('/my-events', methods=['GET'])
@jwt_required()
def get_my_events():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        return jsonify({
            'created_events': [e.to_dict() for e in user.created_events],
            'registered_events': [e.to_dict() for e in user.registered_events]
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
