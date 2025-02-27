import requests
import pandas as pd
from datetime import datetime

def get_dolar(url,
              name: None|str = None,
              start_date="2004-01-01",
              end_date=datetime.today().strftime("%Y-%m-%d")
              ) -> pd.DataFrame:
    start_date_str = "-".join(start_date.split("-")[::-1])
    end_date_str = "-".join(end_date.split("-")[::-1])

    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url + start_date_str + '/' + end_date_str, headers=headers)
        if response.status_code == 200:
            df = response.json()
            df=pd.DataFrame(df)
            df.columns=df.loc[0]
            df = df.drop(labels=0, axis=0)
            if 'Compra' in df.columns:
                df['Compra'] = df['Compra'].str.replace(",", ".").astype(float)
                df['Venta'] = df['Venta'].str.replace(",", ".").astype(float)
            else:
                df['Referencia'] = df['Referencia'].str.replace(",", ".").astype(float)
            df.Fecha=pd.to_datetime(df.Fecha,format='%d/%m/%Y')
            df.sort_values(by=['Fecha'], inplace=True)
            df = df.drop_duplicates("Fecha")
            df=df.reset_index()
            df=df.drop(['index'],axis=1)
            df.set_index('Fecha',inplace=True)
            if isinstance(name,str):
                df.columns= [f'{name}-{c}' for c in df.columns] if len(df.columns)>1 else [name]
            return df
        else:
            print(f"{name if isinstance(name,str) else ''}\n Error {response.status_code}: No se pudo acceder a los datos.")
            return pd.DataFrame()
    except Exception as e:
        print('Error with: \n',url)
        print(e)
        return pd.DataFrame()
        
def main():
    blue = get_dolar("https://mercados.ambito.com//dolar/informal/historico-general/",name='Blue')
    oficial = get_dolar("https://mercados.ambito.com//dolar/oficial/historico-general/",name='Oficial')
    mep = get_dolar("https://mercados.ambito.com//dolarrava/mep/historico-general/",name='MEP')
    ccl = get_dolar("https://mercados.ambito.com//dolarrava/cl/historico-general/",name='CCL')

    dolares = pd.concat([oficial,blue,mep,ccl],axis=1)
    if len(dolares)>0:
        dolares.to_csv('Datos/Dolares.csv')

if __name__=="__main__":
    main()