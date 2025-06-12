from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud, models, auth
from app.database import get_db
from typing import List

router = APIRouter(prefix="/professors", tags=["Professors"])

@router.get("/me", response_model=schemas.ProfessorPublic)
async def read_professor_me(
    current_user: models.Professor = Depends(auth.get_current_active_user)
):
    if not isinstance(current_user, models.Professor):
        raise HTTPException(status_code=403, detail="Not a professor account")
    return current_user

# Add more professor-specific endpoints (e.g., view TCCs they orient)

@router.put("/me", response_model=schemas.ProfessorPublic)
async def update_current_user(
    user_update: schemas.ProfessorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.Professor = Depends(auth.get_current_active_user)
):
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return current_user

@router.post("/tccs/", response_model=schemas.TCCPublic, status_code=status.HTTP_201_CREATED)
async def create_tcc_for_student(
    tcc_in: schemas.TCCCreate,
    db: AsyncSession = Depends(get_db),
    current_professor: models.Professor = Depends(auth.get_current_active_user)
):
    if not isinstance(current_professor, models.Professor):
        raise HTTPException(status_code=403, detail="Apenas professores podem criar TCCs.")

    # Validar se o estudante existe
    student = await crud.get_estudante_by_id(db, tcc_in.estudante_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Estudante com ID {tcc_in.estudante_id} não encontrado.")

    # O orientador é sempre o professor que está logado
    orientador_id = current_professor.id
    
    # Verificar se o estudante já possui um TCC (opcional, regra de negócio)
    existing_tccs = await crud.get_tccs_by_estudante_id(db, tcc_in.estudante_id)
    if existing_tccs:
        raise HTTPException(status_code=400, detail="Este estudante já possui um TCC registrado.")

    # Cria o TCC usando o ID do professor logado como orientador
    return await crud.create_tcc(db=db, tcc_in=tcc_in, orientador_id=orientador_id)

@router.get("/me/tccs", response_model=List[schemas.TCCPublic])
async def get_my_oriented_tccs(
    db: AsyncSession = Depends(get_db),
    current_professor: models.Professor = Depends(auth.get_current_active_user)
):
    if not isinstance(current_professor, models.Professor):
        raise HTTPException(status_code=403, detail="Apenas professores podem ver seus TCCs orientados.")
    
    tccs = await crud.get_tccs_by_orientador_id(db, orientador_id=current_professor.id)
    return tccs

@router.get("/departamento", response_model=List[schemas.ProfessorPublic])
async def list_professores_mesmo_departamento(
    db: AsyncSession = Depends(get_db),
    current_user: models.Professor = Depends(auth.get_current_active_user)
):
    # Permitir apenas coordenador ou admin
    if current_user.role not in [models.UserRole.COORDENADOR, models.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Acesso permitido apenas para coordenador ou admin.")

    professores = await crud.get_professores_by_departamento(db, current_user.departamento)
    return professores

@router.get("/orientandos", response_model=List[schemas.EstudantePublic])
async def get_orientandos(
    db: AsyncSession = Depends(get_db),
    current_user: models.Professor = Depends(auth.get_current_active_user)
):
    if not isinstance(current_user, models.Professor):
        raise HTTPException(status_code=403, detail="Acesso permitido apenas para professores.")
    orientandos = await crud.get_orientandos_by_professor_id(db, current_user.id)
    return orientandos