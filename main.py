import logging
from pathlib import Path

import qlib
from qlib.data import D

# from data import DataStore

logging.basicConfig(level=logging.INFO)


def main():
    # ========== Load data ==========
    # store = DataStore()
    # store.download_data()
    # stock_df = store.load_stocks()
    # store.stock_df_to_csv(stock_df)

    # ========= Qlib validation ==========
    qlib.init(
        provider_uri=str(Path("./copernicus-dev/qlib_data_us").resolve()), region="us"
    )
    result = D.features(
        instruments=["AAPL"],
        fields=["$open", "$close", "$volume", "$vwap", "$factor"],
        start_time="2020-01-02",
        freq="day",
    )
    print(result.head())


if __name__ == "__main__":
    main()
