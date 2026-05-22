from flask_sqlalchemy import SQLAlchemy
import uuid
from datetime import datetime, timezone
import random

db = SQLAlchemy()

def generate_account_number():
    return "".join([str(random.randint(0, 9)) for _ in range(12)])

class VirtualAccount(db.Model):
    __tablename__ = 'virtual_accounts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_number = db.Column(db.String(12), unique=True, nullable=False, default=generate_account_number)
    ifsc_code = db.Column(db.String(20), default="DCEN0000123")
    balance = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_account_id = db.Column(db.String(36), db.ForeignKey('virtual_accounts.id'), nullable=False)
    receiver_account_id = db.Column(db.String(36), db.ForeignKey('virtual_accounts.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False) # 'SUCCESS', 'FAILED'
    idempotency_key = db.Column(db.String(100), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
