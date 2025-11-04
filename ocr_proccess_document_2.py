# Pegar resultado processamento por correlation_id -> salvar em json

import os
import json
import requests
import pandas as pd
import time
from typing import Dict, Any

# ----------------------------------------------------------------------
# CONFIGURAÇÕES GLOBAIS
# ----------------------------------------------------------------------

# URL base para verificar o status
# Substitua por sua URL real, mantendo a estrutura de placeholder para o ID
OCR_STATUS_ENDPOINT = "https://ocr-stg.ambevdevs.com.br/requests/{correlation_id}/status" 

# Arquivo de log gerado pelo Passo 1
LOG_FILE = "./correlation_ids_log.csv"

# Diretórios de saída para arquivos individuais
FILES_OUTPUT_DIR = "./files"
GROUNDTRUTH_OUTPUT_DIR = "./groundedtruths"

# Tempo de espera em segundos entre as checagens (polling)
POLLING_INTERVAL_SECONDS = 15

# Status que indicam que a extração terminou
COMPLETED_STATUSES = ["COMPLETED", "FAILED", "ERROR", "WEBHOOK_FAILED"]

# ----------------------------------------------------------------------
# 1. FUNÇÕES DE SUPORTE
# ----------------------------------------------------------------------

def get_request_status(correlation_id: str) -> Dict[str, Any]:
    """
    Bate no endpoint de status para obter o resultado da extração.
    """
    url = OCR_STATUS_ENDPOINT.format(correlation_id=correlation_id)
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  -> ERRO de requisição para {correlation_id}: {e}")
        return {"status": "REQUEST_ERROR", "error_details": str(e)}

def extract_fields_from_data(data_content: str) -> Dict[str, Any]:
    """
    Analisa o conteúdo complexo da chave 'data', lida com a dupla serialização
    e extrai o dicionário de campos que está dentro de 'content', assumindo que
    o conteúdo é um JSON dinâmico.
    """
    try:
        # 1. Desserializar o conteúdo de 'data' (que é uma string JSON)
        data_json = json.loads(data_content)
        
        # 2. Navegar para o bloco de 'content'
        # Estrutura esperada: data -> choices[0] -> message -> content
        if 'choices' not in data_json or not data_json['choices']:
            return {"extraction_error": "JSON structure missing 'choices' block."}
            
        content_block = data_json['choices'][0].get('message', {}).get('content')
        
        if content_block is None:
            return {"extraction_error": "Content block is missing or null."}
            
        # 3. Tratar o conteúdo de 'content' (pode ser um dict ou uma string JSON)
        if isinstance(content_block, str):
            # Se for uma string, é o JSON dos campos. Desserializamos novamente.
            field_data = json.loads(content_block)
            
        elif isinstance(content_block, dict):
            # Se já for um dict, usamos diretamente (o LLM retornou um objeto)
            field_data = content_block

        else:
            return {"extraction_error": f"Content is of an unexpected type: {type(content_block)}"}
        
        # 4. Assumimos que 'field_data' contém as chaves dinâmicas (os campos)
        return field_data

    except json.JSONDecodeError as e:
        # Captura erros se a string de 'data' ou a string de 'content' não for um JSON válido
        return {"extraction_error": f"Failed to decode nested JSON string: {e}"}
    except Exception as e:
        return {"extraction_error": f"Unexpected error during field extraction: {e}"}

