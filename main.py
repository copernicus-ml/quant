import logging
from pathlib import Path

import pandas as pd
import qlib

from config import get_config
from feature import FeatureEngine, Label
from model import Model

# from store import DataStore

logging.basicConfig(level=logging.INFO)


def init_qlib() -> pd.Series:
    config = get_config()
    bucket = f"{config.bucket_name}-{config.runtime_env}"
    qlib.init(provider_uri=str(Path(f"./{bucket}/qlib_data_us").resolve()), region="us")
    calendar = pd.read_csv(f"./{bucket}/qlib_data_us/calendars/day.txt", header=None)[0]
    return calendar


def main():
    # ========== Load data ==========
    # store = DataStore()
    # # store.download_data()
    # stock_df = store.load_stocks()
    # store.stock_df_to_csv(stock_df)

    # # ========= Qlib validation ==========
    calendar = init_qlib()
    start_time, end_time = calendar.iloc[0], calendar.iloc[-1]
    features, labels = FeatureEngine.getAlpha158(
        start_time=start_time, end_time=end_time, label_type=Label.T5
    )
    splitted_data = Model.split_data(
        features=features,
        labels=labels,
        calendar=calendar,
        label_type=Label.T5,
        train_seg=("2020-01-01", "2023-12-31"),
        valid_seg=("2024-01-01", "2024-12-31"),
        test_seg=("2025-01-01", "2026-12-31"),
    )
    X_train, y_train = splitted_data[0]
    print(X_train)
    print(y_train)


if __name__ == "__main__":
    main()
