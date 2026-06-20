import gspread
from google.oauth2.service_account import Credentials

# Permisos que necesita la app
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Cargar credenciales del archivo JSON
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
client = gspread.authorize(creds)

# Abrir tu Google Sheet por nombre
sheet = client.open("BASE_DATOS_LIMPIA").sheet1

# Leer todos los datos
data = sheet.get_all_records()
print(data)