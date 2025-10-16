from playwright.sync_api import sync_playwright
import pandas as pd
import time
import requests
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
pd.set_option('future.no_silent_downcasting', True)
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

colorscale=[[0, '#ff2c2c'],[0.25, '#FF6A6A'],[0.5, '#FFFFFF'],[0.75, '#5ce65c'],[1, '#008000']]

config = {
    'displayModeBar': 'hover',
    'modeBarButtonsToRemove': [
        'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 
        'hoverClosestCartesian', 'hoverCompareCartesian', 'toggleSpikelines', 'resetScale2d', 'zoom2d'
    ],
    'modeBarButtonsToAdd': ['toImage'],
    'displaylogo': False
}

import time

def setup_browser():
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        })
    return playwright, browser, page

def extract_bonos(page):
    tables = page.locator("table").all()
    table_names = {
        0: "Letras y Tasa Fija",
        1: "BadLar",
        2: "CER",
        3: "Bopreal",
        4: "Bonos en USD",
        5: "Dolar Linked"
    }
    for idx, table in enumerate(tables):
        if idx in table_names:
            try:
                html = table.inner_html()
                # Extrae los encabezados de la tabla
                headers = table.locator('thead th').all_text_contents()
                header_texts = [header.strip() for header in headers]
                # Extrae las filas de la tabla
                rows = table.locator('tbody tr').all()
                table_data = []
                for row in rows:
                    cells = row.locator('td').all_text_contents()
                    row_data = [cell.strip() for cell in cells]
                    table_data.append(row_data)
                # Crea el DataFrame
                df = pd.DataFrame(table_data, columns=header_texts)
                file_name = f"./Datos/Bolsa/Bonos/{table_names[idx]}.csv"
                df.to_csv(file_name, index=False)
                print(f"Tabla {table_names[idx]} guardada como {file_name}")
            except Exception as e:
                print(f"Error al procesar la tabla {table_names[idx]}: {e}")
                continue

def get_iol(url, name):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        divs = soup.select("div.col-md-2.col-xs-4.text-center.bg")
        data = []
        for div in divs:
            try:
                nombre = div.find("h3").get_text(strip=True)
                variacion = div.select_one("h4 span[data-field='Variacion']").get_text(strip=True)
                precio = div.select_one("p span[data-field='UltimoPrecio']").get_text(strip=True)
                data.append({"Nombre": nombre, "Precio": precio, "Var %": variacion})
            except Exception as e:
                print(f"Error al procesar un div: {e}")
        df = pd.DataFrame(data)
        try:
            df['Precio'] = pd.to_numeric(df['Precio'].replace({r"\.": "", r",": "."}, regex=True))
            df['Var %'] = pd.to_numeric(df['Var %'].replace({r"\.": "", r",": ".","%":""}, regex=True))
        except Exception as e:
            print(e)
        df.to_csv(f'./Datos/Bolsa/Equity/{name}.csv', index=False)
        with open(f'./Datos/Bolsa/Equity/{name}.json', "w") as file:
            json.dump(df.to_dict(orient='records'), file, indent=4)
        print(f'Datos de {name} generados')

def extract_spy(page, indices):
    soup = BeautifulSoup(page.content(), 'html.parser')
    tables = soup.find_all('table')
    headers = [header.text.strip() for header in tables[0].find_all('th')]
    rows = [[cell.text.strip().replace('%','').replace('(','').replace(')','') for cell in row.find_all('td')] for row in tables[0].find_all('tr') if row.find_all('td')]
    sp500 = pd.DataFrame(rows, columns=headers)
    sp500.to_csv('./Datos/Bolsa/Equity/SP500.csv', index=False)
    print("S&P500 file created")
    rows = [[cell.text.strip().replace('%','').replace('(','').replace(')','') for cell in row.find_all('td')] for row in tables[1].find_all('tr') if row.find_all('td')]
    indices["SPY"]['Price'] = float(rows[0][2])
    indices["SPY"]['Var'] = float(rows[0][4])
    return indices

def get_probabilities(page):
    page.wait_for_load_state("networkidle")
    soup = BeautifulSoup(page.content(), "lxml")

    # Extraer los datos
    data = {}
    tables = soup.find_all('div', class_="cardWrapper")
    for table in tables:
        # Obtener la fecha de la tabla
        date = table.find('div', class_='fedRateDate').get_text(strip=True)

        focm = {}
        # Iterar sobre las filas de la tabla
        for tr in table.find_all('tr')[1:]:
            tds = tr.find_all('td')
            # Extraer los valores en el primer td y convertirlos a formato adecuado
            focm["-".join([str(num) for num in [int(float(i)*100) for i in tds[0].get_text(strip=True).split(' - ')]])] = [
                float(td.get_text(strip=True)[:-1] if td.get_text(strip=True)[:-1] != '' else '0.0') for td in tds[1:]
            ]

        # Obtener la fecha de actualización
        _today_ = datetime.strptime(" ".join(table.find('div', class_='fedUpdate').get_text(strip=True).split()[1:4]), '%b %d, %Y')
        _yest_ = _today_ - timedelta(days=1)
        _lastweek_ = _today_ - timedelta(days=7)

        # Convertir los datos a un DataFrame
        focm = pd.DataFrame(focm).transpose()
        focm.columns = [_today_.strftime('%b %d, %Y'), _yest_.strftime('%b %d, %Y'), _lastweek_.strftime('%b %d, %Y')]
        data[date] = focm


    dfs_dict = {}
    for key, value in data.items():
        # Incluir el índice como una columna adicional
        value['index'] = value.index
        # Convertir el DataFrame a diccionario y agregarlo al diccionario final
        dfs_dict[key] = value.to_dict(orient='records')
    with open("./Datos/FOCM/Probabilities.json", "w") as json_file:
        json.dump(dfs_dict, json_file, indent=4)
    print('FOCM Probabilities successfully downloaded')

