import os
from dotenv import load_dotenv
from flask_dance.contrib.google import make_google_blueprint, google
app.config['GOOGLE_OAUTH_CLIENT_ID'] = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
app.config['GOOGLE_OAUTH_CLIENT_SECRET'] = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')

load_dotenv()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

google_bp = make_google_blueprint(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    scope=["profile", "email"]
)

app.register_blueprint(google_bp, url_prefix="/login")

@limiter.limit("5/minute")
@app.route('/login/google')
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Failed to fetch user info from Google.", "error")
        return redirect(url_for("login"))
    user_info = resp.json()
    email = user_info.get("email")
    username = user_info.get("name") or (email.split("@")[0] if email else None)
    if not email or not username:
        flash("Google account missing email or username.", "error")
        return redirect(url_for("login"))
    user = User.query.filter_by(email=email).first()
    if not user:
        base_username = username
        count = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{count}"
            count += 1
        user = User(username=username, email=email, oauth_provider='google', is_oauth_user=True)
        try: 
            db.session.add(user)
            db.session.commit()
            flash(f"Account created for {username} via Google login.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating account: {str(e)}", "error")
            return redirect(url_for("login"))   
    else:
        flash(f"Logged in as {user.username} via Google login.", "success")
    login_user(user)
    return redirect(url_for("index"))

# Microsoft 365 / Azure AD Configuration for Quadraam Tenet
from flask_dance.contrib.azure import make_azure_blueprint, azure

AZURE_CLIENT_ID = os.getenv('AZURE_OAUTH_CLIENT_ID')
AZURE_CLIENT_SECRET = os.getenv('AZURE_OAUTH_CLIENT_SECRET')
AZURE_TENANT = os.getenv('AZURE_OAUTH_TENANT', 'common')

azure_bp = make_azure_blueprint(
    client_id=AZURE_CLIENT_ID,
    client_secret=AZURE_CLIENT_SECRET,
    tenant=AZURE_TENANT,
    scope=['User.Read'],
    redirect_to='microsoft_login'
)
app.register_blueprint(azure_bp, url_prefix="/login")

@limiter.limit("5/minute")
@app.route("/login/microsoft")
def microsoft_login():
    """
    Microsoft 365 / Azure AD login handler for Quadraam Tenet
    """
    if not azure.authorized:
        return redirect(url_for("azure.login"))
    
    try:
        resp = azure.get("/v1.0/me")
        if not resp.ok:
            flash("Failed to fetch user info from Microsoft 365.", "error")
            app.logger.error(f"Microsoft API error: {resp.status_code} {resp.text}")
            return redirect(url_for("login"))
        
        user_info = resp.json()
        
        # Extract user information from Microsoft Graph API response
        email = user_info.get("userPrincipalName") or user_info.get("mail")
        given_name = user_info.get("givenName", "")
        surname = user_info.get("surname", "")
        display_name = user_info.get("displayName", "").strip()
        microsoft_id = user_info.get("id")  # Unique user ID from Azure AD
        
        if not email or not microsoft_id:
            flash("Microsoft 365 account missing required information.", "error")
            app.logger.warning(f"Microsoft login missing email or ID: {user_info}")
            return redirect(url_for("login"))
        
        # Create username from display name or email
        if display_name:
            username = display_name.replace(" ", "_").lower()
        else:
            username = email.split("@")[0]
        
        # Check if user exists by Microsoft ID (most reliable)
        user = User.query.filter_by(oauth_provider='microsoft', oauth_id=microsoft_id).first()
        
        if not user:
            # Check if user exists by email (fallback)
            user = User.query.filter_by(email=email).first()
            
            if not user:
                # Create new user
                base_username = username
                count = 1
                while User.query.filter_by(username=username).first():
                    username = f"{base_username}{count}"
                    count += 1
                
                user = User(
                    username=username,
                    email=email,
                    oauth_provider='microsoft',
                    oauth_id=microsoft_id,
                    is_oauth_user=True
                )
                try:
                    db.session.add(user)
                    db.session.commit()
                    activity_logger.info(f"New user created via Microsoft 365: {username} ({email})")
                    flash(f"Account created for {username} via Microsoft 365 login.", "success")
                except Exception as e:
                    db.session.rollback()
                    app.logger.error(f"Error creating Microsoft 365 user: {str(e)}")
                    flash(f"Error creating account: {str(e)}", "error")
                    return redirect(url_for("login"))
            else:
                # Link existing user to Microsoft OAuth
                user.oauth_provider = 'microsoft'
                user.oauth_id = microsoft_id
                user.is_oauth_user = True
                try:
                    db.session.commit()
                    activity_logger.info(f"User linked to Microsoft 365: {user.username}")
                except Exception as e:
                    db.session.rollback()
                    app.logger.error(f"Error linking Microsoft 365 to user: {str(e)}")
        
        # Log in the user
        login_user(user)
        activity_logger.info(f"User logged in via Microsoft 365: {user.username} ({email})")
        flash(f"Logged in as {user.username} via Microsoft 365.", "success")
        
        # Redirect to next page or home
        next_page = request.args.get('next')
        return redirect(next_page or url_for("index"))
        
    except Exception as e:
        app.logger.error(f"Microsoft 365 login error: {str(e)}")
        flash("An error occurred during Microsoft 365 login. Please try again.", "error")
        return redirect(url_for("login"))
