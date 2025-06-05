from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app import schemas, crud, models, auth
from app.database import get_db

router = APIRouter(prefix="/admin", tags=["Admin"])

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

    # Optional: Promote professor to 'coordenador' role if they are not already admin/coordenador
    if professor_to_assign.role == models.UserRole.PROFESSOR:
        await crud.update_professor_role(db, professor_id, models.UserRole.COORDENADOR)
        # Reload professor to reflect role change if needed for response, though assign_coordenador_to_curso doesn't return it directly.
        # professor_to_assign = await crud.get_professor_by_id(db, professor_id) # Refresh

    updated_curso = await crud.assign_coordenador_to_curso(db, curso_id=curso_id, professor_id=professor_id)
    if not updated_curso: # Should be caught by earlier checks, but good practice
        raise HTTPException(status_code=500, detail="Failed to assign coordenador.")
    
    # To include full coordinator details in response, you'd need to adjust schema and query
    # For now, CursoPublic only shows coordenador_id.
    return updated_curso

@router.get("/cursos", response_model=List[schemas.CursoPublic])
async def list_all_cursos(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    # No admin protection for listing courses, assuming it's public or for authenticated users
    # current_user: models.Professor | models.Estudante = Depends(auth.get_current_active_user) 
):
    cursos = await crud.get_cursos(db, skip=skip, limit=limit)
    return cursos