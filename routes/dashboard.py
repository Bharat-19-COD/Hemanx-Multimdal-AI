from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models.emotion import EmotionData
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)
# In each route file, include this function:
def get_db():
    from app import mongo
    return mongo.db

@dashboard_bp.route('/dashboard')
@login_required
def student():
    """Student dashboard with analytics"""
    from app import get_db
    db = get_db()
    
    # Get recent emotions
    recent_emotions = EmotionData.get_user_emotions(db, current_user.id, 10)
    
    # Calculate wellness metrics
    total_sessions = len(recent_emotions)
    positive_sessions = len([e for e in recent_emotions if e.get('data', {}).get('wellness_score', 0) > 5])
    wellness_percentage = (positive_sessions / total_sessions * 100) if total_sessions > 0 else 0
    
    # Weekly progress (simplified - remove the problematic function call)
    weekly_emotions = []  # Empty for now
    
    return render_template('dashboard.html',
                         recent_emotions=recent_emotions,
                         wellness_percentage=wellness_percentage,
                         total_sessions=total_sessions,
                         weekly_emotions=weekly_emotions,
                         now=datetime.utcnow())

@dashboard_bp.route('/api/emotion-chart-data')
@login_required
def emotion_chart_data():
    """API for emotion chart data"""
    from app import get_db
    db = get_db()
    
    emotions = EmotionData.get_user_emotions(db, current_user.id, 7)
    
    dates = []
    wellness_scores = []
    emotions_list = []
    
    for emotion in emotions:
        date_str = emotion['timestamp'].strftime('%m/%d')
        dates.append(date_str)
        wellness_scores.append(emotion.get('data', {}).get('wellness_score', 0))
        emotions_list.append(emotion.get('data', {}).get('dominant_emotion', 'neutral'))
    
    return jsonify({
        'dates': dates[::-1],  # Reverse to show oldest first
        'wellness_scores': wellness_scores[::-1],
        'emotions': emotions_list[::-1]
    })

@dashboard_bp.route('/api/wellness-stats')
@login_required
def wellness_stats():
    """API for wellness statistics"""
    from app import get_db
    db = get_db()
    
    # Calculate various stats
    total_sessions = db.emotion_data.count_documents({'user_id': current_user.id})
    
    # Today's sessions
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_sessions = db.emotion_data.count_documents({
        'user_id': current_user.id,
        'timestamp': {'$gte': today_start}
    })
    
    # Weekly average wellness score
    week_ago = datetime.utcnow() - timedelta(days=7)
    weekly_emotions = list(db.emotion_data.find({
        'user_id': current_user.id,
        'timestamp': {'$gte': week_ago}
    }))
    
    avg_wellness = 0
    if weekly_emotions:
        total_wellness = sum(emotion.get('data', {}).get('wellness_score', 0) for emotion in weekly_emotions)
        avg_wellness = total_wellness / len(weekly_emotions)
    
    return jsonify({
        'total_sessions': total_sessions,
        'today_sessions': today_sessions,
        'avg_wellness': round(avg_wellness, 1),
        'wellness_level': _get_wellness_level(avg_wellness)
    })

def _get_wellness_level(score):
    """Convert wellness score to level"""
    if score >= 7:
        return "Excellent"
    elif score >= 5:
        return "Good"
    elif score >= 3:
        return "Fair"
    else:
        return "Needs Improvement"