# Supabase Authentication Setup

This document explains how to use Supabase authentication with LangConnect.

## Prerequisites

1. Supabase project with URL and anon key configured in `.env`:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key
   ```

2. Set `IS_TESTING=false` in your `.env` file to enable authentication

## API Endpoints

### Authentication Endpoints

- **POST /auth/signup** - Create a new user account
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```

- **POST /auth/signin** - Sign in with existing account
  ```json
  {
    "email": "user@example.com", 
    "password": "password123"
  }
  ```

- **POST /auth/signout** - Sign out (client-side cleanup)

- **POST /auth/refresh** - Refresh access token
  ```json
  {
    "refresh_token": "your-refresh-token"
  }
  ```

- **GET /auth/me** - Get current user info (requires authentication)

### Response Format

Successful authentication returns:
```json
{
  "access_token": "jwt-token",
  "refresh_token": "refresh-token",
  "user_id": "user-uuid",
  "email": "user@example.com"
}
```

## Using Authentication

### In API Requests

Include the access token in the Authorization header:
```
Authorization: Bearer your-access-token
```

### In Streamlit App

The Streamlit app (`Main.py`) now includes:
- Sign in/Sign up forms
- Automatic token management
- Session persistence
- Sign out functionality

### Testing Authentication

Run the test script:
```bash
python test_supabase_auth.py
```

This will test:
1. User signup
2. User signin
3. Authenticated API requests
4. Getting current user info

## Security Notes

1. The `SUPABASE_KEY` in `.env` should be the **anon** key, not the service role key
2. Tokens expire after a certain period - use the refresh endpoint to get new tokens
3. All API endpoints (except /health and /auth/*) require authentication when `IS_TESTING=false`

## Authentication Persistence

### Keeping Login State After Page Refresh

The Streamlit app supports two methods to persist authentication:

1. **Automatic File-Based Storage** (Default)
   - Authentication tokens are automatically saved to `~/.langconnect_auth_cache`
   - Tokens remain valid for 7 days
   - Automatically loads on app restart

2. **Environment Variables** (Optional)
   - Add these to your `.env` file:
   ```
   LANGCONNECT_TOKEN=your-access-token
   LANGCONNECT_EMAIL=your-email@example.com
   ```
   - Useful for development or shared environments

### Security Notes
- The auth cache file is stored in your home directory
- Tokens expire after 7 days for security
- Use environment variables only in secure environments

## Important Notes

### Email Confirmation

By default, Supabase requires email confirmation for new signups. When a user signs up:
1. They will receive a confirmation email
2. They must click the link in the email to confirm their account
3. Only then can they sign in

To disable email confirmation (for testing only):
1. Go to your Supabase project dashboard
2. Navigate to Authentication → Settings
3. Under "Email Auth" disable "Confirm email"

### Testing with Docker

When running with Docker Compose, ensure `IS_TESTING=false` in docker-compose.yml to enable authentication.

## Troubleshooting

- **"Authentication endpoints are disabled in testing mode"** - Set `IS_TESTING=false` in `.env` or docker-compose.yml
- **"Email not confirmed"** - Check your email for confirmation link, or disable email confirmation in Supabase dashboard
- **"Invalid token or user not found"** - Check that your token is valid and not expired
- **Connection errors** - Verify SUPABASE_URL and SUPABASE_KEY are correct