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

@router.get("/students", response_model=List[schemas.EstudantePublic])
async def list_all_students_for_professor(
    db: AsyncSession = Depends(get_db),
    current_professor: models.Professor = Depends(auth.get_current_active_user)
):
    """
    Fornece uma lista de todos os estudantes.
    Destinado para uso do professor no frontend para selecionar um aluno ao criar um TCC.
    Acessível por qualquer professor logado.
    """
    if not isinstance(current_professor, models.Professor):
        raise HTTPException(status_code=403, detail="Acesso permitido apenas para professores.")
    
    # Busca todos os estudantes. Em uma aplicação real, considere paginação.
    students = await crud.get_estudantes(db, skip=0, limit=1000) 
    return students

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

@router.post("/tccs/{tcc_id}/tarefas", response_model=schemas.TarefaPublic, status_code=status.HTTP_201_CREATED)
async def create_task_for_tcc(
    tcc_id: int,
    tarefa_in: schemas.TarefaCreate,
    db: AsyncSession = Depends(get_db),
    current_professor: models.Professor = Depends(auth.get_current_active_user)
):
    """
    Cria uma nova tarefa para um TCC específico. Apenas o orientador do TCC pode criar tarefas.
    """
    if not isinstance(current_professor, models.Professor):
        raise HTTPException(status_code=403, detail="Acesso permitido apenas para professores.")

    # Verifica se o TCC existe e se o professor logado é o orientador
    tcc = await crud.get_tcc_by_id(db, tcc_id)
    if not tcc:
        raise HTTPException(status_code=404, detail="TCC não encontrado.")
    if tcc.orientador_id != current_professor.id:
        raise HTTPException(status_code=403, detail="Você só pode criar tarefas para os TCCs que orienta.")
        
    return await crud.create_tarefa(db=db, tarefa=tarefa_in, tcc_id=tcc_id)

@router.put("/tarefas/{tarefa_id}", response_model=schemas.TarefaPublic)
async def update_task(
    tarefa_id: int,
    tarefa_update: schemas.TarefaUpdate,
    db: AsyncSession = Depends(get_db),
    current_professor: models.Professor = Depends(auth.get_current_active_user)
):
    """
    Atualiza uma tarefa. Apenas o orientador do TCC pode atualizar a tarefa.
    """
    if not isinstance(current_professor, models.Professor):
        raise HTTPException(status_code=403, detail="Acesso permitido apenas para professores.")
        
    tarefa = await crud.get_tarefa_by_id(db, tarefa_id)
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    if tarefa.tcc.orientador_id != current_professor.id:
        raise HTTPException(status_code=403, detail="Você só pode editar tarefas dos TCCs que orienta.")
        
    return await crud.update_tarefa(db=db, tarefa_id=tarefa_id, tarefa_update=tarefa_update)

@router.delete("/tarefas/{tarefa_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    tarefa_id: int,
    db: AsyncSession = Depends(get_db),
    current_professor: models.Professor = Depends(auth.get_current_active_user)
):
    """
    Deleta uma tarefa. Apenas o orientador do TCC pode deletar a tarefa.
    """
    if not isinstance(current_professor, models.Professor):
        raise HTTPException(status_code=403, detail="Acesso permitido apenas para professores.")
        
    tarefa = await crud.get_tarefa_by_id(db, tarefa_id)
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    if tarefa.tcc.orientador_id != current_professor.id:
        raise HTTPException(status_code=403, detail="Você só pode deletar tarefas dos TCCs que orienta.")
        
    await crud.delete_tarefa(db, tarefa_id=tarefa_id)
    return

# Endpoint para o professor (e aluno) ver as tarefas de um TCC
@router.get("/tccs/{tcc_id}/tarefas", response_model=List[schemas.TarefaPublic])
async def get_tasks_for_tcc(
    tcc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.Professor | models.Estudante = Depends(auth.get_current_active_user)
):
    """
    Lista as tarefas de um TCC específico. Acessível pelo orientador ou pelo estudante do TCC.
    """
    tcc = await crud.get_tcc_by_id(db, tcc_id)
    if not tcc:
        raise HTTPException(status_code=404, detail="TCC não encontrado.")
    
    # Verifica se o usuário logado tem permissão
    is_orientador = isinstance(current_user, models.Professor) and tcc.orientador_id == current_user.id
    is_aluno = isinstance(current_user, models.Estudante) and tcc.estudante_id == current_user.id
    
    if not (is_orientador or is_aluno):
        raise HTTPException(status_code=403, detail="Você não tem permissão para visualizar as tarefas deste TCC.")
        
    return await crud.get_tarefas_by_tcc_id(db, tcc_id=tcc_id)
