import random
import typer
import traceback
import itertools
from src.protocol import *
import time
import pstats
import io
import dataclasses as dto 

app = typer.Typer()


@dto.dataclass
class Timed:
    max_coins: int
    degree: int
    set_up: float 
    wallet_creation: float 
    buy_item: float

    def __repr__(self):
        return ', '.join(map(repr, dto.astuple(self)))

@app.command()
def timed_protocol(max_coins: int = 16, degree: int = 1024):
    """
    Execution of the protocol. For testing, see test.protocol.test_protocol

    - TODO: 

    """
    # TODO: This needs a much better explanation
    t0 = time.time()
    pctx = set_up_pctx(max_coins, degree)
    set_up =time.time() - t0
    price = random.getrandbits(pctx.max_coins)
    t0 = time.time()
    wallet = create_coins(price, pctx)
    wallet_creation =time.time() - t0
    t0 = time.time()
    _ = customer_spend_coin(price, wallet, pctx)
    buy_item =time.time() - t0
    return Timed(max_coins, degree, set_up, wallet_creation, buy_item)

@app.command()
def protocol(max_coins: int = 16):
    """
    Execution of the protocol. For testing, see test.protocol.test_protocol

    - TODO: 

    """
    # TODO: This needs a much better explanation
    pctx = set_up_pctx(max_coins)
    price = random.getrandbits(pctx.max_coins)
    wallet = create_coins(price, pctx)
    _ = customer_spend_coin(price, wallet, pctx)


@app.command()
def profile_protocol():
    import cProfile

    coins = 4
    print(f'* Coins {coins}')
    print('@code txt')
    with cProfile.Profile() as pr:
        protocol(coins)
        ps = pstats.Stats(pr).sort_stats(pstats.SortKey.CUMULATIVE)
        ps.print_stats()
    print('@end')


@app.command()
def time_analysis_simple():
    coins = [4, 8, 16, 32, 64]
    degrees = [512, 1024]
    with open('time.csv', 'w') as fd:
        print('max_coins,degree,set_up,wallet_creation,buy_item', file=fd)
        for coin, degree, i in itertools.product(coins, degrees, range(20)):
            try:
                timed = timed_protocol(coin, degree)
                print(repr(timed), file=fd)
            except:
                print(f"\n\n\n{coin}, {degree}, {i}\n")
                traceback.print_exc()


@app.command()
def create_plot(filename='time.csv'):
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    sns.set_theme()
    data = pd.read_csv(filename)
    df = pd.melt(data, id_vars=['max_coins', 'degree'], value_vars=['set_up', 'wallet_creation', 'buy_item'])
    sns.lineplot(df, x='max_coins', y='value', hue='variable', style='degree')
    plt.show()

if __name__ == '__main__':
    app()
