import requests
import re
import os
import urllib3
import time
from datetime import datetime
from dotenv import load_dotenv # <-- NOVIDADE: Carrega segredos de forma segura

# Inicializa o leitor de segredos
load_dotenv()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("1. A iniciar o script...")

# Pegando a data real do computador no momento em que o código roda
hoje = datetime.now()
data_api = hoje.strftime('%Y-%m-%d')

data_obj = datetime.strptime(data_api, '%Y-%m-%d')
data_titulo_geral = data_obj.strftime('%d/%m/%Y')
data_checklist = data_obj.strftime('%d/%m/%y')

# Dicionário para traduzir o dia da semana para português
dias_da_semana = {
    0: 'SEGUNDA-FEIRA', 1: 'TERÇA-FEIRA', 2: 'QUARTA-FEIRA',
    3: 'QUINTA-FEIRA', 4: 'SEXTA-FEIRA', 5: 'SÁBADO', 6: 'DOMINGO'
}
dia_semana_str = dias_da_semana[data_obj.weekday()]

# --- NOVIDADE: Caminho dinâmico! Funciona no Windows e no Linux automaticamente ---
pasta_base = os.path.dirname(os.path.abspath(__file__))

print(f"2. A buscar as aulas do dia {data_titulo_geral} na API...")
url = f"https://prd-lms-api-us.azurewebsites.net/api/Class/GetClassInfos?date={data_api}"

# --- NOVIDADE: Lendo a chave da API do cofre seguro (.env) ---
token_api = os.getenv("API_TOKEN")
if not token_api:
    print("❌ ERRO: Ficheiro .env não encontrado ou 'API_TOKEN' em falta.")
    exit()

cabecalho = {
    'Accept': 'application/json',
    'PartnerAuthorization': token_api
}

try:
    # Adicionado verify=False para ignorar bloqueios de SSL da rede
    resposta = requests.get(url, headers=cabecalho, verify=False)
    dados_da_api = resposta.json()
except Exception as e:
    print(f"❌ ERRO CRÍTICO NA API: Não foi possível ler os dados. Detalhe: {e}")
    exit()

if isinstance(dados_da_api, dict):
    print(f"❌ A API recusou o acesso ou deu erro: {dados_da_api}")
    exit()

if not dados_da_api:
    print("❌ Nenhuma aula encontrada para essa data no sistema da API.")
    exit()

print(f"3. A API devolveu {len(dados_da_api)} aulas. A processar...")

aulas_agrupadas = {}
termos_ignorados = ["PROVA FINAL", "PROVAS FINAIS", "PROVA DE RECUPERAÇÃO", "PROVAS DE RECUPERAÇÃO", "PROCESSO SELETIVO"]

# --- NOVIDADE: Lista de cursos permitidos para a Parte III ---
cursos_permitidos_app = [
    "DSA", "EIB", "GP", "GPRO", "ENGS", "ESGNS", "CBP", "ED", "MKT", "PET", 
    "ESC", "CESG", "NAE", "GVAP", "ELG", "DB", "MBAEPONT", "MBADSAO", "MBAGPONT", 
    "FC", "GN", "GV", "GT", "IAF", "GCMA", "GNIDIA"
]

for aula in dados_da_api:
    try:
        id_aula = str(aula.get('ClassDisciplineId', 'XXXXX'))
        nome_aula = str(aula.get('Discipline', '')).strip().replace(':', '-').replace('!', '-')
        professor = str(aula.get('Teacher', '')).strip()
        
        # --- FILTRO DE PALAVRAS ---
        nome_aula_maiusculo = nome_aula.upper()
        if any(termo in nome_aula_maiusculo for termo in termos_ignorados):
            continue
            
        data_hora_string = str(aula.get('ClassDate', ''))
        if len(data_hora_string) >= 19:
            data_formatada = datetime.strptime(data_hora_string[:10], '%Y-%m-%d').strftime('%y%m%d')
            hora_aula = int(data_hora_string[11:13])
        else:
            data_formatada = data_obj.strftime('%y%m%d')
            hora_aula = 0
            
        lista_turmas = aula.get('ClassCodeAndCourseNames') or []
        
        for turma_completa in lista_turmas:
            codigo_turma = turma_completa.split()[0]
            match_curso = re.search(r'^[A-Za-z]+', turma_completa)
            curso = match_curso.group() if match_curso else "CURSO_INDEFINIDO"

            # --- FILTRO DO DSTEST ---
            if curso.upper() == "DSTEST":
                continue

            chave = (data_formatada, nome_aula, professor, curso)

            if chave not in aulas_agrupadas:
                aulas_agrupadas[chave] = {
                    'turmas_e_ids': [],
                    'hora_aula': hora_aula
                }
            
            if (codigo_turma, id_aula) not in aulas_agrupadas[chave]['turmas_e_ids']:
                aulas_agrupadas[chave]['turmas_e_ids'].append((codigo_turma, id_aula))
    except Exception as e:
        print(f"⚠️ Aviso: Um erro ocorreu ao processar uma aula específica. A ignorar. Erro: {e}")

