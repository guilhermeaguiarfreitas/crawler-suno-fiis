# CrawlerSuno

Crawler criado para webscrap do site Suno Research e geração dos dados em planilha do Google Sheets.

Bibliotecas:
* selenium
* pandas
* webdriver_manager
* io
* BeautifulSoup
* oauth2client
* df2gspread
* datetime

A execução do programa está configurada no Windows Task Scheduler, a tarefa com nome CrawlerSuno_Atualizar_Carteira, salva no formato .xml na pasta Code.

Na pasta de execução do .py é necessário o arquivo serviceaccount.json, com as credenciais da API do Google. 

IMPORTANTE: Para execução do Crawler em outra máquina é necessário editar os arquivos executor.bat, importar o arquivo CrawlerSuno_Atualizar_Carteira.xml no Task Scheduler, e editar as configurações apontando os caminhos corretos.
