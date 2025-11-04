# Docs teste -> base64 -> envio para API -> registro do correlation_id -> salvar logs

import os
import base64
import json
import requests
import pandas as pd
from typing import List, Dict, Any

# ----------------------------------------------------------------------
# CONFIGURAÇÕES GLOBAIS
# ----------------------------------------------------------------------

SUBSCRIPTION_KEY = "0161a5c0261a481ab732f184fab7d592"
AUTHORIZATION_TOKEN = ""

# URL da sua API de extração (substitua por sua URL real)
API_URL = "https://apim-dev.ambevdevs.com.br/ocragent/v1/request_ocr" 

# URL do webhook que sua API irá chamar de volta (substitua por sua URL real)
# Nota: Em um ambiente real, '{{local_url}}' deve ser um endpoint acessível.
WEBHOOK_URL = "https://apim-dev.ambevdevs.com.br/ocragent/v1/webhook_test" 

# Pasta onde seus documentos (PDFs, imagens) estão localizados
# IMPORTANTE: Se estiver no Databricks, use caminhos DBFS (ex: "/dbfs/mnt/data/docs/")
DOCUMENTS_FOLDER = "ocr_files" 

# Definição dos campos que você deseja extrair
# (Este body é um template para sua API, ajuste conforme necessário)
FIELDS_TEMPLATE = [
    {
         "nome_campo":"cuit_emisor",
         "descricao":"Representa o identificador da empresa que gerou a fatura. Rótulos como 'CUIT', 'C.U.I.T', 'CUIT Soc'. 'RUT' 'R.U.T.' o CUIT sao 11 caracteres sempre e os formatos podem ser (XXXXXXXXXXX ou XX-XXXXXXXX-X) e nao pode ser o cuit do Quilmes que e 33508358259 ou 33-50835825-9 e tambem nao o CUIT do ECO DE LOS ANDES 30701009548 ou 30-70100954-8 no RUT sao 12 caracateres e nao pode ser o rut do fnc que e 210114160015 não pode ser o rut de MALTERIA URUGUAY S.A que e 211423400019 não pode o RUT CERVECERIA Y MALTERIA PDU.S.A 210001680013 e tambem nao pode ser o rut de C.A.S.A. ISENBECK que e 30661982000. Caso não encontre retornar N/A. // Formato obrigatório (regex): ^(?!(33508358259|33-50835825-9 210114160015)$)(?:\\d{11}|\\d{12}|\\d{2}-\\d{8}-\\d)$"
      },
      {
         "nome_campo":"cuit_receptor",
         "descricao":"Representa o identificador da empresa que recebe a fatura. Rótulos como 'CUIT', 'C.U.I.T', 'CUIT Soc'. 'RUT' 'R.U.T.' o CUIT sao 11 caracteres sempre e os formatos podem ser (XXXXXXXXXXX ou XX-XXXXXXXX-X) e pode ser o cuit do Quilmes que e 33508358259 ou 33-50835825-9 ou pode ser o CUIT do ECO DE LOS ANDES que e 30701009548 ou 30-70100954-8 para o RUT sao 12 caracateres e pode ser no caso do MALTERIA URUGUAY S.A pode ser 211423400019 ou o RUT da CERVECERIA Y MALTERIA PDU.S.A 210001680013. Caso não encontre retornar N/A. // Formato obrigatório (regex): ^(?!(33508358259|33-50835825-9|210114160015)$)(?:\\d{11}|\\d{12}|\\d{2}-\\d{8}-\\d)$"
      },
      {
         "nome_campo":"razon_social",
         "descricao":"Nome da Empresa Geralmente não vem atribuído a um rótulo, todavia se destacada do restante dos elementos do documentos. Pode estar acompanhado do logo da empresa (Não deve ser 'CERVEC.YMALTERIAQUILMESSAIC' 'CERVECERIAYMALTERIAQUILMES' tambem nao 'ECODELOSANDES' ou 'CERVECERIAARGENTINAS.A.U.ISENBECK' ou 'FABRICANACIONALDECERVEZA' ou 'C.A.S.A.ISENBECK' ou 'MALTERIAURUGUAY' ou 'MALTERIAPDUS.A.'"
      },
      {
         "nome_campo":"punto_de_venta",
         "descricao":"Representa o punto de venta do comprobante. E representado somente nos documentos do 'FACTURA DE CRÉDITO ELECTRÓNICA MiPyMEs (FCE) por 4 ou 5 numeros, exemplos: '00001' '00002' '00003' '00004'  '00005' '00006' '00007' '00009' '00010' '00008'. CASO NAO encontrar peencher com N/A. // Formato obrigatório (regex): ^\\d{4,5}$"
      },
      {
         "nome_campo":"nro_comprobante",
         "descricao":"Representa o número de indentificação da fatura. Rótulos como 'FACTURA', 'NRO.', 'Nº'.'Nro Comprobante'. É um campo numerico. Caso não encontre retornar N/A. "
      },
      {
         "nome_campo":"fecha_comprobante",
         "descricao":"Data do documento. Rótulos como 'Fecha', 'Fecha de Transación'. Caso não encontre retornar N/A."
      },
      {
         "nome_campo":"codigo_afip",
         "descricao":"Geralmente está presente no topo central do documento e é representado por um numero de até 3 digitos, exemplos: '201', '03', '01', '001'. Pode estar acompanhado das seguintes palavras: 'Codigo', 'Nro'. É um campo numerico, retorne somente numeros. Em alguns casos o número pode estar presente abaixo de um quadrado. Caso não encontre retornar N/A."
      },
      {
         "nome_campo":"letra_afip",
         "descricao":"Geralmente está presente no topo central do documento e é representado por uma letra e é acompanhado por números) exemplos: [A, B, C]. É um campo de no formato texto, portanto, quando houver zeros a esquerda, devem ser mantidos exatamente como presente no documento. Caso não encontre retornar N/A."
      },
      {
         "nome_campo":"orden_compra",
         "descricao":"Representa o número da ordem de compra da fatura. Rótulos como 'Nro. OC', 'OC', 'ORDEN DE COMPRA', 'Orden de compra','Referencia Comercial','Orden Compra', 'O. Compra', 'O. C.:', 'PEDIDO DE COMPRA',  'No', 'O.C.No', 'PC','Pedido de compra'. É um campo numérico. Caso não encontre retornar N/A. // Formato obrigatório (regex): \b\\d{10}\b"
      },
      {
         "nome_campo":"importe",
         "descricao":"Valor total da fatura do provedor. Rótulos como 'Total General', 'Total', 'Importe Total'. É um campo numérico. Caso não encontre retornar N/A."
      },
      {
         "nome_campo":"moneda",
         "descricao":"Identificação da moeda da fatura. Pode ser identificado com os próprios simbolos da moeda, como ARS, USD, EUR ou estarem descritos na palavra real, Exemplo 'Peso' neste caso retornar o seu correspondente ARS. Considerar os seguintes comparativos, Peso = ARS, Dolar = USD, Euro = EUR. É um campo de no formato texto. Caso não encontre retornar N/A."
      }
    # Adicione mais campos aqui conforme a necessidade
]

