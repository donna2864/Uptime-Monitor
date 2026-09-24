from app.database import Base, engine
from app.models import CheckResult, Monitor, Incident

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Database created successfully!")