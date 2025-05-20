from .context import Context, AssymetricExtra
from .kyber_context import DilithiumExtra
from sage.all import Integer
import numpy as np
import functools as fun


@fun.lru_cache()
def get_kyber_context() -> Context[None]:
    return Context(
        q=3329,
        degree=256,
        k=4,
        l=4,
        cbd_noise=2,
        rej_sampling_module=5,
        safe_mask=500,
        more=None,
    )


@fun.lru_cache()
def get_dilithium_context() -> Context[DilithiumExtra]:
    # NOTE: NIST Security level 2, Table 2 on
    #  \cite{dilithium-spec}
    q = 8380417
    return Context(
        q=q,
        degree=256,
        k=4,
        l=4,
        cbd_noise=2,
        rej_sampling_module=5,
        safe_mask=500,
        more=DilithiumExtra(gamma1=2**17, gamma2=(q - 1) // 88, beta=78, tau=39),
    )


@fun.lru_cache
def get_context(
    cbd_noise=2, e1_param=100_000, e2_param=200
) -> Context[AssymetricExtra]:
    return Context(
        q=Integer(12 * 1024 + 1),
        degree=1024,
        k=2,
        l=2,
        cbd_noise=cbd_noise,
        rej_sampling_module=5,
        safe_mask=2000,
        more=AssymetricExtra(
            e1_param=e1_param,
            e2_param=e2_param,
        ),
    )


@fun.lru_cache(maxsize=1)
def gotta_go_fast_context() -> Context[AssymetricExtra]:
    return Context(
        q=Integer(12 * 1024 + 1),
        degree=64,
        k=2,
        l=2,
        cbd_noise=2,
        rej_sampling_module=5,
        safe_mask=2000,
        more=AssymetricExtra(
            e1_param=2,
            e2_param=2,
        ),
    )


##########################
def to_numpy(f):
    return np.array([np.array(list(x), dtype=np.int_) for x in f.coefficients()])
