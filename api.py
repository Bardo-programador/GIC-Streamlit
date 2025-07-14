import requests
import json
import pandas as pd


def extract_data():
    API_URL = "https://pncp.gov.br/api/search/?q=Cidades%20Inteligentes&tipos_documento=contrato&ordenacao=-data&pagina=1&tam_pagina=100&status=todos&tipos_contrato=3%7C12%7C2%7C4%7C6%7C7%7C8%7C5%7C11%7C1"
    page_number = 2
    response = requests.get(API_URL)
    data = json.loads(response.text)

    total_absoluto = data['total']
    total_restante = total_absoluto - len(data['items'])
    

    while total_restante > 0:
        response = requests.get(API_URL+f"&pagina={page_number}")
        response = json.loads(response.text)
        data["items"].extend(response["items"])
        total_restante -= len(response['items'])
        page_number += 1

    if total_restante == 0 and len(data["items"]) == total_absoluto:
        print("Tudo certo")
        return data['items']
    else:
        print("Algo deu errado")
        print(f"""
        Total absoluto = {total_absoluto}
        Numero de Items coletados = {len(data["items"])}
        Items faltando = {total_restante}
        Pagina atual = {page_number}           
        """)
