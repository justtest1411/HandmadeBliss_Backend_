from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Product Schemas
class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    category: str
    image_url: Optional[str] = None
    stock: int = 0

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    stock: Optional[int] = None

class Product(ProductBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# User Schemas
class UserBase(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    name: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Wishlist Schemas
class WishlistItemBase(BaseModel):
    product_id: int

class WishlistItem(WishlistItemBase):
    id: int
    user_id: int
    added_at: datetime
    product: Product
    
    class Config:
        from_attributes = True

class Wishlist(BaseModel):
    id: int
    user_id: int
    items: List[WishlistItem]
    
    class Config:
        from_attributes = True

# Contact Schemas
class ContactMessage(BaseModel):
    name: str
    email: str
    phone: str
    message: str
    subject: Optional[str] = None

# Login Schemas
class LoginRequest(BaseModel):
    email_or_phone: str
    password: str

class LoginResponse(BaseModel):
    id: int
    name: str
    email: Optional[str]
    phone: Optional[str]
    access_token: str
    token_type: str = "bearer"
