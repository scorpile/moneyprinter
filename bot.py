import time
import traceback
from datetime import datetime
from discord_webhook import DiscordWebhook, DiscordEmbed
import data  # Importamos las variables de data.py
from client import BinanceClient  # Importamos la clase BinanceClient
from binance.enums import SIDE_BUY, SIDE_SELL
import pandas as pd
from data import symbol

binance_wrapper = BinanceClient()

def getMarketData(avgprices, volumes, interval='1m', symbol=symbol):
    """
    Obtiene datos del mercado utilizando la API de Binance.
    """
    max_retries = 5  # Número máximo de intentos para obtener datos
    retry_delay = 10  # Tiempo de espera entre intentos (en segundos)

    for attempt in range(max_retries):
        try:
            # Obtener datos de velas (kline) desde Binance
            klines = binance_wrapper.client.get_klines(symbol=symbol, interval=interval, limit=100)

            # Convertir los datos en un DataFrame de pandas
            columns = [
                'Open time', 'Open', 'High', 'Low', 'Close', 'Volume',
                'Close time', 'Quote asset volume', 'Number of trades',
                'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'
            ]
            data = pd.DataFrame(klines, columns=columns)

            # Convertir las columnas a tipos numéricos
            data['Open'] = data['Open'].astype(float)
            data['High'] = data['High'].astype(float)
            data['Low'] = data['Low'].astype(float)
            data['Close'] = data['Close'].astype(float)
            data['Volume'] = data['Volume'].astype(float)

            # Verificar si los datos están vacíos
            if data.empty:
                print(f"[WARNING] No se obtuvieron datos en el intento {attempt + 1}. Reintentando...")
                time.sleep(retry_delay)
                continue

            # Imprimir los datos descargados para depuración
            #print("[DEBUG] Datos descargados de Binance:")
            #print(data.tail())  # Mostrar las últimas filas

            # Procesar los datos
            df = data.iloc[::-1]  # Invertir el DataFrame para obtener los datos más recientes al principio

            # Extraer valores escalares
            stockOpen = df['Open'].iloc[0]  # Último valor de Open
            high = df['High'].iloc[0]       # Último valor de High
            low = df['Low'].iloc[0]         # Último valor de Low
            close = df['Close'].iloc[0]     # Último valor de Close
            volume = df['Volume'].iloc[0]   # Último valor de Volume

            # Verificar si el volumen es cero
            if volume == 0:
                print("[WARNING] El volumen es cero. Reintentando...")
                time.sleep(retry_delay)
                continue

            # Calcular VWAP
            VWAPList = (data['Volume'] * (data['High'] + data['Low'] + data['Close']) / 3).cumsum() / data['Volume'].cumsum()
            VWAP = VWAPList.iloc[-1]  # Último valor de VWAP

            # Calcular RSI
            window_length = 14
            close_delta = data['Close'].diff()
            up = close_delta.clip(lower=0)
            down = -1 * close_delta.clip(upper=0)
            ma_up = up.ewm(com=window_length - 1, adjust=True, min_periods=window_length).mean()
            ma_down = down.ewm(com=window_length - 1, adjust=True, min_periods=window_length).mean()
            rsiA = ma_up / ma_down
            rsiList = 100 - (100 / (1 + rsiA))
            rsi = rsiList.iloc[-1]  # Último valor de RSI

            # Calcular EMAs
            ema12 = data['Close'].ewm(span=9, adjust=False).mean().iloc[-1]  # EMA de 12 períodos
            ema26 = data['Close'].ewm(span=21, adjust=False).mean().iloc[-1]  # EMA de 26 períodos
            ema5 = data['Close'].ewm(span=8, adjust=False).mean().iloc[-1]    # EMA de 5 períodos

            # Calcular MACD
            k = data['Close'].ewm(span=12, adjust=False, min_periods=12).mean()
            d = data['Close'].ewm(span=26, adjust=False, min_periods=26).mean()
            macd = k - d
            macd_s = macd.ewm(span=9, adjust=False, min_periods=9).mean()
            macd_h = macd - macd_s

            currentmacd = macd.iloc[-1]    # Último valor de MACD
            currenthisto = macd_h.iloc[-1] # Último valor del histograma MACD

            # Mostrar los indicadores para depuración
            # print("[DEBUG] Indicadores obtenidos:")
            # print(f"stockOpen: {stockOpen}")
            # print(f"high: {high}")
            # print(f"low: {low}")
            # print(f"close: {close}")
            # print(f"volume: {volume}")
            # print(f"VWAP: {VWAP}")
            # print(f"RSI: {rsi}")
            # print(f"EMA12: {ema12}")
            # print(f"EMA26: {ema26}")
            # print(f"EMA5: {ema5}")
            # print(f"MACD: {currentmacd}")
            # print(f"Histogram (MACD): {currenthisto}")
            # print(f"avgprice: {(high + low + close) / 3}")

            # Devolver los datos procesados
            return {
                'stockOpen': stockOpen, 'high': high, 'low': low, 'close': close, 'volume': volume,
                'RSI': rsi, 'MACD': currentmacd, 'VWAP': VWAP, 'STOCH': 0, 'histogram': currenthisto,
                'ema12': ema12, 'ema26': ema26, 'avgprices': avgprices, 'avgprice': (high + low + close) / 3,
                'volumes': volumes, 'macdlist': macd_s, 'ema12list': ema12, 'ema26list': ema26, 'ema5': ema5
            }

        except Exception as e:
            print(f"[ERROR] Error en el intento {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                print(f"[INFO] Reintentando en {retry_delay} segundos...")
                time.sleep(retry_delay)
            else:
                print("[ERROR] No se pudieron obtener los datos después de varios intentos.")
                return None  # Devolver None si no se pueden obtener los datos


class TradeBot:
    def __init__(self):
        print('[TRADEBOT] initializing trading bot...')

        # Inicializar el cliente de Binance
        self.client = BinanceClient()

        # Configuración inicial
        self.openTrades = {}
        self.buyOrders = {}
        self.sellOrders = {}
        self.triggerEvents = {}
        self.url = data.discordwebhook
        self.watching = False
        self.openQT = 0
        self.gains = []
        self.cash = 0  # Inicializar self.cash
        self.buyVal = 0  # Inicializar self.buyVal

        if data.devMode:
            self.accountBalance = 10547.99  # Valor numérico
        else:
            self.accountBalance = float(self.client.get_total_usd_balance())  # Convertir a float

        self.startingBal = float(self.accountBalance)  # Asegurar que sea un valor numérico
        self.cash = float(self.accountBalance)  # Inicializar self.cash con el saldo inicial
        print(f'[TRADEBOT] account balance: ${self.accountBalance:.2f}')

    def getPrice(self, avgprices, volumes, interval='1m', coin=symbol):
        """
        Obtiene el precio actual del mercado.
        """
        #print("[DEBUG] Solicitando Indicadores")
        try:
            # Obtener los indicadores del mercado
            self.price = getMarketData(avgprices, volumes, interval=interval)
            #print("[DEBUG] Indicadores obtenidos!")
            
            # Verificar si self.price es un diccionario y contiene 'close'
            if not isinstance(self.price, dict) or 'close' not in self.price:
                raise ValueError("Los indicadores obtenidos no son válidos o no contienen 'close'.")
            
            # Establecer el precio actual (sin usar .iloc[0] porque es un valor escalar)
            self.priceNum = float(round(self.price['close'], 2))  # Redondear y convertir a float
            
            # Calcular el valor abierto si hay una cantidad abierta
            if self.openQT != 0:
                self.openVal = float(self.priceNum * self.openQT)  # Asegurar que sea un valor numérico
            else:
                self.openVal = 0.0  # Asegurar que sea un valor numérico
            
            # Imprimir el precio establecido
            #print("[DEBUG] Precio establecido: ", self.price)
            
        except Exception as e:
            # Capturar cualquier excepción y mostrar un mensaje de error
            #print(f"[ERROR] Error en getPrice: {e}")
            #print(f"[DEBUG] Tipo de self.price: {type(self.price)}")
            #print(f"[DEBUG] Contenido de self.price: {self.price}")
            self.price = None  # Establecer self.price como None en caso de error
        
        return self.price

    def placeOrder(self, coin, type):
        """
        Coloca una orden de compra o venta.
        """
        success = True
        price = float(self.priceNum)  # Asegurar que sea un valor numérico

        if success:
            if type == 'BUY':
                # Calcular la cantidad a comprar
                balance = float(self.client.get_balance("USDT"))  # Asegurar que sea un valor numérico
                quantity = balance / price
                quantity = round(quantity, 4)  # Ajustar según el tamaño mínimo de la orden

                # Colocar la orden de compra
                self.client.place_order(symbol=coin, side=SIDE_BUY, quantity=quantity)
                self.openQT = float(quantity)  # Asegurar que sea un valor numérico
                self.cash = float(balance - (price * quantity))  # Asegurar que sea un valor numérico
                self.buyPrice = float(price)  # Asegurar que sea un valor numérico
                self.buyQT = float(quantity)  # Asegurar que sea un valor numérico
                self.buyVal = float(self.buyPrice * self.buyQT)  # Asegurar que sea un valor numérico
                self.logData()
            else:
                # Colocar la orden de venta
                print(f'[TRADEBOT] placing SELL order at {self.priceNum}')
                self.client.place_order(symbol=coin, side=SIDE_SELL, quantity=self.openQT)
                self.accountBalance = float(self.cash + (self.priceNum * self.openQT))  # Asegurar que sea un valor numérico
                self.soldVal = float(self.cash + (self.priceNum * self.openQT))  # Asegurar que sea un valor numérico
                self.soldQT = float(self.openQT)  # Asegurar que sea un valor numérico
                self.cash = float(self.accountBalance)  # Asegurar que sea un valor numérico
                self.openQT = 0.0  # Asegurar que sea un valor numérico
                self.logData()

        return success, price

    def logData(self):
        """
        Registra los datos de la operación.
        """
        self.accountBalance = float(round(self.cash + (self.priceNum * self.openQT), 2))  # Asegurar que sea un valor numérico

        if self.accountBalance > self.startingBal:
            self.dayGain = float(self.accountBalance - self.startingBal)  # Asegurar que sea un valor numérico
        elif self.accountBalance < self.startingBal:
            self.dayGain = float(-(self.startingBal - self.accountBalance))  # Asegurar que sea un valor numérico
        else:
            self.dayGain = 0.0  # Asegurar que sea un valor numérico

        if self.openQT != 0:
            self.openVal = float(self.openQT * self.priceNum)  # Asegurar que sea un valor numérico
            if self.openVal > self.buyVal:
                self.openGain = float(self.openVal - self.buyVal)  # Asegurar que sea un valor numérico
            elif self.openVal < self.buyVal:
                self.openGain = float(-(self.buyVal - self.openVal))  # Asegurar que sea un valor numérico
            else:
                self.openGain = 0.0  # Asegurar que sea un valor numérico
        else:
            self.openGain = 0.0  # Asegurar que sea un valor numérico
            self.openVal = 0.0  # Asegurar que sea un valor numérico

    def updateMessage(self):
        """
        Actualiza el mensaje de estado en Discord.
        """
        self.logData()

        self.openGain = self.openVal - self.buyVal

        self.webhook = DiscordWebhook(url=self.url, username='Nyria', content='')
        self.embed = DiscordEmbed(title='[STATUS UPDATE]', description='', color='4200FF')
        self.embed.add_embed_field(name='Time', value=str(time.strftime("%H:%M")))
        self.embed.add_embed_field(name='Account Balance', value=f'**${self.accountBalance:.2f}**')
        self.embed.add_embed_field(name='Current Price', value=f'${self.priceNum:.2f}')
        self.embed.add_embed_field(name='Open QT', value=f'x **{self.openQT:.4f}**')
        self.embed.add_embed_field(name='Market Value', value=f'${self.openVal:.2f}')

        if self.openVal < self.buyVal:
            self.gainPerc = f'-{round((abs(self.openGain) / self.buyVal) * 100, 2)}%'
            self.gainText = f'**-${abs(self.openGain):.2f}** ({self.gainPerc})'
        elif self.openVal > self.buyVal:
            self.gainPerc = f'+{round((self.openGain / self.buyVal) * 100, 2)}%'
            self.gainText = f'**+${self.openGain:.2f}** ({self.gainPerc})'
        else:
            self.gainText = '**$0**'

        self.embed.add_embed_field(name='Open Gain', value=self.gainText)

        if self.accountBalance < self.startingBal:
            self.dayGain = self.startingBal - self.accountBalance
            self.gainPerc = f'-{round((abs(self.dayGain) / self.startingBal) * 100, 2)}%'
            self.gainText = f'**-${abs(self.dayGain):.2f}** ({self.gainPerc})'
        elif self.accountBalance > self.startingBal:
            self.dayGain = self.accountBalance - self.startingBal
            self.gainPerc = f'+{round((self.dayGain / self.startingBal) * 100, 2)}%'
            self.gainText = f'**+${self.dayGain:.2f}** ({self.gainPerc})'
        else:
            self.gainText = '**$0**'

        self.embed.add_embed_field(name='Day Gain', value=self.gainText)

        self.webhook.add_embed(self.embed)
        response = self.webhook.execute()

    def pushDiscordNotif(self, url, type=''):
        """
        Envía una notificación a Discord.
        """
        try:
            if type == 'watching' or self.watching:
                self.color = '3464eb'
                self.title = '[READY]'
                self.desc = '**Now watching $SOL for a scalp due to an oversold dip.**'

            if type == 'sell':
                self.color = 'eb3453'
                self.title = '[SOLD]'
                self.desc = f'**Placed a SELL order in $SOL @ {self.priceNum:.2f}**'

            if type == 'buy':
                self.color = '03fca9'
                self.title = '[PURCHASED]'
                self.desc = f'**Placed a LONG order in $SOL @ {self.priceNum:.2f}**'

            if type == 'start_msg':
                self.color = '53eb34'
                self.title = '[ENABLED]'
                self.desc = '**Trading bot is now enabled.**'

            self.webhook = DiscordWebhook(url=url, username='Nyria', content='')
            self.embed = DiscordEmbed(title=self.title, description=self.desc, color=self.color)
            self.embed.add_embed_field(name='Time', value=str(time.strftime("%H:%M")))

            if type != 'start_msg':
                self.embed.add_embed_field(name='Price', value=f'**${self.priceNum:.2f}**')

                if type == 'buy':
                    self.embed.add_embed_field(name='QT', value=f'x {self.openQT:.4f}')
                    self.embed.add_embed_field(name='Value', value=f'**${self.openVal:.2f}**')

                if type == 'sell':
                    self.embed.add_embed_field(name='QT', value=f'x {self.soldQT:.4f}')

                    self.openGain = self.soldVal - self.buyVal
                    if self.openGain < 0:
                        self.gains.append(-(round((abs(self.openGain) / self.buyVal) * 100, 2)))
                    else:
                        self.gains.append(round((abs(self.openGain) / self.buyVal) * 100, 2))
                    self.avgGain = round(sum(self.gains) / len(self.gains), 2)

                    self.embed.add_embed_field(name='Bought Price', value=f'${self.buyPrice:.2f}')
                    self.embed.add_embed_field(name='Bought Value', value=f'${self.buyVal:.2f}')

                    if self.soldVal > self.buyVal:
                        self.soldValText = f'**${self.soldVal:.2f}** +${round(self.openGain, 2)} (+{round(((self.soldVal - self.buyVal) / self.buyVal) * 100, 2)}%)'
                    else:
                        self.soldValText = f'**${self.soldVal:.2f}** -${round(self.buyVal - self.soldVal, 2)} (-{round(((self.buyVal - self.soldVal) / self.buyVal) * 100, 2)}%)'

                    self.embed.add_embed_field(name='Sold Value', value=self.soldValText)
                    self.embed.add_embed_field(name='New Balance', value=f'**${self.accountBalance:.2f}**')

                    if self.soldVal < self.buyVal:
                        self.gainPerc = f'-{round((abs(self.openGain) / self.buyVal) * 100, 2)}%'
                        self.gainText = f'**-${round(abs(self.openGain), 2)}** ({self.gainPerc})'
                    elif self.soldVal > self.buyVal:
                        self.gainPerc = f'+{round((self.openGain / self.buyVal) * 100, 2)}%'
                        self.gainText = f'**+${round(self.openGain, 2)}** ({self.gainPerc})'
                    else:
                        self.gainText = '**$0**'

                    self.embed.add_embed_field(name='Realized Gain', value=self.gainText)

                    if self.accountBalance < self.startingBal:
                        self.dayGain = self.startingBal - self.accountBalance
                        self.gainPerc = f'-{round((abs(self.dayGain) / self.startingBal) * 100, 2)}%'
                        self.gainText = f'**-${round(abs(self.dayGain), 2)}** ({self.gainPerc})'
                    elif self.accountBalance > self.startingBal:
                        self.dayGain = self.accountBalance - self.startingBal
                        self.gainPerc = f'+{round((self.dayGain / self.startingBal) * 100, 2)}%'
                        self.gainText = f'**+${round(self.dayGain, 2)}** ({self.gainPerc})'
                    else:
                        self.gainText = '**$0**'

                    self.embed.add_embed_field(name='Day Gain', value=self.gainText)

                    if self.avgGain < 0:
                        self.avgGainText = f'-{abs(self.avgGain):.2f}%'
                    else:
                        self.avgGainText = f'+{abs(self.avgGain):.2f}%'

                    self.embed.add_embed_field(name='Trades Taken', value=str(len(self.gains)))
                    self.embed.add_embed_field(name='Avg % Gain', value=self.avgGainText)

            else:
                self.embed.add_embed_field(name='Traded Assets', value='**$SOL**')
                self.embed.add_embed_field(name='Starting Balance', value=f'**${self.accountBalance:.2f}**')

            self.webhook.add_embed(self.embed)
            response = self.webhook.execute()

            return True
        except Exception as exception:
            print(f"Error sending Discord notification: {exception}")
            return False

#PARA PRUEBAS SE EJECUTA bot.py
if __name__ == "__main__":
    bot = TradeBot()
    bot.getPrice([], [], interval='1m', coin=symbol)
    bot.updateMessage()
