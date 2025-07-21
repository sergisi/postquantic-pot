import random
from concurrent.futures import ProcessPoolExecutor
from click import style
import typer
import traceback
import itertools
from src.protocol import *
import time
import pstats
import io
import dataclasses as dto

app = typer.Typer()


# TODO: @sergisi list
# - Canviar item_acquisition per item_preparation
# - Canviar number of ecoins per e-coin denonimation


@dto.dataclass
class Timed:
    max_coins: int
    degree: int
    set_up: float
    items_preraration: float
    wallet_creation: float
    item_acquisition: float
    price: int

    def __repr__(self):
        return ", ".join(map(repr, dto.astuple(self)))


@app.command()
def timed_protocol(max_coins: int = 16, degree: int = 1024, price: int | None = None):
    """
    Execution of the protocol. For testing, see test.protocol.test_protocol

    - TODO:

    """
    # TODO: This needs a much better explanation
    if price == None:
        price = random.getrandbits(max_coins)
    t0 = time.time()
    ctx, ecoins = set_up_ecoins(max_coins, degree)
    set_up = time.time() - t0
    t0 = time.time()
    pctx = items_preparation(ctx, ecoins)
    items_prep = time.time() - t0
    t0 = time.time()
    wallet = create_coins(price, pctx)
    wallet_creation = time.time() - t0
    t0 = time.time()
    _ = customer_spend_coin(price, wallet, pctx)
    item_acquisition = time.time() - t0
    return Timed(
        max_coins, degree, set_up, items_prep, wallet_creation, item_acquisition, price
    )


@app.command()
def protocol(max_coins: int = 16):
    """
    Execution of the protocol. For testing, see test.protocol.test_protocol

    - TODO:

    """
    # TODO: This needs a much better explanation
    ctx, ecoins = set_up_ecoins(max_coins)
    pctx = items_preparation(ctx, ecoins)
    price = random.getrandbits(len(pctx))
    wallet = create_coins(price, pctx)
    _ = customer_spend_coin(price, wallet, pctx)


@app.command()
def profile_protocol(coins: int):
    import cProfile

    with cProfile.Profile() as pr:
        protocol(coins)
        ps = pstats.Stats(pr).sort_stats(pstats.SortKey.CUMULATIVE)
        ps.print_stats()


def _safe_timed_protocol(c):
    coin, _ = c
    try:
        timed = timed_protocol(coin, 1024)
        print(repr(timed), flush=True)
    except:
        print(f"\n\n\n{coin}, {1024}\n", flush=True)
        traceback.print_exc()


def _safe_priced(c):
    coin, _ = c
    try:
        price = 2**coin - 1
        timed = timed_protocol(coin, 1024, price)
        print(repr(timed), flush=True)
    except:
        print(f"\n\n\n{coin}, {1024}\n", flush=True)
        traceback.print_exc()
    try:
        timed = timed_protocol(coin, 1024, 0)
        print(repr(timed), flush=True)
    except:
        print(f"\n\n\n{coin}, {1024}\n", flush=True)
        traceback.print_exc()


@app.command()
def time_analysis_simple():
    coins = [1, 2, 4, 8, 16, 32, 64]
    # coins = [1, 2]
    print(
        "max_coins,degree,set_up,items_preparation,wallet_creation,item_acquisition,price"
    )
    with ProcessPoolExecutor(max_workers=6) as executor:
        executor.map(_safe_timed_protocol, itertools.product(coins, range(12)))


@app.command()
def time_priced():
    coins = [1, 2, 4, 8, 16, 32, 64]
    # coins = [1, 2]
    print(
        "max_coins,degree,set_up,items_preparation,wallet_creation,item_acquisition,price"
    )
    with ProcessPoolExecutor(max_workers=6) as executor:
        executor.map(_safe_priced, itertools.product(coins, range(12)))


