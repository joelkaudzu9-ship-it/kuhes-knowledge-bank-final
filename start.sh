#!/bin/bash
echo "🚀 Starting server on port $PORT"
echo "Binding to 0.0.0.0:$PORT"
gunicorn kuhes_kb.wsgi --bind 0.0.0.0:$PORT --log-level debug