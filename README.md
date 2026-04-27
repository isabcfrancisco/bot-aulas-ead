# Bot de Automação de Relatórios EAD

Este projeto é uma automação desenvolvida em Python para otimizar o fluxo de trabalho da equipe de transmissão de aulas EAD, com foco nas transmissões ao vivo dos programas de **MBA USP Esalq**, realizado pelo instituto Pecege. O script consome dados de uma API educacional, processa as informações e orquestra o envio de relatórios e alertas estruturados diretamente para um canal corporativo do Discord via Webhooks.

## Funcionalidades

* **Integração com API REST:** Conecta-se de forma segura à API do sistema de gestão de aulas.
* **Tratamento e Filtragem de Dados:** Ignora eventos irrelevantes (como provas finais e processos seletivos) e agrupa turmas com os mesmos IDs de disciplina.
* **Geração de Artefatos Locais:** Cria automaticamente ficheiros `.txt` com os títulos das aulas organizados por curso e a checklist de IDs do dia.
* **Notificações no Discord:** Divide e envia mensagens formatadas em blocos para o Discord, respeitando os limites de caracteres da plataforma.
* **Proteção de Credenciais:** Utiliza variáveis de ambiente (`.env`) para garantir que tokens e URLs sensíveis não são expostos.

## Tecnologias Utilizadas

* [**Python 3**](https://www.python.org/): Linguagem principal do projeto.
* [**Requests**](https://pypi.org/project/requests/): Para consumo da API e envio dos Webhooks para o Discord.
* [**Python-dotenv**](https://pypi.org/project/python-dotenv/): Para gestão segura das variáveis de ambiente.

## Como Executar o Projeto

Para correr este projeto na sua máquina local, siga os passos abaixo:

### 1. Clonar o repositório
```bash
git clone [https://github.com/isabcfrancisco/bot-aulas-ead.git](https://github.com/isabcfrancisco/bot-aulas-ead.git)
cd bot-aulas-ead
```

### 2. Instalar as dependências 
```bash
pip install requests python-dotenv urllib3
```

### 3. Configurar as Variáveis de Ambiente
Crie um ficheiro chamado .env na raiz do projeto e adicione as suas credenciais reais (este ficheiro é ignorado pelo Git por segurança):
```bash
API_TOKEN=seu_token_de_acesso_aqui
WEBHOOK_URL=sua_url_do_webhook_do_discord_aqui
```
### 4. Executar o Script
```bash
python gerador_titulos.py
```

# Notas de Desenvolvimento
Este projeto foi construído para correr com 100% de autonomia em servidores Linux (através de agendamento Cron) ou Windows (via Agendador de Tarefas), garantindo o envio diário dos relatórios antes do início das transmissões.


Desenvolvido por **Isabela Correa Francisco**, estudante de Engenharia da Computação no IFSP.
Conecte-se comigo no LinkedIn: (https://www.linkedin.com/in/isabela-correa-fr/)
