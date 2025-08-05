from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid
from pathlib import Path

from app import schemas, crud, models, auth
from app.database import get_db

router = APIRouter(tags=["Tarefas"])

UPLOAD_DIR = Path("uploads/tarefa_arquivos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Endpoint para visualizar as tarefas de um TCC (para aluno e professor)
@router.get("/tccs/{tcc_id}/tarefas", response_model=List[schemas.TarefaPublic])
async def get_tasks_for_tcc(
    tcc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.Professor | models.Estudante = Depends(auth.get_current_active_user)
):
    tcc = await crud.get_tcc_by_id(db, tcc_id)
    if not tcc:
        raise HTTPException(status_code=404, detail="TCC não encontrado.")
    
    is_orientador = isinstance(current_user, models.Professor) and tcc.orientador_id == current_user.id
    is_aluno = isinstance(current_user, models.Estudante) and tcc.estudante_id == current_user.id
    
    if not (is_orientador or is_aluno):
        raise HTTPException(status_code=403, detail="Você não tem permissão para visualizar as tarefas deste TCC.")
        
    return await crud.get_tarefas_by_tcc_id(db, tcc_id=tcc_id)

# NOVO: Endpoint unificado para Professor ou Aluno alterarem o status de uma tarefa.
@router.patch("/tarefas/{tarefa_id}/status", response_model=schemas.TarefaPublic)
async def update_task_status(
    tarefa_id: int,
    status_update: schemas.TarefaUpdate, # Reutiliza o schema, esperando apenas o campo 'status'.
    db: AsyncSession = Depends(get_db),
    current_user: models.Professor | models.Estudante = Depends(auth.get_current_active_user)
):
    """
    Atualiza o status de uma tarefa específica.

    - **Permissão**: Acesso permitido apenas para o orientador do TCC ou o estudante do TCC.
    - **Ação**: Altera o status da tarefa para um dos valores definidos em `StatusTarefa`.
      (a_fazer, fazendo, revisar, feita, concluida)
    """
    tarefa = await crud.get_tarefa_by_id(db, tarefa_id)
    if not tarefa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarefa não encontrada.")

    # Verifica se o usuário logado é o orientador ou o aluno do TCC ao qual a tarefa pertence.
    is_orientador = isinstance(current_user, models.Professor) and tarefa.tcc.orientador_id == current_user.id
    is_aluno = isinstance(current_user, models.Estudante) and tarefa.tcc.estudante_id == current_user.id

    if not (is_orientador or is_aluno):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Você não tem permissão para alterar esta tarefa."
        )
    
    # Validação para garantir que apenas o status seja atualizado por este endpoint
    if status_update.status is None:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="O campo 'status' é obrigatório para esta operação."
        )

    # Cria um objeto de atualização contendo apenas o status para evitar alterações indesejadas.
    update_data = schemas.TarefaUpdate(status=status_update.status)
        
    updated_tarefa = await crud.update_tarefa(db=db, tarefa=tarefa, tarefa_update=update_data)
    return updated_tarefa