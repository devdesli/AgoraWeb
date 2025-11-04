"""
moderation.py - Content Moderation System for Agora
Place this file in the same directory as your app.py
"""

import re
from datetime import datetime
from flask import flash, redirect, url_for, render_template, request
from flask_login import current_user, login_required
from models import db, Todo
import logging

# Get logger
moderation_logger = logging.getLogger('moderation_logger')
print('started moderation.py')

class ContentScanner:
    """
    Scans content for spam, profanity, and suspicious patterns
    """
    
    def __init__(self):
        # Spam keywords and patterns
        self.spam_patterns = [
            r'(?i)(buy now|click here|limited offer|act now)',
            r'(?i)(viagra|cialis|casino|lottery|prize)',
            r'(?i)(make money fast|get rich quick)',
            r'(?i)(weight loss|diet pills)',
            r'https?://[^\s]+.*https?://[^\s]+',  # Multiple URLs
        ]
        
        # Profanity list - add your own words here
        self.profanity_list = [
            # Add inappropriate words here
            'nigger',
            'hitler',
            'homo',
            'kanker',
            'Kanker',
            "Homo",
            'flikker',
            'Adolf Hitler',
        ]
        
        # Suspicious patterns that warrant manual review
        self.suspicious_patterns = [
            r'(.)\1{5,}',  # Repeated characters (aaaaaa)
            r'[A-Z\s]{20,}',  # Excessive caps
            r'[!?]{3,}',  # Multiple punctuation
            r'\d{10,}',  # Long number sequences (phone numbers)
        ]
        
        # Minimum content requirements
        self.min_title_length = 3
        self.min_description_length = 10
        self.max_url_count = 3
    
    def scan_content(self, title, main_question, description, end_product):
        """
        Scans all challenge content for violations
        
        Args:
            title (str): Challenge title
            main_question (str): Main question text
            description (str): Description text
            end_product (str): End product text
            
        Returns:
            dict: {
                'approved': bool,
                'flagged': bool,
                'reason': str or None,
                'status': str ('approved', 'pending', or 'rejected')
            }
        """
        result = {
            'approved': True,
            'flagged': False,
            'reason': None,
            'status': 'approved'
        }
        
        # Combine all text for comprehensive scanning
        full_content = f"{title} {main_question} {description} {end_product}"
        full_content_lower = full_content.lower()
        
        # 1. Check minimum length requirements
        if len(title.strip()) < self.min_title_length:
            result['approved'] = False
            result['flagged'] = True
            result['reason'] = f'Title too short (minimum {self.min_title_length} characters)'
            result['status'] = 'rejected'
            moderation_logger.warning(f"Content rejected: {result['reason']}")
            return result
        
        if len(description.strip()) < self.min_description_length:
            result['approved'] = False
            result['flagged'] = True
            result['reason'] = f'Description too short (minimum {self.min_description_length} characters)'
            result['status'] = 'rejected'
            moderation_logger.warning(f"Content rejected: {result['reason']}")
            return result
        
        # 2. Check for spam patterns
        for pattern in self.spam_patterns:
            if re.search(pattern, full_content_lower):
                result['approved'] = False
                result['flagged'] = True
                result['reason'] = 'Spam content detected'
                result['status'] = 'rejected'
                moderation_logger.warning(f"Spam detected in content: {pattern}")
                return result
        
        # 3. Check for profanity
        for word in self.profanity_list:
            if word.lower() in full_content_lower:
                result['approved'] = False
                result['flagged'] = True
                result['reason'] = 'Inappropriate language detected'
                result['status'] = 'rejected'
                moderation_logger.warning(f"Profanity detected: {word}")
                return result
        
        # 4. Check for excessive links
        url_count = len(re.findall(r'https?://[^\s]+', full_content))
        if url_count > self.max_url_count:
            result['approved'] = False
            result['flagged'] = True
            result['reason'] = f'Too many URLs detected ({url_count} found, max {self.max_url_count})'
            result['status'] = 'pending'
            moderation_logger.info(f"Content flagged: Too many URLs ({url_count})")
            return result
        
        # 5. Check for suspicious patterns (flag for review, don't reject)
        for pattern in self.suspicious_patterns:
            if re.search(pattern, full_content):
                result['approved'] = False
                result['flagged'] = True
                result['reason'] = 'Suspicious pattern detected - needs manual review'
                result['status'] = 'pending'
                moderation_logger.info(f"Suspicious pattern found: {pattern}")
                return result
        
        # All checks passed
        moderation_logger.info("Content passed all moderation checks")
        return result
    
    def add_spam_pattern(self, pattern):
        """Add a new spam pattern to the scanner"""
        self.spam_patterns.append(pattern)
        moderation_logger.info(f"Added spam pattern: {pattern}")
    
    def add_profanity_word(self, word):
        """Add a new profanity word to the scanner"""
        self.profanity_list.append(word.lower())
        moderation_logger.info(f"Added profanity word")
    
    def remove_profanity_word(self, word):
        """Remove a profanity word from the scanner"""
        if word.lower() in self.profanity_list:
            self.profanity_list.remove(word.lower())
            moderation_logger.info(f"Removed profanity word")


