from dataclasses import dataclass

import pandas as pd
from qlib.contrib.data.handler import Alpha158
from qlib.data.dataset import DatasetH

from config.config import get_configs
from data.provider import trading_days

# currently we only train with/estimate 5D changes
T5_LABEL = "Ref($open, -6) / Ref($open, -1) - 1"

configs = get_configs()


@dataclass
class FeatureSpec:
    handler: str
    instruments: str
    label: str
    label_end_offset: int
    preprocessing_version: str


def build_feature_spec() -> FeatureSpec:
    data_config = configs.data
    if data_config.label != T5_LABEL or data_config.label_end_offset != 6:
        raise ValueError("currently we only train with/estimate 5D changes")

    return FeatureSpec(
        handler="Alpha158",
        instruments=data_config.instruments,
        label=data_config.label,
        label_end_offset=data_config.label_end_offset,
        preprocessing_version="process_inf_v1",
    )


def make_handler(
    spec: FeatureSpec, start: str, end: str, *, training: bool
) -> Alpha158:
    if spec.handler != "Alpha158" or spec.preprocessing_version != "process_inf_v1":
        raise ValueError("Unsupported feature and processor version")

    return Alpha158(
        instruments=spec.instruments,
        start_time=start,
        end_time=end,
        label=([spec.label], ["LABEL0"]),
        infer_processors=["ProcessInf"],
        learn_processors=["DropnaLabel"] if training else [],
    )


def build_train_dataset():
    # validate dataset split
    train_end = pd.Timestamp(configs.data.segments.train[1])
    valid_start = pd.Timestamp(configs.data.segments.valid[0])
    valid_end = pd.Timestamp(configs.data.segments.valid[1])
    test_start = pd.Timestamp(configs.data.segments.test[0])
    test_end = pd.Timestamp(configs.data.segments.test[1])
    as_of = pd.Timestamp(configs.data.as_of)
    if train_end >= valid_start:
        raise ValueError(
            "train and validate datasets should be strictly separated",
            f"train end: {train_end}, validate start: {valid_start}",
        )
    if valid_end >= test_start:
        raise ValueError(
            "validate and test datasets should be strictly separated",
            f"validate end: {valid_end}, test start: {test_start}",
        )
    if test_end >= as_of:
        raise ValueError(
            "test end date should be before the as_of date",
            f"test end: {test_end}, as of: {as_of}",
        )
    # build dataset: train | valid | test
    spec = build_feature_spec()
    segments = {}
    for name in ("train", "valid", "test"):
        start, end = configs.data.segments[name]
        days = trading_days(start, end)
        offset = spec.label_end_offset
        if len(days) <= offset:
            raise ValueError(f"{name} size is not enough for building dataset")
        segments[name] = (
            str(days[0]),
            # exclude days with future label
            str(days[-offset - 1]),
        )

    handler = make_handler(
        spec, segments["train"][0], segments["test"][1], training=True
    )
    return DatasetH(handler=handler, segments=segments)
