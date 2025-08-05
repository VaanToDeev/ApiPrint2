from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from app import models, schemas
from app.core.security import get_password_hash
from typing import Optional, List
from datetime import datetime

# --- Estudante CRUD ---
async def get_estudante_by_email(db: AsyncSession, email: str) -> Optional[models.Estudante]:
    result = await db.execute(select(models.Estudante).filter(models.Estudante.email == email))
    return result.scalars().first()

async def get_estudante_by_matricula(db: AsyncSession, matricula: str) -> Optional[models.Estudante]:
    result = await db.execute(select(models.Estudante).filter(models.Estudante.matricula == matricula))
    return result.scalars().first()

async def get_estudante_by_id(db: AsyncSession, estudante_id: int) -> Optional[models.Estudante]:
    result = await db.execute(select(models.Estudante).filter(models.Estudante.id == estudante_id))
    return result.scalars().first()

async def create_estudante(db: AsyncSession, estudante: schemas.EstudanteCreate) -> models.Estudante:
    hashed_password = get_password_hash(estudante.password)
    db_estudante = models.Estudante(
        nome=estudante.nome,
        email=estudante.email,
        hashed_password=hashed_password,
        matricula=estudante.matricula,
        turma=estudante.turma,
        telefone=estudante.telefone,
        curso_id=estudante.curso_id 
    )
    db.add(db_estudante)
    await db.commit()
    await db.refresh(db_estudante)
    return db_estudante

