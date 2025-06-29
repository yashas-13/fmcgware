import os
import sys
sys.path.append(os.path.dirname(__file__))
from database import SessionLocal
import models

def seed_products():
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
    db = SessionLocal()
    for p in products:
        exists = db.query(models.Product).filter_by(product_name=p["product_name"]).first()
        if not exists:
            prod = models.Product(**p)
            db.add(prod)
    db.commit()
    db.close()
    print("Product master data seeded.")

if __name__ == "__main__":
    seed_products()
