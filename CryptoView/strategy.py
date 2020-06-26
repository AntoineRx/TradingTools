"""
Analyse data in real-time and report signals
"""

# Imports
import os
import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
from filelock import FileLock
from CryptoView.logger import Logger
import time

load_dotenv()
DATA = os.getenv('DATA')
STRATEGY = os.getenv('STRATEGY')
FOLDER = os.getenv('FOLDER')


class Strategy:
    def apply(self, df):
        return df


class SimpleStrategy(Strategy):
    def __init__(self):
        self.ichimoku = dict(
            {'ConversionLinePeriods': 20, 'BaseLinePeriods': 60, 'LaggingSpan2Periods': 120, 'Displacement': 30})
        # Logger
        self.logger = Logger()
        # Last processed dataframe
        self.df = None

    @staticmethod
    def strategy_kijun(row):
        return 0 + (1 if row["Close"] > row["Kijun"] else 0) - (1 if row["Close"] < row["Kijun"] else 0)

    @staticmethod
    def strategy_kijun_tenkan(row):
        score = 0 + (1 if row["Kijun"] > row["Tenkan"] else 0) - (1 if row["Kijun"] < row["Tenkan"] else 0)
        return score

    def apply(self, df):
        self.df = df
        self.logger.success("Apply Strategy...")
        # Tenkan
        self.logger.info("Apply Tenkan")
        df['Tenkan'] = (df['High'].rolling(window=self.ichimoku['ConversionLinePeriods']).max()
                        + df['Low'].rolling(window=self.ichimoku['ConversionLinePeriods']).min()) / 2
        # Kijun
        self.logger.info("Apply Kijun")
        df['Kijun'] = (df['High'].rolling(window=self.ichimoku['BaseLinePeriods']).max()
                       + df['Low'].rolling(window=self.ichimoku['BaseLinePeriods']).min()) / 2
        # Senkou A
        self.logger.info("Apply Senkou A")
        df['Senkou_A'] = ((df['Tenkan'] + df['Kijun']) / 2).shift(self.ichimoku['Displacement'])
        # Senkou B
        self.logger.info("Apply Senkou B")
        df['Senkou_B'] = ((df['High'].rolling(window=self.ichimoku['LaggingSpan2Periods']).max()
                           + df['Low'].rolling(window=self.ichimoku['LaggingSpan2Periods']).min()) / 2) \
            .shift(self.ichimoku['Displacement'])
        # Chikou
        self.logger.info("Apply Chikou")
        df['Chikou'] = df['Close'].shift(-self.ichimoku['Displacement'])
        # EMA(55)
        self.logger.info("Apply EMA(55, Close)")
        df['EMA_55'] = df['Close'].ewm(span=55, min_periods=0, adjust=False, ignore_na=False).mean()
        # EMA(99)
        self.logger.info("Apply EMA(99, Close)")
        df['EMA_99'] = df['Close'].ewm(span=99, min_periods=0, adjust=False, ignore_na=False).mean()
        # EMA(222)
        self.logger.info("Apply EMA(222, Close)")
        df['EMA_222'] = df['Close'].ewm(span=222, min_periods=0, adjust=False, ignore_na=False).mean()
        df["Score"] = df.apply(self.strategy_kijun, axis=1)
        self.logger.success("Strategy... OK")
        return df


class StrategyHandler(FileSystemEventHandler):
    def __init__(self, strategy, src, filename):
        self.strategy = strategy
        self.src = src
        self.filename = filename

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(self.src):
            df = self.read()
            df = self.strategy.apply(df)
            self.write(df)

    def read(self):
        lock = FileLock(self.src + '.lock')
        with lock:
            df = pd.read_csv(self.src)
        return df

    def write(self, df):
        lock = FileLock(self.filename + '.lock')
        with lock:
            df.to_csv(self.filename)


if __name__ == "__main__":
    strategy = SimpleStrategy()
    strategy_handler = StrategyHandler(strategy, os.path.join(FOLDER, DATA), os.path.join(FOLDER, STRATEGY))
    observer = Observer()
    observer.schedule(strategy_handler, path="..", recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    # Ctrl + C
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
