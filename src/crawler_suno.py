# %%
import sys
import time
from datetime import datetime
from io import StringIO
import gspread
import pandas as pd
import requests
import yfinance as yf
from bs4 import BeautifulSoup
from df2gspread import df2gspread as d2g
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import os
from dotenv import load_dotenv
import warnings

# Suprime todos os warnings para uma saída mais limpa
warnings.filterwarnings('ignore')

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# %%
# ==============================================================================
# CONFIGURAÇÕES GERAIS (carregadas a partir do arquivo .env)
# ==============================================================================
# --- Credenciais e Acessos ---
SUNO_USERNAME = os.getenv('SUNO_USERNAME')
SUNO_PASSWORD = os.getenv('SUNO_PASSWORD')
BRAPI_TOKEN = os.getenv('BRAPI_TOKEN')
GOOGLE_SHEETS_KEY = os.getenv('GOOGLE_SHEETS_KEY')

# --- Caminhos de Arquivos e Nomes ---
PARQUET_FILE_PATH = os.getenv('PARQUET_FILE_PATH')
GSPREAD_CREDENTIALS_PATH = os.getenv('GSPREAD_CREDENTIALS_PATH')
GSHEET_WORKSHEET_NAME = 'Carteira_Suno'

# --- URLs e Endpoints ---
SUNO_LOGIN_URL = 'https://login.suno.com.br/entrar/cef02de7-1e5a-4b0e-9f41-04e9278aa2d7/'
SUNO_FIIS_URL = 'https://investidor.suno.com.br/carteiras/fiis'
BRAPI_BASE_URL = 'https://brapi.dev/api/quote'

# --- Configurações do Google API ---
GSPREAD_SCOPES = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/spreadsheets'
]



# %%
def setup_webdriver() -> webdriver.Chrome:
    """Configura e inicializa o WebDriver do Selenium."""
    sys.path.insert(0, "/usr/lib/chromium-driver/chromedriver")
    service = Service(ChromeDriverManager().install())
    
    chrome_options = webdriver.ChromeOptions()
    arguments = [
        '--headless', '--no-sandbox', '--disable-dev-shm-usage',
        '--start-maximized', '--window-size=1920,1080', '--disable-gpu',
        '--ignore-certificate-errors', '--disable-extensions',
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
    ]
    for arg in arguments:
        chrome_options.add_argument(arg)
        
    return webdriver.Chrome(service=service, options=chrome_options)


def scrape_suno_portfolio(driver: webdriver.Chrome) -> pd.DataFrame:
    """Realiza o login no site da Suno e extrai os dados da carteira de FIIs."""
    print("Iniciando scraping da carteira Suno FIIs...")
    driver.get(SUNO_LOGIN_URL)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "user_email"))).send_keys(SUNO_USERNAME)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "user_password"))).send_keys(SUNO_PASSWORD)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "login_button"))).click()
    
    WebDriverWait(driver, 25).until(EC.url_contains('home'))
    driver.get(SUNO_FIIS_URL)
    
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'tbody.ant-table-tbody')))
    time.sleep(2)  # Mantido para garantir a renderização completa da página.

    html = driver.execute_script("return document.body.outerHTML;")
    soup = BeautifulSoup(html, 'html.parser')
    
    table_body = soup.find('tbody')
    if not table_body:
        raise ValueError("Tabela de FIIs não encontrada na página.")
        
    list_td = table_body.find_all('td')
    
    scraped_data = []
    # A lógica de iteração (índices fixos) foi mantida para não alterar o resultado.
    i = 11
    step = i - 1
    while True:
        try:
            fii = {
                'ticker': list_td[i].text.replace('Ver relatórios', ''),
                'setor/tipo': list_td[i+1].text,
                'dy esperado': list_td[i+2].text,
                'início': list_td[i+3].text[-10:],
                'preço de entrada ajustado': list_td[i+3].text[:-10],
                'preço atual': list_td[i+4].text.split(',')[0] + ',' + list_td[i+4].text.split(',')[1][:-1].replace('-', ''),
                'preço teto': list_td[i+5].text,
                'alocação': list_td[i+6].text,
                'rentabilidade': list_td[i+7].text,
                'viés': list_td[i+8].text
            }
            scraped_data.append(fii)
            i += step
        except IndexError:
            break
            
    print(f"Scraping finalizado. {len(scraped_data)} FIIs encontrados.")
    return pd.DataFrame(scraped_data)


