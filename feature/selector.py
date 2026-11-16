import logging

import numpy as np
import pandas as pd

from .labels import LABEL_COL_NAME

logger = logging.getLogger(__name__)


class FeatureSelector:
    def __init__(self):
        self.min_samples = 20

    def ic_ir(self, feature_df: pd.DataFrame):
        if LABEL_COL_NAME not in feature_df.columns:
            raise KeyError(f"the input df should have {LABEL_COL_NAME} column")
        features = [
            column
            for column in feature_df.columns
            if column not in {"trade_date", "ts_code", LABEL_COL_NAME}
        ]

        daily_ic_rows = []
        for trade_date, daily_df in feature_df.groupby("trade_date", sort=True):
            ic_values = {}
            for feature_name in features:
                paired = (
                    daily_df[[feature_name, LABEL_COL_NAME]]
                    .replace([np.inf, -np.inf], np.nan)
                    .dropna()
                )
                if len(paired) < self.min_samples:
                    ic_values[feature_name] = np.nan
                    continue
                feature = paired[feature_name]
                label = paired[LABEL_COL_NAME]
                if feature.nunique() < 2 or label.nunique() < 2:
                    ic_values[feature_name] = np.nan
                    continue
                ic_values[feature_name] = feature.corr(label, method="spearman")
            daily_ic_rows.append(pd.Series(ic_values, name=trade_date))
        ic_df = pd.DataFrame(daily_ic_rows)
        ic_df.index.name = "trade_date"
        mean = ic_df.mean()
        std = ic_df.std()
        ir = mean / std
        mean.name = "mean"
        ir.name = "ir"
        dump_data = pd.concat([mean, ir], axis=1)
        dump_data.to_csv("IC-IR.csv")
        return ir