async def get_estudantes(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[models.Estudante]:
    result = await db.execute(select(models.Estudante).offset(skip).limit(limit))
    return result.scalars().all()

# NOVO: Função para deletar um estudante
async def delete_estudante(db: AsyncSession, estudante: models.Estudante):
    await db.delete(estudante)
    await db.commit()

# NOVO: Função para arquivar (inativar) um estudante
async def archive_estudante(db: AsyncSession, estudante: models.Estudante) -> models.Estudante:
    estudante.status = models.StatusEstudante.INATIVO
    await db.commit()
    await db.refresh(estudante)
    return estudante

# NOVO: Função para buscar estudantes por curso e, opcionalmente, por turma
async def get_estudantes_by_curso_and_turma(
    db: AsyncSession, curso_id: int, turma: Optional[str] = None
) -> List[models.Estudante]:
    query = select(models.Estudante).where(models.Estudante.curso_id == curso_id)
    if turma:
        query = query.where(models.Estudante.turma == turma)
    result = await db.execute(query.order_by(models.Estudante.nome))
    return result.scalars().all()


# --- Professor CRUD ---
# MODIFICADO: Adicionado selectinload para otimizar o carregamento do curso coordenado
async def get_professor_by_email(db: AsyncSession, email: str) -> Optional[models.Professor]:
    result = await db.execute(
        select(models.Professor)
        .options(selectinload(models.Professor.curso_coordenado))
        .filter(models.Professor.email == email)
    )
    return result.scalars().first()

async def get_professor_by_siape(db: AsyncSession, siape: str) -> Optional[models.Professor]:
    result = await db.execute(select(models.Professor).filter(models.Professor.siape == siape))
    return result.scalars().first()

async def get_professor_by_id(db: AsyncSession, professor_id: int) -> Optional[models.Professor]:
    result = await db.execute(select(models.Professor).filter(models.Professor.id == professor_id))
    return result.scalars().first()

async def create_professor(db: AsyncSession, professor: schemas.ProfessorCreate, role: models.UserRole = models.UserRole.PROFESSOR) -> models.Professor:
    hashed_password = get_password_hash(professor.password)
    db_professor = models.Professor(
        nome=professor.nome,
        email=professor.email,
        hashed_password=hashed_password,
        siape=professor.siape,
        departamento=professor.departamento,
        titulacao=professor.titulacao,
        telefone=professor.telefone,
        role=role 
    )
    db.add(db_professor)
    await db.commit()
    await db.refresh(db_professor)
    return db_professor

async def get_professores(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[models.Professor]:
    result = await db.execute(select(models.Professor).offset(skip).limit(limit))
    return result.scalars().all()

async def update_professor_role(db: AsyncSession, professor_id: int, new_role: models.UserRole) -> Optional[models.Professor]:
    db_professor = await get_professor_by_id(db, professor_id)
    if db_professor:
        db_professor.role = new_role
        await db.commit()
        await db.refresh(db_professor)
    return db_professor

async def get_professores_by_departamento(db: AsyncSession, departamento: str):
    result = await db.execute(
        select(models.Professor).where(models.Professor.departamento == departamento)
    )
    return result.scalars().all()

# NOVO: Função para deletar um professor
async def delete_professor(db: AsyncSession, professor: models.Professor):
    await db.delete(professor)
    await db.commit()

# NOVO: Função para arquivar (inativar) um professor
async def archive_professor(db: AsyncSession, professor: models.Professor) -> models.Professor:
    professor.status = models.StatusProfessor.INATIVO
    await db.commit()
    await db.refresh(professor)
    return professor

# --- Curso CRUD ---
async def get_curso_by_id(db: AsyncSession, curso_id: int) -> Optional[models.Curso]:
    result = await db.execute(select(models.Curso).filter(models.Curso.id_curso == curso_id))
    return result.scalars().first()

async def get_curso_by_nome(db: AsyncSession, nome_curso: str) -> Optional[models.Curso]:
    result = await db.execute(select(models.Curso).filter(models.Curso.nome_curso == nome_curso))
    return result.scalars().first()

async def create_curso(db: AsyncSession, curso: schemas.CursoCreate) -> models.Curso:
    db_curso = models.Curso(nome_curso=curso.nome_curso)
    db.add(db_curso)
    await db.commit()
    await db.refresh(db_curso)
    return db_curso

async def update_curso(db: AsyncSession, curso_id: int, curso_in: schemas.CursoUpdate) -> Optional[models.Curso]:
    db_curso = await get_curso_by_id(db, curso_id)
    if db_curso:
        update_data = curso_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_curso, key, value)
        await db.commit()
        await db.refresh(db_curso)
    return db_curso

async def get_cursos(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(models.Curso).options(joinedload(models.Curso.coordenador)).offset(skip).limit(limit)
    )
    return result.scalars().all()

async def assign_coordenador_to_curso(db: AsyncSession, curso_id: int, professor_id: int) -> Optional[models.Curso]:
    db_curso = await get_curso_by_id(db, curso_id)
    db_professor = await get_professor_by_id(db, professor_id)
    if not db_curso or not db_professor:
        return None
    db_curso.coordenador_id = professor_id
    await db.commit()
    await db.refresh(db_curso)
    return db_curso

# --- TCC CRUD ---
async def create_tcc(db: AsyncSession, tcc_in: schemas.TCCCreate, orientador_id: int) -> models.TCC:
    db_tcc = models.TCC(
        **tcc_in.model_dump(),
        orientador_id=orientador_id
    )
    db.add(db_tcc)
    await db.commit()
    await db.refresh(db_tcc)
    return db_tcc

async def get_tcc_by_id(db: AsyncSession, tcc_id: int) -> Optional[models.TCC]:
    result = await db.execute(select(models.TCC).options(selectinload(models.TCC.files)).filter(models.TCC.id == tcc_id))
    return result.scalars().first()

async def get_tccs_by_estudante_id(db: AsyncSession, estudante_id: int) -> List[models.TCC]:
    result = await db.execute(select(models.TCC).filter(models.TCC.estudante_id == estudante_id))
    return result.scalars().all()

async def get_tccs_by_orientador_id(db: AsyncSession, orientador_id: int) -> List[models.TCC]:
    result = await db.execute(select(models.TCC).filter(models.TCC.orientador_id == orientador_id))
    return result.scalars().all()

# --- Convite de Orientação CRUD ---
async def create_convite_orientacao(db: AsyncSession, convite: schemas.ConviteOrientacaoCreate, professor_id: int) -> models.OrientacaoConvite:
    db_convite = models.OrientacaoConvite(
        titulo_proposto=convite.titulo_proposto,
        descricao_proposta=convite.descricao_proposta,
        estudante_id=convite.estudante_id,
        professor_id=professor_id
    )
    db.add(db_convite)
    await db.commit()
    await db.refresh(db_convite)
    return db_convite

async def get_convite_by_id(db: AsyncSession, convite_id: int) -> Optional[models.OrientacaoConvite]:
    result = await db.execute(
        select(models.OrientacaoConvite)
        .options(
            selectinload(models.OrientacaoConvite.professor),
            selectinload(models.OrientacaoConvite.estudante)
        )
        .filter(models.OrientacaoConvite.id == convite_id)
    )
    return result.scalars().first()

async def get_convites_by_estudante_id(db: AsyncSession, estudante_id: int) -> List[models.OrientacaoConvite]:
    result = await db.execute(
        select(models.OrientacaoConvite)
        .options(
            selectinload(models.OrientacaoConvite.professor),
            selectinload(models.OrientacaoConvite.estudante)
        )
        .where(models.OrientacaoConvite.estudante_id == estudante_id)
        .order_by(models.OrientacaoConvite.data_convite.desc())
    )
    return result.scalars().all()

async def get_convites_by_professor_id(db: AsyncSession, professor_id: int) -> List[models.OrientacaoConvite]:
    result = await db.execute(
        select(models.OrientacaoConvite)
        .options(
            selectinload(models.OrientacaoConvite.professor),
            selectinload(models.OrientacaoConvite.estudante)
        )
        .where(models.OrientacaoConvite.professor_id == professor_id)
        .order_by(models.OrientacaoConvite.data_convite.desc())
    )
    return result.scalars().all()

async def update_convite_orientacao(db: AsyncSession, convite: models.OrientacaoConvite, update_data: schemas.ConviteOrientacaoUpdate) -> models.OrientacaoConvite:
    convite.status = update_data.status
    convite.data_resposta = datetime.utcnow()
    db.add(convite)
    await db.commit()
    await db.refresh(convite)
    return convite

async def get_pending_convite_for_estudante(db: AsyncSession, estudante_id: int) -> Optional[models.OrientacaoConvite]:
    result = await db.execute(
        select(models.OrientacaoConvite).filter(
            models.OrientacaoConvite.estudante_id == estudante_id,
            models.OrientacaoConvite.status == models.StatusConvite.PENDENTE
        )
    )
    return result.scalars().first()

# --- TCCFile CRUD ---
async def create_tcc_file(db: AsyncSession, tcc_file_in: schemas.TCCFileCreate) -> models.TCCFile:
    db_tcc_file = models.TCCFile(**tcc_file_in.model_dump())
    db.add(db_tcc_file)
    await db.commit()
    await db.refresh(db_tcc_file)
    return db_tcc_file

async def get_tcc_files_by_tcc_id(db: AsyncSession, tcc_id: int) -> List[models.TCCFile]:
    result = await db.execute(select(models.TCCFile).filter(models.TCCFile.tcc_id == tcc_id))
    return result.scalars().all()

async def get_orientandos_by_professor_id(db: AsyncSession, professor_id: int):
    subquery = select(models.TCC.estudante_id).where(models.TCC.orientador_id == professor_id).scalar_subquery()
    result = await db.execute(
        select(models.Estudante).where(models.Estudante.id.in_(subquery))
    )
    return result.scalars().all()

async def create_arquivo(db: AsyncSession, arquivo: schemas.ArquivoCreate, tarefa_id: int) -> models.Arquivo:
    db_arquivo = models.Arquivo(
        **arquivo.model_dump(),
        tarefa_id=tarefa_id
    )
    db.add(db_arquivo)
    await db.commit()
    await db.refresh(db_arquivo)
    return db_arquivo

# --- Tarefa CRUD ---
async def create_tarefa(db: AsyncSession, tarefa: schemas.TarefaCreate, tcc_id: int) -> models.Tarefa:
    db_tarefa = models.Tarefa(
        **tarefa.model_dump(),
        tcc_id=tcc_id,
        status=models.StatusTarefa.A_FAZER
    )
    db.add(db_tarefa)
    await db.commit()
    await db.refresh(db_tarefa)
    return await get_tarefa_by_id(db, db_tarefa.id)

async def get_tarefa_by_id(db: AsyncSession, tarefa_id: int) -> Optional[models.Tarefa]:
    result = await db.execute(
        select(models.Tarefa)
        .options(
            selectinload(models.Tarefa.tcc), 
            selectinload(models.Tarefa.arquivos)
        )
        .where(models.Tarefa.id == tarefa_id)
    )
    return result.scalars().first()

async def get_tarefas_by_tcc_id(db: AsyncSession, tcc_id: int) -> List[models.Tarefa]:
    result = await db.execute(
        select(models.Tarefa).options(selectinload(models.Tarefa.arquivos)).where(models.Tarefa.tcc_id == tcc_id)
    )
    return result.scalars().all()

async def update_tarefa(db: AsyncSession, tarefa: models.Tarefa, tarefa_update: schemas.TarefaUpdate) -> models.Tarefa:
    update_data = tarefa_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tarefa, key, value)
    db.add(tarefa)
    await db.commit()
    await db.refresh(tarefa)
    return await get_tarefa_by_id(db, tarefa.id)

async def delete_tarefa(db: AsyncSession, tarefa: models.Tarefa) -> bool:
    if tarefa:
        await db.delete(tarefa)
        await db.commit()
        return True
    return False

# --- Admin Arquivo CRUD ---
async def create_admin_arquivo(db: AsyncSession, arquivo_in: schemas.AdminArquivoCreate) -> models.AdminArquivo:
    db_arquivo = models.AdminArquivo(**arquivo_in.model_dump())
    db.add(db_arquivo)
    await db.commit()
    await db.refresh(db_arquivo)
    return await db.get(models.AdminArquivo, db_arquivo.id, options=[selectinload(models.AdminArquivo.uploader)])

async def get_admin_arquivos(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[models.AdminArquivo]:
    result = await db.execute(
        select(models.AdminArquivo)
        .options(selectinload(models.AdminArquivo.uploader))
        .offset(skip)
        .limit(limit)
        .order_by(models.AdminArquivo.data_upload.desc())
    )
    return result.scalars().all()