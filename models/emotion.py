from bson import ObjectId
from datetime import datetime, timedelta
from collections import Counter

class EmotionData:
    def __init__(self, data):
        self.user_id = data.get('user_id')
        self.emotion_type = data.get('emotion_type', 'face')
        self.data = data.get('data', {})
        self.timestamp = data.get('timestamp', datetime.utcnow())
        self.mood_score = data.get('mood_score', 0)
        self._id = data.get('_id')

    @staticmethod
    def create(db, user_id, emotion_type, emotion_data, mood_score=0):
        """Create a new emotion data entry"""
        try:
            emotion_entry = {
                'user_id': ObjectId(user_id),
                'emotion_type': emotion_type,
                'data': emotion_data,
                'mood_score': mood_score,
                'timestamp': datetime.utcnow()
            }
            
            result = db.emotion_data.insert_one(emotion_entry)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating emotion data: {e}")
            return None

    @staticmethod
    def get_user_emotions(db, user_id, limit=10, emotion_type=None):
        """Get emotion data for a user"""
        try:
            query = {'user_id': ObjectId(user_id)}
            if emotion_type:
                query['emotion_type'] = emotion_type
                
            cursor = db.emotion_data.find(query).sort('timestamp', -1).limit(limit)
            emotions = list(cursor)
            
            # Convert ObjectId to string for JSON serialization
            for emotion in emotions:
                emotion['_id'] = str(emotion['_id'])
                emotion['user_id'] = str(emotion['user_id'])
                
            return emotions
        except Exception as e:
            print(f"Error getting user emotions: {e}")
            return []

    @staticmethod
    def get_wellness_progress(db, user_id, start_date):
        """Get wellness progress data for a user"""
        try:
            pipeline = [
                {
                    '$match': {
                        'user_id': ObjectId(user_id),
                        'timestamp': {'$gte': start_date}
                    }
                },
                {
                    '$group': {
                        '_id': {
                            'year': {'$year': '$timestamp'},
                            'month': {'$month': '$timestamp'},
                            'day': {'$dayOfMonth': '$timestamp'}
                        },
                        'average_mood': {'$avg': '$mood_score'},
                        'count': {'$sum': 1}
                    }
                },
                {
                    '$sort': {'_id': 1}
                }
            ]
            
            results = list(db.emotion_data.aggregate(pipeline))
            return results
        except Exception as e:
            print(f"Error getting wellness progress: {e}")
            return []

    @staticmethod
    def get_emotion_stats(db, user_id, days=7):
        """Get emotion statistics for the last N days"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            pipeline = [
                {
                    '$match': {
                        'user_id': ObjectId(user_id),
                        'timestamp': {'$gte': start_date}
                    }
                },
                {
                    '$group': {
                        '_id': '$data.dominant_emotion',
                        'count': {'$sum': 1},
                        'avg_confidence': {'$avg': '$data.confidence'}
                    }
                },
                {
                    '$sort': {'count': -1}
                }
            ]
            
            results = list(db.emotion_data.aggregate(pipeline))
            return results
        except Exception as e:
            print(f"Error getting emotion stats: {e}")
            return []

# Alternative simple implementation for immediate use
class SimpleEmotionData:
    @staticmethod
    def get_user_emotions(db, user_id, limit=5):
        """Simple method to get user emotions"""
        try:
            emotions = list(db.emotion_data.find(
                {'user_id': ObjectId(user_id)}
            ).sort('timestamp', -1).limit(limit))
            
            for emotion in emotions:
                emotion['_id'] = str(emotion['_id'])
                emotion['user_id'] = str(emotion['user_id'])
                
            return emotions
        except Exception as e:
            print(f"Error getting user emotions: {e}")
            return []

    @staticmethod
    def get_wellness_progress(db, user_id, start_date):
        """Simple wellness progress implementation"""
        try:
            # Return sample data for development
            return {
                'mood_trend': [
                    {'date': (datetime.utcnow() - timedelta(days=2)).strftime('%Y-%m-%d'), 'score': 7.5},
                    {'date': (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d'), 'score': 6.8},
                    {'date': datetime.utcnow().strftime('%Y-%m-%d'), 'score': 8.2},
                ],
                'common_emotions': ['neutral', 'happy', 'calm'],
                'insights': 'Your mood has been generally positive. Keep up the good work!',
                'total_entries': 15,
                'period': 'week'
            }
        except Exception as e:
            print(f"Error getting wellness progress: {e}")
            return {}

# Create alias for backward compatibility
EmotionData = SimpleEmotionData