# -*- coding: utf-8 -*-
"""
Created on Thu Sep 11 17:21:04 2025
@author: Admin
"""
# routes/__init__.py

from .auth import auth_bp
from .alumni import alumni_bp
from .events import events_bp
from .jobs import jobs_bp
from .messaging import messaging_bp  # corrected import for messaging routes
from .admin import admin_bp

__all__ = ['auth_bp', 'alumni_bp', 'events_bp', 'jobs_bp', 'messaging_bp', 'admin_bp']
