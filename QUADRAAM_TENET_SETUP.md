# Quadraam Tenet (Microsoft 365) Login Setup Guide

## Overview

This document explains how to set up Microsoft 365 / Azure AD login (Quadraam Tenet) for your Challenge Forum application.

## Prerequisites

- Microsoft 365 / Azure AD tenant access
- Admin access to Azure Portal
- Your application's domain/URL

## Step 1: Register Application in Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations** → **New registration**
3. Fill in the registration form:

   - **Name**: Challenge Forum
   - **Supported account types**: Choose based on your organization (typically "Accounts in this organizational directory only")
   - **Redirect URI**: Select "Web" and enter: `http://yourdomain.com/login/azure/authorized`
     - For local development: `http://localhost:5000/login/azure/authorized`

4. Click **Register**

## Step 2: Get Your Credentials

1. After registration, you'll see the **Overview** page
2. Copy these values:
   - **Application (client) ID** → Save as `AZURE_OAUTH_CLIENT_ID`
   - **Directory (tenant) ID** → Save as `AZURE_OAUTH_TENANT`

## Step 3: Create Client Secret

1. Go to **Certificates & secrets** in the left menu
2. Click **New client secret**
3. Set expiration (recommend 24 months)
4. Copy the **Value** (not the ID) → Save as `AZURE_OAUTH_CLIENT_SECRET`
   - ⚠️ **Important**: Copy this immediately as you won't see it again!

## Step 4: Configure API Permissions

1. Go to **API permissions**
2. Click **Add a permission**
3. Select **Microsoft Graph**
4. Select **Delegated permissions**
5. Search for and add:
   - `User.Read` (to read user profile)
6. Click **Grant admin consent**

## Step 5: Update .env File

Add these environment variables to your `.env` file:

```
AZURE_OAUTH_CLIENT_ID=your_client_id_here
AZURE_OAUTH_CLIENT_SECRET=your_client_secret_here
AZURE_OAUTH_TENANT=your_tenant_id_here
```

Example:

```
AZURE_OAUTH_CLIENT_ID=12345678-1234-1234-1234-123456789abc
AZURE_OAUTH_CLIENT_SECRET=abc~1234567890-_abcdefGHIJKLMNOP
AZURE_OAUTH_TENANT=abcdef12-3456-7890-abcd-ef1234567890
```

## Step 6: Run Database Migration

Execute the migration to add OAuth fields to the User model:

```bash
flask db upgrade
```

If you haven't initialized migrations yet:

```bash
flask db init
flask db migrate -m "Add OAuth provider fields"
flask db upgrade
```

## Step 7: Test the Integration

1. Start your Flask app: `python app.py`
2. Go to http://localhost:5000/login
3. Click the **Microsoft 365** button
4. You should be redirected to Microsoft login
5. After login, a new user account will be created automatically

## How It Works

### User Login Flow:

1. User clicks "Microsoft 365" button
2. User is redirected to Microsoft login page
3. User authenticates with their M365 credentials
4. Microsoft redirects back with user authorization
5. Flask fetches user info from Microsoft Graph API
6. User is either:
   - **Logged in** if they already have an account
   - **Created + Logged in** if it's their first time

### User Information Retrieved:

- Email (userPrincipalName)
- Display Name
- First/Last Name
- Unique Microsoft User ID

### Data Stored:

- `oauth_provider`: 'microsoft'
- `oauth_id`: Unique ID from Azure AD
- `is_oauth_user`: True for OAuth users

## Troubleshooting

### "Failed to fetch user info from Microsoft 365"

- Check that API permissions are granted
- Verify `User.Read` permission is enabled
- Check that client ID and secret are correct

### Redirect URI mismatch error

- Ensure the redirect URI in Azure matches exactly: `http://yourdomain.com/login/azure/authorized`
- For development, use `http://localhost:5000/login/azure/authorized`

### User keeps getting created instead of logged in

- Check that the user's email is being captured correctly
- Verify Azure AD is returning the `userPrincipalName` field
- Check logs for the returned user_info

### Tenant issues

- If using `"common"` tenant, users can log in from any Azure AD
- If using specific tenant ID, only users from that organization can log in
- To restrict to specific org, use the tenant ID instead of "common"

## Security Notes

1. **Never commit** your `.env` file with real credentials
2. **Use environment variables** for all sensitive data
3. **HTTPS required** for production (Azure won't allow HTTP redirect URIs)
4. **Token validation**: Flask-Dance handles token validation automatically
5. **CSRF Protection**: Already enabled in the app

## Environment-Specific Redirect URIs

**Local Development:**

- `http://localhost:5000/login/azure/authorized`

**Staging:**

- `https://staging.yourdomain.com/login/azure/authorized`

**Production:**

- `https://yourdomain.com/login/azure/authorized`

Register all these in Azure Portal under **Redirect URIs** to enable testing across environments.

## User Account Linking

If a user has an existing account with the same email:

- Their account will be linked to Microsoft 365
- They can then log in with either method (password or Microsoft 365)
- The `oauth_provider` field will be updated

## Additional Features

You can extend this implementation to:

- Auto-assign user roles based on Azure AD groups
- Sync user information from Microsoft 365 on each login
- Require MFA for sensitive operations
- Access other Microsoft 365 services (OneDrive, Calendar, etc.)

## Support

For issues with Azure AD configuration, visit:

- [Microsoft Identity Platform docs](https://learn.microsoft.com/en-us/azure/active-directory/develop/)
- [Flask-Dance documentation](https://flask-dance.readthedocs.io/)