def fetch_historical_prices(tickers: list) -> pd.DataFrame:
    """Busca o histórico de preços para uma lista de tickers usando a API Brapi."""
    print("\nIniciando a busca de dados históricos de cotações...")
    all_dataframes = []

    for ticker in tickers:
        url = f"{BRAPI_BASE_URL}/{ticker}?range=1mo&interval=1d&token={BRAPI_TOKEN}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data_prices = response.json()
            
            historical_list = data_prices['results'][0]['historicalDataPrice']
            df_fii = pd.DataFrame(historical_list)
            df_fii['ticker'] = ticker
            all_dataframes.append(df_fii)
            print(f" -> Sucesso! {len(df_fii)} registros encontrados para {ticker}.")

        except requests.exceptions.RequestException as e:
            print(f" -> ERRO de requisição para {ticker}: {e}")
        except (KeyError, IndexError):
            print(f" -> ERRO: Ticker '{ticker}' não encontrado ou sem dados na API.")
        time.sleep(1)

    if not all_dataframes:
        return pd.DataFrame()

    hist_1m = pd.concat(all_dataframes, ignore_index=True)
    hist_1m['date'] = pd.to_datetime(hist_1m['date'], unit='s').dt.date
    
    print("\nDownload de dados históricos concluído!")
    return hist_1m[['ticker', 'date', 'open', 'high', 'low', 'close', 'volume']]


def update_historical_data_file(file_path: str, new_data_df: pd.DataFrame):
    """Lê, atualiza e salva o arquivo Parquet com os dados históricos consolidados."""
    print(f"\nAtualizando arquivo de dados históricos em: {file_path}")
    try:
        historical_df = pd.read_parquet(file_path)
    except FileNotFoundError:
        print("Arquivo Parquet não encontrado. Um novo será criado.")
        historical_df = pd.DataFrame()

    combined_df = pd.concat([historical_df, new_data_df], ignore_index=True)
    combined_df.drop_duplicates(subset=['ticker', 'date'], keep='first', inplace=True)
    combined_df.reset_index(drop=True, inplace=True)
    
    combined_df.to_parquet(file_path)
    print("Arquivo Parquet atualizado com sucesso.")


def upload_to_google_sheets(suno_df: pd.DataFrame):
    """Autentica e envia os dados da carteira para a planilha do Google."""
    print("\nIniciando upload para o Google Sheets...")
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(GSPREAD_CREDENTIALS_PATH, GSPREAD_SCOPES)
        client = gspread.authorize(creds)
        
        worksheet = client.open_by_key(GOOGLE_SHEETS_KEY).worksheet(GSHEET_WORKSHEET_NAME)

        d2g.upload(suno_df,
                   GOOGLE_SHEETS_KEY,
                   GSHEET_WORKSHEET_NAME,
                   credentials=creds,
                   row_names=False,
                   clean=True) # O parâmetro 'clean=True' já limpa a planilha antes de inserir.

        # Upload da data de atualização
        now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        update_df = pd.DataFrame({'ultima_atualizacao': [now_str]})
        
        d2g.upload(update_df,
                   GOOGLE_SHEETS_KEY,
                   GSHEET_WORKSHEET_NAME,
                   credentials=creds,
                   start_cell='L1',
                   col_names=True,
                   row_names=False,
                   clean=False) # clean=False aqui para não apagar os outros dados

        print("Upload para Google Sheets concluído com sucesso.")
    except Exception as e:
        print(f"Ocorreu um erro durante o upload para o Google Sheets: {e}")

# %%
def main():
    """Função principal que orquestra a execução do script."""
    driver = setup_webdriver()
    try:
        # 1. Obter dados da carteira Suno
        suno_portfolio_df = scrape_suno_portfolio(driver)
        
        if suno_portfolio_df.empty:
            print("Nenhum dado foi extraído da Suno. Encerrando o script.")
            return

        # 2. Obter cotações históricas
        tickers = suno_portfolio_df['ticker'].tolist()
        historical_prices_df = fetch_historical_prices(tickers)
        
        # 3. Atualizar arquivo Parquet local
        if not historical_prices_df.empty:
            update_historical_data_file(PARQUET_FILE_PATH, historical_prices_df)
        else:
            print("\nNenhum dado histórico foi baixado. O arquivo Parquet não será atualizado.")

        # 4. Enviar dados para o Google Sheets
        upload_to_google_sheets(suno_portfolio_df)

    except Exception as e:
        print(f"\nOcorreu um erro inesperado na execução principal: {e}")
    finally:
        print("\nFinalizando o WebDriver.")
        driver.quit()


if __name__ == "__main__":
    main()


