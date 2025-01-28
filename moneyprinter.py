from discord_webhook import DiscordWebhook, DiscordEmbed
import bot
import data
from datetime import datetime
import time
import csv
import traceback
import numpy as np
from data import symbol

# Initialize the trading bot
bot = bot.TradeBot()

def makeTrade(tradearray, trends, type):
    """
    Performs a buy or sell operation.
    """
    success = False

    if type == 'BUY':
        color = '03fca9'
        title = '[Trading Bot] | [PURCHASED]'
        desc = f'**Placed a LONG order @ {bot.priceNum:.2f}**'

        try:
            success, price = bot.placeOrder(symbol, 'BUY')
        except Exception as exception:
            print('[!] critical error in order placement.')
            traceback.print_exc()
    else:
        color = 'eb3453'
        title = '[Trading Bot] | [SOLD]'
        desc = f'**Placed a SELL order @ {bot.priceNum:.2f}**'

        try:
            success, price = bot.placeOrder(symbol, 'SELL')
        except Exception as exception:
            print('[!] critical error in order placement.')
            traceback.print_exc()

    if success:
        try:
            bot.pushDiscordNotif(data.discordwebhook, type=type.lower())
        except:
            webhook = DiscordWebhook(url=data.discordwebhook, username='Nyria', content='')
            embed = DiscordEmbed(title=title, description=desc, color=color)
            embed.add_embed_field(name='Time', value=str(time.strftime("%H:%M")))
            embed.add_embed_field(name='Price', value=f'${bot.priceNum:.2f}')

            if type == 'SELL':
                embed.add_embed_field(name='New Balance', value=f'**${bot.accountBalance:.2f}**')

                gain = bot.accountBalance - bot.startingBal
                if gain < 0:
                    gainText = f'**-${abs(gain):.2f}**'
                elif gain > 0:
                    gainText = f'**+${gain:.2f}**'
                else:
                    gainText = '**$0**'

                embed.add_embed_field(name='Day Gain', value=gainText)

            webhook.add_embed(embed)
            response = webhook.execute()

    # Log trade
    now = datetime.now()
    dt_string = now.strftime("%d-%m-%Y")
    with open(f'{dt_string}_SOLtrades.csv', 'a') as outputcsv:
        writer_ = csv.writer(outputcsv)
        writer_.writerow(tradearray)
        writer_.writerow(trends)
        outputcsv.close()

    # Determine buy strength
    trndcnt = 0
    for trend in trends:
        if trend == 'FALSE':
            trndcnt += 1
    if trndcnt > 5:
        strong = True
    else:
        strong = False

    return success

def createCSV():
    """
    Creates a CSV file to record trades.
    """
    fields = ['TIME', 'HIGH', 'LOW', 'CLOSE', 'RSI', 'VWAP', 'EMA12', 'EMA26', 'MACD', 'STOCH']
    now = datetime.now()
    dt_string = now.strftime("%d-%m-%Y")

    with open(f'{dt_string}_SOLtrades.csv', 'w') as outputcsv:
        writer_ = csv.writer(outputcsv)
        writer_.writerow(fields)
        outputcsv.close()

