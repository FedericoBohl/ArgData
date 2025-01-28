from playwright.sync_api import sync_playwright
import pandas as pd
import time
import requests
import json
from bs4 import BeautifulSoup
pd.set_option('future.no_silent_downcasting', True)
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import plotly.express as px

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

def plot_sp500():
    # Cargar y procesar datos
    data = pd.merge(
        pd.read_csv('./Datos/Bolsa/Ponderaciones/SP500.csv', delimiter=';'), 
        pd.read_csv('./Datos/Bolsa/Equity/SP500.csv'), 
        on='Symbol'
    ).dropna(subset="Weight")
    
    df_grouped = data.groupby(["Sector", "Symbol"])[["Weight", "% Chg", "Company", "Price"]].min().reset_index()
    df_grouped['% Chg'] = pd.to_numeric(df_grouped['% Chg'])
    
    # Crear gráfico
    fig = px.treemap(
        df_grouped, 
        path=[px.Constant("SP500"), 'Sector', 'Symbol'],
        values='Weight',
        hover_name="% Chg",
        custom_data=["Company", 'Price', "% Chg"],
        color='% Chg', 
        range_color=[-4, 4],
        color_continuous_scale=[
            [0, '#ff2c2c'],
            [0.25, '#FF6A6A'],
            [0.5, '#FFFFFF'],
            [0.75, '#5ce65c'],
            [1, '#008000']
        ],
        labels={'Value': 'Number of Items'},
        color_continuous_midpoint=0
    )
    
    fig.update_traces(
        marker_line_width=1.5, 
        marker_line_color='#404040',
        hovertemplate="<br>".join([
            "<b>Empresa<b>: %{customdata[0]}",
            "<b>Precio (USD)<b>: %{customdata[1]}"
        ])
    )
    
    fig.data[0].texttemplate = "<b>%{label}</b><br>%{customdata[2]}%"
    fig.update_traces(marker=dict(cornerradius=10))
    fig.update_layout(margin=dict(l=1, r=1, t=25, b=25))
    
    # Guardar el gráfico como HTML
    fig.write_html(config=config,file="static/graphs/sp500.html", full_html=False, include_plotlyjs="cdn")

def plot_cedears():
    cedears_w=pd.merge(pd.read_csv('./Datos/Bolsa/Equity/Cedears.csv'), pd.read_csv('./Datos/Bolsa/Ponderaciones/Ratios_Cedears.csv'), right_on='ticker',left_on='Nombre')#.dropna(subset="Weight")
    cedears_w=pd.merge(cedears_w, pd.read_csv('./Datos/Bolsa/Equity/SP500.csv'), right_on='Symbol',left_on='ticker-usd')#.dropna(subset="Weight")
    cedears_w=pd.merge(cedears_w, pd.read_csv('./Datos/Bolsa/Ponderaciones/SP500.csv',delimiter=';'),on='Symbol')#.dropna(subset="Weight")

    df_grouped = cedears_w.groupby(["Sector", "Nombre"])[["Weight", "Var %", "nombre", "Precio"]].min().reset_index()
    fig = px.treemap(df_grouped, 
                    path=[px.Constant("SP500 en Cedears"), 'Sector',  'Nombre'], #Quite 'Industria', en 3
                    values='Weight',
                    hover_name="Var %",
                    custom_data=["nombre",'Precio',"Var %"],
                    color='Var %', 
                    range_color =[-6,6],
                    color_continuous_scale=colorscale,
                    labels={'Value': 'Number of Items'},
                    color_continuous_midpoint=0)
    fig.update_traces(marker_line_width = 1.5,marker_line_color='#404040',
        hovertemplate="<br>".join([
        "<b>Empresa<b>: %{customdata[0]}",
        "<b>Precio (ARS)<b>: %{customdata[1]}"
        ])
        )
    fig.data[0].texttemplate = "<b>%{label}</b><br>%{customdata[2]}%"
    fig.update_traces(marker=dict(cornerradius=10))
    fig.update_layout(margin=dict(l=1, r=1, t=25, b=25))
    fig.write_html(config=config,file="static/graphs/cedears.html", full_html=False, include_plotlyjs="cdn")
        
