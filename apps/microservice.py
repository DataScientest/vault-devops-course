# microservice.py

import os
import requests
from fastapi import FastAPI
from pymongo import MongoClient

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://vault:8200")

ROLE_ID = os.getenv("ROLE_ID")
SECRET_ID = os.getenv("SECRET_ID")

app = FastAPI()


# Authentification AppRole
def get_vault_token():

    url = f"{VAULT_ADDR}/v1/auth/approle/login"

    payload = {
        "role_id": ROLE_ID,
        "secret_id": SECRET_ID
    }

    response = requests.post(url, json=payload)

    return response.json()["auth"]["client_token"]


# Récupération credentials MongoDB dynamiques
def get_mongo_creds(token):

    url = f"{VAULT_ADDR}/v1/database/creds/mongo-role"

    headers = {
        "X-Vault-Token": token
    }

    response = requests.get(url, headers=headers)

    data = response.json()["data"]

    return {
        "username": data["username"],
        "password": data["password"]
    }


@app.get("/")
def root():

    # Auth Vault
    token = get_vault_token()

    # Dynamic creds MongoDB
    creds = get_mongo_creds(token)

    username = creds["username"]
    password = creds["password"]

    # Connexion MongoDB
    mongo_uri = (
        f"mongodb://{username}:{password}"
        f"@mongo:27017/schooldb?authSource=admin"
    )

    client = MongoClient(mongo_uri)

    db = client["schooldb"]

    ecoles = db["ecoles"]

    # Recherche Liora
    liora = ecoles.find_one({"nom": "Liora"})

    if liora:

        return {
            "message": "Connexion MongoDB via Vault AppRole réussie",
            "nom": liora["nom"],
            "adresse": liora["adresse"],
            "produit": liora["produit"],
            "vault_username": username
        }

    return {
        "message": "Ecole non trouvée"
    }
