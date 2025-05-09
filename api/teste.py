import requests

# URL da sua API - substitua pela URL correta
base_url = "http://localhost:8000"  # ou sua URL de produção
token_url = f"{base_url}/token"

# Dados de autenticação
payload = {
    "username": "seu_usuario",
    "password": "sua_senha"
}

# Cabeçalhos - importante utilizar o Content-Type correto
headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

# Fazendo a requisição POST
response = requests.post(token_url, data=payload, headers=headers)

# Verificando a resposta
if response.status_code == 200:
    token_data = response.json()
    access_token = token_data["access_token"]
    token_type = token_data["token_type"]
    print(f"Token obtido com sucesso: {token_type} {access_token}")
else:
    print(f"Erro ao obter token: {response.status_code}")
    print(response.text)