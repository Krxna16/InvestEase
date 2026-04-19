import os
import streamlit as st
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables
load_dotenv()

# Get Database URL and handle Render format mapping bridging postgres:// to postgresql://
raw_db_url = os.getenv("DATABASE_URL")

# Provide fallback for Streamlit Secrets
if not raw_db_url:
    try:
        raw_db_url = st.secrets["DATABASE_URL"]
    except Exception:
        pass

if not raw_db_url:
    raise ValueError("DATABASE_URL environment variable is not set. Please configure it or a .env file locally.")

if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

# Initialize SQLAlchemy Engine with connection scaling resilience
engine = create_engine(raw_db_url, pool_pre_ping=True, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- Relational Models ---

class User(Base):
    """Normalized Users table for central SaaS Auth isolation"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    
    holdings = relationship("Holding", back_populates="owner", cascade="all, delete-orphan")

class Holding(Base):
    """Assets tied natively downstream via ForeignKeys isolating portfolio loads"""
    __tablename__ = 'holdings'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    symbol = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    purchase_price = Column(Float, nullable=False)
    purchase_date = Column(String, nullable=False)
    
    owner = relationship("User", back_populates="holdings")

# --- Auto-Initialization ---
# This initializes schema safely if not present avoiding manual setup logic.
Base.metadata.create_all(bind=engine)

# --- CRUD Operations ---

def add_holding(user_id, symbol, quantity, price, date):
    db = SessionLocal()
    try:
        holding = Holding(
            user_id=user_id, 
            symbol=symbol.upper(), 
            quantity=quantity, 
            purchase_price=price, 
            purchase_date=str(date)
        )
        db.add(holding)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        print(f"DB Insert Object Error: {e}")
    finally:
        db.close()

def get_all_holdings(user_id):
    """Retrieves all stock holdings explicitly filtered locally guaranteeing data isolation."""
    db = SessionLocal()
    try:
        # Utilize pure SQLAlchemy queries bounded through dataframe evaluation directly
        query = db.query(Holding).filter(Holding.user_id == user_id)
        df = pd.read_sql(query.statement, db.bind)
        return df
    finally:
        db.close()

def update_holding(user_id, holding_id, symbol, quantity, price, date):
    db = SessionLocal()
    try:
        holding = db.query(Holding).filter(Holding.id == holding_id, Holding.user_id == user_id).first()
        if holding:
            holding.symbol = symbol.upper()
            holding.quantity = quantity
            holding.purchase_price = price
            holding.purchase_date = str(date)
            db.commit()
    except SQLAlchemyError:
        db.rollback()
    finally:
        db.close()

def delete_holding(user_id, holding_id):
    db = SessionLocal()
    try:
        holding = db.query(Holding).filter(Holding.id == holding_id, Holding.user_id == user_id).first()
        if holding:
            db.delete(holding)
            db.commit()
    except SQLAlchemyError:
        db.rollback()
    finally:
        db.close()

def import_csv(file_path, user_id):
    try:
        df = pd.read_csv(file_path)
        df.columns = ['Symbol', 'Quantity', 'Purchase_Price', 'Purchase_Date']
        
        db = SessionLocal()
        try:
            # Cleanly wipe existing isolated datasets ensuring seamless port
            db.query(Holding).filter(Holding.user_id == user_id).delete()
            db.commit()
            
            for _, row in df.iterrows():
                holding = Holding(
                    user_id=user_id,
                    symbol=str(row['Symbol']).upper(),
                    quantity=float(row['Quantity']),
                    purchase_price=float(row['Purchase_Price']),
                    purchase_date=str(row['Purchase_Date'])
                )
                db.add(holding)
            db.commit()
            return True, f"Successfully imported {len(df)} SaaS portfolio records."
        except SQLAlchemyError as e:
            db.rollback()
            return False, f"PostgreSQL Import failed internally: {e}"
        finally:
            db.close()
    except Exception as e:
        return False, f"CSV Validation Failure: {e}"

def export_csv(user_id, file_path='exported_portfolio.csv'):
    df = get_all_holdings(user_id)
    if not df.empty:
        df_export = df.drop(columns=['id', 'user_id'], errors='ignore')
        df_export.to_csv(file_path, index=False)
        
        if os.path.exists(file_path):
            return True, file_path
    
    return False, "Failed to export isolated dataset."