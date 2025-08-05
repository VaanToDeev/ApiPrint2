from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud, models, auth
from app.database import get_db
from typing import List, Optional
from datetime import date
import uuid
from pathlib import Path

router = APIRouter(prefix="/professors", tags=["Professors"])
UPLOAD_DIR = Path("uploads/tarefa_arquivos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/me", response_model=schemas.ProfessorPublic)
async def read_professor_me(
    current_user: models.Professor = Depends(auth.get_current_active_user)
):
    if not isinstance(current_user, models.Professor):
        raise HTTPException(status_code=403, detail="Not a professor account")
    return current_user

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
    if not isinstance(current_professor, models.Professor):
        raise HTTPException(status_code=403, detail="Acesso permitido apenas para professores.")
    
    students = await crud.get_estudantes(db, skip=0, limit=1000) 
    return students

@router.post("/me/convites-orientacao", response_model=schemas.ConviteOrientacaoPublic, status_code=status.HTTP_201_CREATED)
async def convidar_aluno_para_orientacao(
    convite_in: schemas.ConviteOrientacaoCreate,
    db: AsyncSession = Depends(get_db),
    current_professor: models.Professor = Depends(auth.get_current_active_user)
):
    """
    1. Professor: Convidar aluno para orientação.

    Envia um convite para um aluno para ser orientado em um TCC.
    O professor deve estar logado.
    """
    if not isinstance(current_professor, models.Professor):
        raise HTTPException(status_code=status.HTTP_403, detail="Apenas professores podem enviar convites.")

    estudante = await crud.get_estudante_by_id(db, convite_in.estudante_id)
    if not estudante:
        raise HTTPException(status_code=404, detail=f"Estudante com ID {convite_in.estudante_id} não encontrado.")

    existing_tcc = await crud.get_tccs_by_estudante_id(db, estudante.id)
    if existing_tcc:
        raise HTTPException(status_code=400, detail="Este estudante já possui um TCC registrado.")

    existing_invite = await crud.get_pending_convite_for_estudante(db, estudante.id)
    if existing_invite:
        raise HTTPException(status_code=400, detail="Este estudante já possui um convite de orientação pendente.")
    
    novo_convite = await crud.create_convite_orientacao(db=db, convite=convite_in, professor_id=current_professor.id)
    
    convite_completo = await crud.get_convite_by_id(db, novo_convite.id)
    return convite_completo

@router.get("/me/convites-orientacao", response_model=List[schemas.ConviteOrientacaoPublic])
async def get_meus_convites_enviados(
    db: AsyncSession = Depends(get_db),
    current_professor: models.Professor = Depends(auth.get_current_active_user)
):
    """
    Lista todos os convites de orientação enviados pelo professor logado.
    """
    if not isinstance(current_professor, models.Professor):
        raise HTTPException(status_code=403, detail="Acesso permitido apenas para professores.")
    
    convites = await crud.get_convites_by_professor_id(db, professor_id=current_professor.id)
    return convites


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

# MODIFICADO: Agora aceita um arquivo opcional ao criar a tarefa.
@router.post("/tccs/{tcc_id}/tarefas", response_model=schemas.TarefaPublic, status_code=status.HTTP_201_CREATED)
async def create_task_for_tcc(
    tcc_id: int,
    db: AsyncSession = Depends(get_db),
    current_professor: models.Professor = Depends(auth.get_current_active_user),
    titulo: str = Form(...),
    descricao: Optional[str] = Form(None),
    data_entrega: Optional[date] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    if not isinstance(current_professor, models.Professor):
        raise HTTPException(status_code=403, detail="Acesso permitido apenas para professores.")

    tcc = await crud.get_tcc_by_id(db, tcc_id)
    if not tcc:
        raise HTTPException(status_code=404, detail="TCC não encontrado.")
    if tcc.orientador_id != current_professor.id:
        raise HTTPException(status_code=403, detail="Você só pode criar tarefas para os TCCs que orienta.")
    
    tarefa_in = schemas.TarefaCreate(titulo=titulo, descricao=descricao, data_entrega=data_entrega)
    nova_tarefa = await crud.create_tarefa(db=db, tarefa=tarefa_in, tcc_id=tcc_id)
    
    if file:
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = UPLOAD_DIR / unique_filename
        
        try:
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())
        except Exception as e:
            # Em caso de falha no upload, a tarefa já foi criada.
            # O ideal seria uma transação completa, mas por simplicidade,
            # deixamos a tarefa criada e o professor pode adicionar o arquivo depois.
            raise HTTPException(status_code=500, detail=f"Tarefa criada, mas não foi possível salvar o arquivo: {e}")

        arquivo_in = schemas.ArquivoCreate(nome_arquivo=file.filename, caminho_arquivo=str(file_path))
        await crud.create_arquivo(db, arquivo=arquivo_in, tarefa_id=nova_tarefa.id)

    # Recarrega a tarefa para incluir o novo arquivo na resposta
    tarefa_completa = await crud.get_tarefa_by_id(db, nova_tarefa.id)
    return tarefa_completa


@router.put("/tarefas/{tarefa_id}", response_model=schemas.TarefaPublic)
async def update_task(
    tarefa_id: int,
    tarefa_update: schemas.TarefaUpdate,
    db: AsyncSession = Depends(get_db),
    current_professor: models.Professor = Depends(auth.get_current_active_user)
):
    if not isinstance(current_professor, models.Professor):
        raise HTTPException(status_code=403, detail="Acesso permitido apenas para professores.")
        
    tarefa = await crud.get_tarefa_by_id(db, tarefa_id)
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    if tarefa.tcc.orientador_id != current_professor.id:
        raise HTTPException(status_code=403, detail="Você só pode editar tarefas dos TCCs que orienta.")
        
    return await crud.update_tarefa(db=db, tarefa=tarefa, tarefa_update=tarefa_update)

@router.delete("/tarefas/{tarefa_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    tarefa_id: int,
    db: AsyncSession = Depends(get_db),
    current_professor: models.Professor = Depends(auth.get_current_active_user)
):
    if not isinstance(current_professor, models.Professor):
        raise HTTPException(status_code=403, detail="Acesso permitido apenas para professores.")
        
    tarefa = await crud.get_tarefa_by_id(db, tarefa_id)
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    if tarefa.tcc.orientador_id != current_professor.id:
        raise HTTPException(status_code=403, detail="Você só pode deletar tarefas dos TCCs que orienta.")

    await crud.delete_tarefa(db, tarefa=tarefa)
    return

# NOVO: Endpoint para professor enviar arquivo para uma tarefa existente
@router.post("/tarefas/{tarefa_id}/arquivos", response_model=schemas.ArquivoPublic, status_code=status.HTTP_201_CREATED)
async def professor_upload_file_for_task(
    tarefa_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_professor: models.Professor = Depends(auth.get_current_active_user)
):
    if not isinstance(current_professor, models.Professor):
        raise HTTPException(status_code=403, detail="Acesso permitido apenas para professores.")

    tarefa = await crud.get_tarefa_by_id(db, tarefa_id)
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    if tarefa.tcc.orientador_id != current_professor.id:
        raise HTTPException(status_code=403, detail="Você só pode enviar arquivos para tarefas dos TCCs que orienta.")

    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = UPLOAD_DIR / unique_filename
    
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível salvar o arquivo: {e}")

    arquivo_in = schemas.ArquivoCreate(
        nome_arquivo=file.filename,
        caminho_arquivo=str(file_path)
    )
    
    return await crud.create_arquivo(db=db, arquivo=arquivo_in, tarefa_id=tarefa_id)