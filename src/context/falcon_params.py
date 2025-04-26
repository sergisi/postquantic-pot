import dataclasses as dto


@dto.dataclass
class FalconParameters:
    n: int
    sigma: float
    sigmin: float
    sig_bound: int
    sig_bytelen: int


params: dict[int, FalconParameters] = {
    # FalconParam(2, 2)
    2: FalconParameters(
        2,
        144.81253976308423,
        1.1165085072329104,
        101498,
        44,
    ),
    # FalconParam(4, 2)
    4: FalconParameters(
        4,
        146.83798833523608,
        1.1321247692325274,
        208714,
        47,
    ),
    # FalconParam(8, 2)
    8: FalconParameters(
        8,
        148.83587593064718,
        1.147528535373367,
        428865,
        52,
    ),
    # FalconParam(16, 4)
    16: FalconParameters(
        16,
        151.78340713845503,
        1.170254078853483,
        892039,
        63,
    ),
    # FalconParam(32, 8)
    32: FalconParameters(
        32,
        154.6747794602761,
        1.1925466358390344,
        1852696,
        82,
    ),
    # FalconParam(64, 16)
    64: FalconParameters(
        64,
        157.51308555044122,
        1.2144300507766141,
        3842630,
        122,
    ),
    # FalconParam(128, 32)
    128: FalconParameters(
        128,
        160.30114421975344,
        1.235926056771981,
        7959734,
        200,
    ),
    # FalconParam(256, 64)
    256: FalconParameters(
        256,
        163.04153322607107,
        1.2570545284063217,
        16468416,
        356,
    ),
    # FalconParam(512, 128)
    512: FalconParameters(
        512,
        165.7366171829776,
        1.2778336969128337,
        34034726,
        666,
    ),
    # FalconParam(1024, 256)
    1024: FalconParameters(
        1024,
        168.38857144654395,
        1.298280334344292,
        70265242,
        1280,
    ),
}
