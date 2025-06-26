"""
Authentication service for API key management
"""

import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional
import structlog
from sqlalchemy.orm import Session

from ..models import User
from ..database import get_db_session
from ..config import get_settings

logger = structlog.get_logger()
settings = get_settings()

class AuthService:
    """Handle authentication and API key management"""
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    async def create_user(email: str, is_admin: bool = False) -> tuple[User, str]:
        """Create a new user with API key"""
        api_key = AuthService.generate_api_key()
        hashed_key = AuthService.hash_api_key(api_key)
        
        user = User(
            email=email,
            api_key_hash=hashed_key,
            is_admin=is_admin,
            rate_limit_per_minute=settings.RATE_LIMIT_PER_MINUTE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to database
        async with get_db_session() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)
        
        logger.info("User created", user_id=user.id, email=email)
        return user, api_key
    
    @staticmethod
    async def validate_api_key(api_key: str) -> Optional[User]:
        """Validate an API key and return the user"""
        try:
            hashed_key = AuthService.hash_api_key(api_key)
            
            async with get_db_session() as session:
                user = await session.query(User).filter(
                    User.api_key_hash == hashed_key,
                    User.is_active == True
                ).first()
                
                if user:
                    # Update last_accessed
                    user.last_accessed = datetime.utcnow()
                    await session.commit()
                    
                return user
                
        except Exception as e:
            logger.error("API key validation error", error=str(e))
            return None
    
    @staticmethod
    async def revoke_api_key(user_id: str) -> bool:
        """Revoke a user's API key"""
        try:
            async with get_db_session() as session:
                user = await session.query(User).filter(User.id == user_id).first()
                if user:
                    user.is_active = False
                    user.updated_at = datetime.utcnow()
                    await session.commit()
                    
                    logger.info("API key revoked", user_id=user_id)
                    return True
                    
            return False
            
        except Exception as e:
            logger.error("Error revoking API key", error=str(e), user_id=user_id)
            return False
    
    @staticmethod
    async def refresh_api_key(user_id: str) -> Optional[str]:
        """Generate a new API key for a user"""
        try:
            new_api_key = AuthService.generate_api_key()
            hashed_key = AuthService.hash_api_key(new_api_key)
            
            async with get_db_session() as session:
                user = await session.query(User).filter(User.id == user_id).first()
                if user:
                    user.api_key_hash = hashed_key
                    user.updated_at = datetime.utcnow()
                    await session.commit()
                    
                    logger.info("API key refreshed", user_id=user_id)
                    return new_api_key
                    
            return None
            
        except Exception as e:
            logger.error("Error refreshing API key", error=str(e), user_id=user_id)
            return None
    
    @staticmethod
    def create_jwt_token(user: User, expires_in: int = 3600) -> str:
        """Create a JWT token for API access"""
        payload = {
            "user_id": user.id,
            "email": user.email,
            "is_admin": user.is_admin,
            "exp": datetime.utcnow() + timedelta(seconds=expires_in),
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(payload, settings.API_SECRET_KEY, algorithm="HS256")
    
    @staticmethod
    def verify_jwt_token(token: str) -> Optional[dict]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, settings.API_SECRET_KEY, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid JWT token", error=str(e))
            return None
