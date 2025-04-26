import dataclasses as dto


@dto.dataclass
class Count:
    n: int = 0

    def __call__(self):
        self.n += 1


bob_count = Count()
alice_count = Count()
transmission_count = Count()