def get_indices(page,indices):
    #page.wait_for_load_state("networkidle")
    soup = BeautifulSoup(page.content(), "html.parser")

    indice_div = soup.find('div', {'id': 'indice-1'})

    if indice_div:
        # Extraer los valores dentro del div (suponiendo que los valores están en texto)
        valores = [elem.get_text(strip=True) for elem in indice_div.find_all('div')]
        
        # Filtrar los valores numéricos
        valores_numericos = [v for v in valores if any(c.isdigit() for c in v) or '-' in v][2:]
        indices['Merval']['Price']=float(valores_numericos[0].replace('.','').replace(',','.'))
        indices['Merval']['Var']=float(valores_numericos[1].replace('%','').replace(',','.'))
        
        ul_element = soup.find("ul", class_="chakra-wrap__list css-1r1h")
        if ul_element:
            li_elements = ul_element.find_all("li")
            for li in li_elements:
                p_list=li.find_all('p')
                    #[p.text.strip() for p in li.find_all('p')]
                if 'dolar oficial' in p_list[1].text.strip().lower():
                    print(p_list[0].text.strip(),'-----',p_list[1].text.strip(),'-----',p_list[-1].text.strip())
                    indices['DolarOficial']['Price']=float(p_list[-1].text.strip().replace('.','').replace(',','.'))
                    indices['DolarOficial']['Var']=float(p_list[0].text.strip().replace('%','').replace(',','.'))
                elif 'dolar mep' in p_list[1].text.strip().lower():
                    print(p_list[0].text.strip(),'-----',p_list[1].text.strip(),'-----',p_list[-1].text.strip())
                    indices['DolarMep']['Price']=float(p_list[-1].text.strip().replace('.','').replace(',','.'))
                    indices['DolarMep']['Var']=float(p_list[0].text.strip().replace('%','').replace(',','.'))
                elif 'dolar ccl' in p_list[1].text.strip().lower():
                    print(p_list[0].text.strip(),'-----',p_list[1].text.strip(),'-----',p_list[-1].text.strip())
                    indices['DolarCCL']['Price']=float(p_list[-1].text.strip().replace('.','').replace(',','.'))
                    indices['DolarCCL']['Var']=float(p_list[0].text.strip().replace('%','').replace(',','.'))
    return indices

def main():
    start_time=time.time()
    with open('./Datos/Bolsa/Equity/Indices.json', "r") as file:
        indices = json.load(file)
    playwright, browser, page = setup_browser()
    try:
        page.goto("https://bonistas.com/")
        time.sleep(7)
        extract_bonos(page)
    except Exception as e: print(e)
    try:
        page.goto("https://www.slickcharts.com/sp500")
        time.sleep(5)
        indices = extract_spy(page, indices)
    except Exception as e: print(e)
    try:
        page.goto("https://www.dolarito.ar/")
        time.sleep(5)
        indices = get_indices(page, indices)
    except Exception as e: print(e)
    try:
        page.goto("https://www.investing.com/central-banks/fed-rate-monitor",wait_until="domcontentloaded")
        time.sleep(5)
        get_probabilities(page)
    except Exception as e: print(e)
    try:
        get_iol('https://iol.invertironline.com/mercado/cotizaciones/argentina/acciones/panel-l%C3%ADderes/mapa', 'Lideres')
        get_iol('https://iol.invertironline.com/mercado/cotizaciones/argentina/acciones/panel-general/mapa', 'Galpones')
        get_iol('https://iol.invertironline.com/mercado/cotizaciones/estados-unidos/adrs/argentina/mapa', 'ADR')
        get_iol('https://iol.invertironline.com/mercado/cotizaciones/argentina/cedears/todos/mapa', 'Cedears')

    except Exception as e: print(e)
    finally:
        with open('./Datos/Bolsa/Equity/Indices.json', "w") as file:
            json.dump(indices, file, indent=4)
        browser.close()
        playwright.stop()
        print('\n','---------\n', f'Tiempo transcurrido: {time.time()-start_time}')

if __name__ == "__main__":
    main()
