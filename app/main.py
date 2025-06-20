from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.middleware.cors import CORSMiddleware

# Importações principais que não causam ciclos
from app.database import init_db, AsyncSessionLocal
from app.routers import auth_router, student_router, professor_router, admin_router, tarefa_router
from app.core.config import settings
from app import models, schemas # crud foi removido daqui

app = FastAPI(title="Sistema de Gestão Acadêmica API", version="0.1.0")

app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Frontend origin
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )


# Include routers
app.include_router(auth_router.router)
app.include_router(student_router.router)
app.include_router(professor_router.router)
app.include_router(admin_router.router)
app.include_router(tarefa_router.router)

@app.on_event("startup")
async def on_startup():
    await init_db() # Create tables

    # Importação local de 'crud' para quebrar o ciclo de dependência
    from app import crud
    
    # Create initial Admin Professor if not exists
    async with AsyncSessionLocal() as db:
        try:
            admin_user = await crud.get_professor_by_email(db, email=settings.INITIAL_ADMIN_EMAIL)
            if not admin_user:
                admin_in = schemas.ProfessorCreate(
                    nome=settings.INITIAL_ADMIN_NOME,
                    email=settings.INITIAL_ADMIN_EMAIL,
                    password=settings.INITIAL_ADMIN_SENHA,
                    siape=settings.INITIAL_ADMIN_SIAPE,
                    departamento=settings.INITIAL_ADMIN_DEPARTAMENTO,
                    titulacao=settings.INITIAL_ADMIN_TITULACAO,
                    role=models.UserRole.ADMIN # Explicitly set role here for creation
                )
                await crud.create_professor(db, professor=admin_in, role=models.UserRole.ADMIN) # Pass role explicitly
                print(f"INFO:     Usuário administrador '{settings.INITIAL_ADMIN_EMAIL}' criado.")
            else:
                print(f"INFO:     Usuário administrador '{settings.INITIAL_ADMIN_EMAIL}' já existe.")
        except Exception as e:
            # Imprime o erro específico que ocorre na criação do admin
            print(f"ERRO:     Ocorreu um erro durante a criação do usuário administrador inicial: {e}")


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Bem-vindo à API de Gestão Acadêmica!"}

# To run the app: uvicorn app.main:app --reload
