import requests

# URL da API
base_url = "http://localhost:8000"

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

def testar_acesso(token, descricao, url, metodo="GET", data=None):
    """Função auxiliar para testar acesso às rotas"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    if metodo == "GET":
        response = requests.get(url, headers=headers)
    elif metodo == "PUT":
        response = requests.put(url, headers=headers, json=data)
    elif metodo == "DELETE":
        response = requests.delete(url, headers=headers)
    
    print(f"\n{descricao}")
    print(f"Status: {response.status_code}")
    if response.status_code != 204:  # No Content
        print(f"Resposta: {response.text}")
    print("-" * 50)

def main():
    # Fazer login com diferentes tipos de usuários
    print("Obtendo tokens de acesso...")
    token_coord = fazer_login("coordenador", "Coord@123")
    token_prof = fazer_login("prof.silva", "Prof@123")
    token_aluno = fazer_login("joao.aluno", "Aluno@123")

    # Testar acesso como coordenador
    print("\n=== TESTANDO ACESSO COMO COORDENADOR ===")
    if token_coord:
        # Listar todos os usuários
        testar_acesso(token_coord, "Coordenador tentando listar todos os usuários", f"{base_url}/users/")
        
        # Ver dados de outro usuário
        testar_acesso(token_coord, "Coordenador tentando ver dados de um professor", f"{base_url}/users/2")
        
        # Editar outro usuário
        dados_atualizacao = {"full_name": "Professor Silva Atualizado"}
        testar_acesso(token_coord, "Coordenador tentando editar um professor", f"{base_url}/users/2", "PUT", dados_atualizacao)

    # Testar acesso como professor
    print("\n=== TESTANDO ACESSO COMO PROFESSOR ===")
    if token_prof:
        # Tentar listar todos os usuários (deve falhar)
        testar_acesso(token_prof, "Professor tentando listar todos os usuários", f"{base_url}/users/")
        
        # Ver seus próprios dados (deve funcionar)
        testar_acesso(token_prof, "Professor tentando ver seus próprios dados", f"{base_url}/users/me")
        
        # Tentar ver dados de outro usuário (deve falhar)
        testar_acesso(token_prof, "Professor tentando ver dados de um aluno", f"{base_url}/users/3")

    # Testar acesso como aluno
    print("\n=== TESTANDO ACESSO COMO ALUNO ===")
    if token_aluno:
        # Tentar listar todos os usuários (deve falhar)
        testar_acesso(token_aluno, "Aluno tentando listar todos os usuários", f"{base_url}/users/")
        
        # Ver seus próprios dados (deve funcionar)
        testar_acesso(token_aluno, "Aluno tentando ver seus próprios dados", f"{base_url}/users/me")
        
        # Tentar ver dados de outro usuário (deve falhar)
        testar_acesso(token_aluno, "Aluno tentando ver dados de um professor", f"{base_url}/users/2")

if __name__ == "__main__":
    main() 