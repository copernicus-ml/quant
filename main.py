import logging

from data import DataStore, DownloadType
from feature import FEATURE_META_COLLECTION, FeatureBuilder, LabelGenerator
from feature.selector import FeatureSelector

logging.basicConfig(level=logging.INFO)


def main():
    # Load data
    store = DataStore()
    label_generator = LabelGenerator()
    # store.download_data(type=DownloadType.stocks)
    # store.download_data(type=DownloadType.features)
    stock_df = store.load_stocks()
    original_features_df = store.load_features()

    # Process features
    feature_builder = FeatureBuilder(
        feature_df=original_features_df, columns=list(FEATURE_META_COLLECTION.keys())
    )
    feature_df = feature_builder.get_feature_df().set_index(["ts_code", "trade_date"])

    # Compute labels
    labels_df = label_generator.generate_labels(stock_df).set_index(
        ["ts_code", "trade_date"]
    )
    # add label to the feature dataframe
    store.save_labels(labels_df.reset_index())
    feature_df = feature_df.join(labels_df, on=["ts_code", "trade_date"]).reset_index()

    # feature selector
    selector = FeatureSelector()
    _ = selector.ic_ir(feature_df)


if __name__ == "__main__":
    main()
