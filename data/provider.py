from pathlib import Path

import pandas as pd
import qlib
from qlib.config import REG_US
from qlib.data import D
from qlib.workflow import R

from config import Configs


def initialize(configs: Configs) -> None:
    """
    Initialize qlib. If the data or data uri is invalid, raise FileNotFound Error
    """
    path = configs.qlib.provider_uri
    provider = Path(path).resolve()
    if not provider.is_dir():
        raise FileNotFoundError(f"qlib data does not exist in: {path}")
    qlib.init(provider_uri=str(provider), region=REG_US)

    tracking_uri = Path(configs.tracking.uri).resolve()
    tracking_uri.mkdir(parents=True, exist_ok=True)
    R.set_uri(tracking_uri.as_uri())


def calendar(configs: Configs) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(D.calendar(freq=configs.data.freq))