def compareForEntry(previous, dataDict):
    """
    Compares current data with previous data to determine if a trade should be entered.
    """
    # Ensure that you are comparing scalar values
    stock_open = dataDict['stockOpen'].iloc[-1] if hasattr(dataDict['stockOpen'], 'iloc') else dataDict['stockOpen']
    close_price = dataDict['close'].iloc[-1] if hasattr(dataDict['close'], 'iloc') else dataDict['close']
    previous_close = previous['close'][-1]

    if stock_open < previous_close or close_price < previous_close:
        priceDowntrend = True
    else:
        priceDowntrend = False

    # Compare MACD
    macd = dataDict['MACD'].iloc[-1] if hasattr(dataDict['MACD'], 'iloc') else dataDict['MACD']
    previous_macd = previous['MACD'][-1]
    if macd < previous_macd:
        MACDdowntrend = True
    else:
        MACDdowntrend = False

    # Compare RSI
    rsi = dataDict['RSI'].iloc[-1] if hasattr(dataDict['RSI'], 'iloc') else dataDict['RSI']
    previous_rsi = previous['RSI'][-1]
    if rsi < previous_rsi:
        RSIdowntrend = True
    else:
        RSIdowntrend = False

    # Compare VWAP
    vwap = dataDict['VWAP'].iloc[-1] if hasattr(dataDict['VWAP'], 'iloc') else dataDict['VWAP']
    previous_vwap = previous['VWAP'][-1]
    if close_price < vwap:
        if (vwap - close_price) > (previous_vwap - previous_close):
            LowerFromVWAP = True
        else:
            LowerFromVWAP = False
    else:
        LowerFromVWAP = False

    # Compare STOCH
    stoch = dataDict['STOCH'].iloc[-1] if hasattr(dataDict['STOCH'], 'iloc') else dataDict['STOCH']
    previous_stoch = previous['STOCH'][-1]
    if stoch < previous_stoch:
        STOCHdowntrend = True
    else:
        STOCHdowntrend = False

    # Compare close
    if close_price < previous_close:
        closeDowntrend = True
    else:
        closeDowntrend = False

    # Compare EMA12
    ema12 = dataDict['ema12'].iloc[-1] if hasattr(dataDict['ema12'], 'iloc') else dataDict['ema12']
    previous_ema12 = previous['ema12'][-1]
    if stock_open < ema12 or close_price < ema12:
        if (ema12 - stock_open) > (previous_ema12 - previous['stockOpen'][-1]):
            LowerFromEMA12 = True
        else:
            LowerFromEMA12 = False
    else:
        LowerFromEMA12 = False

    return priceDowntrend, MACDdowntrend, RSIdowntrend, LowerFromVWAP, STOCHdowntrend, closeDowntrend, LowerFromEMA12

def calculate_macd_threshold(macd_values, percentile=0.05):
    """
    Calculates a dynamic MACD threshold by taking the percentile (default 5%).
    If the current MACD falls below this threshold, it is considered to be in the 'very low zone' relative to recent history.

    :param macd_values: List or array of recent MACD values
    :param percentile:  Value between 0 and 1 indicating the percentile
                        (0.05 => 5% of values are below)
    :return:            MACD threshold
    """
    # Convert to numpy array for convenience
    macd_array = np.array(macd_values)

    # Calculate the percentile threshold
    threshold = np.quantile(macd_array, percentile)

    return threshold

# Initial variables
laststatus = 'NULL'
rsis = []
volumes = []
avgprices = []
first = True
histogram = 'NULL'
RSI = 'NULL'
opentime = False
exitNeeded = False
last_secs = '0'
MACDdowntrend = False
RSIdowntrend = False

# Previous data and trends
previous = {'VWAP': [], 'close': [], 'MACD': [], 'RSI': [], 'STOCH': [], 'ema12': [], 'stockOpen': []}
previousTrends = {'priceDowntrend': [], 'MACDdowntrend': [], 'RSIdowntrend': [], 'LowerFromVWAP': [],
                  'STOCHdowntrend': [], 'closeDowntrend': [], 'LowerFromEMA12': []}

# Initialize the trading bot
bot.pushDiscordNotif(data.discordwebhook, type='start_msg')

