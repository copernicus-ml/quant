import os
import re
from dataclasses import dataclass

import yaml
from dotenv import load_dotenv

load_dotenv()
CONFIG_FILE_PATH = "config.yaml"


@dataclass
class ConfigEnv:
    access_key_id: str
    secret_access_key: str
    bucket_name: str
    bucket_endpoint: str
    runtime_env: str


@dataclass
class ConfigQlib:
    provider_uri: str


@dataclass
class ConfigTracking:
    uri: str
    experiment: str


@dataclass
class ConfigSegments:
    train: tuple[str, str]
    valid: tuple[str, str]


@dataclass
class ConfigData:
    as_of: str
    instruments: str
    label: str
    label_end_offset: int
    segments: ConfigSegments
    freq: str


@dataclass
class ConfigModel:
    loss: str
    num_boost_rounds: int
    early_stopping_rounds: int
    learning_rate: float
    num_leaves: int
    max_depth: int
    min_data_in_leaf: int
    bagging_fraction: float
    bagging_freq: int
    feature_fraction: float
    seed: int
    num_threads: int
    verbosity: int


@dataclass
class ConfigPrediction:
    start: str
    end: str
    output: str


@dataclass
class Configs:
    env: ConfigEnv
    qlib: ConfigQlib
    tracking: ConfigTracking
    data: ConfigData
    model: ConfigModel
    prediction: ConfigPrediction


configs: Configs | None = None


def get_configs() -> Configs:
    global configs
    if configs != None:
        return configs
    with open(CONFIG_FILE_PATH) as config_file:
        content = config_file.read()
    pattern = re.compile(r"\$\{(\w+)\}")
    content = pattern.sub(lambda match: os.getenv(match.group(1), ""), content)
    data = yaml.safe_load(content)
    data_config = data["data"].copy()
    data_config["segments"] = ConfigSegments(**data_config["segments"])
    configs = Configs(
        env=ConfigEnv(**data["env"]),
        qlib=ConfigQlib(**data["qlib"]),
        tracking=ConfigTracking(**data["tracking"]),
        data=ConfigData(**data_config),
        model=ConfigModel(**data["model"]),
        prediction=ConfigPrediction(**data["prediction"]),
    )
    return configs
