import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
from datetime import datetime

#   Chequear cual es el último mes en el archivo de Excel
response=requests.get('https://www.argentina.gob.ar/economia/finanzas/datos-mensuales-de-la-deuda/datos')
soup=BeautifulSoup(response.content,'html.parser')
deuda=soup.find_all('a', string='Descargar')[0]['href'].replace('blank:#', '')
print(deuda)

if response.status_code == 200:
    try:
        response = requests.get(deuda)
        # Leer el archivo de Excel en un DataFrame sin guardarlo
        excel_data = io.BytesIO(response.content)
        xls = pd.ExcelFile(excel_data)
        #       DEUDA BRUTA DE LA ADMINISTRACIÓN CENTRAL
        sheet_A1 = pd.read_excel(xls, sheet_name='A.1', skiprows=8).drop(columns=['Unnamed: 0'])
        sheet_A1=sheet_A1.dropna(subset="Unnamed: 1")
        cortes={'TÍTULOS PÚBLICOS':None,
                'LETRAS DEL TESORO':None,
                'PRÉSTAMOS':None,
                '        CORTO PLAZO (1)':None,
                }

        for k in cortes:
            value=sheet_A1[sheet_A1['Unnamed: 1']==k].index
            cortes[k]=value[0]-1
        stop=cortes[list(cortes.keys())[-1]]
        sheet_A1=sheet_A1.loc[:stop]
        titpublicos=sheet_A1.loc[cortes['TÍTULOS PÚBLICOS']:cortes['LETRAS DEL TESORO']]
        letras=sheet_A1.loc[cortes['LETRAS DEL TESORO']:cortes['PRÉSTAMOS']]
        prestamos=sheet_A1.loc[cortes['PRÉSTAMOS']:]

        def fix_df(df:pd.DataFrame):
            sheet_A1=df.transpose()

            sheet_A1.columns = sheet_A1.iloc[0]
            sheet_A1 = sheet_A1[1:]
            sheet_A1.index.name = sheet_A1.columns.name
            # Get the last element in the index that is a datetime
            last_datetime_index = sheet_A1.index[sheet_A1.index.map(lambda x: isinstance(x, datetime))].max()
            # Create a list with the index up to that element (inclusive)
            index_list = list(sheet_A1.index[:sheet_A1.index.get_loc(last_datetime_index) + 1])

            # Add the next following months
            additional_months = sum([" (*)" in str(i) for i in sheet_A1.index])
            for _ in range(additional_months):
                last_datetime_index += pd.DateOffset(months=1)
                index_list.append(last_datetime_index)
            index_list.append(pd.NA)
            sheet_A1.index = index_list
            sheet_A1=sheet_A1.iloc[:-1]
            return sheet_A1

        titpublicos=fix_df(titpublicos)[['TÍTULOS PÚBLICOS',' - Moneda nacional','Deuda no ajustable por CER','Deuda ajustable por CER',' - Moneda extranjera ']]
        titpublicos.columns=['Total','Moneda Nacional','No ajustable por CER','Ajustable por CER','Moneda Extranjera']
        titpublicos.to_csv('Datos/Deuda/TitulosPublicos.csv')

        letras=fix_df(letras)[['LETRAS DEL TESORO',' - Moneda nacional',' - Moneda extranjera ']]
        letras.columns=['Total','Moneda Nacional','Moneda Extranjera']
        letras.to_csv('Datos/Deuda/LetrasTesoro.csv')
        
        prestamos=fix_df(prestamos)
        prestamos.to_csv('Datos/Deuda/Prestamos.csv')
        
        #       PAGOS DE DEUDA BRUTA DE LA ADMINISTRACION CENTRAL
        sheet_A5 = pd.read_excel(xls, sheet_name='A.5',skiprows=11).drop(columns=['Unnamed: 0']).dropna(subset="Unnamed: 1")
        stop=sheet_A5[sheet_A5['Unnamed: 1']=='TOTAL PAGADO POR TIPO DE ACREEDOR E INSTRUMENTO'].index[0]-1
        sheet_A5=sheet_A5.loc[:stop]
        deuda_mon=sheet_A5.transpose()#.iloc[2:-1]
        deuda_mon.columns=deuda_mon.iloc[0]
        deuda_mon=deuda_mon.iloc[1:-1]
        deuda_mon.columns=['Total Pagado', 'Total-Moneda Nacional', 'Capital-Moneda Nacional', 'Intereses-Moneda Nacional', 'Total-Moneda Extranjera', 'Capital-Moneda Extranjera', 'Intereses-Moneda Extranjera']
        deuda_mon.to_csv('Datos/Deuda/PagosDeuda.csv')
    except Exception as e:
        print('Error en la lectura del archivo de Excel\n',e)

else:print('Error en la descarga del archivo\n',response.status_code)