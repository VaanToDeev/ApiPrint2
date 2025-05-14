from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Caminho para o banco de dados SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./users.db"

# Criar engine do SQLAlchemy
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Criar sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criar base para os modelos
Base = declarative_base()

# Função para obter o DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()