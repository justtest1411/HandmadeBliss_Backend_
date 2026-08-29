from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Union
import hashlib
from datetime import datetime, timedelta
import jwt

from database import engine, SessionLocal, Base
from models import Product, User, ContactMessage, wishlist_association
import schemas

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Handmade Bliss API", version="1.0.0")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Secret key for JWT
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"

# Utility Functions
def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return hash_password(plain_password) == hashed_password

def create_access_token(user_id: int):
    """Create JWT token"""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

# ===================== PRODUCTS ENDPOINTS =====================

@app.get("/api/products", response_model=List[schemas.Product])
def get_all_products(
    skip: int = 0,
    limit: int = 100,
    category: str = None,
    db: Session = Depends(get_db)
):
    """Get all products with optional filtering by category"""
    query = db.query(Product)
    
    if category:
        query = query.filter(Product.category == category)
    
    products = query.offset(skip).limit(limit).all()
    return products

@app.get(
    "/api/products/{product_id_or_category}",
    response_model=Union[schemas.Product, List[schemas.Product]]
)
def get_product_or_category(
    product_id_or_category: str,
    db: Session = Depends(get_db)
):
    """Get a product by ID or all products in a category."""
    if product_id_or_category.isdigit():
        product = db.query(Product).filter(
            Product.id == int(product_id_or_category)
        ).first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        return product

    return db.query(Product).filter(
        Product.category == product_id_or_category
    ).all()

@app.post(
    "/api/products",
    response_model=schemas.Product,
    status_code=status.HTTP_201_CREATED
)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db)
):
    """Create a new product (Admin only)"""
    db_product = Product(
        name=product.name,
        description=product.description,
        price=product.price,
        category=product.category,
        image_url=product.image_url,
        stock=product.stock
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.put("/api/products/{product_id}", response_model=schemas.Product)
def update_product(
    product_id: int,
    product: schemas.ProductUpdate,
    db: Session = Depends(get_db)
):
    """Update a product (Admin only)"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    update_data = product.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product (Admin only)"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    db.delete(db_product)
    db.commit()
    return {"detail": "Product deleted successfully"}

# ===================== USER ENDPOINTS =====================

@app.post("/api/register", response_model=schemas.LoginResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = None
    if user.email:
        existing_user = db.query(User).filter(User.email == user.email).first()
    if user.phone and not existing_user:
        existing_user = db.query(User).filter(User.phone == user.phone).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    # Create new user
    db_user = User(
        name=user.name,
        email=user.email,
        phone=user.phone,
        password=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    access_token = create_access_token(db_user.id)
    
    return schemas.LoginResponse(
        id=db_user.id,
        name=db_user.name,
        email=db_user.email,
        phone=db_user.phone,
        access_token=access_token
    )

@app.post("/api/login", response_model=schemas.LoginResponse)
def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Login user with email/phone and password"""
    # Find user by email or phone
    db_user = None
    if "@" in credentials.email_or_phone:
        db_user = db.query(User).filter(User.email == credentials.email_or_phone).first()
    else:
        db_user = db.query(User).filter(User.phone == credentials.email_or_phone).first()
    
    if not db_user or not verify_password(credentials.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token = create_access_token(db_user.id)
    
    return schemas.LoginResponse(
        id=db_user.id,
        name=db_user.name,
        email=db_user.email,
        phone=db_user.phone,
        access_token=access_token
    )

@app.get("/api/users/{user_id}", response_model=schemas.User)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user details"""
    db_user = db.query(User).filter(User.id == user_id).first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return db_user

# ===================== WISHLIST ENDPOINTS =====================

@app.get("/api/wishlist/{user_id}")
def get_wishlist(user_id: int, db: Session = Depends(get_db)):
    """Get user's wishlist"""
    db_user = db.query(User).filter(User.id == user_id).first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    wishlist_items = db_user.wishlist_products
    return {
        "user_id": user_id,
        "items": [
            {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "category": product.category,
                "description": product.description,
                "image_url": product.image_url
            }
            for product in wishlist_items
        ]
    }

@app.post("/api/wishlist/{user_id}/add/{product_id}")
def add_to_wishlist(
    user_id: int,
    product_id: int,
    db: Session = Depends(get_db)
):
    """Add product to wishlist"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if db_product not in db_user.wishlist_products:
        db_user.wishlist_products.append(db_product)
        db.commit()
    
    return {"detail": "Product added to wishlist"}

@app.delete("/api/wishlist/{user_id}/remove/{product_id}")
def remove_from_wishlist(
    user_id: int,
    product_id: int,
    db: Session = Depends(get_db)
):
    """Remove product from wishlist"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if db_product in db_user.wishlist_products:
        db_user.wishlist_products.remove(db_product)
        db.commit()
    
    return {"detail": "Product removed from wishlist"}

# ===================== CONTACT ENDPOINTS =====================

@app.post("/api/contact")
def send_contact_message(
    message: schemas.ContactMessage,
    db: Session = Depends(get_db)
):
    """Send a contact message"""
    db_message = ContactMessage(
        name=message.name,
        email=message.email,
        phone=message.phone,
        subject=message.subject,
        message=message.message
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    return {
        "detail": "Message sent successfully",
        "message_id": db_message.id
    }

@app.get("/api/contact-messages")
def get_contact_messages(db: Session = Depends(get_db)):
    """Get all contact messages (Admin only)"""
    messages = db.query(ContactMessage).all()
    return messages

# ===================== HEALTH CHECK =====================

@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "message": "Welcome to Handmade Bliss API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/api/health")
def health_check():
    """API health check"""
    return {"status": "healthy"}
