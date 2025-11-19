from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from models.emotion import EmotionData
from services.face_analysis import analyze_face_from_b64
from services.text_analysis import analyze_text
from services.voice_analysis import analyze_audio_file
from services.wellness_recommender import WellnessRecommender
from services.file_utils import save_upload, allowed_file
import base64
import os
from datetime import datetime

emotion_bp = Blueprint('emotion', __name__)
wellness_recommender = WellnessRecommender()

# In each route file, include this function:
def get_db():
    from app import mongo
    return mongo.db

@emotion_bp.route('/detection')
@login_required
def detection():
    """Enhanced emotion detection page"""
    return render_template('emotion_detection.html')

@emotion_bp.route('/analyze/comprehensive', methods=['POST'])
@login_required
def analyze_comprehensive():
    """Comprehensive emotion analysis from all sources with wellness recommendations"""
    try:
        emotion_data = {}
        
        # Analyze face if provided
        if request.json and 'image' in request.json:
            face_result = analyze_face_from_b64(request.json['image'])
            if 'error' not in face_result:
                emotion_data['face_emotion'] = face_result
        
        # Analyze text if provided
        if request.json and 'text' in request.json:
            text_result = analyze_text(request.json['text'])
            if 'error' not in text_result:
                emotion_data['text_emotion'] = text_result
        
        # Analyze voice if provided (separate file upload)
        if 'audio' in request.files and request.files['audio'].filename:
            audio_file = request.files['audio']
            if allowed_file(audio_file.filename):
                filepath = save_upload(audio_file)
                if filepath:
                    voice_result = analyze_audio_file(filepath)
                    if 'error' not in voice_result:
                        emotion_data['voice_emotion'] = voice_result
                    # Clean up
                    try:
                        os.remove(filepath)
                    except:
                        pass
        
        if not emotion_data:
            return jsonify({
                'success': False, 
                'error': 'No valid emotion data provided'
            })
        
        # Get wellness recommendations
        wellness_result = wellness_recommender.get_wellness_recommendations(emotion_data)
        
        # Save to database
        from app import get_db
        db = get_db()
        
        wellness_score = _calculate_comprehensive_wellness_score(emotion_data)
        
        emotion_record = {
            'emotion_data': emotion_data,
            'wellness_score': wellness_score,
            'wellness_recommendations': wellness_result.get('recommendations', ''),
            'overall_emotion': wellness_result['emotion_summary']['overall_emotion'],
            'analysis_type': 'comprehensive',
            'sources_used': wellness_result['emotion_summary']['sources_analyzed']
        }
        
        EmotionData.create_emotion_record(db, current_user.id, 'comprehensive', emotion_record)
        
        return jsonify({
            'success': True,
            'emotion_analysis': emotion_data,
            'wellness_recommendations': wellness_result,
            'wellness_score': wellness_score,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Keep existing individual analysis routes but enhance them...
@emotion_bp.route('/analyze/face', methods=['POST'])
@login_required
def analyze_face():
    """Enhanced face analysis with wellness recommendations"""
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'success': False, 'error': 'No image data provided'})
        
        result = analyze_face_from_b64(data['image'])
        
        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']})
        
        # Get wellness recommendations for face emotion
        wellness_result = wellness_recommender.get_wellness_recommendations({
            'face_emotion': result
        })
        
        # Save to database
        from app import get_db
        db = get_db()
        
        wellness_score = _calculate_wellness_score(result['dominant_emotion'])
        
        emotion_record = {
            'dominant_emotion': result['dominant_emotion'],
            'emotion_scores': result['emotions'],
            'confidence': result.get('confidence', 0),
            'wellness_score': wellness_score,
            'wellness_recommendations': wellness_result.get('recommendations', ''),
            'analysis_type': 'face'
        }
        
        EmotionData.create_emotion_record(db, current_user.id, 'face', emotion_record)
        
        return jsonify({
            'success': True,
            'dominant_emotion': result['dominant_emotion'],
            'emotions': result['emotions'],
            'confidence': result.get('confidence', 0),
            'wellness_score': wellness_score,
            'wellness_recommendations': wellness_result,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def _calculate_comprehensive_wellness_score(emotion_data: dict) -> int:
    """Calculate comprehensive wellness score from multiple emotion sources"""
    scores = []
    weights = []
    
    if 'face_emotion' in emotion_data:
        emotion = emotion_data['face_emotion'].get('dominant_emotion', 'neutral')
        confidence = emotion_data['face_emotion'].get('confidence', 50) / 100
        scores.append(_emotion_to_score(emotion))
        weights.append(confidence)
    
    if 'text_emotion' in emotion_data:
        emotion = emotion_data['text_emotion'].get('emotion', 'neutral')
        confidence = emotion_data['text_emotion'].get('score', 0.5)
        scores.append(_emotion_to_score(emotion))
        weights.append(confidence)
    
    if 'voice_emotion' in emotion_data:
        emotion = emotion_data['voice_emotion'].get('dominant_emotion', 'neutral')
        confidence = emotion_data['voice_emotion'].get('confidence', 0.5)
        scores.append(_emotion_to_score(emotion))
        weights.append(confidence)
    
    if not scores:
        return 5
    
    # Weighted average
    weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
    total_weight = sum(weights)
    
    return int(weighted_sum / total_weight)

def _emotion_to_score(emotion: str) -> int:
    """Convert emotion to wellness score (1-10)"""
    emotion = emotion.lower()
    
    positive_emotions = ['happy', 'surprise', 'calm', 'positive', 'excited', 'joy']
    negative_emotions = ['sad', 'angry', 'fear', 'disgust', 'negative', 'anxiety']
    
    if emotion in positive_emotions:
        return 8
    elif emotion in negative_emotions:
        return 3
    else:
        return 5

def _calculate_wellness_score(emotion):
    """Legacy function for individual analysis"""
    return _emotion_to_score(emotion)