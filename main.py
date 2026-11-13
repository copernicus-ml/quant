import logging

from data import DataStore, DownloadType
from feature import FEATURE_META_COLLECTION, FeatureBuilder

logging.basicConfig(level=logging.INFO)


def main():
    store = DataStore()
    # store.download_data(type=DownloadType.stocks)
    # store.download_data(type=DownloadType.features)
    features_df = store.load_features()
    feature_builder = FeatureBuilder(
        feature_df=features_df, columns=list(FEATURE_META_COLLECTION.keys())
    )
    print(feature_builder.feature_df.tail(10))
    # print(feature_builder.feature_df.columns)
    original_columns = set(features_df.columns)
    preserved_columns = set(feature_builder.feature_df.columns)
    diff = original_columns.difference(preserved_columns)
    print(sorted(diff))


if __name__ == "__main__":
    main()
