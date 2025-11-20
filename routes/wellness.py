from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from services.wellness_recommender import WellnessRecommender
from datetime import datetime, timedelta

wellness_bp = Blueprint('wellness', __name__)
recommender = WellnessRecommender()

# Use a function to get the database connection to avoid circular imports
def get_db():
    from app import mongo
    return mongo.db
@wellness_bp.route('/')
@login_required
def wellness():
    """Main wellness dashboard with comprehensive recommendations"""
    
    # Wellness activities data
    activities = {
        'meditation': [
            {
                'title': '5-Minute Morning Meditation',
                'description': 'Start your day with calm and focus',
                'duration': '5 min',
                'difficulty': 'Beginner',
                'youtube_id': 'inpok4MKVLM'
            },
            {
                'title': 'Stress Relief Meditation',
                'description': 'Release tension and find peace',
                'duration': '10 min',
                'difficulty': 'Beginner',
                'youtube_id': 'z6X5oEIg6Ak'
            },
            {
                'title': 'Body Scan Meditation',
                'description': 'Deep relaxation for mind and body',
                'duration': '15 min',
                'difficulty': 'Intermediate',
                'youtube_id': 'ihO02wUzgkc'
            },
            {
                'title': 'Mindfulness Meditation',
                'description': 'Cultivate present moment awareness',
                'duration': '20 min',
                'difficulty': 'Intermediate',
                'youtube_id': 'ZToicYcHIOU'
            }
        ],
        'yoga': [
            {
                'title': 'Morning Yoga Flow',
                'description': 'Energize your body and mind',
                'duration': '15 min',
                'difficulty': 'Beginner',
                'youtube_id': 'VaoV1PrYft4'
            },
            {
                'title': 'Yoga for Stress Relief',
                'description': 'Gentle poses to calm your nervous system',
                'duration': '20 min',
                'difficulty': 'Beginner',
                'youtube_id': 'COp7BR_Dvps'
            },
            {
                'title': 'Evening Yoga Stretch',
                'description': 'Unwind and prepare for restful sleep',
                'duration': '15 min',
                'difficulty': 'Beginner',
                'youtube_id': 'BiWDsfZ3zbo'
            },
            {
                'title': 'Power Yoga Workout',
                'description': 'Build strength and flexibility',
                'duration': '30 min',
                'difficulty': 'Advanced',
                'youtube_id': 'v7AYKMP6rOE'
            }
        ],
        'breathing': [
            {
                'title': '4-7-8 Breathing',
                'description': 'Calm anxiety and promote sleep',
                'duration': '3 min',
                'difficulty': 'Beginner',
                'youtube_id': 'gz4G31LGyog'
            },
            {
                'title': 'Box Breathing',
                'description': 'Reduce stress and improve focus',
                'duration': '5 min',
                'difficulty': 'Beginner',
                'youtube_id': 'tEmt1Znux58'
            },
            {
                'title': 'Alternate Nostril Breathing',
                'description': 'Balance energy and calm the mind',
                'duration': '7 min',
                'difficulty': 'Intermediate',
                'youtube_id': '8VwufJrUhic'
            },
            {
                'title': 'Wim Hof Breathing',
                'description': 'Boost energy and immune system',
                'duration': '10 min',
                'difficulty': 'Advanced',
                'youtube_id': 'tybOi4hjZFQ'
            }
        ]
    }
    
    # Badges system
    badges = [
        {'name': '7 Days', 'icon': '🔥', 'description': 'Complete activities for 7 consecutive days'},
        {'name': 'Zen Master', 'icon': '🧘', 'description': 'Complete 20 meditation sessions'},
        {'name': 'Yoga Pro', 'icon': '🤸', 'description': 'Complete 15 yoga sessions'},
        {'name': 'Breath Work', 'icon': '💨', 'description': 'Complete 10 breathing exercises'},
        {'name': 'Early Bird', 'icon': '🌅', 'description': 'Complete morning activities 5 times'},
        {'name': 'Night Owl', 'icon': '🌙', 'description': 'Complete evening activities 5 times'},
    ]
    
    return render_template('wellness.html', 
                         activities=activities,
                         badges=badges)


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

