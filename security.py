from pwdlib import PasswordHash
from datetime import timezone,timedelta,datetime
import jwt
from typing import Any
from core.config import settings

password_hash = PasswordHash.recommended()


class Security:

    def verify_password(
        self,
        user_credential_password: str,
        user_saved_password: str
    ) -> bool:
        return password_hash.verify(
            user_credential_password,
            user_saved_password
        )

    def hashed_password(self, user_password: str) -> str:
        return password_hash.hash(user_password)
    
    @staticmethod
    def create_access_Token(self,user_id:str):
        now= datetime.now(timezone.utc)
        expire=now+timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRES_TIME)
        
        payload: dict[str,Any]={
            "sub": str(user_id),
            "iat": now,
            "exp": expire,
            "role": "user",
            "type": "access"
        }
        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            settings.JWT_ALGORITHM
        )
    