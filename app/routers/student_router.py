from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud, models, auth
from app.database import get_db
from typing import List
import os
import uuid # For unique filenames
from pathlib import Path
from datetime import datetime # Import datetime

router = APIRouter(prefix="/students", tags=["Students"])


# Configurações de upload de arquivo adicionado agora
UPLOAD_DIR = Path("uploads/tcc_files")
ALLOWED_FILE_TYPES = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"] # .pdf, .docx
MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


@router.get("/me", response_model=schemas.EstudantePublic)
async def read_student_me(
    current_user: models.Estudante = Depends(auth.get_current_active_user)
):
    if not isinstance(current_user, models.Estudante):
        raise HTTPException(status_code=403, detail="Not a student account")
    return current_user

# Add more student-specific endpoints here based on ERD (e.g., view TCCs)

#adicionado agora
@router.post("/tccs/{tcc_id}/upload_file", response_model=schemas.TCCFilePublic, status_code=status.HTTP_201_CREATED)
async def upload_tcc_file(
    tcc_id: int,
    file: UploadFile = File(...),
    current_user: models.Estudante = Depends(auth.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if not isinstance(current_user, models.Estudante):
        raise HTTPException(status_code=403, detail="Apenas estudantes podem fazer upload de arquivos de TCC.")

    # 1. Validar a existência do TCC e a propriedade
    tcc = await crud.get_tcc_by_id(db, tcc_id)
    if not tcc:
        raise HTTPException(status_code=404, detail="TCC não encontrado.")
    
    if tcc.estudante_id != current_user.id:
        raise HTTPException(status_code=403, detail="Você só pode fazer upload de arquivos para seus próprios TCCs.")

    # 2. Validar o tipo de arquivo
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de arquivo inválido. Tipos permitidos são: {', '.join([ft.split('/')[-1] for ft in ALLOWED_FILE_TYPES])}"
        )

    # 3. Validar o tamanho do arquivo
    file.file.seek(0, os.SEEK_END) # Move para o final do arquivo
    file_size = file.file.tell() # Obtém a posição atual (que é o tamanho)
    file.file.seek(0) # Volta para o início

    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"O tamanho do arquivo excede o limite de {MAX_FILE_SIZE_MB}MB."
        )
    
    # 4. Gerar nome de arquivo e caminho únicos
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = UPLOAD_DIR / unique_filename

    # 5. Salvar o arquivo no disco
    try:
        with open(file_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)  # Lê o arquivo em blocos de 1MB
                if not chunk:
                    break
                buffer.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível salvar o arquivo: {e}")

    # 6. Criar registro no banco de dados
    tcc_file_in_db = schemas.TCCFilePublic(
        tcc_id=tcc_id,
        filename=file.filename, # Armazena o nome original do arquivo
        filepath=str(file_path), # Armazena o caminho no servidor
        filetype=file.content_type,
        upload_date=datetime.now()
    )
    db_tcc_file = await crud.create_tcc_file(db, tcc_file_in=tcc_file_in_db)

    return db_tcc_file

# Opcional: Adicionar endpoint para obter arquivos de TCC para um TCC específico
@router.get("/tccs/{tcc_id}/files", response_model=List[schemas.TCCFilePublic])
async def get_tcc_files(
    tcc_id: int,
    current_user: models.Estudante = Depends(auth.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if not isinstance(current_user, models.Estudante):
        raise HTTPException(status_code=403, detail="Não é uma conta de estudante.")

    tcc = await crud.get_tcc_by_id(db, tcc_id)
    if not tcc:
        raise HTTPException(status_code=404, detail="TCC não encontrado.")
    
    if tcc.estudante_id != current_user.id:
        raise HTTPException(status_code=403, detail="Você só pode visualizar arquivos para seus próprios TCCs.")

    files = await crud.get_tcc_files_by_tcc_id(db, tcc_id)
    return files

# Opcional: Adicionar endpoint para estudantes criarem seus próprios TCCs (se aplicável)
@router.post("/tccs/", response_model=schemas.TCCPublic, status_code=status.HTTP_201_CREATED)
async def create_new_tcc(
    tcc_in: schemas.TCCCreate,
    current_user: models.Estudante = Depends(auth.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if not isinstance(current_user, models.Estudante):
        raise HTTPException(status_code=403, detail="Apenas estudantes podem criar TCCs diretamente através deste endpoint.")
    
    if tcc_in.estudante_id != current_user.id:
        raise HTTPException(status_code=403, detail="Você só pode criar TCCs para o seu próprio ID de estudante.")
    
    # Validar se o orientador existe
    orientador = await crud.get_professor_by_id(db, tcc_in.orientador_id)
    if not orientador:
        raise HTTPException(status_code=404, detail="Orientador (Professor) não encontrado.")
    
    # Verificar se o estudante já possui um TCC (opcional, depende das regras de negócio)
    existing_tccs = await crud.get_tccs_by_estudante_id(db, current_user.id)
    if existing_tccs: # Exemplo: apenas um TCC por estudante
        raise HTTPException(status_code=400, detail="O estudante já possui um TCC registrado.")

    return await crud.create_tcc(db=db, tcc_in=tcc_in)