@wellness_bp.route('/api/personalized-recommendations')
@login_required
def personalized_recommendations():
    """Get personalized wellness recommendations based on user's emotion history"""
    try:
        db = get_db()
        from models.emotion import EmotionData
        
        # Get recent emotions
        recent_emotions = EmotionData.get_user_emotions(db, current_user.id, 5)
        
        # Analyze dominant emotions
        emotion_counts = {}
        for emotion_record in recent_emotions:
            emotion = emotion_record.get('data', {}).get('dominant_emotion', 'neutral')
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # Get most common emotion
        dominant_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else 'neutral'
        
        # Personalized recommendations based on emotion
        recommendations = get_emotion_based_activities(dominant_emotion)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'dominant_emotion': dominant_emotion
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@wellness_bp.route('/api/user-progress')
@login_required
def user_progress():
    """Get user wellness progress and stats"""
    try:
        db = get_db()
        
        # Get user data
        user_data = db.users.find_one({'_id': current_user.id})
        
        # Get activity completion stats
        activities_completed = db.wellness_activities.count_documents({
            'user_id': current_user.id,
            'completed': True
        })
        
        # Calculate weekly consistency
        week_ago = datetime.utcnow() - timedelta(days=7)
        weekly_activities = db.wellness_activities.count_documents({
            'user_id': current_user.id,
            'completed_at': {'$gte': week_ago}
        })
        
        consistency_percentage = min(100, (weekly_activities / 7) * 100)
        
        return jsonify({
            'success': True,
            'wellness_score': user_data.get('wellness_score', 5),
            'level': user_data.get('level', 1),
            'badges': user_data.get('badges', []),
            'activities_completed': activities_completed,
            'weekly_stats': {
                'activities': weekly_activities,
                'consistency_percentage': consistency_percentage
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@wellness_bp.route('/api/complete-activity', methods=['POST'])
@login_required
def complete_activity():
    """Mark an activity as completed"""
    try:
        data = request.get_json()
        db = get_db()
        
        # Record activity completion
        activity_record = {
            'user_id': current_user.id,
            'type': data.get('type'),
            'duration': data.get('duration', 10),
            'completed': True,
            'completed_at': datetime.utcnow()
        }
        
        db.wellness_activities.insert_one(activity_record)
        
        # Update user wellness score
        db.users.update_one(
            {'_id': current_user.id},
            {'$inc': {'wellness_score': 0.1}}
        )
        
        return jsonify({
            'success': True,
            'message': 'Activity completed successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def get_emotion_based_activities(emotion):
    """Get personalized activities based on emotion"""
    emotion = emotion.lower()
    
    activities_map = {
        'sad': [
            {
                'title': 'Uplifting Meditation',
                'description': 'Boost your mood with positive affirmations',
                'duration': '10 min',
                'difficulty': 'Beginner',
                'type': 'meditation',
                'youtube_id': 'z6X5oEIg6Ak'
            },
            {
                'title': 'Energizing Yoga Flow',
                'description': 'Move your body to lift your spirits',
                'duration': '15 min',
                'difficulty': 'Beginner',
                'type': 'yoga',
                'youtube_id': 'VaoV1PrYft4'
            }
        ],
        'angry': [
            {
                'title': 'Anger Release Meditation',
                'description': 'Let go of frustration and find calm',
                'duration': '10 min',
                'difficulty': 'Beginner',
                'type': 'meditation',
                'youtube_id': 'z6X5oEIg6Ak'
            },
            {
                'title': 'Calming Breathwork',
                'description': 'Cool down with controlled breathing',
                'duration': '5 min',
                'difficulty': 'Beginner',
                'type': 'breathing',
                'youtube_id': 'tEmt1Znux58'
            }
        ],
        'anxious': [
            {
                'title': 'Anxiety Relief Meditation',
                'description': 'Ground yourself and find peace',
                'duration': '15 min',
                'difficulty': 'Beginner',
                'type': 'meditation',
                'youtube_id': 'ihO02wUzgkc'
            },
            {
                'title': '4-7-8 Breathing',
                'description': 'Calm your nervous system instantly',
                'duration': '3 min',
                'difficulty': 'Beginner',
                'type': 'breathing',
                'youtube_id': 'gz4G31LGyog'
            }
        ],
        'happy': [
            {
                'title': 'Gratitude Meditation',
                'description': 'Amplify your positive emotions',
                'duration': '10 min',
                'difficulty': 'Beginner',
                'type': 'meditation',
                'youtube_id': 'inpok4MKVLM'
            },
            {
                'title': 'Joyful Yoga Flow',
                'description': 'Celebrate your happiness with movement',
                'duration': '20 min',
                'difficulty': 'Intermediate',
                'type': 'yoga',
                'youtube_id': 'v7AYKMP6rOE'
            }
        ]
    }
    
    return activities_map.get(emotion, activities_map['happy'])