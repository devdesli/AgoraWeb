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