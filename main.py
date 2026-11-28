import logging

from config import get_configs
from data.provider import calendar, initialize

logging.basicConfig(level=logging.INFO)


def main():
    configs = get_configs()
    initialize(configs)
    print(calendar(configs))


if __name__ == "__main__":
    main()
