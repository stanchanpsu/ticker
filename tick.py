import sys
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.axes as axes
from datetime import datetime
import yfinance as yf
import signal
from matplotlib.ticker import StrMethodFormatter

MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 30
MARKET_CLOSE_HOUR = 16


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

    def init(self):
        mpl.rcParams['toolbar'] = 'None'
        _, ax = plt.subplots(num=self.symbol, facecolor="black")
        plt.subplots_adjust(left=0.09, right=0.9, top=1.0, bottom=0.0)
        self.axes = ax
        ax.set_facecolor("black")
        ax.spines['bottom'].set_color("white")
        ax.spines['left'].set_color("white")
        ax.tick_params(axis="y", colors="white")
        ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.2f}'))
        ax.xaxis.set_ticks([])

        self._start_day()
        return self

    def backfill(self):
        ticker = yf.Ticker(self.symbol)
        meta = ticker.history_metadata
        last_day = meta["currentTradingPeriod"]["regular"]
        start = last_day["start"]
        end = last_day["end"]
        self.start = datetime.fromtimestamp(start)
        self.end = datetime.fromtimestamp(end)
        history = ticker.history(start=start, end=end, interval=self.interval)
        self.current_x = len(history["Close"])
        self.x = list(range(self.current_x))
        self.y = history["Close"].tolist()
        self.axes.plot(self.x, self.y)
        return self

    def _start_day(self):
        self.x = []
        self.y = []
        self.current_x = 0
        plt.cla()

        ticker = yf.Ticker(self.symbol)
        self.open = ticker.info['currentPrice']
        self.axes.axhline(y=self.open, color='white', linestyle=':')

    def tick(self):
        killer = GracefulKiller()

        last_annotation = None
        while not killer.kill_now:
            now = datetime.now()
            # If the trading day is over, just listen for GUI events.
            if (now.hour >= MARKET_CLOSE_HOUR or
                now.hour < MARKET_OPEN_HOUR or
                    (now.hour == MARKET_OPEN_HOUR and now.minute < MARKET_OPEN_MINUTE)):
                plt.pause(5.0)
                continue
            # If the trading day is just starting, clear the previous chart.
            if now.hour == MARKET_OPEN_HOUR and now.minute == MARKET_OPEN_MINUTE:
                self._start_day()

            # Trading day:
            self.x.append(self.current_x)
            ticker = yf.Ticker(self.symbol)
            price = ticker.info['currentPrice']
            price_string = f'{price:,.2f}'
            y = float(price_string)
            self.y.append(y)
            color = 'green' if price >= self.open else 'red'
            self.axes.plot(self.x, self.y, c=color)
            if last_annotation is not None:
                last_annotation.remove()
            last_annotation = self.axes.annotate(price_string, (1, y), xytext=(6, 0),
                                                 xycoords=self.axes.get_yaxis_transform(),
                                                 textcoords='offset points', color=color, fontsize=12)
            plt.pause(5.0)
            self.current_x += 1
        self._cleanup()

    def _cleanup(self):
        plt.close()


if __name__ == '__main__':

    stock_symbol = 'SNAP'
    if len(sys.argv) > 1:
        stock_symbol = sys.argv[1]

    Ticker(symbol=stock_symbol).init().backfill().tick()
