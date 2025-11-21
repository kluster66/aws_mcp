# -*- coding: utf-8 -*-
import logging
import os
import datetime
import boto3
from typing import Any
from mcp.server.fastmcp import FastMCP
from botocore.exceptions import ClientError, NoCredentialsError

# Initialisation
server = FastMCP("aws-mcp-server")

# --- Tes fonctions helpers ---
def _handle_aws_error(e: Exception, service: str) -> str:
    # (Garde ton code de gestion d'erreur ici, identique à avant)
    return f"Error {service}: {str(e)}"

# --- Tes Outils ---
@server.tool(name="list_s3_buckets")
def list_s3_buckets() -> Any:
    try:
        s3 = boto3.client('s3')
        response = s3.list_buckets()
        return [b["Name"] for b in response.get("Buckets", [])]
    except Exception as e:
        return _handle_aws_error(e, "S3")

@server.tool(name="list_ec2_instances")
def list_ec2_instances(region: str = "eu-west-3") -> Any:
    # (Garde ton code EC2 ici)
    try:
        ec2 = boto3.client('ec2', region_name=region)
        # ... ta logique ...
        return "Liste des instances..." 
    except Exception as e:
        return _handle_aws_error(e, "EC2")
    
@server.tool(name="get_monthly_cost")
def get_monthly_cost() -> Any:
    """
    Récupère le coût total AWS du mois en cours (Month-to-Date).
    Retourne le montant et la devise (USD).
    """
    try:
        # Client Cost Explorer
        ce = boto3.client('ce')
        
        # Calcul des dates : du 1er du mois à aujourd'hui
        now = datetime.datetime.now()
        start_date = now.replace(day=1).strftime('%Y-%m-%d')
        end_date = now.strftime('%Y-%m-%d')
        
        # Si on est le 1er du mois, Cost Explorer peut raler si start == end.
        # On recule d'un jour pour l'affichage si besoin, ou on gère l'exception.
        if start_date == end_date:
             return "Début de mois : pas encore assez de données pour calculer le coût."

        # Appel API
        response = ce.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost']
        )
        
        # Extraction propre pour le LLM
        result = response['ResultsByTime'][0]['Total']['UnblendedCost']
        amount = round(float(result['Amount']), 2)
        unit = result['Unit']
        
        return f"Coût total estimé ({start_date} au {end_date}) : {amount} {unit}"

    except Exception as e:
        return _handle_aws_error(e, "Cost Explorer")


@server.tool(name="get_cost_breakdown")
def get_cost_breakdown() -> Any:
    """
    Liste les 5 services les plus coûteux ce mois-ci.
    Utile pour comprendre où part l'argent (EC2, S3, RDS...).
    """
    try:
        ce = boto3.client('ce')
        
        # Dates
        now = datetime.datetime.now()
        start_date = now.replace(day=1).strftime('%Y-%m-%d')
        end_date = now.strftime('%Y-%m-%d')
        
        if start_date == end_date:
             return "Pas assez de données (1er du mois)."

        # Appel API avec GroupBy
        response = ce.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        # On nettoie et on trie pour avoir les plus gros consommateurs en premier
        services = []
        for item in response['ResultsByTime'][0]['Groups']:
            service_name = item['Keys'][0]
            amount = float(item['Metrics']['UnblendedCost']['Amount'])
            if amount > 0: # On ignore les services à 0$
                services.append({"Service": service_name, "Cost": amount})
        
        # Tri décroissant et Top 5
        services.sort(key=lambda x: x['Cost'], reverse=True)
        top_5 = services[:5]
        
        # Formatage lisible pour le LLM (arrondi)
        return [f"{s['Service']}: {round(s['Cost'], 2)}$" for s in top_5]

    except Exception as e:
        return _handle_aws_error(e, "Cost Explorer")

# C'EST TOUT. PAS DE "server.run()" À LA FIN.