print("4. A gerar os textos e relatórios...")

titulos_por_curso = {}
lista_checklist = []
lista_teste_class = [] 
turmas_parte_3 = [] # NOVO: Lista apenas com as turmas autorizadas para o App
ids_ja_adicionados_checklist = set() 

for chave, info in aulas_agrupadas.items():
    data_formatada, nome_aula, professor, curso = chave
    
    lista_apenas_ids = list(dict.fromkeys([f"#{item[1]}" for item in info['turmas_e_ids']]))
    ids_juntos = " ".join(lista_apenas_ids)

    titulo_final = f"{ids_juntos} {data_formatada} - {nome_aula} - Prof. {professor}({curso})\n"

    if curso not in titulos_por_curso:
        titulos_por_curso[curso] = []
    titulos_por_curso[curso].append(titulo_final)

    if info['hora_aula'] >= 17:
        for codigo_turma, id_aula in info['turmas_e_ids']:
            if id_aula not in ids_ja_adicionados_checklist:
                lista_checklist.append(f"{codigo_turma}: {id_aula}\n")
                lista_teste_class.append(f"🟠Ao-Vivo | {info['hora_aula']}H | {codigo_turma}")
                
                # NOVO: Filtra para a Parte 3 (Teste do App)
                if curso.upper() in cursos_permitidos_app:
                    turmas_parte_3.append(codigo_turma)
                    
                ids_ja_adicionados_checklist.add(id_aula)

# Organização e formatação da lista de turmas da Parte 3 com vírgulas e "e" no final
if len(turmas_parte_3) > 1:
    texto_turmas_app = ", ".join(turmas_parte_3[:-1]) + " e " + turmas_parte_3[-1]
elif len(turmas_parte_3) == 1:
    texto_turmas_app = turmas_parte_3[0]
else:
    texto_turmas_app = "Nenhuma turma elegível hoje"

corpo_aulas_teste = "\n".join(lista_teste_class) if lista_teste_class else "Nenhuma aula agendada para após as 17h."

saudacao_extra = " Bom final de semana para vocês!" if data_obj.weekday() == 4 else ""

# ==============================================================================
# TEMPLATES DE TEXTO DAS PARTES I, II e III
# ==============================================================================
texto_teste_class = f"""Boa tarde, pessoal, tudo bem?{saudacao_extra}

PARTE I - TESTE DO CLASS
=========================================================================================
TESTE MBX CHAT MBAUSP {dia_semana_str} {data_titulo_geral}
✅Ativação do Chat: Tudo ok nos padrões
✅Chat:  Interações de Moderação, Mensagem de alunos e Q&A estão funcionando corretamente
🚀Tempo de Resposta do Chat: Envio de mensagens instantâneo tanto para envio quanto para respostas.
✅MBXApp: Mensagens enviadas corretamente e sem nenhum bug visual.
=========================================================================================
LEGENDA DO STATUS DAS AULAS:
🟢| Ao-Vivo:
🟠| Aguardando transmissão:
🔴| Aula com algum problema:
⚪| Aula cancelada:
==================MBX================
{corpo_aulas_teste}
======================================================================
Ambiente: Funcionando normalmente  (Nome da aula, Moderação, Material, Ambiente Virtual e Q&A)
Alunos na aula: Todos os alunos estão adicionados no planejamento.
==================================================================================================="""

texto_parte_2_e_3 = f"""PARTE II - TESTE DA TRANSMISSÃO
===================================================================================================
✅ SRT configurado como Primário
✅ Stream ligado e configurado corretamente
✅ Imagem do External recebida corretamente
✅ Tela transmitida corresponde ao curso correto
✅ Transmissão chegando no MBX sem erro de delay ou travamento
✅ Embed do M3U8 na Skylar correto
✅ Evento do Skylar corresponde ao evento no Kaltura
✅ Idiomas da aula corretos na Skylar
✅ Player do MBX funcionando corretamente
✅ Teste da pausa realizado com sucesso (Delay controlado)
✅ Função Tela cheia funcionando normalmente
✅ Função Picture in Picture funcionando normalmente
✅ Todos os Canais ativos e transmitindo corretamente
✅ Canal 4 com opção de legendagem ativada
✅ Canal 5 internacional com legendas e embed corretos (se houver)
✅ Slides e materiais de apoio disponíveis para download

📌 Observações Técnicas:

✅ Decklink funcionando
✅ Som da aula
✅ Vídeo de espera da aula

===================================================================================================
PARTE III - TESTE DAS AULAS NO APP
===================================================================================================
MBX APP: {texto_turmas_app}. 
🟠 Vídeo: Nos padrões e Ao-Vivo
🟠 Nome da aula:  Nos padrões e Ao-Vivo 
🟠 Slides:  Nos padrões e Ao-Vivo
==================================================================================================="""

