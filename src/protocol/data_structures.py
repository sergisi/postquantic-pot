import collections
from collections.abc import Sized
import dataclasses as dto

import typing
from src.poly import PolyVec
from src.protocol.pk import AESCyphertext


@dto.dataclass
class Ecoin:
    m: PolyVec
    r1: PolyVec
    r2: PolyVec
    s: PolyVec
    id_x: PolyVec
