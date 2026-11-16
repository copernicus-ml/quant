import pandas as pd

# in the current state, we only select columns.
# No needto implement normalizations/winsorize at this time. Just use the calculated results


class FeatureBuilder:
    def __init__(self, feature_df: pd.DataFrame, columns: list[str]):
        self.feature_df = feature_df[[*columns]]

    def get_feature_df(self):
        feature_df = self.feature_df.drop(columns=["industry"])
        return feature_df
