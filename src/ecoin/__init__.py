import dataclasses as dto
from . import kyber
from . import dilithium


@dto.dataclass
class Valued:
    kyber: kyber.Kyber
    dilithium: dilithium.Dilithium


@dto.dataclass
class NonValued:
    pass
