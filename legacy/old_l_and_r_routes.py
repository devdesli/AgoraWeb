@limiter.limit("5/minute")
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = CSRFOnlyForm()

    if current_user.is_authenticated:
        app.logger.info(f"{current_user.username} already logged in")
        flash('You are already logged in.', "succes")
        return redirect(url_for('index'))

    if form.validate_on_submit():  # this only checks CSRF token
        username_or_email = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        app.logger.info(f"Login attempt - Username/Email")  # Debug log
        
        # Try to find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email)
        ).first()
        
        if user:
            #print(f"User found in database")  # Debug log
            if user.check_password(password):
                login_user(user)
                next_page = request.args.get('next')
                app.logger.info(f"user, logged in succesfully")
                return redirect(next_page or url_for('index'))
            else:
                app.logger.error(f"Password incorrect for user")  # Debug log
                flash("Invalid username/email or password", "error")
        else:
            app.logger.error(f"User not found ")  # Debug log
            flash("Invalid username/email or password", "error")

    
    return render_template('login.html', form=form)

@limiter.limit("5/minute")
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = CSRFOnlyForm()

    if current_user.is_authenticated:
        app.logger.info(f"user already logged in")
        flash('You are already logged in.', "succes")
        return redirect(url_for('index'))
    
    if request.method == 'POST' and form.validate():
        real_name = request.form.get('real_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if password != confirm_password:
            app.logger.error(f"Passwords do not match")
            flash('Passwords do not match', "error")
            return redirect(url_for('register', form=form))
        
        if User.query.filter_by(username=username).first():
            app.logger.error(f"username already exists")
            flash("Registration failed. Please try again.", "error")
            return redirect(url_for('register', form=form))
        
        if User.query.filter_by(email=email).first():
            app.logger.error(f"email already registered")
            flash("Registration failed. Please try again.", "error")
            return redirect(url_for('register', form=form))
        
        user = User(username=username, email=email, real_name=real_name)
        
        try: 
          if len(password) < 10:
            flash("Password must be at least 10 characters.", "error")
            return redirect(url_for('register', form=form))
          user.set_password(password)
          db.session.add(user)
          db.session.commit()
          app.logger.info(f"User succesfully registered")
          flash('Registration successful! Please log in.', "succes")
          return redirect(url_for('login'))
        except Exception as e:
         app.logger.error(f"error while registering user {e}")
    return render_template('register.html', form=form)

@limiter.limit("5/minute")
@app.route('/logout')
@login_required
def logout():
    activity_logger.info(f"{current_user} {current_user.username}, logged out")
    logout_user()
    return redirect(url_for('index'))

@limiter.limit("5/minute")
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = CSRFOnlyForm()
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST' and form.validate():
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            token = user.set_reset_token() # Generate and save the token
            
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message(
                subject='Password Reset Request',
                sender=app.config['MAIL_USERNAME'], # Use app.config for sender
                recipients=[user.email]
            )
            msg.body = f"""To reset your password, visit the following link:
{reset_url}

If you did not make this request then simply ignore this email and no changes will be made.
"""
            try:
                mail.send(msg)
                flash('A password reset link has been sent to your email.', 'info')
                app.logger.info(f"{email}, requested password reset link and email has been send")
            except Exception as e:
                flash(f'Failed to send email. Please try again later. Error: {str(e)}', 'error')
                db.session.rollback() # Rollback the token generation if email fails
                app.logger.error(f"Email sending error db rolled back: {e}") # Log the error for debugging
        else:
            # It's good practice not to reveal if an email exists for security reasons
            flash('If an account with that email exists, a password reset link has been sent.', 'info')
            app.logger.info(f"Reset link sent to {email}")
        
        return redirect(url_for('auth_login'))
    
    return render_template('forgot.html', form=form)

@limiter.limit("5/minute")
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    form = CSRFOnlyForm()
    if current_user.is_authenticated:
        app.logger.info(f"{current_user} {current_user.username}, already logged in")
        flash("already logged in")
        return redirect(url_for('index'))

    user = User.query.filter_by(reset_token=token).first()

    if not user or not user.verify_reset_token(token):
        app.logger.error(f"{token}, is invalid or expired for {user}")
        flash('That is an invalid or expired token.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST' and form.validate():
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not password or not confirm_password:
            flash('Please enter both password and confirm password.', 'error')
            return render_template('reset_password.html', token=token, form=form)

        if password != confirm_password:
            app.logger.info(f"Passwords not matching for {user}")
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token, form=form)

        user.set_password(password)
        user.reset_token = None # Clear the token after successful reset
        user.reset_token_expiration = None # Clear the expiration
        db.session.commit()
        app.logger.info(f"Password for {user} {user.username}, succesfully reset")
        flash('Your password has been reset successfully!', 'success')
        return redirect(url_for('auth_login'))

    return render_template('reset.html', token=token, form=form)

@limiter.limit("5/minute")
@app.route('/reset_user_password/<int:id>', methods=['POST']) # Change to POST for better security
@login_required
def reset_user_password(id):
    # Only master users can reset passwords
    if not current_user.is_master:
        activity_logger.info(f"{current_user} {current_user.username}, tried to reset user password without master role")
        abort(403)

    user = User.query.get_or_404(id)

    # Prevent master admin from resetting their own password this way (or other admins)
    if user.is_master and user.id == current_user.id:
        activity_logger.info(f"Master tried to reset own password through master panel permission denied")
        flash("You cannot reset your own master password this way.", "error")
        return redirect(url_for('admin'))

    # Generate a reset token for the user
    token = user.set_reset_token() # This method is already defined in your User model

    # Construct the reset URL
    reset_url = url_for('reset_password', token=token, _external=True)

    msg = Message(
        subject='Administrator initiated Password Reset Request',
        sender=app.config['MAIL_USERNAME'],
        recipients=[user.email]
    )
    msg.body = f"""Hello {user.username},

An administrator has initiated a password reset for your account on Agora.

To set a new password, please visit the following link:
{reset_url}

This link is valid for a limited time. If you did not request this, or if you believe this is in error, please ignore this email. Your current password will remain unchanged until you follow the link and set a new one.

Thank you,
Maakplaats Team
"""

    try:
        mail.send(msg)
        db.session.commit() # Commit the token to the database after successful email sending
        activity_logger.info(f"Admin reseted password of {user.username} email send to {user.email}")
        flash(f"Password reset link sent to '{user.username}' ({user.email}). User must use the link to set a new password.", "info")
    except Exception as e:
        db.session.rollback() # Rollback the token generation if email fails
        flash(f"Failed to send password reset email to '{user.username}'. Error: {str(e)}", 'error')
        error_logger(f"Admin or master {current_user.username} forced reset email error: {e}") # Log the error for debugging

    return redirect(url_for('admin'))