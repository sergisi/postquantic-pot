# TODO: DO the documentation you idiot
"""
Protocol

"""

import dataclasses as dto

from src import falcon
from src.context import Context
from .bank import Bank
from .customer import Customer
from .pk import PublicKey, aes, AESCyphertext


__all__ = [
    "Bank",
    "Customer",
    "PublicKey",
    "aes",
    "AESCyphertext",
    "Protocol",
    "set_up",
]


@dto.dataclass
class Protocol:
    """ """

    bank: Bank
    customer: Customer
    ctx: Context


def set_up(
    ctx: Context, identity: str = "Melon", falc: falcon.MyFalcon | None = None
) -> Protocol:
    """
    Sets up the relevant actors and their keys.
    """
    if falc is None:
        falc = falcon.MyFalcon(ctx)
    pk = PublicKey(
        a_mat=falc.A,
        b0_mat=ctx.random_vector(),
        b1_mat=ctx.random_vector(),
        b2_mat=ctx.random_vector(),
        d_mat=ctx.random_vector(size=3),
    )
    bank = Bank(pk, falc, ctx)
    customer = Customer(pk, ctx, identity)
    return Protocol(bank, customer, ctx)
