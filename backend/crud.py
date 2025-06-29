from sqlalchemy.orm import Session
from database import SessionLocal
import models
import schemas
from datetime import date, timedelta, datetime
import uuid
from typing import Optional

def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).offset(skip).limit(limit).all()

def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def get_batches(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Batch).offset(skip).limit(limit).all()

def create_batch_with_products(db: Session, batch_data: dict, products: list):
    # Convert date strings to date objects if needed
    def parse_date(val):
        if isinstance(val, date):
            return val
        if isinstance(val, str):
            try:
                return datetime.strptime(val, "%Y-%m-%d").date()
            except Exception:
                return None
        return None
    # Auto-generate batch_id if not provided
    batch_id = batch_data.get("batch_id")
    if not batch_id or batch_id.strip() == "":
        # Format: BATCH-YYYYMMDD-XXX (incremental)
        today_str = datetime.now().strftime("%Y%m%d")
        last_batch = db.query(models.Batch).filter(models.Batch.batch_id.like(f"BATCH-{today_str}-%")).order_by(models.Batch.batch_id.desc()).first()
        if last_batch and last_batch.batch_id.split('-')[-1].isdigit():
            next_num = int(last_batch.batch_id.split('-')[-1]) + 1
        else:
            next_num = 1
        batch_id = f"BATCH-{today_str}-{str(next_num).zfill(3)}"
        batch_data["batch_id"] = batch_id
    # Check for existing batch_id
    existing_batch = db.query(models.Batch).filter_by(batch_id=batch_id).first()
    if existing_batch:
        raise ValueError(f"Batch with batch_id {batch_id} already exists.")
    # Create the Batch (event)
    db_batch = models.Batch(
        batch_id=batch_id,
        manufacturing_date=parse_date(batch_data.get("manufacturing_date")),
        received_date=parse_date(batch_data.get("received_date")),
        expiry_date=parse_date(batch_data.get("expiry_date")),
        owner_type=batch_data.get("owner_type"),
        owner_id=batch_data.get("owner_id")
    )
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    # Create BatchProduct records
    batch_products = []
    for prod in products:
        bp = models.BatchProduct(
            batch_id=db_batch.batch_id,
            product_id=prod['product_id'],
            initial_quantity=prod['initial_quantity'],
            current_quantity=prod['current_quantity'],
            qc_status=prod.get('qc_status', 'Approved')
        )
        db.add(bp)
        batch_products.append(bp)
    db.commit()
    return db_batch, batch_products

def create_batch_units(db: Session, batch_id: str, product_id: int, quantity: float, location: Optional[str] = None):
    units = []
    for _ in range(int(quantity)):
        unit_uid = str(uuid.uuid4())
        unit = models.BatchUnit(
            unit_uid=unit_uid,
            batch_id=batch_id,
            product_id=product_id,
            status="Available",
            location=location
        )
        db.add(unit)
        units.append(unit)
    db.commit()
    return units

def get_inventory(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Inventory).offset(skip).limit(limit).all()

def create_inventory(db: Session, inventory: schemas.InventoryCreate):
    db_inventory = models.Inventory(**inventory.dict())
    db.add(db_inventory)
    db.commit()
    db.refresh(db_inventory)
    return db_inventory

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate, hashed_password: str):
    db_user = models.User(
        username=user.username,
        email=user.email,
        role=user.role,
        hashed_password=hashed_password,
        is_active=user.is_active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_alerts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Alert).offset(skip).limit(limit).all()

def create_alert(db: Session, alert: schemas.AlertCreate):
    db_alert = models.Alert(**alert.dict())
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert

def create_action_log(db: Session, action_log: schemas.ActionLogCreate):
    db_action_log = models.ActionLog(**action_log.dict())
    db.add(db_action_log)
    db.commit()
    db.refresh(db_action_log)
    return db_action_log

def dispatch_product(db: Session, retailer_id: int, product_id: int, batch_id: str, quantity: float):
    # 1. Check distributor inventory for the batch-product
    inv = db.query(models.Inventory).filter_by(product_id=product_id, batch_id=batch_id, location='warehouse').first()
    if not inv or inv.current_quantity < quantity:
        return False, 'Insufficient stock in distributor inventory.'
    # 2. Deduct from distributor inventory
    inv.current_quantity -= quantity
    # 3. Deduct from BatchProduct as well
    batch_product = db.query(models.BatchProduct).filter_by(batch_id=batch_id, product_id=product_id).first()
    if batch_product:
        batch_product.current_quantity -= quantity
    # 4. Add to retailer inventory (create or update)
    retailer_inv = db.query(models.Inventory).filter_by(product_id=product_id, batch_id=batch_id, location=f'retailer_{retailer_id}').first()
    if retailer_inv:
        retailer_inv.current_quantity += quantity
    else:
        retailer_inv = models.Inventory(
            product_id=product_id,
            batch_id=batch_id,
            location=f'retailer_{retailer_id}',
            current_quantity=quantity
        )
        db.add(retailer_inv)
    # 5. Add action log
    log = models.ActionLog(
        user_id=retailer_id,
        action="dispatch",
        details=f"Dispatched {quantity} of product {product_id} (batch {batch_id}) to retailer {retailer_id}",
        timestamp=date.today()
    )
    db.add(log)
    # 6. Add alert for retailer
    alert = models.Alert(
        user_id=retailer_id,
        message=f"You have received {quantity} units of product {product_id} (batch {batch_id}) in your inventory.",
        is_read=False,
        created_at=date.today()
    )
    db.add(alert)
    db.commit()
    return True, 'Product dispatched successfully.'

def get_batch_units(db: Session, batch_id: Optional[str] = None, product_id: Optional[int] = None, location: Optional[str] = None):
    query = db.query(models.BatchUnit)
    if batch_id:
        query = query.filter(models.BatchUnit.batch_id == batch_id)
    if product_id:
        query = query.filter(models.BatchUnit.product_id == product_id)
    if location:
        query = query.filter(models.BatchUnit.location == location)
    return query.all()

def create_dispatch_request(db: Session, retailer_id: int, product_id: int, batch_id: str, quantity: float):
    from datetime import date
    req = models.DispatchRequest(
        retailer_id=retailer_id,
        product_id=product_id,
        batch_id=batch_id,
        quantity=quantity,
        status="pending",
        created_at=date.today()
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req

def get_dispatch_requests(db: Session, status: Optional[str] = None):
    q = db.query(models.DispatchRequest)
    if status:
        q = q.filter(models.DispatchRequest.status == status)
    return q.order_by(models.DispatchRequest.created_at.desc()).all()

def approve_dispatch_request(db: Session, request_id: int, approve: bool):
    req = db.query(models.DispatchRequest).filter_by(id=request_id).first()
    if not req or req.status != "pending":
        return False, "Request not found or already processed."
    if approve:
        # Actually dispatch the product
        ok, msg = dispatch_product(db, req.retailer_id, req.product_id, req.batch_id, req.quantity)
        if not ok:
            return False, msg
        req.status = "approved"
    else:
        req.status = "rejected"
    db.commit()
    return True, "Request processed."
