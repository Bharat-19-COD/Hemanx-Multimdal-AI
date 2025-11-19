from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from services.db_utils import get_db
from models.user import User

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_settings():
    """User profile settings page"""
    db = get_db()
    user = db.users.find_one({'_id': current_user.id})

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')

        # Validate inputs
        if not name or not email:
            flash("Please fill in all required fields", "error")
            return render_template('settings/profile.html', user=user)

        if not User.validate_email(email):
            flash("Please enter a valid email address", "error")
            return render_template('settings/profile.html', user=user)

        # Check if email is already taken by another user
        existing_user = db.users.find_one({
            'email': email.lower().strip(),
            '_id': {'$ne': current_user.id}
        })
        
        if existing_user:
            flash("Email address is already registered", "error")
            return render_template('settings/profile.html', user=user)

        # Update user info in MongoDB
        db.users.update_one(
            {'_id': current_user.id},
            {'$set': {'name': name.strip(), 'email': email.lower().strip()}}
        )
        
        flash("Profile updated successfully!", "success")
        return redirect(url_for('settings.profile_settings'))

    return render_template('settings/profile.html', user=user)

@settings_bp.route('/security', methods=['GET', 'POST'])
@login_required
def security_settings():
    """Security and password settings"""
    db = get_db()
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate current password
        user_data = db.users.find_one({'_id': current_user.id})
        if not User.authenticate(db, current_user.email, current_password):
            flash("Current password is incorrect", "error")
            return render_template('settings/security.html')
        
        # Validate new password
        is_valid, msg = User.validate_password(new_password)
        if not is_valid:
            flash(msg, "error")
            return render_template('settings/security.html')
        
        if new_password != confirm_password:
            flash("New passwords do not match", "error")
            return render_template('settings/security.html')
        
        # Update password
        import bcrypt
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        db.users.update_one(
            {'_id': current_user.id},
            {'$set': {'password': hashed_password}}
        )
        
        flash("Password updated successfully!", "success")
        return redirect(url_for('settings.security_settings'))
    
    return render_template('settings/security.html')

@settings_bp.route('/notifications', methods=['GET', 'POST'])
@login_required
def notification_settings():
    """Notification preferences"""
    db = get_db()
    
    if request.method == 'POST':
        email_notifications = request.form.get('email_notifications') == 'on'
        weekly_reports = request.form.get('weekly_reports') == 'on'
        activity_reminders = request.form.get('activity_reminders') == 'on'
        
        # Update notification preferences
        db.users.update_one(
            {'_id': current_user.id},
            {'$set': {
                'notifications': {
                    'email': email_notifications,
                    'weekly_reports': weekly_reports,
                    'activity_reminders': activity_reminders
                }
            }}
        )
        
        flash("Notification preferences updated!", "success")
        return redirect(url_for('settings.notification_settings'))
    
    # Get current notification settings
    user = db.users.find_one({'_id': current_user.id})
    notifications = user.get('notifications', {})
    
    return render_template('settings/notifications.html', notifications=notifications)

@settings_bp.route('/privacy')
@login_required
def privacy_settings():
    """Privacy settings page"""
    return render_template('settings/privacy.html')

@settings_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account"""
    try:
        db = get_db()
        
        # Delete user data
        db.users.delete_one({'_id': current_user.id})
        db.emotion_data.delete_many({'user_id': current_user.id})
        
        flash("Your account has been deleted successfully", "success")
        return redirect(url_for('auth.index'))
        
    except Exception as e:
        flash("Error deleting account. Please try again.", "error")
        return redirect(url_for('settings.profile_settings'))