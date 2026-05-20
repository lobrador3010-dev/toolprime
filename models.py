from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import create_engine
from pathlib import Path

DATABASE_URL = f"sqlite:///{Path(__file__).parent / 'toolprime.db'}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()

class Category(Base):
    __tablename__ = "categories"
    id        = Column(Integer, primary_key=True, index=True)
    name      = Column(String(255), nullable=False)
    slug      = Column(String(255), unique=True, index=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    parent   = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent")
    products = relationship("Product", back_populates="category")

class Brand(Base):
    __tablename__ = "brands"
    id   = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True)
    products = relationship("Product", back_populates="brand")

class Product(Base):
    __tablename__ = "products"
    id            = Column(Integer, primary_key=True, index=True)
    sku           = Column(String(120), unique=True, index=True, nullable=True)
    name          = Column(String(500), nullable=False)
    slug          = Column(String(600), unique=True, index=True)
    price         = Column(Float, nullable=False)
    old_price     = Column(Float, nullable=True)
    unit          = Column(String(32), default="шт")
    description   = Column(Text, nullable=True)
    features      = Column(Text, nullable=True)
    complectation = Column(Text, nullable=True)
    image_url     = Column(String(1024), nullable=True)
    image         = Column(String(1024), nullable=True)
    source_url    = Column(String(1024), nullable=True)
    in_stock      = Column(Boolean, default=True)
    category_id   = Column(Integer, ForeignKey("categories.id"), nullable=True)
    brand_id      = Column(Integer, ForeignKey("brands.id"), nullable=True)
    category = relationship("Category", back_populates="products")
    brand    = relationship("Brand", back_populates="products")
