from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET, ORDER_TYPE_LIMIT
import data  # Import variables from data.py

class BinanceClient:
    def __init__(self):
        # Use variables from data.py
        self.api_key = data.apiKey
        self.api_secret = data.apiSecret
        
        # Initialize the Binance client
        self.client = Client(self.api_key, self.api_secret)

    def get_price(self, symbol):
        """
        Gets the current price of a symbol (e.g., SOLUSDT).
        """
        ticker = self.client.get_symbol_ticker(symbol=symbol)
        return float(ticker['price'])

    def place_order(self, symbol, side, quantity, order_type=ORDER_TYPE_MARKET, price=None):
        """
        Places an order on Binance.
        :param symbol: Trading symbol (e.g., SOLUSDT).
        :param side: Order side (BUY or SELL).
        :param quantity: Quantity to buy or sell.
        :param order_type: Order type (default is ORDER_TYPE_MARKET).
        :param price: Price (only for limit orders).
        """
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity,
                price=price
            )
            return order
        except Exception as e:
            print(f"Error placing order: {e}")
            return None

    def get_account_info(self):
        """
        Gets account information, including balances.
        """
        return self.client.get_account()

    def get_balance(self, asset):
        """
        Gets the available balance of a specific asset (e.g., USDT).
        """
        balance = self.client.get_asset_balance(asset=asset)
        return float(balance['free'])

    def get_total_usd_balance(self):
        """
        Calculates the total USD balance by summing up the value of all assets.
        """
        account_info = self.get_account_info()
        total_usd = 0

        for balance in account_info['balances']:
            asset = balance['asset']
            free = float(balance['free'])

            if free > 0:
                if asset == "USDT":
                    # If the asset is USDT, add directly to the total
                    total_usd += free
                else:
                    # Try to get the price in USDT
                    symbol_usdt = f"{asset}USDT"
                    try:
                        ticker = self.client.get_symbol_ticker(symbol=symbol_usdt)
                        price = float(ticker['price'])
                        total_usd += free * price
                    except Exception as e:
                        # If USDT pair doesn't exist, try with BTC
                        symbol_btc = f"{asset}BTC"
                        try:
                            ticker_btc = self.client.get_symbol_ticker(symbol=symbol_btc)
                            price_btc = float(ticker_btc['price'])

                            # Get BTC price in USDT
                            ticker_btc_usdt = self.client.get_symbol_ticker(symbol="BTCUSDT")
                            btc_price_usdt = float(ticker_btc_usdt['price'])

                            # Calculate value in USD
                            total_usd += free * price_btc * btc_price_usdt
                        except Exception as e:
                            print(f"Could not get price for {asset}: {e}")

        return total_usd

    def get_historical_klines(self, symbol, interval, start_str, end_str=None):
        """
        Gets historical kline (candlestick) data for a specific symbol and interval.
        """
        klines = self.client.get_historical_klines(symbol, interval, start_str, end_str)
        return klines
    
# FOR TESTING, EXECUTE client.py
if __name__ == "__main__":
    client = BinanceClient()
    
    # Get the price of SOLUSDT
    price = client.get_price("SOLUSDT")
    print(f"Price of SOLUSDT: {price}")
    
    # Get the balance of USDT
    usdt_balance = client.get_balance("USDT")
    print(f"USDT Balance: {usdt_balance}")
    
    # Get the total balance in USD
    total_usd_balance = client.get_total_usd_balance()
    print(f"Total balance in USD: {total_usd_balance}")
