from backend.database import SessionLocal
from backend.models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()

username = "admin"
password = "admin123"
email = "admin@example.com"
role = "Distributor"

hashed_password = pwd_context.hash(password)

user = db.query(User).filter(User.username == username).first()
if not user:
    user = User(username=username, email=email, role=role, hashed_password=hashed_password, is_active=True)
    db.add(user)
    db.commit()
    print("Test user created.")
else:
    print("User already exists.")
db.close()
