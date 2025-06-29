from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base

class Supplier(Base):
    __tablename__ = "suppliers"
    supplier_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    contact = Column(String)
    products = relationship("Product", back_populates="supplier")

class Product(Base):
    __tablename__ = "products"
    product_id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False, default="")
    product_name = Column(String, index=True, nullable=False)
    category = Column(String, nullable=False)
    description = Column(String, default="")
    image_url = Column(String, default="")
    measurement_unit = Column(String, nullable=False)
    standard_pack_size = Column(Float, nullable=False, default=1)
    price_inr = Column(Float, nullable=False, default=0)
    expiry_period_days = Column(Integer, nullable=False, default=1)
    reorder_level = Column(Integer, nullable=False, default=1)
    supplier_id = Column(Integer, ForeignKey("suppliers.supplier_id"))
    is_active = Column(Boolean, default=True)
    supplier = relationship("Supplier", back_populates="products")

class Batch(Base):
    __tablename__ = "batches"
    batch_id = Column(String, primary_key=True, index=True)
    manufacturing_date = Column(Date, nullable=True)
    received_date = Column(Date)
    expiry_date = Column(Date)
    owner_type = Column(String)  # 'Distributor' or 'Retailer'
    owner_id = Column(Integer)
    # Relationships
    products = relationship("BatchProduct", back_populates="batch")

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"))
    batch_id = Column(String, ForeignKey("batches.batch_id"))
    location = Column(String)  # warehouse or retailer id
    current_quantity = Column(Float)
    product = relationship("Product")
    batch = relationship("Batch")

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)  # 'Distributor' or 'Retailer'
    email = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)

class Alert(Base):
    __tablename__ = "alerts"
    alert_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    message = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(Date)
    user = relationship("User")

class ActionLog(Base):
    __tablename__ = "action_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    action = Column(String, nullable=False)
    details = Column(String)
    timestamp = Column(Date, nullable=False)
    user = relationship("User")

class BatchUnit(Base):
    __tablename__ = "batch_units"
    unit_uid = Column(String, primary_key=True, index=True)  # Unique per unit
    batch_id = Column(String, ForeignKey("batches.batch_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    status = Column(String, default="Available")  # Optional: Available, Dispatched, etc.
    location = Column(String, nullable=True)  # Optional: warehouse, retailer, etc.
    batch = relationship("Batch")
    product = relationship("Product")

class BatchProduct(Base):
    __tablename__ = "batch_products"
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String, ForeignKey("batches.batch_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    initial_quantity = Column(Float)
    current_quantity = Column(Float)
    qc_status = Column(String, default="Approved")
    batch = relationship("Batch", back_populates="products")
    product = relationship("Product")

class DispatchRequest(Base):
    __tablename__ = "dispatch_requests"
    id = Column(Integer, primary_key=True, index=True)
    retailer_id = Column(Integer, ForeignKey("users.user_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    batch_id = Column(String, ForeignKey("batches.batch_id"))
    quantity = Column(Float)
    status = Column(String, default="pending")  # pending, approved, rejected
    created_at = Column(Date)
    # Relationships
    retailer = relationship("User", foreign_keys=[retailer_id])
    product = relationship("Product", foreign_keys=[product_id])
    batch = relationship("Batch", foreign_keys=[batch_id])

# Update SKU for products where SKU is NULL or empty
def update_product_sku(session):
    from sqlalchemy import update
    stmt = update(Product).where(Product.sku == None).values(sku="SKU-" + Product.product_id)
    session.execute(stmt)
    session.commit()
