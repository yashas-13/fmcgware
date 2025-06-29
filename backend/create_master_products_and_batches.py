import os
import sys
from datetime import date, timedelta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from models import Product, Batch
import schemas
import crud
import database
from sqlalchemy.orm import Session

def main():
    db: Session = database.SessionLocal()
    # Master product data
    products = [
        {"product_name": "Low-Carb Multi Seeds Atta", "category": "Flour", "standard_pack_size": 1, "measurement_unit": "kg", "price_inr": 480, "expiry_period_days": 180},
        {"product_name": "Low-Carb Multi Seed Dosa Mix", "category": "Flour", "standard_pack_size": 1, "measurement_unit": "kg", "price_inr": 480, "expiry_period_days": 180},
        {"product_name": "Coconut Flour", "category": "Flour", "standard_pack_size": 1, "measurement_unit": "kg", "price_inr": 480, "expiry_period_days": 180},
        {"product_name": "Khapli Wheat Flour", "category": "Flour", "standard_pack_size": 1, "measurement_unit": "kg", "price_inr": 250, "expiry_period_days": 180},
        {"product_name": "Khapli Rava", "category": "Flour", "standard_pack_size": 1, "measurement_unit": "kg", "price_inr": 250, "expiry_period_days": 180},
        {"product_name": "Coconut Mixture", "category": "Snacks", "standard_pack_size": 0.5, "measurement_unit": "kg", "price_inr": 270, "expiry_period_days": 90},
        {"product_name": "Multi-Seeds Nippat", "category": "Snacks", "standard_pack_size": 0.25, "measurement_unit": "kg", "price_inr": 270, "expiry_period_days": 90},
        {"product_name": "Multi Seed Chakli", "category": "Snacks", "standard_pack_size": 0.25, "measurement_unit": "kg", "price_inr": 270, "expiry_period_days": 90},
        {"product_name": "Coconut Oil", "category": "Oil", "standard_pack_size": 1, "measurement_unit": "L", "price_inr": 380, "expiry_period_days": 90},
        {"product_name": "Groundnut Oil", "category": "Oil", "standard_pack_size": 1, "measurement_unit": "L", "price_inr": 410, "expiry_period_days": 90},
    ]
    for idx, prod in enumerate(products, 1):
        sku = f"SKU{idx:03d}"
        prod_data = schemas.ProductCreate(
            sku=sku,
            product_name=prod["product_name"],
            category=prod["category"],
            description="",
            image_url="",
            measurement_unit=prod["measurement_unit"],
            standard_pack_size=prod["standard_pack_size"],
            price_inr=prod["price_inr"],
            expiry_period_days=prod["expiry_period_days"],
            reorder_level=10,
            supplier_id=None,
            is_active=True
        )
        db_product = db.query(Product).filter_by(product_name=prod["product_name"]).first()
        if not db_product:
            db_product = crud.create_product(db, prod_data)
        # Create a batch for each product
        today = date.today()
        batch_id = f"BATCH{idx:03d}-{today.strftime('%Y%m%d')}"
        mfg_date = today - timedelta(days=10)
        expiry_date = today + timedelta(days=prod["expiry_period_days"])
        batch_data = schemas.BatchCreate(
            batch_id=batch_id,
            product_id=db_product.product_id,
            manufacturing_date=mfg_date,
            received_date=today,
            expiry_date=expiry_date,
            initial_quantity=prod["standard_pack_size"],
            current_quantity=prod["standard_pack_size"],
            owner_type="Distributor",
            owner_id=1,
            qc_status="Approved"
        )
        db_batch = db.query(Batch).filter_by(batch_id=batch_id).first()
        if not db_batch:
            crud.create_batch(db, batch_data)
    db.close()

if __name__ == "__main__":
    main()
