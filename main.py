import logging

from data import DataStore, DownloadType
from feature import FEATURE_META_COLLECTION, FeatureBuilder, LabelGenerator

logging.basicConfig(level=logging.INFO)


def main():
    store = DataStore()
    label_generator = LabelGenerator()
    # store.download_data(type=DownloadType.stocks)
    # store.download_data(type=DownloadType.features)
    stock_df = store.load_stocks()
    # features_df = store.load_features()
    # feature_builder = FeatureBuilder(
    #     feature_df=features_df, columns=list(FEATURE_META_COLLECTION.keys())
    # )
    # print(feature_builder.feature_df.columns)
    # original_columns = set(features_df.columns)
    # preserved_columns = set(feature_builder.feature_df.columns)
    processed_df = label_generator.generate_labels(stock_df)
    store.save_labels(processed_df)


if __name__ == "__main__":
    main()
