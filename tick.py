import signal
import sys
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter
from datetime import datetime
import yfinance as yf


MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 30
MARKET_OPEN_SECOND = 15


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        self.kill_now = True


class Ticker:
    def __init__(self, symbol: str):
        self.symbol = symbol

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

    def _start_day(self):
        self.x = []
        self.y = []
        self.current_x = 0
        plt.cla()

        # Open price (will be wrong if this program is started after the trading day's start)
        ticker = yf.Ticker(self.symbol)
        # Don't use 'open' because there's a lag in the data given by the API.
        self.open = ticker.info['currentPrice']
        self.axes.axhline(y=self.open, color='white', linestyle=':')

    def tick(self):
        killer = GracefulKiller()

        last_annotation = None
        while not killer.kill_now:
            now = datetime.now()

            ticker = yf.Ticker(self.symbol)
            meta = ticker.history_metadata
            last_day = meta["currentTradingPeriod"]["regular"]
            start = datetime.fromtimestamp(last_day["start"])
            end = datetime.fromtimestamp(last_day["end"])

            # If we're not in a trading day, just listen for GUI events (to be able to close the window).
            if (now < start or now > end):
                plt.pause(5.0)
                continue

            # If the trading day is just starting, clear the previous chart.
            if now.hour == MARKET_OPEN_HOUR and now.minute == MARKET_OPEN_MINUTE and now.second < MARKET_OPEN_SECOND:
                self._start_day()

            # Trading day:
            self.x.append(self.current_x)
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

    t = Ticker(symbol=stock_symbol)
    t.tick()
