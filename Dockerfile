FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# CORRECTION OFFICIELLE : On ajoute le dossier d'installation de pip au PATH
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Installation
RUN pip install --no-cache-dir boto3 uvicorn fastmcp

# Copie du code
COPY aws_mcp_server.py .

EXPOSE 8000

# COMMANDE OFFICIELLE (Telle que décrite dans le Wiki)
# Le CLI 'fastmcp' va :
# 1. Charger ton fichier
# 2. Trouver l'objet 'server'
# 3. Lancer un serveur web Uvicorn optimisé SSE
CMD ["fastmcp", "run", "aws_mcp_server.py", "--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]