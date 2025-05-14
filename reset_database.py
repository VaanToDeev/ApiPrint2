import os
from app.database import Base, engine

def reset_database():
    # Remover o banco de dados existente
    if os.path.exists("users.db"):
        os.remove("users.db")
        print("Banco de dados antigo removido.")
    
    # Criar novo banco de dados com a estrutura atualizada
    Base.metadata.create_all(bind=engine)
    print("Novo banco de dados criado com sucesso!")

if __name__ == "__main__":
    reset_database() 