# Main loop
while True:
    # Update previous data
    if first:
        pass
    else:
        previous['VWAP'].append(VWAP)
        previous['close'].append(close)
        previous['MACD'].append(MACD)
        previous['RSI'].append(RSI)
        previous['STOCH'].append(STOCH)
        previous['ema12'].append(ema12)
        previous['stockOpen'].append(stockOpen)

    # Get market data
    dataWorking = False
    while dataWorking == False:
        try:
            dataDict = bot.getPrice(avgprices, volumes)
            dataDict5m = bot.getPrice(avgprices, volumes, interval='5m')
            dataDict15m = bot.getPrice(avgprices, volumes, interval='15m')
            dataWorking = True
        except:
            time.sleep(10)
            pass

    # Assign market data
    high = dataDict['high']
    stockOpen = dataDict['stockOpen']
    low = dataDict['low']
    close = dataDict['close']
    bot.priceNum = close
    volume = dataDict['volume']
    RSI = dataDict['RSI']
    MACD = dataDict['MACD']
    VWAP = dataDict['VWAP']
    STOCH = dataDict['STOCH']
    histogram = dataDict['histogram']
    ema12 = dataDict['ema12']
    ema26 = dataDict['ema26']
    ema5 = dataDict['ema5']
    avgprices = dataDict['avgprices']
    avgprice = dataDict['avgprice']
    volumes = dataDict['volumes']

    if first:
        previous['VWAP'].append(VWAP)
        previous['close'].append(close)
        previous['MACD'].append(MACD)
        previous['RSI'].append(RSI)
        previous['STOCH'].append(STOCH)
        previous['ema12'].append(ema12)
        previous['stockOpen'].append(stockOpen)
        lowestMACD = MACD
        lowestRSI  = RSI

    high5m = dataDict5m['high']
    stockOpen5m = dataDict5m['stockOpen']
    low5m = dataDict5m['low']
    close5m = dataDict5m['close']
    volume5m = dataDict5m['volume']
    RSI5m = dataDict5m['RSI']
    MACD5m = dataDict5m['MACD']
    VWAP5m = dataDict5m['VWAP']
    STOCH5m = dataDict5m['STOCH']
    histogram5m = dataDict5m['histogram']
    ema125m = dataDict5m['ema12']
    ema265m = dataDict5m['ema26']
    ema55m = dataDict5m['ema5']
    avgprices5m = dataDict5m['avgprices']
    avgprice5m = dataDict5m['avgprice']
    volumes5m = dataDict5m['volumes']

    high15m = dataDict15m['high']
    stockOpen15m = dataDict15m['stockOpen']
    low15m = dataDict15m['low']
    close15m = dataDict15m['close']
    volume15m = dataDict15m['volume']
    RSI15m = dataDict15m['RSI']
    MACD15m = dataDict15m['MACD']
    VWAP15m = dataDict15m['VWAP']
    STOCH15m = dataDict15m['STOCH']
    histogram15m = dataDict15m['histogram']
    ema1215m = dataDict15m['ema12']
    ema2615m = dataDict15m['ema26']
    ema515m = dataDict15m['ema5']
    avgprices15m = dataDict15m['avgprices']
    avgprice15m = dataDict15m['avgprice']
    volumes15m = dataDict15m['volumes']

    if first == True:
        first = False
        RSIdowntrend = False
    else:
        priceDowntrend, MACDdowntrend, RSIdowntrend, LowerFromVWAP, STOCHdowntrend, closeDowntrend, LowerFromEMA12 = compareForEntry(
            previous, dataDict)
        previousTrends['priceDowntrend'].append(priceDowntrend)
        previousTrends['MACDdowntrend'].append(MACDdowntrend)
        previousTrends['RSIdowntrend'].append(RSIdowntrend)
        previousTrends['LowerFromVWAP'].append(LowerFromVWAP)
        previousTrends['STOCHdowntrend'].append(STOCHdowntrend)
        previousTrends['closeDowntrend'].append(closeDowntrend)
        previousTrends['LowerFromEMA12'].append(LowerFromEMA12)

        if len(previous['VWAP']) > 40:
            for key, value in previous.items():
                previous[key] = value[-30:]

        if len(previousTrends['priceDowntrend']) > 50:
            for key, value in previousTrends.items():
                previousTrends[key] = value[20:]

    # Update time
    now = datetime.now()
    lastminute = now.strftime("%M")
    current_time = now.strftime("%H:%M")
    current_secs = now.strftime("%S")
    if str(current_secs) == str(last_secs):
        time.sleep(1)

    last_secs = current_secs

    # Print message to console
    print()
    print()
    print('###############################')
    print()
    print(f'[TRADEBOT]            [{current_time}]')
    print(f'[TRADEBOT]     PRICE | ${round(avgprice, 2)}')
    print(f'[TRADEBOT]       RSI | {RSI}')
    print(f'[TRADEBOT]      MACD | {MACD}')
    print(f'[TRADEBOT]     EMA12 | {ema12}')
    print(f'[TRADEBOT]     EMA26 | {ema26}')

    print()
    print('###############################')

    # Check conditions to enter a trade
    try:
        testa = previous['close'][-1]
    except:
        testa = close

    if len(previous['close']) > 19:
        testBool = previous['close'][-20] > stockOpen
    else:
        testBool = RSIdowntrend

    lowestMACD = min(lowestMACD, MACD)
    lowestRSI  = min(lowestRSI, RSI)

    # Algorithm to place a trade
    macd_hist = previous['MACD'][-100:]
    MACD_THRESHOLD = calculate_macd_threshold(macd_hist, percentile=0.1)
    MACD_THRESHOLD = -0.08

    if close < ema12 and close < ema265m and close < ema5 and \
    (RSI5m < 44) and testBool:
        if (MACD < previous['MACD'][-1] or MACD < previous['MACD'][-2] or MACDdowntrend):
            if histogram < 0:
                print('[TRADEBOT] watching for a trade.')

                # Update previous data
                previous['VWAP'].append(VWAP)
                previous['close'].append(close)
                previous['MACD'].append(MACD)
                previousMACD = MACD
                previous['RSI'].append(RSI)
                previous['STOCH'].append(STOCH)
                previous['ema12'].append(ema12)
                previous['stockOpen'].append(stockOpen)

                # Send Discord message
                bot.watching = True
                pushDiscordMessageSuccess = bot.pushDiscordNotif(data.discordwebhook, type='watching')
                if pushDiscordMessageSuccess != True:
                    print('[TRADEBOT] CRITICAL ERROR IN DISCORD MESSAGE SYSTEM!')

                # Control variables
                trade = True
                waitForUptrend = False
                possible = False
                wait = False
                newCsv = False

                tradearray = []

                watch_price = close
                lowest_price_during_watch = close
                time_in_watch = 0

                # Loop to place the trade
                while trade:
                    # Update time
                    now = datetime.now()
                    minute = now.strftime("%M")
                    current_time = now.strftime("%H:%M:%S")
                    while minute == lastminute:
                        time.sleep(2)
                        now = datetime.now()
                        minute = now.strftime("%M")
                        current_secs = now.strftime("%S")

                    if str(current_secs) == str(last_secs):
                        time.sleep(1)

                    last_secs = current_secs
                    lastminute = minute

                    # Get new data
                    dataWorking = False
                    while dataWorking == False:
                        try:
                            dataDict = bot.getPrice(avgprices, volumes)
                            dataDict5m = bot.getPrice(avgprices, volumes, interval='5m')
                            dataDict15m = bot.getPrice(avgprices, volumes, interval='15m')
                            dataWorking = True
                        except:
                            time.sleep(2)
                            pass

                    # Save current trends
                    priceDowntrend, MACDdowntrend, RSIdowntrend, LowerFromVWAP, STOCHdowntrend, closeDowntrend, LowerFromEMA12 = compareForEntry(
                        previous, dataDict)
                    previousTrends['priceDowntrend'].append(priceDowntrend)
                    previousTrends['MACDdowntrend'].append(MACDdowntrend)
                    previousTrends['RSIdowntrend'].append(RSIdowntrend)
                    previousTrends['LowerFromVWAP'].append(LowerFromVWAP)
                    previousTrends['STOCHdowntrend'].append(STOCHdowntrend)
                    previousTrends['closeDowntrend'].append(closeDowntrend)
                    previousTrends['LowerFromEMA12'].append(LowerFromEMA12)

                    avgprices = dataDict['avgprices']
                    volumes = dataDict['volumes']

                    # Save current time
                    now = datetime.now()
                    current_time = now.strftime("%H:%M:%S")

                    # Save trade data
                    tradearray = [current_time, dataDict['high'], dataDict['low'], dataDict['close'], dataDict['RSI'],
                                dataDict['VWAP'], dataDict['ema12'], dataDict['ema26'], dataDict['MACD'],
                                dataDict['STOCH']]

                    # Assign data
                    high = dataDict['high']
                    stockOpen = dataDict['stockOpen']
                    low = dataDict['low']
                    close = dataDict['close']
                    volume = dataDict['volume']
                    RSI = dataDict['RSI']
                    MACD = dataDict['MACD']
                    VWAP = dataDict['VWAP']
                    STOCH = dataDict['STOCH']
                    histogram = dataDict['histogram']
                    ema12 = dataDict['ema12']
                    ema26 = dataDict['ema26']
                    ema5 = dataDict['ema5']
                    avgprices = dataDict['avgprices']
                    avgprice = dataDict['avgprice']
                    volumes = dataDict['volumes']

                    high5m = dataDict5m['high']
                    stockOpen5m = dataDict5m['stockOpen']
                    low5m = dataDict5m['low']
                    close5m = dataDict5m['close']
                    volume5m = dataDict5m['volume']
                    RSI5m = dataDict5m['RSI']
                    MACD5m = dataDict5m['MACD']
                    VWAP5m = dataDict5m['VWAP']
                    STOCH5m = dataDict5m['STOCH']
                    histogram5m = dataDict5m['histogram']
                    ema125m = dataDict5m['ema12']
                    ema265m = dataDict5m['ema26']
                    ema55m = dataDict5m['ema5']
                    avgprices5m = dataDict5m['avgprices']
                    avgprice5m = dataDict5m['avgprice']
                    volumes5m = dataDict5m['volumes']

                    high15m = dataDict15m['high']
                    stockOpen15m = dataDict15m['stockOpen']
                    low15m = dataDict15m['low']
                    close15m = dataDict15m['close']
                    volume15m = dataDict15m['volume']
                    RSI15m = dataDict15m['RSI']
                    MACD15m = dataDict15m['MACD']
                    VWAP15m = dataDict15m['VWAP']
                    STOCH15m = dataDict15m['STOCH']
                    histogram15m = dataDict15m['histogram']
                    ema1215m = dataDict15m['ema12']
                    ema2615m = dataDict15m['ema26']
                    ema515m = dataDict15m['ema5']
                    avgprices15m = dataDict15m['avgprices']
                    avgprice15m = dataDict15m['avgprice']
                    volumes15m = dataDict15m['volumes']

                    print()
                    print()
                    print('###############################')
                    print()
                    print(f'[TRADEBOT]            [{current_time}]')
                    print(f'[TRADEBOT]     PRICE | ${round(avgprice, 2)}')
                    print(f'[TRADEBOT]       RSI | {RSI}')
                    print(f'[TRADEBOT]      MACD | {MACD}')
                    print(f'[TRADEBOT]     EMA12 | {ema12}')
                    print(f'[TRADEBOT]     EMA26 | {ema26}')
                    print(f'[TRADEBOT]    STATUS | watching for a trade.. ')

                    print()
                    print('###############################')

                    # Compare with the previous minute
                    currentTrends = [priceDowntrend, MACDdowntrend, RSIdowntrend, LowerFromVWAP, STOCHdowntrend,
                                    closeDowntrend, LowerFromEMA12]

                    # Count bearish trends in the current minute
                    trueCntNow = 0
                    trueCnt = 0
                    trueCnt_ = 0
                    trueCnt__ = 0

                    for trend in currentTrends:
                        if trend is True:
                            trueCntNow = trueCntNow + 1

                    # Count bearish trends in the previous minute
                    try:
                        for trend, arr in previousTrends.items():
                            if arr[-2] is True:
                                trueCnt = trueCnt + 1

                        for trend, arr in previousTrends.items():
                            if arr[-3] is True:
                                trueCnt_ = trueCnt_ + 1

                        for trend, arr in previousTrends.items():
                            if arr[-4] is True:
                                trueCnt__ = trueCnt__ + 1
                    except:
                        trueCnt_ = 0
                        trueCnt__ = 0

                    atrVal = abs(close - (previous['stockOpen'][-1])) * 1.5
                    print("MACD_THRESHOLD: ", MACD_THRESHOLD)
                    # if close > previous['close'][-2] \
                    #         and (stockOpen > ema12 or close > ema12) and \
                    #         (stockOpen > ema55m or close > ema55m) and \
                    #         MACDdowntrend is False and \
                    #         lowestMACD < MACD_THRESHOLD and \
                    #         RSIdowntrend is False and (lowestRSI < 35 and lowestRSI > 25):
                    if (
                        lowestRSI < 35
                        and RSI > previous['RSI'][-1]
                        and close > ema5  # the price crosses the EMA5 or exceeds it at close
                        and MACD > previousMACD  # or "histogram" > histogram[-1], rising
                        and not RSIdowntrend     # RSI stops declining (optional)
                    ):
                        # Essential variables
                        entryPrice = close
                        entryTrueCnt = trueCntNow

                        tradearray.append('TRADE A')  # Record the algorithm used
                        makeTrade(tradearray, currentTrends, 'BUY')  # Place the trade
                        print(f'[TRADEBOT] placing LONG trade at {round(close, 2)}')
                        print('[TRADEBOT] algo A')
                        exitNeeded = True
                        trade = False

                    # elif lowestMACD < MACD_THRESHOLD and lowestRSI < 30 and close > ema5 and \
                    #         RSIdowntrend is False and (stockOpen > ema55m or close > ema55m) and previous['close'][
                    #     -1] > ema55m and close > previous['close'][-3]:
                    elif (
                        lowestRSI < 30
                        and MACD[-1] < MACD[-2] < MACD[-3]  # was decreasing
                        and MACD > previousMACD            # current MACD rises compared to last (change in slope)
                        and (histogram[-1] > histogram[-2])  # histogram rising
                        and close > ema12
                        and RSI < 45
                    ):
                        # Essential variables
                        entryPrice = close
                        entryTrueCnt = trueCntNow

                        tradearray.append('TRADE B')  # Record the algorithm used
                        makeTrade(tradearray, currentTrends, 'BUY')  # Place the trade
                        print(f'[TRADEBOT] placing LONG trade at {round(close, 2)}')
                        print('[TRADEBOT] algo B')
                        exitNeeded = True
                        trade = False

                        signal_still_valid = (
                            close < ema12 and close < ema265m and close < ema5
                            and RSI5m < 44
                            and histogram < 0
                            and (MACD < previous['MACD'][-1] or MACD < previous['MACD'][-2] or MACDdowntrend)
                        )

                        if not signal_still_valid:
                            # Check if the signal was lost due to "already rose" or "fell more"
                            # Example: if RSI5m > 50 => "escaped"
                            #          if RSI5m < 20 => continues to sink...
                            # Decide if you exit.
                            print("[TRADEBOT] Signal invalidated, exiting watching mode.")
                            trade = False
                            break

                        # 4) Add a "filter" if the price falls much more than a %
                        if close < watch_price * 0.97:
                            print("[TRADEBOT] Fell more than an additional 3%. Exiting watching.")
                            trade = False
                            break

                        # 5) Timeout by candles/time
                        time_in_watch += 1
                        if time_in_watch >= 10:
                            print("[TRADEBOT] 10 iterations have passed in watching mode without entering. Exiting.")
                            trade = False
                            break                

                    # Save previous data
                    previous['VWAP'].append(VWAP)
                    previous['close'].append(close)
                    previous['MACD'].append(MACD)
                    previousMACD = MACD
                    previous['RSI'].append(RSI)
                    previous['STOCH'].append(STOCH)
                    previous['ema12'].append(ema12)
                    previous['stockOpen'].append(stockOpen)

                consider = False
                loopNum = 0

                # Loop to exit the trade
                while exitNeeded:
                    loopNum += 1
                    bot.logData()

                    if loopNum == 5:
                        bot.updateMessage()
                        loopNum = 0

                    # Save previous data
                    previous['VWAP'].append(VWAP)
                    previous['close'].append(close)
                    previous['MACD'].append(MACD)
                    previous['RSI'].append(RSI)
                    previous['STOCH'].append(STOCH)
                    previous['ema12'].append(ema12)
                    previous['stockOpen'].append(stockOpen)

                    # Update time
                    now = datetime.now()
                    minute = now.strftime("%M")
                    current_time = now.strftime("%H:%M")
                    while minute == lastminute:
                        time.sleep(2)
                        now = datetime.now()
                        minute = now.strftime("%M")
                        current_secs = now.strftime("%S")

                    if str(current_secs) == str(last_secs):
                        time.sleep(1)

                    last_secs = current_secs
                    lastminute = minute

                    # Get new data
                    dataWorking = False
                    while dataWorking == False:
                        try:
                            dataDict = bot.getPrice(avgprices, volumes)
                            dataWorking = True
                        except:
                            time.sleep(2)
                            pass

                    # Save current trends
                    priceDowntrend, MACDdowntrend, RSIdowntrend, LowerFromVWAP, STOCHdowntrend, closeDowntrend, LowerFromEMA12 = compareForEntry(
                        previous, dataDict)
                    previousTrends['priceDowntrend'].append(priceDowntrend)
                    previousTrends['MACDdowntrend'].append(MACDdowntrend)
                    previousTrends['RSIdowntrend'].append(RSIdowntrend)
                    previousTrends['LowerFromVWAP'].append(LowerFromVWAP)
                    previousTrends['STOCHdowntrend'].append(STOCHdowntrend)
                    previousTrends['closeDowntrend'].append(closeDowntrend)
                    previousTrends['LowerFromEMA12'].append(LowerFromEMA12)

                    avgprices = dataDict['avgprices']
                    volumes = dataDict['volumes']

                    # Save current time
                    now = datetime.now()
                    current_time = now.strftime("%H:%M")

                    # Save trade data
                    tradearray = [current_time, dataDict['high'], dataDict['low'], dataDict['close'], dataDict['RSI'],
                                dataDict['VWAP'], dataDict['ema12'], dataDict['ema26'], dataDict['MACD'],
                                dataDict['STOCH']]

                    # Assign data
                    high = dataDict['high']
                    stockOpen = dataDict['stockOpen']
                    low = dataDict['low']
                    close = dataDict['close']
                    volume = dataDict['volume']
                    RSI = dataDict['RSI']
                    MACD = dataDict['MACD']
                    VWAP = dataDict['VWAP']
                    STOCH = dataDict['STOCH']
                    histogram = dataDict['histogram']
                    ema12 = dataDict['ema12']
                    ema26 = dataDict['ema26']
                    ema5 = dataDict['ema5']
                    avgprices = dataDict['avgprices']
                    avgprice = dataDict['avgprice']
                    volumes = dataDict['volumes']

                    high5m = dataDict5m['high']
                    stockOpen5m = dataDict5m['stockOpen']
                    low5m = dataDict5m['low']
                    close5m = dataDict5m['close']
                    volume5m = dataDict5m['volume']
                    RSI5m = dataDict5m['RSI']
                    MACD5m = dataDict5m['MACD']
                    VWAP5m = dataDict5m['VWAP']
                    STOCH5m = dataDict5m['STOCH']
                    histogram5m = dataDict5m['histogram']
                    ema125m = dataDict5m['ema12']
                    ema265m = dataDict5m['ema26']
                    ema55m = dataDict5m['ema5']
                    avgprices5m = dataDict5m['avgprices']
                    avgprice5m = dataDict5m['avgprice']
                    volumes5m = dataDict5m['volumes']

                    high15m = dataDict15m['high']
                    stockOpen15m = dataDict15m['stockOpen']
                    low15m = dataDict15m['low']
                    close15m = dataDict15m['close']
                    volume15m = dataDict15m['volume']
                    RSI15m = dataDict15m['RSI']
                    MACD15m = dataDict15m['MACD']
                    VWAP15m = dataDict15m['VWAP']
                    STOCH15m = dataDict15m['STOCH']
                    histogram15m = dataDict15m['histogram']
                    ema1215m = dataDict15m['ema12']
                    ema2615m = dataDict15m['ema26']
                    ema515m = dataDict15m['ema5']
                    avgprices15m = dataDict15m['avgprices']
                    avgprice15m = dataDict15m['avgprice']
                    volumes15m = dataDict15m['volumes']

                    print()
                    print()
                    print('###############################')
                    print()
                    print(f'[TRADEBOT]            [{current_time}]')
                    print(f'[TRADEBOT]     PRICE | ${round(avgprice, 2)}')
                    print(f'[TRADEBOT]   OPEN QT | x{bot.openQT:.4f}')
                    print(f'[TRADEBOT]  OPEN VAL | ${float(bot.openQT * round(avgprice, 2)):.2f}')

                    print()
                    print('###############################')

                    # Count bearish trends in the current minute
                    trueCnt = 0
                    trueCnt_ = 0
                    trueCnt__ = 0

                    for trend, arr in previousTrends.items():
                        if arr[-1] is True:
                            trueCnt = trueCnt + 1

                    for trend, arr in previousTrends.items():
                        if arr[-2] is True:
                            trueCnt_ = trueCnt_ + 1

                    for trend, arr in previousTrends.items():
                        if arr[-3] is True:
                            trueCnt__ = trueCnt__ + 1

                    # Price difference
                    difference = round(avgprice, 2) - entryPrice
                    lastdifference = previous['close'][-1] - entryPrice

                    # Algorithm to determine exits
                    if difference > .4:
                        tradearray.append('7302734')
                        print('7302734')
                        makeTrade(tradearray, currentTrends, 'SELL')
                        exitNeeded = False

                    elif difference > lastdifference + .12:
                        print('a82352')

                        if consider == True:
                            makeTrade(tradearray, currentTrends, 'SELL')
                            consider = False
                            exitNeeded = False

                        tradearray.append('a8932')
                        print('a8932')
                        consider = True

                    elif difference <= -.13:
                        tradearray.append('a893')

                        if consider == True or difference <= .2:
                            tradearray.append('894')
                            print('894')
                            makeTrade(tradearray, currentTrends, 'SELL')
                            exitNeeded = False

                        elif trueCnt >= entryTrueCnt + 2 and trueCnt >= trueCnt_ + 1:
                            tradearray.append('895')
                            print('895')
                            makeTrade(tradearray, currentTrends, 'SELL')
                            exitNeeded = False

                    if trueCnt > entryTrueCnt + 1:
                        tradearray.append('a32235423')
                        print('a32235423')
                        consider = True

                    if trueCnt > trueCnt_ + 1:
                        tradearray.append('a523563')
                        print('a523563')
                        consider = True

                    if trueCnt >= trueCnt__ + 2:
                        tradearray.append('a12345423')
                        print('a12345423')
                        consider = True

                    if minute == lastminute:
                        while minute == lastminute:
                            time.sleep(1)
                            now = datetime.now()
                            minute = now.strftime("%M")

            now = datetime.now()
            minute = now.strftime("%M")

            while minute == lastminute:
                time.sleep(2)
                now = datetime.now()
                minute = now.strftime("%M")
            time.sleep(1)
