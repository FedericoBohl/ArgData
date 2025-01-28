Este repositorio abierto tiene el fin de proveer datos del mercado argentino e internacional gratis y de acceso simple y rápido.

Los datos vienen guardados en archivos delimitados por coma (csv) y pueden acceder a ellos mediante **Python** con librerias como pandas o requests o mediante **Excel** conectandose al link de la base. Un simple ejemplo en python sería el siguiente:

```python
import pandas as pd

# URL del archivo CSV en GitHub (debe ser el enlace "raw")
url = "https://raw.githubusercontent.com/FedericoBohl/ArgData/main/Datos/Bolsa/Bonos/CER.csv"

# Leer el CSV directamente desde GitHub
df = pd.read_csv(url)

# Mostrar las primeras filas
print(df.head())
```

Debería remplazar "Bolsa" por "FOCM" si quiere obtener el JSON con las probabilidades implícitas que el mercado pricea para la tasas de interés a ser anunciada en próximas reuniones del FOCM. Siga el path dentro de la carpeta Datos de este repositorio para tener referencia de como obtener cada csv en particular.
