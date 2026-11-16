from typing import cast

import pandas as pd

LABEL_COL_NAME = "label"

future_return_col = "future_return"
rank_group_keys = ["trade_date"]


class LabelGenerator:
    def __init__(self):
        self.forward_days = 5  # calculate future 5 days return

    def calculate_future_return(self, df: pd.DataFrame) -> pd.Series:
        grouped = df.groupby("ts_code", sort=False)
        T_N_1 = grouped.shift(-(self.forward_days + 1))  # T + N + 1
        T_1 = grouped.shift(-1)  # T + 1
        future_return = (T_N_1["adj_open"] / T_1["adj_open"]) - 1
        return future_return

    def assign_rank_pct_labels(self, df: pd.DataFrame) -> pd.Series:
        """
        for the first version, we only use rank pct as labels
        we can expand the label categories in the future, when needed
        """
        labels = df.groupby(rank_group_keys)[future_return_col].rank(pct=True)
        return cast(pd.Series, labels)

    def generate_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df[["ts_code", "trade_date", "adj_open", "adj_close"]].copy()  # pyright: ignore[reportAssignmentType]
        df = df.sort_values(["ts_code", "trade_date"])
        df[future_return_col] = self.calculate_future_return(df)
        df[LABEL_COL_NAME] = self.assign_rank_pct_labels(df)
        df = df.drop(columns=["adj_open", "adj_close", future_return_col])
        return df
