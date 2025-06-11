from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from app import models, schemas
from app.core.security import get_password_hash
from typing import Optional, List

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

# --- Professor CRUD ---
async def get_professor_by_email(db: AsyncSession, email: str) -> Optional[models.Professor]:
    result = await db.execute(select(models.Professor).filter(models.Professor.email == email))
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
        update_data = curso_in.model_dump(exclude_unset=True) # Usar model_dump para Pydantic v2
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
async def create_tcc(db: AsyncSession, tcc_in: schemas.TCCCreate) -> models.TCC:
    db_tcc = models.TCC(**tcc_in.model_dump()) # Usar model_dump para Pydantic v2
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

# --- TCCFile CRUD ---
async def create_tcc_file(db: AsyncSession, tcc_file_in: schemas.TCCFileCreate) -> models.TCCFile:
    db_tcc_file = models.TCCFile(**tcc_file_in.model_dump()) # Usar model_dump para Pydantic v2
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