# Initialize the global content scanner
content_scanner = ContentScanner()


def scan_challenge_content(title, main_question, description, end_product, user):
    """
    Wrapper function to scan challenge content
    Returns scan result dict
    """
    moderation_logger.info(f"Scanning content from user: {user.username}")
    return content_scanner.scan_content(title, main_question, description, end_product)


def should_bypass_moderation(user):
    """
    Determines if a user should bypass content moderation
    Admins and masters bypass moderation
    """
    return user.is_admin or user.is_master


def get_moderation_status(user, scan_result):
    """
    Determines the final moderation status for a challenge
    
    Args:
        user: The user creating the challenge
        scan_result: Result dict from content_scanner.scan_content()
        
    Returns:
        tuple: (approved, is_approved, is_flagged, flag_reason, moderation_status)
    """
    # Admins and masters bypass moderation
    if should_bypass_moderation(user):
        return (True, True, False, None, 'approved')
    
    # Regular users follow scan result
    return (
        scan_result['approved'],
        scan_result['approved'],
        scan_result['flagged'],
        scan_result['reason'],
        scan_result['status']
    )


# ===== ROUTE HANDLERS =====

def setup_moderation_routes(app):
    """
    Register moderation routes with the Flask app
    Call this function in your app.py: setup_moderation_routes(app)
    """
    
    @app.route('/admin/moderation')
    @login_required
    def admin_moderation():
        """View all flagged challenges needing review"""
        if not (current_user.is_master or current_user.is_admin):
            flash('You are not authorized to view this page.', 'error')
            return redirect(url_for('index'))
        
        from forms import CSRFOnlyForm
        form = CSRFOnlyForm()
        
        # Get all pending/flagged challenges
        pending_challenges = Todo.query.filter_by(
            moderation_status='pending',
            is_flagged=True
        ).order_by(Todo.date_created.desc()).all()
        
        # Get rejected challenges (last 50)
        rejected_challenges = Todo.query.filter_by(
            moderation_status='rejected'
        ).order_by(Todo.date_created.desc()).limit(50).all()
        
        moderation_logger.info(
            f"Admin {current_user.username} accessed moderation panel. "
            f"Pending: {len(pending_challenges)}, Rejected: {len(rejected_challenges)}"
        )
        
        return render_template('admin_moderation.html', 
                             challenges=pending_challenges,
                             rejected_challenges=rejected_challenges,
                             form=form)
    
    @app.route('/admin/moderate/<int:id>/<action>', methods=['POST'])
    @login_required
    def moderate_challenge(id, action):
        """Approve or reject a flagged challenge"""
        if not (current_user.is_master or current_user.is_admin):
            flash('You are not authorized to perform this action.', 'error')
            return redirect(url_for('index'))
        
        challenge = Todo.query.get_or_404(id)
        
        if action == 'approve':
            challenge.approved = True
            challenge.is_approved = True
            challenge.moderation_status = 'approved'
            challenge.is_flagged = False
            challenge.flag_reason = None
            flash(f'Challenge "{challenge.title}" approved!', 'success')
            moderation_logger.info(
                f"Admin {current_user.username} approved challenge {challenge.id} "
                f"by {challenge.name}"
            )
            
        elif action == 'reject':
            challenge.approved = False
            challenge.is_approved = False
            challenge.moderation_status = 'rejected'
            # Keep flag and reason for record
            flash(f'Challenge "{challenge.title}" rejected.', 'warning')
            moderation_logger.info(
                f"Admin {current_user.username} rejected challenge {challenge.id} "
                f"by {challenge.name}"
            )
        else:
            flash('Invalid moderation action.', 'error')
            return redirect(url_for('admin_moderation'))
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            moderation_logger.error(f"Error moderating challenge {id}: {e}")
            flash('Error processing moderation action.', 'error')
        
        return redirect(url_for('admin_moderation'))
    
    @app.route('/admin/moderation/stats')
    @login_required
    def moderation_stats():
        """View moderation statistics"""
        if not (current_user.is_master or current_user.is_admin):
            flash('You are not authorized to view this page.', 'error')
            return redirect(url_for('index'))
        
        stats = {
            'pending': Todo.query.filter_by(moderation_status='pending').count(),
            'approved': Todo.query.filter_by(moderation_status='approved').count(),
            'rejected': Todo.query.filter_by(moderation_status='rejected').count(),
            'flagged': Todo.query.filter_by(is_flagged=True).count(),
        }
        
        return render_template('moderation_stats.html', stats=stats)


# ===== LOGGING SETUP =====

def setup_moderation_logging(app):
    """
    Setup moderation-specific logging
    Call this in your app.py after creating the app
    """
    import os
    from logging.handlers import RotatingFileHandler
    
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] in %(module)s: %(message)s'
    )
    
    # Moderation log
    moderation_handler = RotatingFileHandler(
        'logs/moderation.log', 
        maxBytes=10240, 
        backupCount=3
    )
    moderation_handler.setLevel(logging.INFO)
    moderation_handler.setFormatter(formatter)
    
    moderation_logger.setLevel(logging.INFO)
    moderation_logger.addHandler(moderation_handler)
    
    app.logger.info("Moderation logging initialized")