# Arquivo de log para guardar os IDs de correlação
LOG_FILE = "./correlation_ids_log.csv"

# ----------------------------------------------------------------------
# 1. FUNÇÕES DE SUPORTE
# ----------------------------------------------------------------------

def encode_file_to_base64(file_path: str) -> str:
    """Lê um arquivo binário e o codifica em Base64."""
    try:
        with open(file_path, "rb") as file:
            return base64.b64encode(file.read()).decode("utf-8")
    except Exception as e:
        print(f"Erro ao codificar o arquivo {file_path}: {e}")
        return ""

def create_api_body(base64_content: str, fields: List[Dict[str, str]]) -> Dict[str, Any]:
    """Cria o body JSON para a requisição da API."""
    return {
        "document_type": "docfield_extractor",
        "webhook_url": WEBHOOK_URL,
        "base64_file": base64_content,
        "input": [{
            "campos": fields
        }]
    }

def process_documents(folder_path: str, fields: List[Dict[str, str]], api_url: str):
    """
    Processa todos os arquivos na pasta, envia para a API e registra os IDs.
    """
    
    if not os.path.isdir(folder_path):
        print(f"ERRO: A pasta de documentos '{folder_path}' não foi encontrada.")
        print("Crie a pasta ou altere a variável DOCUMENTS_FOLDER.")
        return

    api_headers = {
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': SUBSCRIPTION_KEY,
        # O token de autorização pode vir com prefixo 'Bearer ' ou similar.
        # Use a variável Authorization Token que contém o prefixo, se necessário.
        'Authorization': AUTHORIZATION_TOKEN, 
    }

    log_data = []

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        if os.path.isfile(file_path):
            print(f"\n[PROCESSANDO] {filename}...")
            
            # 1. Codificar em Base64
            base64_content = encode_file_to_base64(file_path)
            if not base64_content:
                continue

            # 2. Criar Body da Requisição
            body = create_api_body(base64_content, fields)
            # print(f"body = {body}")

            # 3. Enviar para a API
            try:
                print(f"headers = {api_headers}")
                response = requests.post(api_url, headers=api_headers, json=body, timeout=30)
                response.raise_for_status() # Lança exceção para status codes 4xx/5xx
                
                # 4. Processar a Resposta
                response_json = response.json()
                correlation_id = response_json.get("correlation_id", "N/A")
                
                print(f"  -> Sucesso! Correlation ID: {correlation_id}")
                
                # 5. Registrar Log
                log_data.append({
                    "file_name": filename,
                    "correlation_id": correlation_id,
                    "status": "SENT_SUCCESS",
                    "api_response": json.dumps(response_json)
                })

            except requests.exceptions.RequestException as e:
                print(f"  -> ERRO na requisição da API para {filename}: {e}")
                log_data.append({
                    "file_name": filename,
                    "correlation_id": "N/A",
                    "status": "API_ERROR",
                    "api_response": str(e)
                })
            
    # Salvar o log final
    if log_data:
        df_log = pd.DataFrame(log_data)
        df_log.to_csv(LOG_FILE, index=False)
        print(f"\n--- Processo Concluído ---\nLog salvo em: {LOG_FILE}")
        # No Databricks, você pode usar display(df_log) para ver a tabela
        display(df_log)
    else:
        print("\nNenhum documento processado com sucesso.")

# ----------------------------------------------------------------------
# 2. EXECUÇÃO PRINCIPAL
# ----------------------------------------------------------------------

# Criar a pasta de documentos se ela não existir (útil para testes locais)
# No Databricks, você deve garantir que o caminho DBFS já exista.
if not os.path.exists(DOCUMENTS_FOLDER):
    os.makedirs(DOCUMENTS_FOLDER)
    print(f"A pasta '{DOCUMENTS_FOLDER}' foi criada. Coloque seus arquivos nela.")
    
if API_URL == "SUA_URL_DA_API_DE_EXTRACAO_AQUI":
    print("\nATENÇÃO: Por favor, substitua a variável 'API_URL' pela URL real da sua API antes de executar.")
else:
    process_documents(DOCUMENTS_FOLDER, FIELDS_TEMPLATE, API_URL)