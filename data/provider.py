from pathlib import Path
from typing import cast

import pandas as pd
import qlib
from qlib.config import REG_US
from qlib.data import D
from qlib.workflow import R

from config import get_configs

configs = get_configs()


def initialize() -> None:
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


def calendar() -> pd.DatetimeIndex:
    return pd.DatetimeIndex(D.calendar(freq=configs.data.freq))


def trading_days(start: str, end: str) -> pd.DatetimeIndex:
    start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(end)
    days = calendar()
    if start_ts > end_ts:
        raise ValueError(
            f"start data is later than end date. start: {start_ts}, end: {end_ts}"
        )
    if days.empty or end_ts > days[-1]:
        raise ValueError(
            f"requested end date is later than calendar end date. requested: {end_ts}, calendar: {days[-1]}"
        )
    selected = days[(days >= start_ts) & (days <= end_ts)]
    if selected.empty:
        raise ValueError("no available date within the request window")
    return cast(pd.DatetimeIndex, selected)
