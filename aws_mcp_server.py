# -*- coding: utf-8 -*-
"""
Serveur MCP (Model Context Protocol) pour l'interaction avec les services AWS.

Ce script utilise le framework FastMCP pour exposer des fonctions Python en tant qu'outils
accessibles via une API REST. Il fournit des outils pour interagir avec les services AWS
tels que S3 et EC2.

Prérequis:
- Les identifiants AWS (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) doivent être configurés
  en tant que variables d'environnement.
- Les dépendances Python (boto3, mcp) doivent être installées.

Le serveur démarre sur http://0.0.0.0:5001 par défaut.
"""

import logging
import os
print("Script started")
from typing import Optional, Dict, Any, List

import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from mcp.server.fastmcp.server import FastMCP

# --- Configuration du Logging ---
# Configure le logging pour écrire dans un fichier 'server.log'.
# Le niveau est réglé sur INFO pour capturer les événements importants.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Vérification des Identifiants AWS ---
# Il est crucial de vérifier la présence des identifiants AWS au démarrage.
# Si les variables d'environnement ne sont pas définies, un avertissement est émis.
# Le script continuera à fonctionner, mais les appels AWS échoueront.
if not os.getenv("AWS_ACCESS_KEY_ID") or not os.getenv("AWS_SECRET_ACCESS_KEY"):
    logging.warning("Les identifiants AWS (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) ne sont pas définis dans les variables d'environnement.")

# --- Test de création du client Boto3 ---
try:
    boto3.client('s3')
    logging.info("Client Boto3 créé avec succès.")
except (NoCredentialsError, PartialCredentialsError) as e:
    logging.error("Erreur de credentials Boto3: %s", e)
except Exception as e:
    logging.error("Une erreur inattendue est survenue lors de la création du client boto3: %s", e)

# --- Initialisation du Serveur MCP ---
server = FastMCP(
    "aws-mcp-server",
    host="0.0.0.0",
    port=5001
)
# --- Démarrage du Serveur ---
if __name__ == '__main__':
    logging.info("Démarrage du serveur MCP...")
    # La méthode run() lance le serveur et le fait écouter les requêtes entrantes.
    # Le serveur sera accessible sur l'URL configurée (par ex. http://localhost:5001).
    # Les outils seront listés sur http://localhost:5001/tools.
    server.run()
    logging.info("Le serveur MCP a été arrêté.")
while True:
    pass
print("Server initialized")

# --- Implémentation des Outils (Tools) ---

def _handle_aws_error(e: Exception, service: str) -> Dict[str, Any]:
    """
    Gère les exceptions courantes de boto3 et retourne un dictionnaire d'erreur standardisé.
    """
    if isinstance(e, (NoCredentialsError, PartialCredentialsError)):
        logging.error("Erreur d'authentification AWS pour le service %s: %s", service, e)
        return {"error": "Erreur d'authentification AWS. Veuillez configurer vos identifiants (credentials)."}
    if isinstance(e, ClientError):
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", "An unknown client error occurred.")
        logging.error("Erreur client AWS (%s) - Code: %s, Message: %s", service, error_code, error_message)
        return {"error": f"Erreur client AWS ({service}): {error_message} (Code: {error_code})"}
    
    logging.error("Une erreur inattendue est survenue (%s): %s", service, e)
    return {"error": f"Une erreur inattendue est survenue ({service}): {str(e)}"}


@server.tool(
    name="list_s3_buckets",
    description="Liste tous les compartiments (buckets) S3 dans le compte AWS."
)
def aws_list_s3_buckets() -> Dict[str, Any]:
    """
    Liste les noms de tous les buckets S3.
    
    :return: Un dictionnaire contenant une liste de noms de buckets ou une erreur.
    """
    logging.info("Exécution de l'outil 'list_s3_buckets'.")
    try:
        # La création du client à l'intérieur de la fonction permet une meilleure isolation
        # et garantit que chaque appel est indépendant.
        s3_client = boto3.client('s3')
        response = s3_client.list_buckets()
        
        # Extrait uniquement les noms pour une réponse plus propre et légère.
        bucket_names: List[str] = [bucket['Name'] for bucket in response.get('Buckets', [])]
        logging.info("Succès de la récupération de %d buckets S3.", len(bucket_names))
        
        return {"buckets": bucket_names}
    except Exception as e:
        return _handle_aws_error(e, "S3")


@server.tool(
    name="list_ec2_instances",
    description="Liste les instances EC2. Un filtre sur la région peut être appliqué."
)
def aws_list_ec2_instances(region: Optional[str] = None) -> Dict[str, Any]:
    """
    Liste les détails des instances EC2 pour une région donnée ou la région par défaut.
    
    :param region: Optionnel. La région AWS dans laquelle lister les instances (ex: 'us-east-1').
                   Si non spécifiée, la région par défaut configurée dans l'environnement sera utilisée.
    :return: Un dictionnaire contenant une liste de détails sur les instances ou une erreur.
    """
    logging.info("Exécution de l'outil 'list_ec2_instances' pour la région: %s.", region or "défaut")
    try:
        # Le client est créé avec la région spécifiée, ce qui est essentiel pour EC2.
        ec2_client = boto3.client('ec2', region_name=region) if region else boto3.client('ec2')
        response = ec2_client.describe_instances()
        
        instances_details: List[Dict[str, Any]] = []
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                instance_info = {
                    "InstanceId": instance.get('InstanceId'),
                    "InstanceType": instance.get('InstanceType'),
                    "State": instance.get('State', {}).get('Name'),
                    "PublicIpAddress": instance.get('PublicIpAddress', 'N/A'),
                    "PrivateIpAddress": instance.get('PrivateIpAddress', 'N/A'),
                    "Region": ec2_client.meta.region_name  # Ajoute la région à la réponse
                }
                instances_details.append(instance_info)
        
        logging.info("Succès de la récupération de %d instances EC2 dans la région %s.", len(instances_details), ec2_client.meta.region_name)
        return {"instances": instances_details}
    except Exception as e:
        return _handle_aws_error(e, "EC2")


@server.tool(
    name="health_check",
    description="Vérifie si le serveur MCP est opérationnel et répond."
)
def health_check() -> Dict[str, str]:
    """
    Un point d'entrée simple pour vérifier la santé du serveur.
    
    :return: Un dictionnaire indiquant que le service est 'ok'.
    """
    logging.info("Exécution de l'outil 'health_check'.")
    return {"status": "ok"}
