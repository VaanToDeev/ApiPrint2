import requests
import json

# URL da sua API - substitua pela URL correta
base_url = "http://localhost:8000"

def criar_usuario(dados_usuario):
    """Função auxiliar para criar usuário"""
    response = requests.post(f"{base_url}/users/", json=dados_usuario)
    if response.status_code == 201:
        print(f"Usuário {dados_usuario['username']} criado com sucesso!")
        return response.json()
    else:
        print(f"Erro ao criar usuário {dados_usuario['username']}: {response.status_code}")
        print(response.text)
        return None

def fazer_login(username, password):
    """Função auxiliar para fazer login e obter token"""
    data = {
        "username": username,
        "password": password
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(f"{base_url}/token", data=data, headers=headers)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Erro ao obter token: {response.status_code}")
        print(response.text)
        return None

# Criar coordenador
coordenador = {
    "email": "coordenador@faculdade.com",
    "username": "coordenador",
    "full_name": "Coordenador do Curso",
    "password": "Coord@123",
    "user_type": "coordenador"
}

# Criar o coordenador primeiro
coord_criado = criar_usuario(coordenador)
if coord_criado:
    # Obter token do coordenador
    token_coord = fazer_login("coordenador", "Coord@123")
    
    if token_coord:
        # Headers com autorização para criar outros usuários
        headers_auth = {"Authorization": f"Bearer {token_coord}"}
        
        # Lista de professores para criar
        professores = [
            {
                "email": "prof.silva@faculdade.com",
                "username": "prof.silva",
                "full_name": "Professor Silva",
                "password": "Prof@123",
                "user_type": "professor"
            },
            {
                "email": "prof.santos@faculdade.com",
                "username": "prof.santos",
                "full_name": "Professora Santos",
                "password": "Prof@456",
                "user_type": "professor"
            }
        ]
        
        # Lista de alunos para criar
        alunos = [
            {
                "email": "joao@aluno.faculdade.com",
                "username": "joao.aluno",
                "full_name": "João da Silva",
                "password": "Aluno@123",
                "user_type": "aluno"
            },
            {
                "email": "maria@aluno.faculdade.com",
                "username": "maria.aluno",
                "full_name": "Maria Oliveira",
                "password": "Aluno@456",
                "user_type": "aluno"
            },
            {
                "email": "pedro@aluno.faculdade.com",
                "username": "pedro.aluno",
                "full_name": "Pedro Santos",
                "password": "Aluno@789",
                "user_type": "aluno"
            }
        ]
        
        # Criar professores
        print("\nCriando professores...")
        for professor in professores:
            criar_usuario(professor)
        
        # Criar alunos
        print("\nCriando alunos...")
        for aluno in alunos:
            criar_usuario(aluno)
        
        # Testar listagem de usuários
        print("\nListando todos os usuários (como coordenador)...")
        response = requests.get(f"{base_url}/users/", headers=headers_auth)
        if response.status_code == 200:
            usuarios = response.json()
            print(f"Total de usuários cadastrados: {len(usuarios)}")
            for usuario in usuarios:
                print(f"- {usuario['full_name']} ({usuario['user_type']})")
        else:
            print(f"Erro ao listar usuários: {response.status_code}")
            print(response.text)