@app.command()
def create_plot_priced(filename="time-coin.csv"):
    """
    Creates a plot given a csv file
    """
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme()
    data = pd.read_csv(filename)
    data["price"] = data["price"].map(lambda x: 0 if x == 0 else 1)
    df = pd.melt(
        data,
        id_vars=["max_coins", "price"],
        value_vars=["wallet_creation", "item_acquisition"],
    )
    sns.lineplot(df, x="max_coins", y="value", hue="variable")
    plt.xlabel("#E-coins")
    plt.ylabel("Time (s)")
    plt.savefig("plot.png")
    plt.clf()
    sns.lineplot(data, x="max_coins", y="set_up")
    plt.xlabel("#E-coins")
    plt.ylabel("Time (s)")
    plt.savefig("plot-set-up.png")
    plt.clf()
    data["ratio"] = data["item_acquisition"] / data["max_coins"]
    # Define line styles for different hue values
    linestyles = ["solid", "dashed", "dotted", "dashdot"]
    unique_groups = sorted(data["max_coins"].unique())
    palette = sns.color_palette("flare", len(unique_groups) * 2)
    # Plot manually with different linestyles
    plt.figure(figsize=(8, 5))
    for i, group in enumerate(unique_groups):
        subset = data[data["max_coins"] == group]
        sns.kdeplot(
            data=subset[subset["price"] == 0],
            x="ratio",
            label=f"{group}, 0",
            linestyle=linestyles[i * 2 % len(linestyles)],
            color=palette[i * 2],
        )
        sns.kdeplot(
            data=subset[subset["price"] == 1],
            x="ratio",
            label=f"{group}, 1",
            linestyle=linestyles[(i * 2 + 1) % len(linestyles)],
            color=palette[i * 2 + 1],
        )
    plt.legend(title="E-coins denomination")
    plt.xlabel("Time (s)")
    plt.ylabel("Density")
    plt.savefig("density.png")
    plt.clf()
    sns.kdeplot(data, x="ratio", hue="price")
    plt.xlabel("Time (s)")
    plt.ylabel("Density")
    plt.savefig("price.png")
    plt.clf()


@app.command()
def create_plot(filename="time.csv"):
    """
    Creates a plot given a csv file
    """
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme()
    data = pd.read_csv(filename)
    df = pd.melt(
        data,
        id_vars=["max_coins", "degree"],
        value_vars=["wallet_creation", "item_acquisition", "items_preparation"],
    )
    sns.lineplot(df, x="max_coins", y="value", hue="variable")
    plt.xlabel("#E-coins")
    plt.ylabel("Time (s)")
    plt.savefig("plot.png")
    plt.clf()
    sns.lineplot(data, x="max_coins", y="set_up")
    plt.xlabel("#E-coins")
    plt.ylabel("Time (s)")
    plt.savefig("plot-set-up.png")
    plt.clf()
    data["ratio"] = data["item_acquisition"] / data["max_coins"]
    # Define line styles for different hue values
    linestyles = ["solid", "dashed", "dotted", "dashdot"]
    unique_groups = sorted(data["max_coins"].unique())
    palette = sns.color_palette("flare", len(unique_groups))
    # Plot manually with different linestyles
    plt.figure(figsize=(8, 5))
    for i, group in enumerate(unique_groups):
        subset = data[data["max_coins"] == group]
        sns.kdeplot(
            data=subset,
            x="ratio",
            label=group,
            linestyle=linestyles[i % len(linestyles)],
            color=palette[i],
        )
    plt.legend(title="#E-coins")
    plt.xlabel("Time (s)")
    plt.ylabel("Density")
    plt.savefig("density.png")
    plt.clf()


@app.command()
def create_table(filename="time.csv"):
    import pandas as pd

    data = pd.read_csv(filename)
    if "price" in data.columns:
        del data["price"]
    data.style.format(precision=3)
    data = data[[col for col in data.columns if col != "degree"]]
    print(data.groupby(["max_coins"]).mean().style.format(precision=2).to_latex())


if __name__ == "__main__":
    app()
