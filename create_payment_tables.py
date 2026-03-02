import sys
sys.path.insert(0, '.')

from app.database import engine, Base

# Import ALL models so SQLAlchemy knows about all tables
from app.models.user import User
from app.models.conversation import Conversation, Message, TrainingData
from app.models.document import Document
from payments.models import Subscription, UsageLog, PaymentEvent

# Create all tables in correct order
Base.metadata.create_all(bind=engine)
print('All tables created successfully!')