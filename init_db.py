from vidseek.database import engine, Base
from vidseek.models import User

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")