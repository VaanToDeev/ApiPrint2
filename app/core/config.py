from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # Variáveis que a sua aplicação FastAPI realmente precisa
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    INITIAL_ADMIN_NOME: str
    INITIAL_ADMIN_EMAIL: str
    INITIAL_ADMIN_SENHA: str
    INITIAL_ADMIN_SIAPE: str
    INITIAL_ADMIN_DEPARTAMENTO: str
    INITIAL_ADMIN_TITULACAO: str

    # Configuração do Pydantic-Settings
    # model_config é o novo nome para a classe interna Config a partir do Pydantic V2
    # extra='ignore' diz ao Pydantic para ignorar quaisquer campos extras
    # que não estão definidos neste modelo.
    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