try:
    with open(os.path.join(pasta_base, 'titulos_gerados.txt'), 'w', encoding='utf-8') as arquivo_txt:
        arquivo_txt.write(f"Títulos das Aulas do dia {data_titulo_geral}\n")
        arquivo_txt.write("-" * 40 + "\n")
        for curso, lista_de_titulos in titulos_por_curso.items():
            arquivo_txt.write(f"{curso}:\n")
            for titulo in lista_de_titulos:
                arquivo_txt.write(titulo)
            arquivo_txt.write("\n")

    with open(os.path.join(pasta_base, 'checklist_ids.txt'), 'w', encoding='utf-8') as arquivo_checklist:
        arquivo_checklist.write(f"IDs das Aulas {data_checklist}:\n") 
        if len(lista_checklist) > 0:
            for item in lista_checklist:
                arquivo_checklist.write(item)
        else:
            arquivo_checklist.write("Nenhuma aula agendada para após as 17h hoje.\n")
except Exception as e:
    print(f"❌ ERRO AO GUARDAR OS FICHEIROS: {e}")
    exit()

print("5. Ficheiros guardados. A preparar envio para o Discord...")

# --- NOVIDADE: Lendo o webhook do Discord do cofre seguro (.env) ---
url_webhook = os.getenv("WEBHOOK_URL")
if not url_webhook:
    print("❌ ERRO: Ficheiro .env não encontrado ou 'WEBHOOK_URL' em falta.")
    exit()

with open(os.path.join(pasta_base, 'titulos_gerados.txt'), 'r', encoding='utf-8') as arquivo_titulos:
    texto_titulos_lidos = arquivo_titulos.read()

with open(os.path.join(pasta_base, 'checklist_ids.txt'), 'r', encoding='utf-8') as arquivo_ids_lidos:
    texto_checklist_lido = arquivo_ids_lidos.read()

crases = "```"
ids_usuarios_mencionar = [
    "1359699529896562860",
    "959477595198615573",
    "210128534251896833",
    "1270760387423502510",
    "1481278186468671489",
]
mencoes_usuarios = " ".join(f"<@{user_id}>" for user_id in ids_usuarios_mencionar)

# ==============================================================================
# ENVIOS PARA O DISCORD (Em 4 passos)
# ==============================================================================

# 1. Enviar Parte 1
print("   -> A enviar a Mensagem 1 (Teste do Class)...")
mensagem_1 = f"🚀 **Resumo Diário de Aulas Gerado!**\n{mencoes_usuarios}\n\n**Relatório Teste do Class:**\n{crases}text\n{texto_teste_class}{crases}"
requests.post(url_webhook, json={"content": mensagem_1, "allowed_mentions": {"parse": [], "users": ids_usuarios_mencionar}}, verify=False)
time.sleep(1) 

# 2. Enviar Parte 2 e 3 (Transmissão e App)
print("   -> A enviar a Mensagem 2 (Transmissão e App)...")
mensagem_2 = f"**Continuação dos Testes:**\n{crases}text\n{texto_parte_2_e_3}{crases}"
requests.post(url_webhook, json={"content": mensagem_2}, verify=False)
time.sleep(1)

# 3. Enviar Checklist de IDs
print("   -> A enviar a Mensagem 3 (IDs)...")
mensagem_3 = f"**Checklist de IDs:**\n{crases}text\n{texto_checklist_lido}{crases}"
requests.post(url_webhook, json={"content": mensagem_3}, verify=False)
time.sleep(1)

# 4. Enviar Títulos
print("   -> A enviar a Mensagem 4 (Títulos)...")
if len(texto_titulos_lidos) < 1900:
    mensagem_4 = f"**Títulos para as Transmissões:**\n{crases}text\n{texto_titulos_lidos}{crases}"
    requests.post(url_webhook, json={"content": mensagem_4}, verify=False)
else:
    print("      (Muitas aulas hoje! A dividir os títulos em partes para o Discord aceitar...)")
    linhas_titulos = texto_titulos_lidos.split('\n')
    pedaco_texto = ""
    numero_parte = 1
    
    for linha in linhas_titulos:
        # Se juntar esta linha passar do limite, envia o que tem e começa um novo pedaço
        if len(pedaco_texto) + len(linha) > 1900:
            msg = f"**Títulos para as Transmissões (Parte {numero_parte}):**\n{crases}text\n{pedaco_texto}{crases}"
            requests.post(url_webhook, json={"content": msg}, verify=False)
            time.sleep(1)
            pedaco_texto = linha + "\n"
            numero_parte += 1
        else:
            pedaco_texto += linha + "\n"
            
    # Envia o restinho que sobrou
    if pedaco_texto.strip():
        msg = f"**Títulos para as Transmissões (Parte {numero_parte}):**\n{crases}text\n{pedaco_texto}{crases}"
        requests.post(url_webhook, json={"content": msg}, verify=False)

print("✅ 6. SUCESSO ABSOLUTO! O relatório completo foi enviado para o Discord!")