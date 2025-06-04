# Use uma imagem base oficial do Python
FROM python:3.12-slim

# Defina o diretório de trabalho no container
WORKDIR /app

# Copie o arquivo de dependências primeiro para aproveitar o cache do Docker
COPY requirements.txt requirements.txt

# Instale as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copie o restante do código da sua aplicação para o diretório de trabalho
COPY ./app /app/app

# Comando para executar a aplicação (ajuste se necessário)
# EXPOSE 8000 # Opcional, pois o docker-compose já faz o mapeamento
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
