# Comando mágico do Databricks para instalar bibliotecas se necessário
# %pip install pandas scikit-learn

import pandas as pd
import json
from sklearn.metrics import precision_recall_fscore_support
from typing import Dict, Any, List

# ----------------------------------------------------------------------
# 1. FUNÇÕES DE SUPORTE
# ----------------------------------------------------------------------

def load_json_data(file_path: str) -> Dict[str, Any]:
    """Carrega dados JSON de um caminho de arquivo."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERRO: Arquivo não encontrado em {file_path}")
        return {}
    except json.JSONDecodeError:
        print(f"ERRO: Conteúdo inválido no JSON em {file_path}")
        return {}

def calculate_extraction_metrics(
    ground_truth_json: Dict[str, Any],
    prediction_json: Dict[str, Any]
) -> Dict[str, float]:
    """
    Calcula Precision, Recall e F1 Score comparando dois dicionários JSON
    campo a campo.

    Esta é a abordagem ideal para extração de campos:

    - True Positives (TP): Um campo que está no Ground Truth E foi extraído
      CORRETAMENTE no Prediction (valor idêntico).
    - False Positives (FP): Um campo que foi extraído no Prediction, mas
      NÃO está no Ground Truth ou está INCORRETO.
    - False Negatives (FN): Um campo que está no Ground Truth, mas
      NÃO foi extraído no Prediction (campo faltando) ou foi extraído
      INCORRETAMENTE.

    O score é calculado no NÍVEL DO CAMPO (field-level).
    """

    # 1. Obter todos os campos únicos de ambos os JSONs
    all_fields = set(ground_truth_json.keys()) | set(prediction_json.keys())
    
    # Inicializa contadores
    true_positives = 0
    false_positives = 0
    false_negatives = 0

    # 2. Iterar sobre todos os campos e classificar cada ocorrência
    for field_name in all_fields:
        gt_value = ground_truth_json.get(field_name)
        pred_value = prediction_json.get(field_name)

        # Tratar valores None/vazios para simplificar a comparação
        # Assumimos que None/vazio significa que o campo não foi extraído (FN)
        # se ele estava presente no Ground Truth.
        gt_value_present = gt_value is not None and gt_value != ""
        pred_value_present = pred_value is not None and pred_value != ""

        # Caso 1: O campo existe no Ground Truth (é um campo-alvo)
        if gt_value_present:
            if pred_value_present and str(gt_value).strip() == str(pred_value).strip():
                # Acerto: O agente extraiu o campo e o valor está correto.
                true_positives += 1
            else:
                # Erro tipo FN: O agente errou o valor ou não extraiu o campo.
                false_negatives += 1
        
        # Caso 2: O campo NÃO existe no Ground Truth
        if not gt_value_present:
            if pred_value_present:
                # Erro tipo FP: O agente extraiu algo que não deveria estar lá.
                # Exemplo: Extraiu 'Total Tax' quando o GT não tem esse campo.
                false_positives += 1
        
        # Caso 3: O campo não existe em nenhum (ignorar)

    # 3. Calcular Precision, Recall e F1 Score Agregados
    
    # Proteção contra divisão por zero
    if (true_positives + false_positives) == 0:
        precision = 0.0
    else:
        precision = true_positives / (true_positives + false_positives)

    if (true_positives + false_negatives) == 0:
        recall = 0.0
    else:
        recall = true_positives / (true_positives + false_negatives)

    if (precision + recall) == 0:
        f1_score = 0.0
    else:
        f1_score = 2 * (precision * recall) / (precision + recall)

    return {
        "TP": true_positives,
        "FP": false_positives,
        "FN": false_negatives,
        "Precision": precision,
        "Recall": recall,
        "F1_Score": f1_score
    }

# ----------------------------------------------------------------------
# 2. DADOS DE EXEMPLO (Simulação de Arquivos JSON)
# ----------------------------------------------------------------------

# 2.1. Simulação do JSON Ground Truth (O QUE DEVERIA SER EXTRAÍDO)
ground_truth_data = {
    "invoice_number": "INV-89745",
    "issue_date": "2023-10-25",
    "total_amount": "1500.50",
    "supplier_name": "Tech Solutions Inc.",
    "is_credit_note": "False",
    "client_id": "CLIENT-001" # Campo presente no GT
}

# 2.2. Simulação do JSON Gerado pelo OCR Agent (O QUE FOI EXTRAÍDO)
prediction_data = {
    "invoice_number": "INV-89745", # Acerto (TP)
    "issue_date": "2023-10-23",  # Erro de valor (FN)
    "total_amount": "1500,50",  # Erro de formato, depende de padronização (FN)
    "supplier_name": "Tech Solutions Inc.", # Acerto (TP)
    "tax_amount": "100.00",    # Campo extra (FP)
    "client_id": ""            # Não extraído / Vazio (FN)
}

# 2.3. Salvar temporariamente para simular a leitura de arquivos
# No Databricks, você deve carregar de um DBFS path, Azure Blob ou Unity Catalog
gt_path = "/tmp/ground_truth_sim.json"
pred_path = "/tmp/prediction_sim.json"

# Salvar os arquivos simulados
with open(gt_path, 'w') as f:
    json.dump(ground_truth_data, f, indent=4)
with open(pred_path, 'w') as f:
    json.dump(prediction_data, f, indent=4)

print(f"Arquivos de simulação criados em {gt_path} e {pred_path}")
print("-" * 50)

# ----------------------------------------------------------------------
# 3. EXECUÇÃO DA AVALIAÇÃO (para um único documento)
# ----------------------------------------------------------------------

print("--- AVALIAÇÃO DE UM ÚNICO DOCUMENTO ---")

# Carregar os JSONs simulados
gt = load_json_data(gt_path)
pred = load_json_data(pred_path)

# Calcular métricas
metrics = calculate_extraction_metrics(gt, pred)

# Imprimir resultados
print(f"Ground Truth (GT): {gt}")
print(f"Prediction (PR): {pred}")
print("\nRESULTADOS DA EXTRAÇÃO:")
for key, value in metrics.items():
    print(f"  {key}: {value:.4f}" if isinstance(value, float) else f"  {key}: {value}")

print("-" * 50)


# ----------------------------------------------------------------------
# 4. AVALIAÇÃO DE MÚLTIPLOS DOCUMENTOS (AGREGAÇÃO)
# ----------------------------------------------------------------------

# Em um cenário real, você teria uma lista de JSONs Ground Truth e Predictions
# correspondentes a um conjunto de testes de 100+ documentos.

print("--- AVALIAÇÃO AGREGADA DE MÚLTIPLOS DOCUMENTOS ---")

# Simulação de um dataset de resultados de 3 documentos
# (Usando o cálculo do documento 1 + outros exemplos)
all_ground_truths = [
    ground_truth_data,
    {"id": "doc2", "name": "user2"}, # GT Doc 2
    {"id": "doc3", "address": "Rua A", "city": "SP"} # GT Doc 3
]

all_predictions = [
    prediction_data,
    {"id": "doc2", "name": "user_2_errado"}, # PR Doc 2: ID Correto (TP), Name Errado (FN)
    {"id": "doc3", "address": "Rua A"} # PR Doc 3: Address Correto (TP), City Faltando (FN)
]

# Variáveis para agregação em todos os campos de todos os documentos
total_tp = 0
total_fp = 0
total_fn = 0
results_per_document = []

# Iterar sobre o dataset completo
for i, (gt_doc, pred_doc) in enumerate(zip(all_ground_truths, all_predictions)):
    doc_metrics = calculate_extraction_metrics(gt_doc, pred_doc)
    
    total_tp += doc_metrics['TP']
    total_fp += doc_metrics['FP']
    total_fn += doc_metrics['FN']
    results_per_document.append({'Documento': f'Doc {i+1}', **doc_metrics})


# 5. CÁLCULO FINAL AGREGADO (Micro-average F1)

# Recalcular métricas baseadas nos totais acumulados
# (Melhor forma de ver a performance geral do modelo)
if (total_tp + total_fp) == 0:
    micro_precision = 0.0
else:
    micro_precision = total_tp / (total_tp + total_fp)

if (total_tp + total_fn) == 0:
    micro_recall = 0.0
else:
    micro_recall = total_tp / (total_tp + total_fn)

if (micro_precision + micro_recall) == 0:
    micro_f1_score = 0.0
else:
    micro_f1_score = 2 * (micro_precision * micro_recall) / (micro_precision + micro_recall)


# 6. EXIBIÇÃO DOS RESULTADOS NO DATABRICKS

print("\nRESULTADOS POR DOCUMENTO:")
# Use display(pd.DataFrame(...)) no Databricks para uma tabela interativa
display(pd.DataFrame(results_per_document)) 

print("\n--- MÉTRICAS GERAIS (MICRO-AVERAGE) ---")
print(f"Total True Positives (TP): {total_tp}")
print(f"Total False Positives (FP): {total_fp}")
print(f"Total False Negatives (FN): {total_fn}")
print(f"\nPrecision Agregada: {micro_precision:.4f}")
print(f"Recall Agregado:    {micro_recall:.4f}")
print(f"F1 Score Agregado:  {micro_f1_score:.4f}")