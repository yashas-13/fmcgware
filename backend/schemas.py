from pydantic import BaseModel
from typing import Optional, List
from datetime import date
import models

class SupplierBase(BaseModel):
    name: str
    contact: Optional[str] = None

class SupplierCreate(SupplierBase):
    pass

class Supplier(SupplierBase):
    supplier_id: int
    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    sku: str
    product_name: str
    category: str
    description: Optional[str] = ""
    image_url: Optional[str] = ""
    measurement_unit: str
    standard_pack_size: float
    price_inr: float
    expiry_period_days: int
    reorder_level: int
    supplier_id: Optional[int]
    is_active: Optional[bool] = True

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    product_id: int
    class Config:
        from_attributes = True

class BatchBase(BaseModel):
    batch_id: str
    manufacturing_date: Optional[date] = None
    received_date: Optional[date] = None
    expiry_date: Optional[date] = None
    owner_type: str
    owner_id: int

class BatchCreate(BatchBase):
    pass

class Batch(BatchBase):
    class Config:
        from_attributes = True

class InventoryBase(BaseModel):
    product_id: int
    batch_id: str
    location: str
    current_quantity: float

class InventoryCreate(InventoryBase):
    pass

class Inventory(InventoryBase):
    id: int
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str
    email: str
    role: str
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: str

class User(UserBase):
    user_id: int
    class Config:
        from_attributes = True

class AlertBase(BaseModel):
    user_id: int
    message: str
    is_read: Optional[bool] = False
    created_at: date

class AlertCreate(AlertBase):
    pass

class Alert(AlertBase):
    alert_id: int
    class Config:
        from_attributes = True

class ActionLogBase(BaseModel):
    user_id: Optional[int] = None
    action: str
    details: Optional[str] = None
    timestamp: date

class ActionLogCreate(ActionLogBase):
    pass

class ActionLog(ActionLogBase):
    id: int
    class Config:
        from_attributes = True

class DispatchRequestBase(BaseModel):
    retailer_id: int
    product_id: int
    batch_id: str
    quantity: float
    status: Optional[str] = "pending"
    created_at: Optional[date] = None

class DispatchRequestCreate(DispatchRequestBase):
    pass

class DispatchRequest(DispatchRequestBase):
    id: int
    class Config:
        from_attributes = True

class DispatchApproveRequest(BaseModel):
    id: int
    approve: bool

class DispatchResponse(BaseModel):
    success: bool
    message: str

class BatchUnitBase(BaseModel):
    unit_uid: str
    batch_id: str
    product_id: int
    status: Optional[str] = "Available"
    location: Optional[str] = None

class BatchUnitCreate(BatchUnitBase):
    pass

class BatchUnit(BatchUnitBase):
    class Config:
        from_attributes = True

class BatchProductBase(BaseModel):
    batch_id: str
    product_id: int
    initial_quantity: float
    current_quantity: float
    qc_status: Optional[str] = "Approved"

class BatchProductCreate(BatchProductBase):
    pass

class BatchProduct(BatchProductBase):
    id: int
    class Config:
        from_attributes = True
