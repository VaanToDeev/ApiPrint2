import requests

# URL da sua API - substitua pela URL correta
base_url = "http://localhost:8000"  # ou sua URL de produção
token_url = f"{base_url}/token"

# Dados de autenticação - use seus dados reais
username = "TioYaminho"
password = "jv140302"

# Formato correto para OAuth2PasswordRequestForm
data = {
    "username": username,
    "password": password
}

# Cabeçalhos - importante utilizar o Content-Type correto
headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

# Fazendo a requisição POST
response = requests.post(token_url, data=data, headers=headers)

# Verificando a resposta
if response.status_code == 200:
    token_data = response.json()
    access_token = token_data["access_token"]
    token_type = token_data["token_type"]
    print(f"Token obtido com sucesso: {token_type} {access_token}")
    
    # Teste de acesso a um endpoint protegido
    protected_url = f"{base_url}/users/me"
    auth_header = {"Authorization": f"Bearer {access_token}"}
    user_response = requests.get(protected_url, headers=auth_header)
    
    if user_response.status_code == 200:
        print("Acesso autenticado bem-sucedido!")
        print(user_response.json())
    else:
        print(f"Erro ao acessar endpoint protegido: {user_response.status_code}")
        print(user_response.text)
else:
    print(f"Erro ao obter token: {response.status_code}")
    print(response.text)