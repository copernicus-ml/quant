import logging
import os
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
from pyarrow import fs

from config import get_config

INDEX_DIR = "index"
STOCK_DIR = "stock"
META_DIR = "meta"
FEATURE_DIR = "feature"

STOCK_LIST_FILENAME_PREFIX = "stock_list"

MAX_WORKERS = 8

logger = logging.getLogger(__name__)


class DownloadType(str, Enum):
    stocks = "stock"
    features = "features"


class DataStore:
    def __init__(self):
        config = get_config().store
        # Setup R2 connection and filenames
        endpoint = config.bucket_endpoint.replace("https://", "").replace("http://", "")
        self.fs = fs.S3FileSystem(
            access_key=config.access_key_id,
            secret_key=config.secret_access_key,
            region="auto",
            scheme="https",
            endpoint_override=endpoint,
        )
        self.bucket_name = config.bucket_name
        self.stock_list_filename = STOCK_LIST_FILENAME_PREFIX
        if config.runtime_env not in ["dev", "prod"]:
            logger.error('invalid runtime evn, should be "dev" or "prod"')
            raise OSError("invalid runtime env")
        self.bucket_name = f"{self.bucket_name}-{config.runtime_env}"
        self.stock_list_filename = f"{self.stock_list_filename}"

        # Setup local path
        self._ensure_local_dirs()
        self._r2_stock_list_path = f"{self.bucket_name}/{META_DIR}/{self.stock_list_filename}_{config.runtime_env}.csv"
        self._r2_stocks_path = f"{self.bucket_name}/{STOCK_DIR}"
        self._r2_features_path = f"{self.bucket_name}/{FEATURE_DIR}"
        self._local_stock_list_path = f"./{self._r2_stock_list_path}"
        self._local_stocks_path = f"./{self._r2_stocks_path}"
        self._local_features_path = f"./{self._r2_features_path}"
        self._local_labels_path = f"./{self.bucket_name}/labels.csv"

    def get_stock_list(self) -> pd.DataFrame:
        stock_list_path = Path(self._local_stock_list_path)
        if not stock_list_path.exists():
            logger.info("downloading stock list from R2 storage...")
            with (
                self.fs.open_input_file(self._r2_stock_list_path) as source,
                stock_list_path.open("wb") as target,
            ):
                shutil.copyfileobj(source, target)
        df = pd.read_csv(stock_list_path)
        return df

    def download_data(self, type: DownloadType = DownloadType.stocks):
        stock_list_df = self.get_stock_list()
        stocks = stock_list_df["ts_code"].to_list()
        # concurrent download data
        completed = 0
        counter_lock = threading.Lock()
        download_fn = (
            self._download_stock
            if type == DownloadType.stocks
            else self._download_feature
        )
        with ThreadPoolExecutor(
            max_workers=MAX_WORKERS, thread_name_prefix="download_stock"
        ) as executor:
            futures = {
                executor.submit(download_fn, ticker): ticker for ticker in stocks
            }
            for future in as_completed(futures):
                ticker = futures[future]
                try:
                    future.result()
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        f"failed to download {type} data for {ticker}: {exc!s}"
                    )
                finally:
                    with counter_lock:
                        completed += 1
                        if completed % 10 == 0 or completed == len(stocks):
                            logger.info(
                                f"{completed}/{len(stocks)} {type} task completed"
                            )
        logger.info(f"{type} download completed")

    def _download_stock(self, ticker: str):
        remote_file = f"{self._r2_stocks_path}/{ticker}.parquet"
        local_path = f"{self._local_stocks_path}/{ticker}.parquet"
        with (
            self.fs.open_input_file(remote_file) as source,
            open(local_path, "wb") as target,
        ):
            shutil.copyfileobj(source, target)

    def _download_feature(self, ticker: str):
        remote_file = f"{self._r2_features_path}/{ticker}.parquet"
        local_path = f"{self._local_features_path}/{ticker}.parquet"
        with (
            self.fs.open_input_file(remote_file) as source,
            open(local_path, "wb") as target,
        ):
            shutil.copyfileobj(source, target)

    # def load_single_stock(
    #     self, ts_code: str, filters: list[tuple] | None = None
    # ) -> pd.DataFrame:
    #     stock_path = f"{self._local_stocks_path}/{ts_code}.parquet"
    #     table = pq.read_table(stock_path, filters=filters)
    #     df = table.to_pandas()
    #     df = df.set_index("trade_date")
    #     return df

    # def load_single_feature(
    #     self, ts_code: str, filters: list[tuple] | None = None
    # ) -> pd.DataFrame:
    #     stock_path = f"{self._local_features_path}/{ts_code}.parquet"
    #     table = pq.read_table(stock_path, filters=filters)
    #     df = table.to_pandas()
    #     df = df.set_index("trade_date")
    #     return df

    def load_stocks(self) -> pd.DataFrame:
        """
        should not include index when loading stocks, because we might need to
        set different level of index in feature-building and label generation
        """
        dataset = pq.ParquetDataset(self._local_stocks_path)
        table = dataset.read()
        df = table.to_pandas()
        df = df.sort_values(["ts_code", "trade_date"])
        return df

    def load_features(self) -> pd.DataFrame:
        """
        should not include index when loading features, because we might need to
        set different level of index in feature-building and label generation
        """
        dataset = pq.ParquetDataset(self._local_features_path)
        table = dataset.read()
        df = table.to_pandas()
        return df

    def save_labels(self, df: pd.DataFrame):
        Path(self._local_labels_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(self._local_labels_path, index=False)

    def _ensure_local_dirs(self):
        for folder in [INDEX_DIR, STOCK_DIR, META_DIR, FEATURE_DIR]:
            os.makedirs(f"./{self.bucket_name}/{folder}", exist_ok=True)
