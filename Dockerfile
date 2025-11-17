# Utiliser une image Python officielle comme image de base
FROM python:3.10-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier des dépendances dans le répertoire de travail
COPY requirements.txt .

# Installer les dépendances
# --no-cache-dir pour ne pas stocker le cache pip et réduire la taille de l'image
# --trusted-host pypi.python.org pour éviter les problèmes de SSL dans certains environnements
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

# Copier le reste du code de l'application
COPY . .

# Exposer le port sur lequel le serveur MCP écoute
EXPOSE 5001

# La commande pour lancer l'application lorsque le conteneur démarre
CMD ["python", "aws_mcp_server.py"]
