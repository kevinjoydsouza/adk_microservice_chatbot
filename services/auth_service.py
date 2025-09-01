import jwt
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import os
from fastapi import HTTPException, status
import firebase_admin
from firebase_admin import auth

class AuthService:
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60 * 24  # 24 hours

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token or Firebase ID token"""
        try:
            # Try Firebase ID token first
            if self._is_firebase_token(token):
                return await self._verify_firebase_token(token)
            else:
                # Try JWT token
                return await self._verify_jwt_token(token)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def _is_firebase_token(self, token: str) -> bool:
        """Check if token looks like a Firebase ID token"""
        # Firebase tokens are typically longer and have 3 parts separated by dots
        parts = token.split('.')
        return len(parts) == 3 and len(token) > 500

    async def _verify_firebase_token(self, token: str) -> Dict[str, Any]:
        """Verify Firebase ID token"""
        try:
            decoded_token = auth.verify_id_token(token)
            return {
                "uid": decoded_token["uid"],
                "email": decoded_token.get("email"),
                "name": decoded_token.get("name"),
                "picture": decoded_token.get("picture"),
                "provider": "firebase"
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Firebase token"
            )

    async def _verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """Verify custom JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            return {
                "uid": user_id,
                "email": payload.get("email"),
                "name": payload.get("name"),
                "provider": "jwt"
            }
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create a new JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    async def create_user_session(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a user session with JWT token"""
        token_data = {
            "sub": user_data["uid"],
            "email": user_data.get("email"),
            "name": user_data.get("name")
        }
        access_token = self.create_access_token(token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,
            "user": user_data
        }