from marshmallow import fields, Schema, validate

class VirtualAccountCreateSchema(Schema):
    initial_deposit = fields.Decimal(required=False, load_default=0.00, validate=validate.Range(min=0))

class VirtualAccountResponseSchema(Schema):
    id = fields.String(dump_only=True)
    account_number = fields.String(dump_only=True)
    ifsc_code = fields.String(dump_only=True)
    balance = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    
class VirtualAccountBalanceSchema(Schema):
    id = fields.String(dump_only=True)
    balance = fields.Decimal(dump_only=True)
    
class TransactionCreateSchema(Schema):
    sender_id = fields.String(required=True)
    receiver_id = fields.String(required=True)
    amount = fields.Decimal(required=True, validate=validate.Range(min=0.01))

class TransactionResponseSchema(Schema):
    id = fields.String(dump_only=True)
    sender_account_id = fields.String(dump_only=True)
    receiver_account_id = fields.String(dump_only=True)
    amount = fields.Decimal(dump_only=True)
    status = fields.String(dump_only=True)
    idempotency_key = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

class PaginationQuerySchema(Schema):
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Int(load_default=10, validate=validate.Range(min=1, max=100))
