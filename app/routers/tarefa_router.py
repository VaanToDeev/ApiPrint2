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


# Endpoint para professor criar uma tarefa para um TCC
@router.post("/tccs/{tcc_id}/tarefas", response_model=schemas.TarefaPublic, status_code=status.HTTP_201_CREATED)
async def create_task_for_tcc(
    tcc_id: int,
    tarefa_in: schemas.TarefaCreate,
    db: AsyncSession = Depends(get_db),
    current_professor: models.Professor = Depends(auth.get_current_active_user)
):
    if not isinstance(current_professor, models.Professor):
        raise HTTPException(status_code=403, detail="Acesso permitido apenas para professores.")

    tcc = await crud.get_tcc_by_id(db, tcc_id)
    if not tcc or tcc.orientador_id != current_professor.id:
        raise HTTPException(status_code=403, detail="TCC não encontrado ou você não é o orientador.")
        
    return await crud.create_tarefa(db=db, tarefa_in=tarefa_in, tcc_id=tcc_id)

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

# Endpoint para professor editar uma tarefa
@router.put("/tarefas/{tarefa_id}", response_model=schemas.TarefaPublic)
async def update_task(
    tarefa_id: int,
    tarefa_update: schemas.TarefaUpdate,
    db: AsyncSession = Depends(get_db),
    current_professor: models.Professor = Depends(auth.get_current_active_user)
):
    tarefa = await crud.get_tarefa_by_id(db, tarefa_id)
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    if tarefa.tcc.orientador_id != current_professor.id:
        raise HTTPException(status_code=403, detail="Você só pode editar tarefas dos TCCs que orienta.")
        
    return await crud.update_tarefa(db=db, tarefa=tarefa, tarefa_update=tarefa_update)

# Endpoint para estudante atualizar o status de uma tarefa
@router.patch("/tarefas/{tarefa_id}/status", response_model=schemas.TarefaPublic)
async def update_task_status_by_student(
    tarefa_id: int,
    status_update: schemas.TarefaUpdate, # Reutiliza o schema, mas apenas o campo 'status' será usado
    db: AsyncSession = Depends(get_db),
    current_student: models.Estudante = Depends(auth.get_current_active_user)
):
    if not isinstance(current_student, models.Estudante):
        raise HTTPException(status_code=403, detail="Acesso permitido apenas para estudantes.")

    tarefa = await crud.get_tarefa_by_id(db, tarefa_id)
    if not tarefa or tarefa.tcc.estudante_id != current_student.id:
        raise HTTPException(status_code=403, detail="Tarefa não encontrada ou não pertence a você.")

    # Garante que o estudante só possa atualizar o status
    update_data = schemas.TarefaUpdate(status=status_update.status)
        
    return await crud.update_tarefa(db=db, tarefa=tarefa, tarefa_update=update_data)

# Endpoint para professor deletar uma tarefa
@router.delete("/tarefas/{tarefa_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    tarefa_id: int,
    db: AsyncSession = Depends(get_db),
    current_professor: models.Professor = Depends(auth.get_current_active_user)
):
    tarefa = await crud.get_tarefa_by_id(db, tarefa_id)
    if not tarefa:
        return # Se não encontrou, a exclusão é idempotente
    if tarefa.tcc.orientador_id != current_professor.id:
        raise HTTPException(status_code=403, detail="Você só pode deletar tarefas dos TCCs que orienta.")
        
    await crud.delete_tarefa(db, tarefa=tarefa)
    return

# Endpoint para estudante enviar um arquivo para uma tarefa
@router.post("/tarefas/{tarefa_id}/arquivos", response_model=schemas.ArquivoPublic, status_code=status.HTTP_201_CREATED)
async def upload_file_for_task(
    tarefa_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_student: models.Estudante = Depends(auth.get_current_active_user)
):
    if not isinstance(current_student, models.Estudante):
        raise HTTPException(status_code=403, detail="Acesso permitido apenas para estudantes.")

    tarefa = await crud.get_tarefa_by_id(db, tarefa_id)
    if not tarefa or tarefa.tcc.estudante_id != current_student.id:
        raise HTTPException(status_code=403, detail="Tarefa não encontrada ou não pertence a você.")
        
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = UPLOAD_DIR / unique_filename
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    arquivo_in = schemas.ArquivoCreate(nome_arquivo=file.filename, caminho_arquivo=str(file_path))
    
    await crud.update_tarefa(db, tarefa=tarefa, tarefa_update=schemas.TarefaUpdate(status=models.StatusTarefa.REVISAR))
    
    return await crud.create_arquivo(db, arquivo_in=arquivo_in, tarefa_id=tarefa_id)
