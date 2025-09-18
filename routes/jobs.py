# -*- coding: utf-8 -*-
"""
Created on Thu Sep 11 17:03:16 2025

@author: Admin
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Job, User, UserRole, db
from datetime import datetime

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/', methods=['GET'])
@jwt_required()
def get_jobs():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', '')
        search = request.args.get('search', '')

        query = Job.query

        if status and status in [s.value for s in JobStatus]:
            query = query.filter(Job.status == JobStatus(status))

        if search:
            query = query.filter(Job.title.ilike(f'%{search}%'))

        query = query.order_by(Job.created_at.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        jobs = pagination.items

        return jsonify({
            'jobs': [job.to_dict() for job in jobs],
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

@jobs_bp.route('/<int:job_id>', methods=['GET'])
@jwt_required()
def get_job(job_id):
    try:
        job = Job.query.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        return jsonify({'job': job.to_dict()}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@jobs_bp.route('/', methods=['POST'])
@jwt_required()
def create_job():
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if current_user.role not in [UserRole.ADMIN, UserRole.ALUMNI]:
            return jsonify({'error': 'Permission denied'}), 403

        data = request.get_json()
        required_fields = ['title', 'description', 'company']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        job = Job(
            title=data['title'],
            description=data['description'],
            company=data['company'],
            location=data.get('location'),
            job_type=data.get('job_type'),
            experience_level=data.get('experience_level'),
            salary_range=data.get('salary_range'),
            skills_required=data.get('skills_required'),
            application_url=data.get('application_url'),
            application_deadline=datetime.fromisoformat(data['application_deadline']) if data.get('application_deadline') else None,
            poster_id=current_user_id
        )
        db.session.add(job)
        db.session.commit()

        return jsonify({'message': 'Job posted successfully', 'job': job.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@jobs_bp.route('/<int:job_id>', methods=['PUT'])
@jwt_required()
def update_job(job_id):
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        job = Job.query.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        if current_user.role != UserRole.ADMIN and job.poster_id != current_user_id:
            return jsonify({'error': 'Permission denied'}), 403

        data = request.get_json()
        for field in ['title','description','company','location','job_type','experience_level','salary_range','skills_required','application_url','status']:
            if field in data:
                setattr(job, field, data[field])
        if 'application_deadline' in data:
            job.application_deadline = datetime.fromisoformat(data['application_deadline'])

        db.session.commit()
        return jsonify({'message': 'Job updated successfully', 'job': job.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@jobs_bp.route('/<int:job_id>/close', methods=['POST'])
@jwt_required()
def close_job(job_id):
    try:
        current_user_id = get_jwt_identity()
        job = Job.query.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        current_user = User.query.get(current_user_id)
        if current_user.role != UserRole.ADMIN and job.poster_id != current_user_id:
            return jsonify({'error': 'Permission denied'}), 403

        job.status = JobStatus.CLOSED
        db.session.commit()
        return jsonify({'message': 'Job closed successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
