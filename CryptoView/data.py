"""
Get real-time data from Binance.
"""

# Imports
import json
import os
import time

from binance.client import Client
from binance.websockets import BinanceSocketManager

import numpy as np
import pandas as pd

from CryptoView.logger import Logger
from dotenv import load_dotenv
from filelock import FileLock

load_dotenv()
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')
INFO = os.getenv('INFO')
FOLDER = os.getenv('FOLDER')
DATA = os.getenv('DATA')


class BinanceManager:
    def __init__(self, api_key=None, secret_key=None):
        # Binance API Client
        self.client = Client(api_key, secret_key)
        # Binance API websocket
        self.socket = BinanceSocketManager(self.client)
        # Panda dataFrame
        self.df = None
        # Trading asset
        self.symbol = None
        # Interval
        self.interval = None
        # Logger
        self.logger = Logger()
        # File to save data
        self.filename = None

    def start(self, symbol, interval, startTime=None, filename="data.csv"):
        self.logger.success("Manager start")
        self.symbol = symbol
        self.interval = interval
        self.filename = filename
        self.get_historical_klines(self.symbol, interval, startTime)
        self.logger.success("Socket start")
        self.socket.start()
        self.logger.success("Socket kline start")
        self.socket.start_kline_socket(self.symbol, self.klines_callback, interval=self.interval)
        return self

    def get_historical_klines(self, symbol="btcusdt", interval="1h", startTime=None, endTime=None, limit=500):
        self.logger.info("Get historical klines")
        # fetch klines
        data = self.client.futures_klines(symbol=symbol, interval=interval, startTime=startTime, endTime=endTime, limit=limit)
        # Keep only the first 6 columns
        data = np.array(data)[:, 0:6]
        # Create a DataFrame with annotated columns
        df = pd.DataFrame(data, columns=["Date", "Open", "High", "Low", "Close", "Volume"])
        # Convert Date from ms to Datetime
        df["Date"] = pd.to_datetime(df["Date"], unit="ms")
        # Convert columns to numeric values
        df["Open"] = pd.to_numeric(df["Open"], errors="coerce")
        df["High"] = pd.to_numeric(df["High"], errors="coerce")
        df["Low"] = pd.to_numeric(df["Low"], errors="coerce")
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce")
        # Set Date column as index
        df.set_index("Date", inplace=True)
        self.df = df
        self.write()
        return df

    def klines_callback(self, msg):
        self.logger.info("Websocket: Updating last kline")
        if msg['e'] == 'error':
            print("[!] ERROR: Klines websocket does not work.")
            return self

        # [Kline start time, Open price, High price, Low price, Close price, Base asset volume
        kline = np.array([msg['k']['t'], msg['k']['o'], msg['k']['h'], msg['k']['l'], msg['k']['c'], msg['k']['v']])
        # Create a Tableau with annotated columns
        df = pd.DataFrame([kline], columns=["Date", "Open", "High", "Low", "Close", "Volume"])
        # Convert Date from ms to Datetime
        df["Date"] = pd.to_datetime(df["Date"], unit="ms")
        # Convert columns to numeric values
        df["Open"] = pd.to_numeric(df["Open"], errors="coerce")
        df["High"] = pd.to_numeric(df["High"], errors="coerce")
        df["Low"] = pd.to_numeric(df["Low"], errors="coerce")
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce")
        df.set_index("Date", inplace=True)
        # If is not a new kline
        if self.df.last_valid_index() == df.last_valid_index():
            # Update last kline value
            self.df.drop(self.df.last_valid_index(), inplace=True)
        # Append df to main df
        self.df = self.df.append(df, ignore_index=False)
        # Update data
        self.write()
        return self

    def write(self):
        if self.filename is not None:
            lock = FileLock(self.filename + '.lock')
            with lock:
                self.df.to_csv(self.filename)

    def stop(self):
        self.logger.success("Manager stop")
        self.socket.close()
        return self


if __name__ == "__main__":
    # Read info
    content = ""
    with open(INFO, 'r') as f:
        content = f.read()
    info = json.loads(content)
    manager = BinanceManager(BINANCE_API_KEY, BINANCE_API_SECRET)
    manager.start(info.get("symbol", "btcusdt"), info.get("interval", "5m"), info.get("startTime", None), os.path.join(FOLDER, DATA))
    try:
        while True:
            time.sleep(1)
    # Ctrl + C
    except KeyboardInterrupt:
        manager.stop()