def plot_adr(data):
    data_merv = pd.merge(pd.read_csv('./Datos/Bolsa/Equity/ADR.csv'), data, right_on='Nombre-USD',left_on='Nombre').dropna()
    #data_merv['Var%'] = [float(i.replace(',', '.')) for i in data_merv["Var%"]]

    # Agrupamos los datos por 'Sector' y 'Nombre'
    df_grouped = data_merv.groupby(["Sector", "Nombre-USD"])[["CAP (MM)", "Var %", "Nombre Completo", "Precio"]].min().reset_index()
    fig = px.treemap(df_grouped, 
                    path=[px.Constant("Bolsa Argentina"), 'Sector',  'Nombre-USD'], #Quite 'Industria', en 3
                    values='CAP (MM)',
                    hover_name="Var %",
                    custom_data=["Nombre Completo",'Precio',"Var %"],
                    color='Var %', 
                    range_color =[-6,6],color_continuous_scale=colorscale,
                    labels={'Value': 'Number of Items'},
                    color_continuous_midpoint=0)
    fig.update_traces(marker_line_width = 1.5,marker_line_color='#404040',
        hovertemplate="<br>".join([
        "<b>Empresa<b>: %{customdata[0]}",
        "<b>Precio (ARS)<b>: %{customdata[1]}"
        ])
        )
    fig.data[0].texttemplate = "<b>%{label}</b><br>%{customdata[2]}%"
    fig.update_traces(marker=dict(cornerradius=10))
    fig.update_layout(margin=dict(l=1, r=1, t=25, b=25))
    fig.write_html(config=config,file=f"static/graphs/ADR.html", full_html=False, include_plotlyjs="cdn",default_width='50%')

def plot_acciones(data,data_now_merv,name):
    data_merv = pd.merge(data_now_merv, data, on='Nombre').dropna(subset='CAP (MM)')
    df_grouped = data_merv.groupby(["Sector", "Nombre"])[["CAP (MM)", "Var %", "Nombre Completo", "Precio"]].min().reset_index()
    fig = px.treemap(df_grouped, 
                    path=[px.Constant("Bolsa Argentina"), 'Sector',  'Nombre'], #Quite 'Industria', en 3
                    values='CAP (MM)',
                    hover_name="Var %",
                    custom_data=["Nombre Completo",'Precio',"Var %"],
                    color='Var %', 
                    range_color =[-6,6],color_continuous_scale=colorscale,
                    labels={'Value': 'Number of Items'},
                    color_continuous_midpoint=0)
    fig.update_traces(marker_line_width = 1.5,marker_line_color='#404040',
        hovertemplate="<br>".join([
        "<b>Empresa<b>: %{customdata[0]}",
        "<b>Precio (ARS)<b>: %{customdata[1]}"
        ])
        )
    fig.data[0].texttemplate = "<b>%{label}</b><br>%{customdata[2]}%"
    fig.update_traces(marker=dict(cornerradius=10))
    fig.update_layout(margin=dict(l=1, r=1, t=25, b=25))
    fig.write_html(config=config,file=f"static/graphs/{name}.html", full_html=False, include_plotlyjs="cdn")

def setup_browser():
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
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
        df.to_csv(name, index=False)

def extract_spy(page, indices):
    soup = BeautifulSoup(page.content(), 'html.parser')
    tables = soup.find_all('table')
    headers = [header.text.strip() for header in tables[0].find_all('th')]
    rows = [[cell.text.strip().replace('%','').replace('(','').replace(')','') for cell in row.find_all('td')] for row in tables[0].find_all('tr') if row.find_all('td')]
    sp500 = pd.DataFrame(rows, columns=headers)
    sp500.to_csv('./Datos/Bolsa/Equity/SP500.csv', index=False)
    print("S&P500 file created")
    indices["SPY"]['Price'] = float(rows[0][2])
    indices["SPY"]['Var'] = float(rows[0][4])
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
    except: pass
    try:
        page.goto("https://www.slickcharts.com/sp500")
        time.sleep(5)
        indices = extract_spy(page, indices)
    except: pass
    try:
        get_iol('https://iol.invertironline.com/mercado/cotizaciones/argentina/acciones/panel-l%C3%ADderes/mapa', './Datos/Bolsa/Equity/Lideres.csv')
    except Exception as e: print(e)
    finally:
        with open('./Datos/Bolsa/Equity/Indices.json', "w") as file:
            json.dump(indices, file, indent=4)
        browser.close()
        playwright.stop()
        plot_sp500()
        plot_cedears()
        data = pd.read_csv('./Datos/Bolsa/Ponderaciones/bolsa_arg.csv', delimiter=';')
        plot_acciones(data[data['Lider'] == 'Si'],pd.read_csv('./Datos/Bolsa/Equity/Lideres.csv'),name='lideres')
        plot_acciones(data[data['Lider'] == 'No'],pd.read_csv('./Datos/Bolsa/Equity/Galpones.csv'),name='galpones')
        plot_adr(data[data['ADR'] == 'Si'])
        print('\n','---------\n', f'Tiempo transcurrido: {time.time()-start_time}')

if __name__ == "__main__":
    main()
