from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from services.db_utils import get_db
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@login_required
def dashboard():
    """Admin dashboard"""
    if current_user.role != 'admin':
        return redirect(url_for('dashboard.student'))
    
    db = get_db()
    
    # Get admin statistics
    total_users = db.users.count_documents({})
    total_students = db.users.count_documents({'role': 'student'})
    total_admins = db.users.count_documents({'role': 'admin'})
    total_sessions = db.emotion_data.count_documents({})
    
    # Recent emotions for activity feed
    recent_emotions = list(db.emotion_data.find().sort('timestamp', -1).limit(10))
    
    # Platform analytics
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_users = db.users.count_documents({'created_at': {'$gte': today}})
    today_sessions = db.emotion_data.count_documents({'timestamp': {'$gte': today}})
    
    return render_template('admin.html',
                         total_users=total_users,
                         total_students=total_students,
                         total_admins=total_admins,
                         total_sessions=total_sessions,
                         recent_emotions=recent_emotions,
                         today_users=today_users,
                         today_sessions=today_sessions,
                         now=datetime.utcnow())

@admin_bp.route('/admin/users')
@login_required
def user_management():
    """User management page"""
    if current_user.role != 'admin':
        return redirect(url_for('dashboard.student'))
    
    db = get_db()
    users = list(db.users.find().sort('created_at', -1))
    
    return render_template('admin/users.html', users=users)

@admin_bp.route('/admin/analytics')
@login_required
def analytics():
    """Advanced analytics page"""
    if current_user.role != 'admin':
        return redirect(url_for('dashboard.student'))
    
    db = get_db()
    
    # Emotion distribution
    emotion_pipeline = [
        {'$group': {
            '_id': '$data.dominant_emotion',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}}
    ]
    emotion_distribution = list(db.emotion_data.aggregate(emotion_pipeline))
    
    # User growth (last 30 days)
    month_ago = datetime.utcnow() - timedelta(days=30)
    user_growth = list(db.users.aggregate([
        {'$match': {'created_at': {'$gte': month_ago}}},
        {'$group': {
            '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$created_at'}},
            'count': {'$sum': 1}
        }},
        {'$sort': {'_id': 1}}
    ]))
    
    return render_template('admin/analytics.html',
                         emotion_distribution=emotion_distribution,
                         user_growth=user_growth)

@admin_bp.route('/admin/api/platform-stats')
@login_required
def platform_stats():
    """API for platform statistics"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    db = get_db()
    
    # Weekly activity
    week_ago = datetime.utcnow() - timedelta(days=7)
    weekly_activity = list(db.emotion_data.aggregate([
        {'$match': {'timestamp': {'$gte': week_ago}}},
        {'$group': {
            '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$timestamp'}},
            'sessions': {'$sum': 1},
            'avg_wellness': {'$avg': '$data.wellness_score'}
        }},
        {'$sort': {'_id': 1}}
    ]))
    
    # User engagement
    active_users = db.emotion_data.distinct('user_id', {
        'timestamp': {'$gte': week_ago}
    })
    
    return jsonify({
        'weekly_activity': weekly_activity,
        'active_users': len(active_users),
        'avg_session_wellness': 7.2,  # This would be calculated
        'popular_emotion': 'happy'    # This would be calculated
    })

@admin_bp.route('/admin/api/user/<user_id>')
@login_required
def get_user_data(user_id):
    """Get specific user data"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    db = get_db()
    
    user = db.users.find_one({'_id': user_id})
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get user's emotion history
    user_emotions = list(db.emotion_data.find(
        {'user_id': user_id}
    ).sort('timestamp', -1).limit(20))
    
    return jsonify({
        'user': {
            'name': user['name'],
            'email': user['email'],
            'role': user['role'],
            'created_at': user['created_at'].isoformat(),
            'wellness_score': user.get('wellness_score', 0),
            'level': user.get('level', 1)
        },
        'recent_emotions': [
            {
                'type': e['emotion_type'],
                'emotion': e['data'].get('dominant_emotion', e['data'].get('sentiment', 'unknown')),
                'wellness_score': e['data'].get('wellness_score', 0),
                'timestamp': e['timestamp'].isoformat()
            }
            for e in user_emotions
        ]
    })