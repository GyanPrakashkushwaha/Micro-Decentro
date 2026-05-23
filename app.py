from flask import Flask, request, jsonify
from flask_smorest import Api, Blueprint, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config
from models import db, VirtualAccount, Transaction
from schemas import (
    VirtualAccountCreateSchema, VirtualAccountResponseSchema, 
    VirtualAccountBalanceSchema, TransactionCreateSchema, 
    TransactionResponseSchema, PaginationQuerySchema
)

from auth import require_api_key

# Global Limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"])

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    limiter.init_app(app)

    api = Api(app)

    # Register blueprints
    from app import v1_bp
    api.register_blueprint(v1_bp)

    with app.app_context():
        db.create_all()

    return app

v1_bp = Blueprint(
    "v1", "v1", url_prefix="/v1", description="Micro-Decentro Core API"
)

@v1_bp.route("/virtual-accounts", methods=["POST"])
@v1_bp.arguments(VirtualAccountCreateSchema)
@v1_bp.response(201, VirtualAccountResponseSchema)
@v1_bp.doc(security=[{"ApiKeyAuth": []}])
@require_api_key
def create_virtual_account(kwargs):
    """Creates a new virtual account. (Accepts an optional initial deposit)."""
    initial_deposit = kwargs.get("initial_deposit", 0.00)
    
    new_account = VirtualAccount(balance=initial_deposit)
    db.session.add(new_account)
    db.session.commit()
    
    return new_account

@v1_bp.route("/virtual-accounts/<string:account_id>/balance", methods=["GET"])
@v1_bp.response(200, VirtualAccountBalanceSchema)
@v1_bp.doc(security=[{"ApiKeyAuth": []}])
@require_api_key
def get_balance(account_id):
    """Returns the current balance of the given account ID."""
    account = db.session.get(VirtualAccount, account_id)
    if not account:
        abort(404, message="Virtual Account not found")
    
    return account

@v1_bp.route("/transactions/payout", methods=["POST"])
@v1_bp.arguments(TransactionCreateSchema)
@v1_bp.response(201, TransactionResponseSchema)
@v1_bp.doc(security=[{"ApiKeyAuth": []}])
@require_api_key
def process_payout(kwargs):
    """Initiates a transfer between two accounts with Idempotency."""
    idempotency_key = request.headers.get("Idempotency-Key")
    
    if idempotency_key:
        # Check if transaction already exists for this idempotency key
        existing_txn = Transaction.query.filter_by(idempotency_key=idempotency_key).first()
        if existing_txn:
            return existing_txn, 200 # Return cached result, HTTP 200 instead of 201
            
    sender_id = kwargs["sender_id"]
    receiver_id = kwargs["receiver_id"]
    amount = kwargs["amount"]
    
    if sender_id == receiver_id:
        abort(400, message="Sender and Receiver cannot be the same")
        
    try:
        # Sort IDs to avoid deadlocks when locking rows
        account_ids = sorted([sender_id, receiver_id])
        
        # Row-level locking to prevent race conditions
        accounts = VirtualAccount.query.filter(VirtualAccount.id.in_(account_ids)).with_for_update().all()
        
        # Map them back
        account_map = {acc.id: acc for acc in accounts}
        sender = account_map.get(sender_id)
        receiver = account_map.get(receiver_id)
        
        if not sender:
            abort(404, message=f"Sender account not found")
        if not receiver:
            abort(404, message=f"Receiver account not found")
            
        if sender.balance < amount:
            # We log failed transactions as well
            failed_txn = Transaction(
                sender_account_id=sender_id,
                receiver_account_id=receiver_id,
                amount=amount,
                status='FAILED',
                idempotency_key=idempotency_key
            )
            db.session.add(failed_txn)
            db.session.commit()
            abort(400, message="Insufficient balance")
            
        # Deduct and Add
        sender.balance -= amount
        receiver.balance += amount
        
        success_txn = Transaction(
            sender_account_id=sender_id,
            receiver_account_id=receiver_id,
            amount=amount,
            status='SUCCESS',
            idempotency_key=idempotency_key
        )
        db.session.add(success_txn)
        db.session.commit()
        
        return success_txn
        
    except Exception as e:
        db.session.rollback()
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            raise e
        abort(500, message="An internal error occurred during transaction processing")

@v1_bp.route("/virtual-accounts/<string:account_id>/transactions", methods=["GET"])
@v1_bp.arguments(PaginationQuerySchema, location="query")
@v1_bp.response(200, TransactionResponseSchema(many=True))
@v1_bp.doc(security=[{"ApiKeyAuth": []}])
@require_api_key
def get_transactions(query_args, account_id):
    """Returns a paginated list of transaction history for a specific account."""
    account = db.session.get(VirtualAccount, account_id)
    if not account:
        abort(404, message="Virtual Account not found")
        
    page = query_args.get("page", 1)
    per_page = query_args.get("per_page", 10)
    
    # Transactions where account is either sender or receiver
    transactions = Transaction.query.filter(
        (Transaction.sender_account_id == account_id) | 
        (Transaction.receiver_account_id == account_id)
    ).order_by(Transaction.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return transactions.items

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
