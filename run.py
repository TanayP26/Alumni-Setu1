# -*- coding: utf-8 -*-
"""
Created on Thu Sep 11 17:06:54 2025

@author: Admin
"""


#!/usr/bin/env python3
from app import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
