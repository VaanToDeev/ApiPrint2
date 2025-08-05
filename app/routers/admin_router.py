from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app import schemas, crud, models, auth
from app.database import get_db
import uuid
from pathlib import Path

router = APIRouter(prefix="/admin", tags=["Admin"])
UPLOAD_DIR = Path("uploads/admin_arquivos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/users/students", response_model=List[schemas.EstudantePublic])
async def list_students(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_admin: models.Professor = Depends(auth.get_current_admin_user) # Protect endpoint
):
    students = await crud.get_estudantes(db, skip=skip, limit=limit)
    return students

@router.get("/users/professors", response_model=List[schemas.ProfessorPublic])
async def list_professors(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_admin: models.Professor = Depends(auth.get_current_admin_user)
):
    professors = await crud.get_professores(db, skip=skip, limit=limit)
    return professors

@router.post("/cursos", response_model=schemas.CursoPublic, status_code=status.HTTP_201_CREATED)
async def create_new_curso(
    curso_in: schemas.CursoCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: models.Professor = Depends(auth.get_current_admin_user)
):
    db_curso = await crud.get_curso_by_nome(db, nome_curso=curso_in.nome_curso)
    if db_curso:
        raise HTTPException(status_code=400, detail=f"Curso com nome '{curso_in.nome_curso}' já existe.")
    return await crud.create_curso(db=db, curso=curso_in)

@router.put("/cursos/{curso_id}/assign-coordenador/{professor_id}", response_model=schemas.CursoPublic)
async def assign_coordenador(
    curso_id: int,
    professor_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: models.Professor = Depends(auth.get_current_admin_user)
):
    professor_to_assign = await crud.get_professor_by_id(db, professor_id)
    if not professor_to_assign:
        raise HTTPException(status_code=404, detail=f"Professor with ID {professor_id} not found.")

    curso = await crud.get_curso_by_id(db, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail=f"Curso with ID {curso_id} not found.")

    if professor_to_assign.role == models.UserRole.PROFESSOR:
        await crud.update_professor_role(db, professor_id, models.UserRole.COORDENADOR)
        
    updated_curso = await crud.assign_coordenador_to_curso(db, curso_id=curso_id, professor_id=professor_id)
    if not updated_curso:
        raise HTTPException(status_code=500, detail="Failed to assign coordenador.")
    
    return updated_curso

@router.get("/cursos", response_model=List[schemas.CursoPublic])
async def list_all_cursos(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    cursos = await crud.get_cursos(db, skip=skip, limit=limit)
    return cursos

@router.put("/cursos/{curso_id}", response_model=schemas.CursoPublic)
async def update_curso(
    curso_id: int,
    curso_in: schemas.CursoCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: models.Professor = Depends(auth.get_current_admin_user)
):
    db_curso = await crud.get_curso_by_id(db, curso_id)
    if not db_curso:
        raise HTTPException(status_code=404, detail="Curso não encontrado.")
    return await crud.update_curso(db, curso_id, curso_in)

@router.delete("/cursos/{curso_id}", status_code=204)
async def delete_curso(
    curso_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: models.Professor = Depends(auth.get_current_admin_user)
):
    curso = await crud.get_curso_by_id(db, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso não encontrado.")
    await db.delete(curso)
    await db.commit()
    return

# NOVO: Endpoint para admin enviar um arquivo geral para todos os estudantes
@router.post("/arquivos-gerais", response_model=schemas.AdminArquivoPublic, status_code=status.HTTP_201_CREATED)
async def upload_general_file(
    db: AsyncSession = Depends(get_db),
    current_admin: models.Professor = Depends(auth.get_current_admin_user),
    file: UploadFile = File(...),
    descricao: Optional[str] = Form(None)
):
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = UPLOAD_DIR / unique_filename

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível salvar o arquivo: {e}")

    arquivo_in = schemas.AdminArquivoCreate(
        nome_arquivo=file.filename,
        caminho_arquivo=str(file_path),
        descricao=descricao,
        uploader_id=current_admin.id
    )

    return await crud.create_admin_arquivo(db, arquivo_in=arquivo_in)