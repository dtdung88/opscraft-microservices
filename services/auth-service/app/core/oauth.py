from fastapi import HTTPException, status
from typing import Optional
import httpx
import jwt
from datetime import datetime, timedelta, timezone

from config import settings

class OAuthProvider:
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.config = self._get_provider_config(provider_name)
    
    def _get_provider_config(self, provider: str) -> dict:
        configs = {
            "google": {
                "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "scopes": ["openid", "email", "profile"]
            },
            "github": {
                "auth_url": "https://github.com/login/oauth/authorize",
                "token_url": "https://github.com/login/oauth/access_token",
                "userinfo_url": "https://api.github.com/user",
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "scopes": ["user:email"]
            }
        }
        
        return configs.get(provider, {})
    
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Generate OAuth authorization URL"""
        params = {
            "client_id": self.config["client_id"],
            "redirect_uri": redirect_uri,
            "scope": " ".join(self.config["scopes"]),
            "response_type": "code",
            "state": state
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.config['auth_url']}?{query_string}"
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config["token_url"],
                data={
                    "client_id": self.config["client_id"],
                    "client_secret": self.config["client_secret"],
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                },
                headers={"Accept": "application/json"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange code for token"
                )
            
            return response.json()
    
    async def get_user_info(self, access_token: str) -> dict:
        """Get user information from OAuth provider"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.config["userinfo_url"],
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user info"
                )
            
            return response.json()

# OAuth routes
from fastapi import APIRouter, Query, Request
from sqlalchemy.orm import Session

oauth_router = APIRouter()

@oauth_router.get("/{provider}/login")
async def oauth_login(
    provider: str,
    request: Request,
    redirect_uri: str = Query(...)
):
    """Initiate OAuth login flow"""
    oauth = OAuthProvider(provider)
    
    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Store state in Redis with expiration
    redis_client = request.app.state.redis
    await redis_client.setex(f"oauth_state:{state}", 600, redirect_uri)
    
    auth_url = oauth.get_authorization_url(redirect_uri, state)
    
    return {"authorization_url": auth_url}

@oauth_router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Handle OAuth callback"""
    oauth = OAuthProvider(provider)
    
    # Verify state
    redis_client = request.app.state.redis
    redirect_uri = await redis_client.get(f"oauth_state:{state}")
    
    if not redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state"
        )
    
    # Exchange code for token
    token_data = await oauth.exchange_code_for_token(code, redirect_uri.decode())
    
    # Get user info
    user_info = await oauth.get_user_info(token_data["access_token"])
    
    # Find or create user
    from app.services.auth_service import AuthService
    auth_service = AuthService(db)
    
    email = user_info.get("email")
    username = user_info.get("login") or user_info.get("email").split("@")[0]
    
    user = auth_service.get_user_by_email(email)
    
    if not user:
        # Create new user from OAuth
        user = auth_service.create_oauth_user(
            username=username,
            email=email,
            full_name=user_info.get("name"),
            provider=provider,
            provider_id=str(user_info.get("id"))
        )
    
    # Create JWT tokens
    tokens = auth_service.create_tokens(user)
    
    return tokens