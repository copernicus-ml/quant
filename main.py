import logging
from pathlib import Path

import lightgbm as lgb
import pandas as pd
import qlib
from qlib.contrib.evaluate import backtest_daily
from qlib.contrib.strategy.signal_strategy import TopkDropoutStrategy

from config import get_config
from feature import FeatureEngine, Label
from model import Model

# from store import DataStore

logging.basicConfig(level=logging.INFO)


def init_qlib() -> pd.Series:
    config = get_config()
    bucket = f"{config.bucket_name}-{config.runtime_env}"
    qlib.init(provider_uri=str(Path(f"./{bucket}/qlib_data_us").resolve()), region="us")
    calendar = pd.read_csv(f"./{bucket}/qlib_data_us/calendars/day.txt", header=None)[0]
    return calendar


def main():
    # ========== Load data ==========
    # store = DataStore()
    # stock_df = store.load_stocks()
    # store.stock_df_to_csv(stock_df)

    # ========= Qlib validation ==========
    calendar = init_qlib()
    start_time, end_time = calendar.iloc[0], calendar.iloc[-1]
    features, labels = FeatureEngine.getAlpha158(
        start_time=start_time, end_time=end_time, label_type=Label.T5
    )
    splitted_data = Model.split_data(
        features=features,
        labels=labels,
        calendar=calendar,
        label_type=Label.T5,
        train_seg=("2020-01-01", "2023-12-31"),
        valid_seg=("2025-01-01", "2025-12-31"),
        test_seg=("2026-10-01", "2026-12-31"),
    )
    X_train, y_train = splitted_data[0]
    X_valid, y_valid = splitted_data[1]
    X_test, y_test = splitted_data[2]

    print(f"Features: {X_train.shape[1]}")
    print(f"Train: {len(X_train):,}, valid: {len(X_valid):,}, test: {len(X_test):,}")

    model = lgb.LGBMRegressor(
        objective="regression",
        n_estimators=2000,
        learning_rate=0.02,
        num_leaves=15,
        max_depth=-1,
        min_child_samples=300,
        subsample=0.8,
        subsample_freq=1,
        colsample_bytree=0.8,
        random_state=2026,
        verbosity=1,
    )

    model.fit(
        X_train,
        y_train,
        eval_X=X_valid,
        eval_y=y_valid,
        eval_metric="l2",
        callbacks=[
            lgb.early_stopping(stopping_rounds=100),
            lgb.log_evaluation(period=100),
        ],
    )

    for i in range(2):
        digraph = lgb.create_tree_digraph(model, tree_index=i)
        digraph.render(f"lightgbm_tree_{i}", format="png", cleanup=True)

    prediction = model.predict(X_test)
    results = pd.DataFrame({"prediction": prediction}, index=X_test.index)
    results["label"] = y_test

    output_path = Path("lgbm_test_predictions_2026.csv")
    results.reset_index().to_csv(output_path, index=False)
    print(f"Saved {len(results):,} predictions to {output_path.resolve()}")

    signal = results["prediction"].sort_index()
    signal_dates = signal.index.get_level_values("datetime")
    symbols = signal.index.get_level_values("instrument").unique().tolist()
    trading_days = pd.DatetimeIndex(pd.to_datetime(calendar))

    # T 日收盘产生信号，策略在 T+1 开盘成交。
    # Qlib 会读取上一交易日的信号，只需移动回测起止日期。
    start = trading_days[trading_days.get_loc(signal_dates.min()) + 1]
    end = trading_days[trading_days.get_loc(signal_dates.max()) + 1]

    report, positions = backtest_daily(
        start_time=start,
        end_time=end,
        strategy=TopkDropoutStrategy(signal=signal, topk=50, n_drop=5),
        account=1_000_000,
        benchmark=symbols,
        exchange_kwargs={
            "deal_price": "open",
            "limit_threshold": None,
            "open_cost": 0.0,
            "close_cost": 0.0,
            "min_cost": 0,
        },
    )

    # Qlib 的 return 是扣费前日收益，cost 是当日交易费用占比。
    report["net_return"] = report["return"] - report["cost"]
    report["strategy_nav"] = (1 + report["net_return"]).cumprod()
    report["benchmark_nav"] = (1 + report["bench"]).cumprod()

    # 初始净值为 1，首日亏损也计入回撤。
    peak = report["strategy_nav"].cummax().clip(lower=1.0)
    report["drawdown"] = report["strategy_nav"] / peak - 1

    strategy_return = report["strategy_nav"].iloc[-1] - 1
    benchmark_return = report["benchmark_nav"].iloc[-1] - 1
    print(f"\n回测区间：{start.date()} 至 {end.date()}")
    print(f"策略累计收益（扣费后）：{strategy_return:.2%}")
    print(f"等权基准累计收益：{benchmark_return:.2%}")
    print(f"累计收益差：{(strategy_return - benchmark_return) * 100:.2f} 个百分点")
    print(f"策略最大回撤：{report['drawdown'].min():.2%}")
    print(f"平均每日换手率：{report['turnover'].mean():.2%}")

    report.to_csv("lgbm_backtest_2026.csv", index_label="datetime")
    ax = report[["strategy_nav", "benchmark_nav"]].plot(
        title="2026 backtest", ylabel="Growth", figsize=(10, 5), grid=True
    )
    ax.figure.tight_layout()
    ax.figure.savefig("lgbm_backtest_2026.png", dpi=150)


if __name__ == "__main__":
    main()
