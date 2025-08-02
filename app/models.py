from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, UTC

Base = declarative_base()

class Sale(Base):
    __tablename__ = 'sales'
    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    quantity_sold = Column(Integer, nullable=False)
    total_sale = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    profit = Column(Float, nullable=False)
    currency = Column(String, default="TRY")
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))

class Expense(Base):
    __tablename__ = 'expenses'
    id = Column(Integer, primary_key=True, index=True)
    expense_type = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(Text)
    currency = Column(String, default="TRY")
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))


