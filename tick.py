import sys
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.axes as axes
from datetime import datetime
import yfinance as yf
import signal
from matplotlib.ticker import StrMethodFormatter

FREQUENCIES = {
    "1m": 60.0,
    "2m": 120.0,
    "5m": 600.0,
}


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        self.kill_now = True


class Ticker:
    def __init__(self, symbol: str, interval="1m"):
        self.symbol = symbol
        self.interval = interval
        self.frequency = FREQUENCIES[interval]

    def init(self):
        mpl.rcParams['toolbar'] = 'None'
        _, ax = plt.subplots(num=self.symbol)
        self.axes = ax
        ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.2f}'))
        ax.xaxis.set_ticks([])

        ticker = yf.Ticker(self.symbol)
        open = ticker.info['open']
        ax.axhline(y=open, color='grey', linestyle=':')
        return self

    def backfill(self):
        ticker = yf.Ticker(self.symbol)
        meta = ticker.history_metadata
        last_day = meta["currentTradingPeriod"]["regular"]
        start = last_day["start"]
        end = last_day["end"]
        history = ticker.history(start=start, end=end, interval=self.interval)
        self.current_x = len(history["Close"])
        self.x = list(range(self.current_x))
        self.y = history["Close"].tolist()
        self.axes.plot(self.x, self.y)
        return self

    # TODO: only tick if it's a trading day.
    def tick(self):
        killer = GracefulKiller()

        last_annotation = None
        while not killer.kill_now:
            self.x.append(self.current_x)
            ticker = yf.Ticker(self.symbol)
            price = ticker.info['currentPrice']
            price_string = f'{price:,.2f}'
            y = float(price_string)
            self.y.append(y)
            open = ticker.info['open']
            color = 'green' if price >= open else 'red'
            self.axes.plot(self.x, self.y, c=color)
            if last_annotation is not None:
                last_annotation.remove()
            last_annotation = self.axes.annotate(price_string, (self.current_x, y),
                                                 xytext=(-30, 15),
                                                 textcoords='offset points', color=color)
            plt.pause(self.frequency)
            self.current_x += 1
        self._cleanup()

    def _cleanup(self):
        plt.close()


if __name__ == '__main__':

    stock_symbol = 'SNAP'
    if len(sys.argv) > 1:
        stock_symbol = sys.argv[1]

    Ticker(symbol=stock_symbol).init().backfill().tick()
