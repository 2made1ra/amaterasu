# Import all the models, so that Base has them before being imported by Alembic
from app.db.base_class import Base
from app.models.user import User
from app.models.document import Document
from app.models.contract_fact import ContractFact
from app.models.extraction_run import ExtractionRun
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
