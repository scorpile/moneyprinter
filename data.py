import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener las configuraciones desde el archivo .env
apiKey = os.getenv('BINANCE_API_KEY')
apiSecret = os.getenv('BINANCE_API_SECRET')
discordwebhook = os.getenv('DISCORD_WEBHOOK')
devMode = os.getenv('DEV_MODE', 'False').lower() == 'true'  # Convertir a booleano

symbol = 'SOLUSDT'
