import logging

from data import DataStore

logging.basicConfig(level=logging.INFO)


def main():
    store = DataStore()
    # feature_calculator = FeatureCalculator()
    # store.download_stocks()
    # store.download_features()


if __name__ == "__main__":
    main()
