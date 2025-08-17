# Crawler Suno FIIs

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Projeto de automação para extrair a carteira recomendada de Fundos de Investimento Imobiliário (FIIs) do portal Suno e consolidar os dados em uma planilha do Google Sheets.

## 📖 Sobre o Projeto

Este projeto foi criado para automatizar a coleta de informações da carteira de FIIs recomendada pela Suno, eliminando a necessidade de copiar e colar dados manualmente. O script realiza o login na plataforma, extrai as informações da tabela, busca dados históricos de cotações e, por fim, atualiza uma planilha pessoal no Google Sheets, servindo como uma fonte de dados centralizada para controle de investimentos.

### ✨ Principais Funcionalidades

* **Login Automatizado:** Realiza o login de forma segura na área de assinantes da Suno.
* **Web Scraping:** Utiliza Selenium e BeautifulSoup para navegar e extrair os dados da tabela de FIIs.
* **Enriquecimento de Dados:** Busca o histórico de cotações do último mês para cada FII através da API da [Brapi](https://brapi.dev/).
* **Persistência Local:** Mantém e atualiza um banco de dados histórico de cotações em um arquivo Parquet (`cotacaohistorica.parquet`).
* **Integração com Google Sheets:** Limpa e atualiza uma planilha designada com os dados mais recentes da carteira e a data da última atualização.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.9+
* **Web Scraping:** Selenium, BeautifulSoup4
* **Manipulação de Dados:** Pandas
* **APIs:** Requests (para Brapi), Gspread & df2gspread (para Google Sheets)
* **Automação:** Scripts .bat e Agendador de Tarefas do Windows
* **Configuração:** Python-dotenv

---

## 🚀 Começando

Siga as instruções abaixo para configurar e executar o projeto em sua máquina local.

### Pré-requisitos

* [Python 3.9](https://www.python.org/downloads/) ou superior
* [Git](https://git-scm.com/downloads)
* Acesso de assinante ao portal da Suno
* Uma conta de serviço do Google Cloud com as APIs do Google Drive e Google Sheets ativadas.

### Instalação

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/guilhermeaguiarfreitas/crawler-suno-fiis.git](https://github.com/guilhermeaguiarfreitas/crawler-suno-fiis.git)
    cd crawler-suno-fiis
    ```

2.  **Crie e ative um ambiente virtual (Recomendado):**
    ```bash
    # Criar o ambiente
    python -m venv venv

    # Ativar no Windows
    .\venv\Scripts\activate

    # Ativar no Linux/Mac
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

---

## ⚙️ Configuração

Para que o script funcione, são necessários dois arquivos de configuração que **não** são versionados no Git por segurança.

1.  **Credenciais do Google (`serviceaccount.json`)**
    * Crie um projeto no [Google Cloud Console](https://console.cloud.google.com/).
    * Ative as APIs **Google Drive API** e **Google Sheets API**.
    * Crie uma Conta de Serviço, gere uma chave JSON e faça o download.
    * Renomeie o arquivo para `serviceaccount.json` e coloque-o dentro da pasta `config/` na raiz do projeto.
    * **Importante:** Compartilhe sua planilha no Google Sheets com o e-mail do cliente (`client_email`) que está dentro do arquivo JSON.

2.  **Variáveis de Ambiente (`.env`)**
    * Na raiz do projeto, crie um arquivo chamado `.env`.
    * Copie o conteúdo abaixo e preencha com suas informações:

    ```env
    # Credenciais de acesso ao portal Suno
    SUNO_USERNAME="seu_email_suno@exemplo.com"
    SUNO_PASSWORD="sua_senha_suno"

    # Token da API Brapi ([https://brapi.dev/](https://brapi.dev/))
    BRAPI_TOKEN="SEU_TOKEN_BRAPI"

    # Chave da sua Planilha Google
    GOOGLE_SHEETS_KEY="CHAVE_DA_SUA_PLANILHA_AQUI"

    # Caminho para o arquivo Parquet (ajuste se necessário)
    PARQUET_FILE_PATH="data/cotacaohistorica.parquet"

    # Caminho para as credenciais do Google
    GSPREAD_CREDENTIALS_PATH="config/serviceaccount.json"
    ```

---

## ▶️ Uso

Após a instalação e configuração, execute o script principal através do terminal:

```bash
python src/crawler_suno.py