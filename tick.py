import sys
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.axes as axes
from datetime import datetime
import yfinance as yf
import signal
from matplotlib.ticker import StrMethodFormatter


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        self.kill_now = True


def init(symbol):
    mpl.rcParams['toolbar'] = 'None'
    fig, ax = plt.subplots()
    ax.set_title(symbol)
    ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.2f}'))
    ax.xaxis.set_ticks([])

    snap = yf.Ticker(symbol)
    open = snap.info['open']
    ax.axhline(y=open, color='grey', linestyle=':')
    return ax


def tick(ax: axes.Axes, stock_symbol: str):
    killer = GracefulKiller()

    count = 0
    x = []
    prices = []
    last_annotation = None
    while not killer.kill_now:
        count += 1
        x.append(count)
        snap = yf.Ticker(stock_symbol)
        price = snap.info['currentPrice']
        price_string = f'{price:,.2f}'
        y = float(price_string)
        prices.append(float(price_string))
        open = snap.info['open']
        color = 'green' if price >= open else 'red'
        ax.plot(x, prices, c=color)
        if last_annotation is not None:
            last_annotation.remove()
        last_annotation = ax.annotate(price_string, (count, y),
                                      xytext=(-30, 15),
                                      textcoords='offset points', color=color)
        plt.pause(2.0)


def cleanup():
    plt.close()


if __name__ == '__main__':

    stock_symbol = 'SNAP'
    if len(sys.argv) > 1:
        stock_symbol = sys.argv[1]
    ax = init(stock_symbol)
    tick(ax, stock_symbol)
    cleanup()
