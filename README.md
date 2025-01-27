# moneyprinter
This is a Python - Binance Trading Autonomous Bot

It is based on https://github.com/xozxro/cryptoprinter, who also based it on Nyria's work.

I did a complete refactor of the scripts, for using it with Binance API instead of FX and yFinance.

At his moment, i have the Discord and Binance integration fully working, but i am testing the entry conditions because it is not entering on any trade.  Debuging those rules takes a lot of time.

I have another 3 Trade Bots of my own creation, and those starts trades a little too fast, so they end with a profit of 0% (not good, but not bad), and i am testing all of those bots at the same time.

You can see my other projects: ... adding them soon

Prerequisite

Python

Update the .env file with your Binance api keys and secret, and the Discord channel webhook URL

Installation

If you are new to Python, place the files on a folder, open a shell (terminal), go to that folder, and type:  

python -m venv .venv

source ./.venv/bin/activate

pip install python-binance discord-webhook python-dotenv pandas numpy

Then you run the bot by:  python3 moneyprinter.py

Development

Want to contribute? Please do it! If you think you can contribute to this project please go on.

Contributions

If you wanna donate, so i can continue working on those Automatic Trade Bots, my Binance ID is: 322411022

Here is a QR so you can donate directly:

<img src="https://github.com/scorpile/moneyprinter/raw/main/binance.jpg?raw=true" alt="Binance QR" style="width: 400px;">

Important!

This is a work in progress, you wont gain any money at current state! If you wanna test, take in mind you will be risking your money and i wont be responsible of any loss.
