from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from services.wellness_recommender import WellnessRecommender
from datetime import datetime, timedelta

wellness_bp = Blueprint('wellness', __name__)
recommender = WellnessRecommender()
# In each route file, include this function:
def get_db():
    from app import mongo
    return mongo.db
# Use a function to get the database connection to avoid circular imports
def get_db():
    from app import mongo
    return mongo.db
@wellness_bp.route('/')
@login_required
def wellness():
    """Main wellness dashboard"""
    return render_template('wellness_dashboard.html')


@wellness_bp.route('/recommendations')
@login_required
def recommendations():
    """Wellness recommendations dashboard"""
    return render_template('wellness_recommendations.html')

@wellness_bp.route('/get-recommendations', methods=['POST'])
@login_required
def get_wellness_recommendations():
    """Get wellness recommendations using Google Generative AI"""
    try:
        data = request.get_json()
        emotion = data.get('emotion', 'neutral')
        context = data.get('context', '')
        
        # Get recommendations
        recommendations = recommender.get_recommendations(emotion, context)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@wellness_bp.route('/preferences', methods=['POST'])
@login_required
def save_preferences():
    """Save user wellness preferences"""
    try:
        data = request.get_json()
        db = get_db()
        
        # Update user preferences in database
        db.users.update_one(
            {'_id': current_user.id},
            {'$set': {
                'wellness_preferences': data,
                'preferences_updated': datetime.utcnow()
            }}
        )
        
        return jsonify({
            'success': True,
            'message': 'Preferences saved successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@wellness_bp.route('/progress')
@login_required
def wellness_progress():
    """Wellness progress tracking"""
    try:
        db = get_db()
        
        # Get wellness scores over time
        time_period = request.args.get('period', 'week')
        
        if time_period == 'week':
            start_date = datetime.utcnow() - timedelta(days=7)
        elif time_period == 'month':
            start_date = datetime.utcnow() - timedelta(days=30)
        else:
            start_date = datetime.utcnow() - timedelta(days=7)
        
        # Get emotion data for progress tracking
        from models.emotion import EmotionData
        progress_data = EmotionData.get_wellness_progress(db, current_user.id, start_date)
        
        return jsonify({
            'success': True,
            'progress': progress_data,
            'period': time_period
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@wellness_bp.route('/journal')
@login_required
def wellness_journal():
    """Wellness journal page"""
    return render_template('wellness_journal.html')