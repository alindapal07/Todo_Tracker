from sqlalchemy.ext.asyncio import AsyncSession
from models.user_model import User
from sqlalchemy import select


class UserRepository:
    def __init__(self,db:AsyncSession):
        self.db=db
        
    async def create(self,user:User )-> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def get_user_by_id(self,user_id:str)-> User|None:
        statement =select(User).where(User.id==user_id)
        result= await self.db.execute(statement)
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self,user_email:str)->User|None:
        statement=select(User).where(User.email==user_email)
        result= await self.db.execute(statement)
        return result.scalar_one_or_none()
    
    async def get_all_user(self)->list[User]:
        statement=select(User)
        # return list(self.db.execute(statement).all())
        result= await self.db.execute(statement)
        return list(result.scalars().all())
    
    async def update(self,user: User)->User:
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def delete(self,user:User)->None:
        await self.db.delete(user)
        await self.db.commit()