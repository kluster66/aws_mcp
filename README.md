# Serveur MCP pour AWS avec Docker

Ce projet est un serveur MCP (Model Context Protocol) qui expose des fonctionnalités AWS (lister les buckets S3, lister les instances EC2) via une API REST. Il est construit en Python avec la bibliothèque `mcp` et est conçu pour être déployé facilement avec Docker.

## Prérequis

1.  **Docker et Docker Compose** : Assurez-vous qu'ils sont installés sur votre machine.
2.  **Configuration des identifiants AWS** : Le serveur utilise `boto3`, qui a besoin de vos identifiants AWS. La méthode recommandée est d'avoir votre fichier `~/.aws/credentials` configuré. Le fichier `docker-compose.yml` est déjà configuré pour monter ce répertoire dans le conteneur.

    Ne codez **jamais** vos identifiants en dur dans le code.

## Lancement du serveur avec Docker Compose

La méthode recommandée pour lancer le serveur est d'utiliser Docker Compose.

1.  **Accédez au répertoire du projet :**
    ```bash
    cd aws_mcp
    ```

2.  **Lancez le service :**
    Cette commande va construire l'image Docker (si elle n'existe pas) et démarrer le conteneur en arrière-plan.
    ```bash
    docker-compose up --build -d
    ```

Le serveur est maintenant en cours d'exécution et accessible sur `http://localhost:5001`.

### Commandes utiles Docker Compose

*   **Pour voir les logs du serveur :**
    ```bash
    docker-compose logs -f
    ```

*   **Pour arrêter et supprimer le conteneur :**
    ```bash
    docker-compose down
    ```

## Points d'entrée (Endpoints) du Protocole

Le serveur implémente le Model Context Protocol via les points d'entrée standard gérés par la bibliothèque `mcp`.

### 1. Découverte des outils (`/tools`)

Permet de lister les outils disponibles et leur schéma.

*   **URL** : `/tools`
*   **Méthode** : `GET`
*   **Réponse** : Un JSON contenant la liste des outils, leur description et leurs paramètres.

**Exemple avec `curl`:**
```bash
curl http://localhost:5001/tools
```

### 2. Exécution d'un outil (`/execute`)

Permet de lancer un outil spécifique avec des arguments.

*   **URL** : `/execute`
*   **Méthode** : `POST`
*   **Corps de la requête (Body)** : Un JSON spécifiant le nom de l'outil et ses arguments.
    ```json
    {
      "tool_name": "nom_de_l_outil",
      "arguments": {
        "param1": "valeur1"
      }
    }
    ```
*   **Réponse** : Un JSON contenant le résultat de l'exécution de l'outil.

**Exemples avec `curl`:**

*   **Lister les buckets S3 :**
    ```bash
    curl -X POST -H "Content-Type: application/json" \
         -d '{"tool_name": "list_s3_buckets"}' \
         http://localhost:5001/execute
    ```

*   **Lister les instances EC2 dans une région spécifique :**
    ```bash
    curl -X POST -H "Content-Type: application/json" \
         -d '{"tool_name": "list_ec2_instances", "arguments": {"region": "us-west-2"}}' \
         http://localhost:5001/execute
    ```