def create_response_file(correlation_id: str, file_name: str, extracted_data: Dict[str, Any], status_response: Dict[str, Any]) -> None:
    """
    Cria arquivo individual no formato esperado na pasta /files
    """
    # Criar estrutura para /files
    file_structure = {
        "id": correlation_id,
        "agent_name": "ocr_extraction_agent",
        "file_name": file_name,
        "response_data": extracted_data,
        "metadata": {
            "extraction_timestamp": status_response.get("timestamp", ""),
            "processing_status": status_response.get("status", ""),
            "model_used": "openai/gpt-4-vision"
        }
    }
    
    # Garantir que o diretório existe
    os.makedirs(FILES_OUTPUT_DIR, exist_ok=True)
    
    # Salvar arquivo individual
    output_file = os.path.join(FILES_OUTPUT_DIR, f"ocr_response_{correlation_id}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(file_structure, f, indent=2, ensure_ascii=False)

def create_groundtruth_file(correlation_id: str, file_name: str, extracted_data: Dict[str, Any]) -> None:
    """
    Cria arquivo individual no formato esperado na pasta /groundedtruths
    """
    # Criar estrutura para /groundedtruths
    groundtruth_structure = {
        "id": correlation_id,
        "file_name": file_name,
        "expected_response": extracted_data
    }
    
    # Garantir que o diretório existe
    os.makedirs(GROUNDTRUTH_OUTPUT_DIR, exist_ok=True)
    
    # Salvar arquivo individual
    output_file = os.path.join(GROUNDTRUTH_OUTPUT_DIR, f"ocr_ground_truth_{correlation_id}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(groundtruth_structure, f, indent=2, ensure_ascii=False)


# ----------------------------------------------------------------------
# 2. EXECUÇÃO PRINCIPAL
# ----------------------------------------------------------------------

def collect_results():
    if not os.path.exists(LOG_FILE):
        print(f"ERRO: Arquivo de log '{LOG_FILE}' não encontrado.")
        print("Certifique-se de que o script do Passo 1 foi executado e salvou o log.")
        return

    # 1. Carregar IDs de correlação do Passo 1
    try:
        df_log = pd.read_csv(LOG_FILE)
        # Filtra apenas os IDs que foram enviados com sucesso, caso haja erros no log
        ids_to_process = df_log[df_log['status'] == 'SENT_SUCCESS']
        if ids_to_process.empty:
             print("Nenhum ID de correlação válido encontrado para processamento.")
             return
    except Exception as e:
        print(f"ERRO ao ler o arquivo de log CSV: {e}")
        return

    pending_requests = ids_to_process.to_dict('records')
    processed_count = 0
    
    print(f"Iniciando coleta de resultados para {len(pending_requests)} requisições...")
    
    # Loop de polling até que todos os resultados sejam coletados
    while pending_requests:
        print(f"\n[POLLING] Checando {len(pending_requests)} requisições pendentes...")
        
        # Usamos uma cópia para iterar enquanto modificamos a lista original
        for request_info in list(pending_requests):
            
            file_name = request_info['file_name']
            corr_id = request_info['correlation_id']
            
            status_response = get_request_status(corr_id)
            current_status = status_response.get("status", "UNKNOWN")
            
            print(f"  -> {file_name} ({corr_id}): Status atual: {current_status}")

            if current_status in COMPLETED_STATUSES:
                
                # 2. Processamento do Resultado Final
                extraction_data = {}
                
                # Tenta extrair dados se existirem, independente do status
                if status_response.get("data"):
                    extraction_data = extract_fields_from_data(status_response["data"])
                    print(f"  -> Dados extraídos com sucesso para {corr_id}")
                
                else:
                    # Registra o erro para que o humano saiba que precisa de entrada manual
                    extraction_data = {"extraction_status": current_status, "error_details": status_response.get("error_details", "N/A")}
                    print(f"  -> Nenhum dado encontrado para {corr_id}, status: {current_status}")

                # 3. Criar arquivos individuais nas pastas /files e /groundedtruths
                try:
                    create_response_file(corr_id, file_name, extraction_data, status_response)
                    create_groundtruth_file(corr_id, file_name, extraction_data)
                    processed_count += 1
                    print(f"  -> Arquivos criados para {corr_id}")
                except Exception as e:
                    print(f"  -> ERRO ao criar arquivos para {corr_id}: {e}")
                
                # Remove da lista de pendentes
                pending_requests.remove(request_info)

        if pending_requests:
            # Espera antes de checar novamente
            print(f"\nAguardando {POLLING_INTERVAL_SECONDS} segundos...")
            time.sleep(POLLING_INTERVAL_SECONDS)
        else:
            print("\nTodos os resultados foram coletados.")

    # 4. Relatório final
    if processed_count > 0:
        print(f"\n--- Processo de Coleta Concluído ---")
        print(f"Arquivos processados: {processed_count}")
        print(f"Arquivos de resposta salvos em: {FILES_OUTPUT_DIR}/")
        print(f"Arquivos de ground truth salvos em: {GROUNDTRUTH_OUTPUT_DIR}/")
    else:
        print("\nNenhum arquivo foi processado.")

# ----------------------------------------------------------------------
# INICIAR COLETA
# ----------------------------------------------------------------------
if OCR_STATUS_ENDPOINT == "https://seu-servidor-stg.com/requests/{correlation_id}/status":
    print("\nATENÇÃO: Por favor, substitua a variável 'OCR_STATUS_ENDPOINT' pela URL real da sua API antes de executar.")
else:
    collect_results()
