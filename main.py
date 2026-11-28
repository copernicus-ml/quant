import logging

from data import build_feature_spec, initialize
from data.dataset import build_train_dataset

logging.basicConfig(level=logging.INFO)


def main():
    initialize()
    ds = build_train_dataset()
    print(ds)


if __name__ == "__main__":
    main()
