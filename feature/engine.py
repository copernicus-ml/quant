from enum import Enum
from typing import cast

import numpy as np
import pandas as pd
from qlib.contrib.data.handler import Alpha158
from qlib.data.dataset.handler import DataHandlerLP


class Label(Enum):
    T5 = "t5"


label = {Label.T5: ("Ref($open, -6) / Ref($open, -1) - 1", "LABEL0")}


class FeatureEngine:
    @staticmethod
    def getAlpha158(
        start_time: str, end_time: str, label_type: Label
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        label_expr, label_name = label[label_type]
        handler = Alpha158(
            instruments="all",
            start_time=start_time,
            end_time=end_time,
            infer_processors=[],
            learn_processors=[],
            label=([label_expr], [label_name]),
        )
        data = handler.fetch(col_set=["feature", "label"], data_key=DataHandlerLP.DK_R)
        features = data["feature"].replace([np.inf, -np.inf], np.nan)
        labels = (
            cast(pd.DataFrame, data["label"])
            .iloc[:, 0]
            .replace([np.inf, -np.inf], np.nan)
        )

        # remove records with na label
        valid_label = labels.notna()
        features = features[valid_label]
        labels = labels[valid_label]
        return cast(pd.DataFrame, features), cast(pd.DataFrame, labels)
