import random
from src.protocol import *
import time
import pstats
import io

def timed_main():
    """
    Execution of the protocol. For testing, see test.protocol.test_protocol

    - TODO: 

    """
    # TODO: This needs a much better explanation
    t0 = time.time()
    pctx = set_up_pctx()
    print(f'Set-up time {time.time() - t0}')
    price = random.getrandbits(pctx.max_coins)
    t0 = time.time()
    wallet = create_coins(price, pctx)
    print(f'Wallet creation {time.time() - t0}')
    t0 = time.time()
    _ = customer_spend_coin(price, wallet, pctx)
    print(f'Buy Item {time.time() - t0}')

def main():
    """
    Execution of the protocol. For testing, see test.protocol.test_protocol

    - TODO: 

    """
    # TODO: This needs a much better explanation
    pctx = set_up_pctx()
    price = random.getrandbits(pctx.max_coins)
    wallet = create_coins(price, pctx)
    _ = customer_spend_coin(price, wallet, pctx)

import cProfile

if __name__ == "__main__":
    with cProfile.Profile() as pr:
        main()
        ps = pstats.Stats(pr).sort_stats(pstats.SortKey.CUMULATIVE)
        ps.print_stats()


