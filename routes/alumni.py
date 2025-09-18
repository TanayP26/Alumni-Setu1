# -*- coding: utf-8 -*-
"""
Created on Thu Sep 11 17:02:25 2025

@author: Admin
"""


from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, UserRole, db
from sqlalchemy import or_, and_

alumni_bp = Blueprint('alumni', __name__)

@alumni_bp.route('/directory', methods=['GET'])
@jwt_required()
def get_alumni_directory():
    try:
        current_user_id = get_jwt_identity()

        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        graduation_year = request.args.get('graduation_year', type=int)
        department = request.args.get('department', '')
        industry = request.args.get('industry', '')
        city = request.args.get('city', '')
        company = request.args.get('company', '')

        # Build query
        query = User.query.filter(User.is_active == True, User.is_verified == True)

        # Apply filters
        if search:
            search_filter = or_(
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%'),
                User.current_company.ilike(f'%{search}%'),
                User.current_position.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)

        if graduation_year:
            query = query.filter(User.graduation_year == graduation_year)

        if department:
            query = query.filter(User.department.ilike(f'%{department}%'))

        if industry:
            query = query.filter(User.industry.ilike(f'%{industry}%'))

        if city:
            query = query.filter(User.city.ilike(f'%{city}%'))

        if company:
            query = query.filter(User.current_company.ilike(f'%{company}%'))

        # Order by latest first
        query = query.order_by(User.created_at.desc())

        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        alumni = pagination.items

        return jsonify({
            'alumni': [user.to_dict() for user in alumni],
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

@alumni_bp.route('/<int:alumni_id>', methods=['GET'])
@jwt_required()
def get_alumni_profile(alumni_id):
    try:
        user = User.query.get(alumni_id)

        if not user or not user.is_active:
            return jsonify({'error': 'Alumni not found'}), 404

        return jsonify({
            'alumni': user.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alumni_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_alumni_stats():
    try:
        # Total alumni count
        total_alumni = User.query.filter_by(role=UserRole.ALUMNI, is_active=True).count()

        # Alumni by graduation year
        graduation_years = db.session.query(
            User.graduation_year,
            db.func.count(User.id).label('count')
        ).filter_by(role=UserRole.ALUMNI, is_active=True).group_by(User.graduation_year).all()

        # Alumni by department
        departments = db.session.query(
            User.department,
            db.func.count(User.id).label('count')
        ).filter_by(role=UserRole.ALUMNI, is_active=True).group_by(User.department).all()

        # Alumni by industry
        industries = db.session.query(
            User.industry,
            db.func.count(User.id).label('count')
        ).filter(
            User.role == UserRole.ALUMNI,
            User.is_active == True,
            User.industry.isnot(None)
        ).group_by(User.industry).all()

        # Alumni by location
        locations = db.session.query(
            User.city,
            db.func.count(User.id).label('count')
        ).filter(
            User.role == UserRole.ALUMNI,
            User.is_active == True,
            User.city.isnot(None)
        ).group_by(User.city).all()

        return jsonify({
            'total_alumni': total_alumni,
            'by_graduation_year': [{'year': year, 'count': count} for year, count in graduation_years],
            'by_department': [{'department': dept, 'count': count} for dept, count in departments],
            'by_industry': [{'industry': ind, 'count': count} for ind, count in industries],
            'by_location': [{'city': city, 'count': count} for city, count in locations]
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alumni_bp.route('/search/suggestions', methods=['GET'])
@jwt_required()
def get_search_suggestions():
    try:
        search_type = request.args.get('type', 'all')  # all, departments, companies, industries, cities
        query = request.args.get('q', '')

        suggestions = []

        if search_type in ['all', 'departments']:
            departments = db.session.query(User.department).filter(
                User.department.ilike(f'%{query}%'),
                User.department.isnot(None)
            ).distinct().limit(10).all()
            suggestions.extend([{'type': 'department', 'value': dept[0]} for dept in departments])

        if search_type in ['all', 'companies']:
            companies = db.session.query(User.current_company).filter(
                User.current_company.ilike(f'%{query}%'),
                User.current_company.isnot(None)
            ).distinct().limit(10).all()
            suggestions.extend([{'type': 'company', 'value': comp[0]} for comp in companies])

        if search_type in ['all', 'industries']:
            industries = db.session.query(User.industry).filter(
                User.industry.ilike(f'%{query}%'),
                User.industry.isnot(None)
            ).distinct().limit(10).all()
            suggestions.extend([{'type': 'industry', 'value': ind[0]} for ind in industries])

        if search_type in ['all', 'cities']:
            cities = db.session.query(User.city).filter(
                User.city.ilike(f'%{query}%'),
                User.city.isnot(None)
            ).distinct().limit(10).all()
            suggestions.extend([{'type': 'city', 'value': city[0]} for city in cities])

        return jsonify({
            'suggestions': suggestions[:20]  # Limit to 20 suggestions
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alumni_bp.route('/mentorship/matches', methods=['GET'])
@jwt_required()
def get_mentorship_matches():
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({'error': 'User not found'}), 404

        # Find potential mentors (alumni with more experience in similar industry/field)
        matches = []

        if current_user.role == UserRole.STUDENT:
            # Student looking for mentors
            mentor_query = User.query.filter(
                User.role == UserRole.ALUMNI,
                User.is_active == True,
                User.is_verified == True,
                User.id != current_user_id
            )

            # Match by department if available
            if current_user.department:
                mentor_query = mentor_query.filter(User.department == current_user.department)

            mentors = mentor_query.limit(10).all()
            matches = [mentor.to_dict() for mentor in mentors]

        elif current_user.role == UserRole.ALUMNI:
            # Alumni looking for mentees
            mentee_query = User.query.filter(
                User.role == UserRole.STUDENT,
                User.is_active == True,
                User.is_verified == True,
                User.id != current_user_id
            )

            # Match by department if available
            if current_user.department:
                mentee_query = mentee_query.filter(User.department == current_user.department)

            mentees = mentee_query.limit(10).all()
            matches = [mentee.to_dict() for mentee in mentees]

        return jsonify({
            'matches': matches
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
