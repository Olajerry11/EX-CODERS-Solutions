#!/bin/bash
echo "Starting X-CODERS Hackathon Backend..."
(cd backend && source venv/Scripts/activate && python manage.py runserver) &

echo "Starting X-CODERS Hackathon Frontend..."
(cd frontend && npm run dev) &

echo "Both servers are starting!"
echo "Backend: http://127.0.0.1:8000"
echo "Frontend: http://localhost:5173"

wait
