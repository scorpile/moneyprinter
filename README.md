# 💸 MoneyPrinter

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![License](https://img.shields.io/github/license/scorpile/moneyprinter)
![Stars](https://img.shields.io/github/stars/scorpile/moneyprinter?style=social)

**MoneyPrinter** is a Python-based autonomous trading bot designed for Binance. Leveraging advanced technical indicators and robust trading strategies, MoneyPrinter aims to execute profitable trades automatically.

---

## 📈 Table of Contents

- [💸 MoneyPrinter](#-moneyprinter)
  - [📋 Overview](#-overview)
  - [🔧 Features](#-features)
  - [📝 Detailed Trading Strategy](#-detailed-trading-strategy)
    - [1. Technical Indicators Utilized](#1-technical-indicators-utilized)
    - [2. Trade Entry Conditions](#2-trade-entry-conditions)
    - [3. Trade Execution and Monitoring](#3-trade-execution-and-monitoring)
    - [4. Trade Exit Conditions](#4-trade-exit-conditions)
    - [5. Risk Management and Data Handling](#5-risk-management-and-data-handling)
    - [6. Overall Strategy Workflow](#6-overall-strategy-workflow)
  - [🚀 Getting Started](#-getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Configuration](#configuration)
    - [Running the Bot](#running-the-bot)
  - [🛠️ Development](#️-development)
    - [Contributing](#contributing)
  - [💖 Donations](#-donations)
  - [⚠️ Disclaimer](#-disclaimer)

---

## 📋 Overview

MoneyPrinter is an autonomous trading bot built with Python, integrated with Binance and Discord. It automates the process of executing buy and sell orders based on a sophisticated combination of technical indicators and predefined trading rules. 

**Key Highlights:**
- **Refactored Codebase:** Transitioned from FX and yFinance APIs to Binance API for enhanced performance.
- **Discord Integration:** Real-time notifications and trade updates via Discord.
- **Multiple Trading Strategies:** Includes multiple bots to diversify trading strategies.

---

## 🔧 Features

- **Automated Trading:** Executes trades based on technical indicators without manual intervention.
- **Real-Time Notifications:** Integrates with Discord to provide instant updates on trade activities.
- **Comprehensive Strategy:** Utilizes RSI, MACD, VWAP, EMA, and STOCH for informed trading decisions.
- **Risk Management:** Implements stop-loss mechanisms and dynamic thresholds to mitigate risks.
- **Data Logging:** Maintains detailed logs of all trades for analysis and optimization.

---

## 📝 Detailed Trading Strategy

### 1. Technical Indicators Utilized

- **Relative Strength Index (RSI):**
  - Measures the speed and change of price movements.
  - Identifies overbought or oversold conditions.

- **Moving Average Convergence Divergence (MACD):**
  - A trend-following momentum indicator.
  - Consists of the MACD line, signal line, and histogram.

- **Volume Weighted Average Price (VWAP):**
  - Provides the average price a security has traded at throughout the day.
  - Serves as a benchmark for assessing the current price level.

- **Exponential Moving Averages (EMA):**
  - EMAs give more weight to recent prices, making them more responsive.
  - Uses EMA12, EMA26, and EMA5 to determine short-term and medium-term trends.

- **Stochastic Oscillator (STOCH):**
  - Compares a particular closing price of a security to a range of its prices over a certain period.
  - Identifies overbought and oversold levels.

### 2. Trade Entry Conditions

The strategy identifies buy opportunities based on two primary sets of conditions: **Trade A** and **Trade B**.

#### **Trade A Conditions:**

- **RSI Threshold:** RSI below 35 (oversold conditions).
- **RSI Trend:** Increasing compared to the previous value (potential upward momentum).
- **Price vs. EMA5:** Closing price above the 5-period EMA (short-term uptrend).
- **MACD Confirmation:** Current MACD value higher than the previous value (bullish momentum).
- **RSI Stability:** RSI not in a downtrend (maintained bullish momentum).

#### **Trade B Conditions:**

- **RSI Threshold:** RSI below 30 (strong oversold conditions).
- **MACD Trend:** Decreasing over the last three periods but starting to rise (potential reversal).
- **Histogram Direction:** Increasing MACD histogram (supports bullish signal).
- **Price vs. EMA12:** Closing price above the 12-period EMA (medium-term uptrend).
- **RSI Level:** RSI below 45 (avoids overbought scenarios while indicating upward momentum).

When either set of conditions is met, the bot initiates a **BUY** order (LONG position) and enters a "watching" mode to monitor the trade's progress.

### 3. Trade Execution and Monitoring

Upon meeting the entry conditions, the bot performs the following actions:

- **Placing Orders:**
  - Executes a **BUY** order using the `placeOrder` method.
  - Sends a notification to a Discord webhook detailing the trade execution.

- **Logging:**
  - Records trade details, including timestamp, price, and indicator values, into a CSV file for future reference and analysis.

- **Watching Mode:**
  - Monitors the trade's progress by continuously fetching new market data.
  - Evaluates price relative to EMAs and monitors RSI and MACD trends to decide on exiting the trade.

### 4. Trade Exit Conditions

The strategy employs multiple exit conditions to secure profits or minimize losses:

- **Profit Targets:**
  - **Immediate Profit:** If the price difference from the entry point exceeds \$0.40, a **SELL** order is triggered.
  - **Incremental Profit:** If the price difference surpasses the last recorded difference by \$0.12, the bot considers selling to capitalize on upward movement.

- **Stop-Loss Mechanism:**
  - **Price Drop:** If the price falls more than 13% below the entry point, a **SELL** order is executed.
  - **Additional Drop:** If the price declines by an additional 3% (totaling a 16% drop), the bot exits the trade.

- **Trend Reversal:**
  - **RSI and MACD Indicators:** If RSI declines and MACD shows a downward trend, indicating weakening bullish momentum, the bot exits the trade.

- **Timeouts:**
  - **Iteration Limit:** If the bot remains in watching mode for 10 iterations without meeting any exit conditions, it automatically exits the trade.

### 5. Risk Management and Data Handling

- **Dynamic MACD Threshold:**
  - Calculates a dynamic MACD threshold based on the 10th percentile of recent MACD values to identify potential reversal points.

- **Data Logging and Trimming:**
  - Maintains a history of indicator values and trends.
  - Trims historical data to retain only the most recent 30 to 50 data points for responsiveness.

- **Discord Notifications:**
  - Provides real-time updates on trade executions, including BUY and SELL orders, current price, RSI, MACD, and other relevant indicators.
  - Alerts the user when monitoring for potential trades or when critical errors occur.

### 6. Overall Strategy Workflow

1. **Initialization:**
   - Sets up necessary variables and creates a CSV file to log trades.
   - Sends a start message to Discord to indicate that the trading bot is active.

2. **Data Acquisition:**
   - Continuously fetches current, 5-minute, and 15-minute interval market data, including price, volume, and indicator values.

3. **Trend Analysis:**
   - Compares the latest data with historical data to identify trends in price, RSI, MACD, VWAP, STOCH, and EMAs.
   - Determines whether indicators are in a downtrend or showing signs of reversal.

4. **Trade Decision Making:**
   - Evaluates whether the current market conditions meet the predefined criteria for **Trade A** or **Trade B**.
   - If conditions are met, executes a **BUY** order and enters the watching mode to monitor the trade.

5. **Trade Monitoring and Exit:**
   - In watching mode, the bot continuously assesses new data to decide whether to hold, realize profits, or cut losses based on exit conditions.
   - Logs all relevant data and updates Discord notifications accordingly.

6. **Loop Continuation:**
   - After exiting a trade, the bot resumes data acquisition and trend analysis to identify new trading opportunities.

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+** installed on your machine.
- **Binance Account:** Obtain API keys from your Binance account.
- **Discord Account:** Create a Discord webhook URL for notifications.

### Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/scorpile/moneyprinter.git
   cd moneyprinter
   ```

2. **Set Up Virtual Environment:**

   ```bash
   python -m venv .venv
   ```

3. **Activate Virtual Environment:**

   ```bash
   git clone https://github.com/scorpile/moneyprinter.git
   cd moneyprinter
   ```

4. **Install Dependencies:**

   ```bash
   pip install python-binance discord-webhook python-dotenv pandas numpy
   ```

5. **Running the Bot:**

   After setting up the virtual environment and installing the dependencies, you should set your Binance API key & secret, and the Discord Channel Webhook into the .env file, then you can run the bot using the following command:

   ```bash
   python moneyprinter.py
   ```

## 🛠️ Development

### Contributing

Contributions are welcome! Whether it's reporting bugs, suggesting features, or submitting pull requests, your support is appreciated.

### 💖 Donations

If you find this project useful and would like to support its development, consider donating. Your contributions help in maintaining and enhancing the bot.

Binance ID: 322411022

<img src="https://github.com/scorpile/moneyprinter/raw/main/binance.jpg?raw=true" alt="Binance QR" style="width: 400px;">

### ⚠️ Disclaimer

## Important:

MoneyPrinter is a work in progress. Currently, it does not guarantee any profits. Trading cryptocurrencies involves significant risk, and you may lose money. Use this bot at your own risk. The developer is not responsible for any financial losses incurred while using this bot.
