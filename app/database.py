import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=True) # echo=True for debugging SQL
AsyncSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

MAX_DB_RETRIES = 5
DB_RETRY_DELAY_SECONDS = 5

async def init_db():
    retries = 0
    while True:
        try:
            async with engine.begin() as conn:
                # await conn.run_sync(Base.metadata.drop_all) # Use with caution
                await conn.run_sync(Base.metadata.create_all)
            print(f"INFO:     Conexão com o banco de dados '{settings.DATABASE_URL.split('@')[-1]}' estabelecida e tabelas inicializadas.")
            break  # Sucesso
        except OperationalError as e:
            retries += 1
            error_message_lower = str(e).lower()
            # Extrai o host e a porta da DATABASE_URL para a mensagem de log
            db_address_info = "desconhecido"
            if '@' in settings.DATABASE_URL:
                db_address_info = settings.DATABASE_URL.split('@')[-1].split('/')[0]

            if retries > MAX_DB_RETRIES:
                print(f"ERRO:     Falha ao conectar ao banco de dados em '{db_address_info}' após {MAX_DB_RETRIES} tentativas. Desistindo.")
                raise
            
            print(f"AVISO:    Falha na conexão com o banco de dados em '{db_address_info}'. Tentando novamente em {DB_RETRY_DELAY_SECONDS}s... (Tentativa {retries}/{MAX_DB_RETRIES})")
            print(f"          Detalhes do erro: {e}")
            await asyncio.sleep(DB_RETRY_DELAY_SECONDS)
        except Exception as e:
            print(f"ERRO:     Um erro inesperado ocorreu durante a inicialização do banco de dados: {e}")
            raise