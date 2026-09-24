from repositories.user_repositories import UserRepository
from schemas.user_schema import(
    userBase,
    userResponse,
    userIn
)
from models.user_model import User
from security import Security





class userService:
    def __init__(self,repository:UserRepository):
        self.repository=repository
        self.security=Security()
                
    async def register_user(self,user_data:userBase)->User:
        # check if the user already exist
        existing=await self.repository.get_user_by_email(user_data.email)
        if existing:
            raise ValueError("User with this email address already exist!")
        
         # Hash password
        hashed_password = self.security.hashed_password(
            user_data.password
        )
         
        # created user
        user = User(
            name=user_data.name,
            email=user_data.email,
            password=hashed_password,
        )
        # save user
        created_user=await self.repository.create(user)
        
        # generate access token
        access_token= Security.create_access_Token(created_user.id)
        
        return {
        "user": created_user,
        "access_token": access_token,
        "token_type": "bearer"
    }

    
    
    
    async def login_user(self,user_data:userIn):
        # check if the user exist then run operation else break
        existing= await self.repository.get_user_by_email(user_data.email)
        if not existing:
            raise ValueError("Invalid email and password !")
        is_valid = self.security.verify_password(
            user_data.password,
            existing.password_hash
        )
        if not is_valid:
            raise ValueError("Invalid email or password ! ")
        
        access_token= Security.create_access_Token(str(existing.id))
        return {
        "user": existing,
        "access_token": access_token,
        "token_type": "bearer"
    }