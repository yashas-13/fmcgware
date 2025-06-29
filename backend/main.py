from fastapi import FastAPI, Depends, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import models
import schemas
import crud
import database
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import func, and_
from datetime import date
from fastapi.staticfiles import StaticFiles
import os
from database import Base, engine
from sqlalchemy.exc import IntegrityError
from fastapi import status

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

SECRET_KEY = "your-secret-key"  # Change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(db, username: str, password: str):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# --- Product Endpoints ---
@app.get("/api/products", response_model=list[schemas.Product])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_products(db, skip=skip, limit=limit)

# --- Role-based permission for product creation ---
@app.post("/api/products", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    if current_user.role != "Distributor":
        raise HTTPException(status_code=403, detail="Only Distributors can add products.")
    return crud.create_product(db, product)

# --- Supplier Endpoints ---
@app.get("/api/suppliers", response_model=list[schemas.Supplier])
def read_suppliers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_suppliers(db, skip=skip, limit=limit)

@app.post("/api/suppliers", response_model=schemas.Supplier)
def create_supplier(supplier: schemas.SupplierCreate, db: Session = Depends(get_db)):
    return crud.create_supplier(db, supplier)

# --- Batch Endpoints ---
@app.get("/api/batches", response_model=list[schemas.Batch])
def read_batches(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    if current_user.role == "Retailer":
        return db.query(models.Batch).filter(models.Batch.owner_type == "Retailer", models.Batch.owner_id == current_user.user_id).offset(skip).limit(limit).all()
    return crud.get_batches(db, skip=skip, limit=limit)

@app.post("/api/batches", response_model=schemas.Batch)
def create_batch(batch: schemas.BatchCreate, db: Session = Depends(get_db)):
    raise HTTPException(status_code=400, detail="Use /api/batches/multi for multi-product batches.")

@app.post("/api/batches/multi", response_model=schemas.Batch)
def create_multi_product_batch(
    batch_data: dict = Body(...),
    products: list = Body(...),
    db: Session = Depends(get_db)
):
    db_batch, batch_products = crud.create_batch_with_products(db, batch_data, products)
    return db_batch

# --- Inventory Endpoints ---
@app.get("/api/inventory", response_model=list[schemas.Inventory])
def read_inventory(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    if current_user.role == "Retailer":
        return db.query(models.Inventory).filter(models.Inventory.location == f"retailer_{current_user.user_id}").offset(skip).limit(limit).all()
    return crud.get_inventory(db, skip=skip, limit=limit)

@app.post("/api/inventory", response_model=schemas.Inventory)
def create_inventory(inventory: schemas.InventoryCreate, db: Session = Depends(get_db)):
    return crud.create_inventory(db, inventory)

# --- User Endpoints ---
@app.get("/api/users", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_users(db, skip=skip, limit=limit)

@app.post("/api/users", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(user.password)
    try:
        created_user = crud.create_user(db, user, hashed_password)
    except IntegrityError as e:
        db.rollback()
        if 'users.email' in str(e.orig):
            raise HTTPException(status_code=400, detail="Email already registered.")
        if 'users.username' in str(e.orig):
            raise HTTPException(status_code=400, detail="Username already registered.")
        raise HTTPException(status_code=400, detail="Integrity error: " + str(e.orig))
    from datetime import date
    action_log = schemas.ActionLogCreate(
        user_id=created_user.user_id,
        action="register",
        details=f"User {created_user.username} registered.",
        timestamp=date.today()
    )
    crud.create_action_log(db, action_log)
    return created_user

# --- Alert Endpoints ---
@app.get("/api/alerts", response_model=list[schemas.Alert])
def read_alerts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return db.query(models.Alert).filter(models.Alert.user_id == current_user.user_id).offset(skip).limit(limit).all()

@app.post("/api/alerts", response_model=schemas.Alert)
def create_alert(alert: schemas.AlertCreate, db: Session = Depends(get_db)):
    return crud.create_alert(db, alert)

# JWT Authentication
# --- Role-based logic: include role in JWT and /api/me ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/api/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/me", response_model=schemas.User)
def read_users_me(current_user: schemas.User = Depends(get_current_user)):
    return current_user

# --- Analytics: Inventory Valuation Endpoint ---
@app.get("/api/analytics/inventory-valuation")
def inventory_valuation(db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    # Sum of (current_quantity * price_inr) for all inventory
    q = db.query(models.Inventory, models.Product).join(models.Product, models.Inventory.product_id == models.Product.product_id)
    total_value = 0
    breakdown = []
    for inv, prod in q:
        value = (inv.current_quantity or 0) * (prod.price_inr or 0)
        total_value += value
        breakdown.append({
            "product_id": prod.product_id,
            "product_name": prod.product_name,
            "category": prod.category,
            "current_quantity": inv.current_quantity,
            "price_inr": prod.price_inr,
            "value": value
        })
    return {"total_value": total_value, "breakdown": breakdown}

# --- Analytics: Near-Expiry Batches ---
@app.get("/api/analytics/near-expiry-batches")
def near_expiry_batches(days: int = 15, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    today = date.today()
    threshold = today + timedelta(days=days)
    # Join Batch and BatchProduct, filter by expiry and current_quantity
    results = db.query(models.Batch, models.BatchProduct).join(models.BatchProduct, models.Batch.batch_id == models.BatchProduct.batch_id)
    results = results.filter(
        models.Batch.expiry_date <= threshold,
        models.BatchProduct.current_quantity > 0
    ).all()
    return [
        {
            "batch_id": b.batch_id,
            "product_id": bp.product_id,
            "expiry_date": b.expiry_date,
            "current_quantity": bp.current_quantity,
            "qc_status": bp.qc_status
        }
        for b, bp in results
    ]

# --- Analytics: Stock by Category ---
@app.get("/api/analytics/stock-by-category")
def stock_by_category(db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    q = db.query(models.Product.category, func.sum(models.Inventory.current_quantity))\
        .join(models.Inventory, models.Product.product_id == models.Inventory.product_id)\
        .group_by(models.Product.category).all()
    return [{"category": cat, "total_quantity": qty} for cat, qty in q]

# --- FEFO Batch Picking Logic ---
@app.get("/api/pick-batch/fefo")
def pick_batch_fefo(product_id: int, quantity: float, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    # Find batches for product, sorted by earliest expiry, with available quantity
    batches = db.query(models.Batch).filter(
        and_(models.Batch.product_id == product_id, models.Batch.current_quantity > 0)
    ).order_by(models.Batch.expiry_date.asc()).all()
    picked = []
    remaining = quantity
    for batch in batches:
        if remaining <= 0:
            break
        pick_qty = min(batch.current_quantity, remaining)
        picked.append({
            "batch_id": batch.batch_id,
            "expiry_date": batch.expiry_date,
            "pick_quantity": pick_qty
        })
        remaining -= pick_qty
    if remaining > 0:
        return {"error": "Not enough stock", "picked": picked}
    return {"picked": picked}

# Mount the static files directory for frontend
frontend_path = os.path.join(os.path.dirname(__file__), "../my-frontend-app/public")
app.mount("/static", StaticFiles(directory=os.path.abspath(frontend_path), html=True), name="static")

AVAILABLE_ROLES = ["Distributor", "Retailer"]

@app.get("/api/roles", tags=["auth"])
def get_roles():
    """Return available user roles for registration."""
    return {"roles": AVAILABLE_ROLES}

# --- Master Product Data Seeding ---
def seed_master_products():
    products = [
        {"product_name": "Low-Carb Multi Seeds Atta", "category": "Flour", "standard_pack_size": 1, "measurement_unit": "kg", "price_inr": 480, "expiry_period_days": 180},
        {"product_name": "Low-Carb Multi Seed Dosa Mix", "category": "Flour", "standard_pack_size": 1, "measurement_unit": "kg", "price_inr": 480, "expiry_period_days": 180},
        {"product_name": "Coconut Flour", "category": "Flour", "standard_pack_size": 1, "measurement_unit": "kg", "price_inr": 480, "expiry_period_days": 180},
        {"product_name": "Khapli Wheat Flour", "category": "Flour", "standard_pack_size": 1, "measurement_unit": "kg", "price_inr": 250, "expiry_period_days": 180},
        {"product_name": "Khapli Rava", "category": "Flour", "standard_pack_size": 1, "measurement_unit": "kg", "price_inr": 250, "expiry_period_days": 180},
        {"product_name": "Coconut Mixture", "category": "Snacks", "standard_pack_size": 500, "measurement_unit": "g", "price_inr": 270, "expiry_period_days": 90},
        {"product_name": "Multi-Seeds Nippat", "category": "Snacks", "standard_pack_size": 250, "measurement_unit": "g", "price_inr": 270, "expiry_period_days": 90},
        {"product_name": "Multi Seed Chakli", "category": "Snacks", "standard_pack_size": 250, "measurement_unit": "g", "price_inr": 270, "expiry_period_days": 90},
        {"product_name": "Coconut Oil", "category": "Oil", "standard_pack_size": 1, "measurement_unit": "L", "price_inr": 380, "expiry_period_days": 90},
        {"product_name": "Groundnut Oil", "category": "Oil", "standard_pack_size": 1, "measurement_unit": "L", "price_inr": 410, "expiry_period_days": 90},
    ]
    db = database.SessionLocal()
    for p in products:
        exists = db.query(models.Product).filter_by(product_name=p["product_name"]).first()
        if not exists:
            prod = models.Product(**p)
            db.add(prod)
    db.commit()
    db.close()

# Ensure master data is loaded before app starts
@app.on_event("startup")
def ensure_master_data():
    seed_master_products()

# --- Batch Grouping and Reporting Endpoints ---
from fastapi.responses import JSONResponse

@app.get("/api/batch-groups")
def get_batch_groups(db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    batches = db.query(models.Batch).all()
    groups = {}
    for b in batches:
        if b.batch_id not in groups:
            groups[b.batch_id] = {
                "batch_id": b.batch_id,
                "manufacturing_date": b.manufacturing_date,
                "expiry_date": b.expiry_date,
                "products": []
            }
        # Get all products for this batch
        batch_products = db.query(models.BatchProduct).filter(models.BatchProduct.batch_id == b.batch_id).all()
        for bp in batch_products:
            groups[b.batch_id]["products"].append({
                "product_id": bp.product_id,
                "current_quantity": bp.current_quantity,
                "initial_quantity": bp.initial_quantity,
                "qc_status": bp.qc_status
            })
    return list(groups.values())

@app.get("/api/batch-report/{batch_id}")
def get_batch_report(batch_id: str, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    batch = db.query(models.Batch).filter(models.Batch.batch_id == batch_id).first()
    batch_products = db.query(models.BatchProduct).filter(models.BatchProduct.batch_id == batch_id).all()
    inventory = db.query(models.Inventory).filter(models.Inventory.batch_id == batch_id).all()
    dispatches = [inv for inv in inventory if inv.location.startswith('retailer_')]
    return {
        "batch_id": batch_id,
        "products": [
            {
                "product_id": bp.product_id,
                "current_quantity": bp.current_quantity,
                "initial_quantity": bp.initial_quantity,
                "qc_status": bp.qc_status
            } for bp in batch_products
        ],
        "inventory": [
            {
                "product_id": i.product_id,
                "location": i.location,
                "current_quantity": i.current_quantity
            } for i in inventory
        ],
        "dispatches": [
            {
                "product_id": d.product_id,
                "location": d.location,
                "current_quantity": d.current_quantity
            } for d in dispatches
        ]
    }

# --- Dispatch Endpoints ---
@app.post("/api/dispatch", response_model=schemas.DispatchResponse)
def dispatch_product(request: schemas.DispatchRequest, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    if current_user.role != "Distributor":
        raise HTTPException(status_code=403, detail="Only Distributors can dispatch products.")
    success, message = crud.dispatch_product(db, request.retailer_id, request.product_id, request.batch_id, request.quantity)
    if not success:
        return schemas.DispatchResponse(success=False, message=message)
    return schemas.DispatchResponse(success=True, message=message)

@app.post("/api/dispatch-request", response_model=schemas.DispatchRequest)
def create_dispatch_request_api(request: schemas.DispatchRequestCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    if current_user.role != "Distributor":
        raise HTTPException(status_code=403, detail="Only Distributors can request dispatch.")
    req = crud.create_dispatch_request(db, request.retailer_id, request.product_id, request.batch_id, request.quantity)
    return req

@app.get("/api/dispatch-requests", response_model=list[schemas.DispatchRequest])
def list_dispatch_requests_api(status: Optional[str] = Query(None), db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return crud.get_dispatch_requests(db, status=status)

@app.post("/api/dispatch-approve")
def approve_dispatch_api(request: schemas.DispatchApproveRequest, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    if current_user.role != "Distributor":
        raise HTTPException(status_code=403, detail="Only Distributors can approve dispatches.")
    ok, msg = crud.approve_dispatch_request(db, request.id, request.approve)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}

@app.get("/api/batches/{batch_id}/history", response_model=list[schemas.ActionLog])
def get_batch_history(batch_id: str, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    # Return all action logs mentioning this batch_id in details
    logs = db.query(models.ActionLog).filter(models.ActionLog.details.contains(f"batch {batch_id}")).order_by(models.ActionLog.timestamp.desc()).all()
    return logs

@app.get("/api/inventory/{inventory_id}/history", response_model=list[schemas.ActionLog])
def get_inventory_history(inventory_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    # Return all action logs mentioning this inventory_id in details
    logs = db.query(models.ActionLog).filter(models.ActionLog.details.contains(f"inventory {inventory_id}")).order_by(models.ActionLog.timestamp.desc()).all()
    return logs

@app.get("/api/batch-units")
def get_batch_units_api(batch_id: Optional[str] = None, product_id: Optional[int] = None, location: Optional[str] = None, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    units = crud.get_batch_units(db, batch_id=batch_id, product_id=product_id, location=location)
    return [schemas.BatchUnit.from_orm(u) for u in units]
