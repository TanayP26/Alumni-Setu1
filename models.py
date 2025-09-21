# -*- coding: utf-8 -*-
"""
Created on Thu Sep 11 17:00:11 2025
@author: Admin
"""
from extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum

# Enum definitions
class UserRole(Enum):
    ALUMNI = 'alumni'
    STUDENT = 'student'
    ADMIN = 'admin'
    FACULTY = 'faculty'

class EventStatus(Enum):
    UPCOMING = 'upcoming'
    ONGOING = 'ongoing'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

class JobStatus(Enum):
    ACTIVE = 'active'
    CLOSED = 'closed'
    DRAFT = 'draft'

# Association table for event attendees
event_attendees = db.Table(
    'event_attendees',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('event_id', db.Integer, db.ForeignKey('events.id'), primary_key=True),
    db.Column('registered_at', db.DateTime, default=datetime.utcnow)
)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.ALUMNI, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(15))
    profile_picture = db.Column(db.String(255))
    bio = db.Column(db.Text)
    graduation_year = db.Column(db.Integer)
    course = db.Column(db.String(100))
    department = db.Column(db.String(100))
    student_id = db.Column(db.String(50))
    current_company = db.Column(db.String(100))
    current_position = db.Column(db.String(100))
    industry = db.Column(db.String(100))
    experience_years = db.Column(db.Integer)
    skills = db.Column(db.Text)  # JSON string or comma-separated
    linkedin_url = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))

    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy='dynamic')
    created_events = db.relationship('Event', backref='creator', lazy='dynamic')
    registered_events = db.relationship('Event', secondary=event_attendees, backref='attendees')
    posted_jobs = db.relationship('Job', backref='poster', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role.value if self.role else None,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'phone': self.phone,
            'profile_picture': self.profile_picture,
            'bio': self.bio,
            'graduation_year': self.graduation_year,
            'course': self.course,
            'department': self.department,
            'student_id': self.student_id,
            'current_company': self.current_company,
            'current_position': self.current_position,
            'industry': self.industry,
            'experience_years': self.experience_years,
            'skills': self.skills,
            'linkedin_url': self.linkedin_url,
            'city': self.city,
            'state': self.state,
            'country': self.country,
        }
        if include_sensitive:
            data['email'] = self.email
        return data

# The new Message model for messaging feature
class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'subject': self.subject,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'is_read': self.is_read
        }

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime)
    location = db.Column(db.String(255))
    is_virtual = db.Column(db.Boolean, default=False)
    virtual_link = db.Column(db.String(255))
    max_attendees = db.Column(db.Integer)
    registration_deadline = db.Column(db.DateTime)
    status = db.Column(db.Enum(EventStatus), default=EventStatus.UPCOMING)
    banner_image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'start_datetime': self.start_datetime.isoformat() if self.start_datetime else None,
            'end_datetime': self.end_datetime.isoformat() if self.end_datetime else None,
            'location': self.location,
            'is_virtual': self.is_virtual,
            'virtual_link': self.virtual_link,
            'max_attendees': self.max_attendees,
            'registration_deadline': self.registration_deadline.isoformat() if self.registration_deadline else None,
            'status': self.status.value if self.status else None,
            'banner_image': self.banner_image,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'creator_id': self.creator_id,
        }

class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    job_type = db.Column(db.String(50))
    experience_level = db.Column(db.String(50))
    salary_range = db.Column(db.String(100))
    skills_required = db.Column(db.Text)
    application_url = db.Column(db.String(255))
    application_deadline = db.Column(db.DateTime)
    status = db.Column(db.Enum(JobStatus), default=JobStatus.ACTIVE)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'company': self.company,
            'location': self.location,
            'job_type': self.job_type,
            'experience_level': self.experience_level,
            'salary_range': self.salary_range,
            'skills_required': self.skills_required,
            'application_url': self.application_url,
            'application_deadline': self.application_deadline.isoformat() if self.application_deadline else None,
            'status': self.status.value if self.status else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'poster_id': self.poster_id,
        }

class Donation(db.Model):
    __tablename__ = 'donations'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    purpose = db.Column(db.String(200))
    message = db.Column(db.Text)
    is_anonymous = db.Column(db.Boolean, default=False)
    payment_status = db.Column(db.String(50), default='pending')
    transaction_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    donor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'currency': self.currency,
            'purpose': self.purpose,
            'message': self.message,
            'is_anonymous': self.is_anonymous,
            'payment_status': self.payment_status,
            'transaction_id': self.transaction_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'donor_id': self.donor_id,
        }

class NewsletterSubscriber(db.Model):
    __tablename__ = 'newsletter_subscribers'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'is_active': self.is_active,
            'subscribed_at': self.subscribed_at.isoformat() if self.subscribed_at else None
        }
