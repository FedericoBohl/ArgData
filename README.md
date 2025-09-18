This open repository aims to provide free, simple, and fast access to data from the Argentine and international markets.

The data is stored in comma-delimited files (CSV) and can be accessed using Python with libraries such as pandas or requests, or through Excel by connecting to the database link via Data > Get Data > From File > From Text/CSV. A simple example in Python would be the following:

```python
import pandas as pd

# URL of the CSV file on GitHub (must be the "raw" link)
url = "https://raw.githubusercontent.com/FedericoBohl/ArgData/main/Datos/Bolsa/Bonos/CER.csv"

# Read the CSV directly from GitHub
df = pd.read_csv(url)

# Display the first rows
print(df.head())
```

You should replace "Bolsa" with "FOCM" if you want to obtain the JSON with the implied probabilities that the market is pricing for the interest rates to be announced in upcoming FOCM meetings. Follow the path inside the "Datos" folder of this repository to reference how to obtain each specific CSV.
