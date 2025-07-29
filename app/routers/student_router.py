from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud, models, auth
from app.database import get_db
from typing import List
import os
import uuid
from pathlib import Path
from datetime import datetime

router = APIRouter(prefix="/students", tags=["Students"])

UPLOAD_DIR = Path("uploads/tcc_files")
ALLOWED_FILE_TYPES = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

@router.get("/me", response_model=schemas.EstudantePublic)
async def read_student_me(
    current_user: models.Estudante = Depends(auth.get_current_active_user)
):
    if not isinstance(current_user, models.Estudante):
        raise HTTPException(status_code=403, detail="Not a student account")
    return current_user

# NOVO: Endpoint para listar todos os professores para um aluno logado.
@router.get("/professors", response_model=List[schemas.ProfessorPublic])
async def list_all_professors_for_student(
    db: AsyncSession = Depends(get_db),
    current_student: models.Estudante = Depends(auth.get_current_active_user)
):
    """
    Lista todos os professores cadastrados no sistema.
    Acesso permitido para qualquer estudante autenticado.
    """
    if not isinstance(current_student, models.Estudante):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso permitido apenas para estudantes.")
    
    professores = await crud.get_professores(db, skip=0, limit=1000) # Limite alto para buscar todos
    return professores

@router.get("/me/convites-orientacao", response_model=List[schemas.ConviteOrientacaoPublic])
async def get_meus_convites_recebidos(
    db: AsyncSession = Depends(get_db),
    current_student: models.Estudante = Depends(auth.get_current_active_user)
):
    """
    Lista todos os convites de orientação recebidos pelo estudante logado.
    """
    if not isinstance(current_student, models.Estudante):
        raise HTTPException(status_code=403, detail="Acesso permitido apenas para contas de estudante.")
    
    convites = await crud.get_convites_by_estudante_id(db, estudante_id=current_student.id)
    return convites

@router.post("/me/convites-orientacao/{convite_id}/responder", response_model=schemas.ConviteRespostaPublic)
async def responder_convite_orientacao(
    convite_id: int,
    resposta: schemas.ConviteOrientacaoUpdate,
    db: AsyncSession = Depends(get_db),
    current_student: models.Estudante = Depends(auth.get_current_active_user)
):
    """
    2. Aluno: Aceitar/Recusar convite de orientação.

    Permite que o estudante logado aceite ou recuse um convite pendente.
    Se o convite for aceito, um novo TCC é criado automaticamente e retornado na resposta.
    """
    if not isinstance(current_student, models.Estudante):
        raise HTTPException(status_code=403, detail="Acesso permitido apenas para contas de estudante.")

    convite = await crud.get_convite_by_id(db, convite_id)
    if not convite:
        raise HTTPException(status_code=404, detail="Convite não encontrado.")
    if convite.estudante_id != current_student.id:
        raise HTTPException(status_code=403, detail="Este convite não pertence a você.")
    if convite.status != models.StatusConvite.PENDENTE:
        raise HTTPException(status_code=400, detail=f"Este convite já foi respondido com o status '{convite.status.value}'.")
    if resposta.status not in [models.StatusConvite.ACEITO, models.StatusConvite.RECUSADO]:
        raise HTTPException(status_code=400, detail="A resposta deve ser 'aceito' ou 'recusado'.")

    novo_tcc = None

    if resposta.status == models.StatusConvite.ACEITO:
        existing_tcc = await crud.get_tccs_by_estudante_id(db, current_student.id)
        if existing_tcc:
            raise HTTPException(status_code=409, detail="Conflito: Você já possui um TCC registrado e não pode aceitar um novo convite.")

    # Atualiza o status do convite no banco de dados
    await crud.update_convite_orientacao(db, convite=convite, update_data=resposta)

    # Se foi aceito, cria o TCC
    if resposta.status == models.StatusConvite.ACEITO:
        tcc_in = schemas.TCCCreate(
            titulo=convite.titulo_proposto,
            descricao=convite.descricao_proposta,
            estudante_id=convite.estudante_id,
        )
        novo_tcc = await crud.create_tcc(db=db, tcc_in=tcc_in, orientador_id=convite.professor_id)

    # CORREÇÃO: Busca novamente o convite pelo ID para garantir que todos os relacionamentos
    # (professor, estudante) sejam carregados pelo `selectinload` presente em `crud.get_convite_by_id`.
    # Isso resolve o erro `MissingGreenlet`.
    convite_completo = await crud.get_convite_by_id(db, convite_id)

    return schemas.ConviteRespostaPublic(convite=convite_completo, tcc=novo_tcc)


@router.get("/me/tccs", response_model=List[schemas.TCCPublic])
async def get_my_tccs(
    db: AsyncSession = Depends(get_db),
    current_student: models.Estudante = Depends(auth.get_current_active_user)
):
    if not isinstance(current_student, models.Estudante):
        raise HTTPException(status_code=403, detail="Acesso permitido apenas para contas de estudante.")
    
    tccs = await crud.get_tccs_by_estudante_id(db, estudante_id=current_student.id)
    return tccs

@router.post("/tccs/{tcc_id}/upload_file", response_model=schemas.TCCFilePublic, status_code=status.HTTP_201_CREATED)
async def upload_tcc_file(
    tcc_id: int,
    file: UploadFile = File(...),
    current_user: models.Estudante = Depends(auth.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if not isinstance(current_user, models.Estudante):
        raise HTTPException(status_code=403, detail="Apenas estudantes podem fazer upload de arquivos de TCC.")

    tcc = await crud.get_tcc_by_id(db, tcc_id)
    if not tcc:
        raise HTTPException(status_code=404, detail="TCC não encontrado.")
    
    if tcc.estudante_id != current_user.id:
        raise HTTPException(status_code=403, detail="Você só pode fazer upload de arquivos para seus próprios TCCs.")

    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de arquivo inválido. Tipos permitidos são: {', '.join([ft.split('/')[-1] for ft in ALLOWED_FILE_TYPES])}"
        )

    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"O tamanho do arquivo excede o limite de {MAX_FILE_SIZE_MB}MB."
        )
    
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = UPLOAD_DIR / unique_filename

    try:
        with open(file_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                buffer.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível salvar o arquivo: {e}")

    tcc_file_in_db = schemas.TCCFileCreate(
        tcc_id=tcc_id,
        filename=file.filename,
        filepath=str(file_path),
        filetype=file.content_type,
    )
    db_tcc_file = await crud.create_tcc_file(db, tcc_file_in=tcc_file_in_db)

    return db_tcc_file

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
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    if tarefa.tcc.estudante_id != current_student.id:
        raise HTTPException(status_code=403, detail="Você só pode enviar arquivos para suas próprias tarefas.")
        
    unique_id = uuid.uuid4()
    file_extension = Path(file.filename).suffix
    unique_filename = f"{unique_id}{file_extension}"
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
    
    await crud.update_tarefa(db, tarefa, schemas.TarefaUpdate(status=models.StatusTarefa.FEITA))
    
    return await crud.create_arquivo(db, arquivo=arquivo_in, tarefa_id=tarefa_id)