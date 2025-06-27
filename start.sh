#!/usr/bin/env bash

# Run Gunicorn to serve the Flask application
# The Flask app instance is named 'app' in 'app.py'
# 0.0.0.0:$PORT binds to all available network interfaces on the assigned port by Render
gunicorn --bind 0.0.0.0:$PORT app:app
