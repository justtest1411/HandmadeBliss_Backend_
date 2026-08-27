from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# Association table for Wishlist (many-to-many relationship)
wishlist_association = Table(
    'wishlist_association',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True)
)

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category = Column(String(100), index=True)
    image_url = Column(String(500))
    stock = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    wishlists = relationship(
        "User",
        secondary=wishlist_association,
        back_populates="wishlist_products"
    )


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    phone = Column(String(20), unique=True, index=True, nullable=True)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    wishlist_products = relationship(
        "Product",
        secondary=wishlist_association,
        back_populates="wishlists"
    )


class ContactMessage(Base):
    __tablename__ = "contact_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20))
    subject = Column(String(255))
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
