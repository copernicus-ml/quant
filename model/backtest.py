# """Five-trading-day, open-to-open backtest of daily model predictions.

# Run from the project root: python -m model.backtest predictions.csv
# """

# import argparse
# from pathlib import Path

# import numpy as np
# import pandas as pd
# import qlib
# from qlib.data import D


# def backtest(predictions, opens, calendar, top_n=10, cost_bps=10):
#     """Trade equally weighted top-N signals every five sessions.

#     A signal at T enters at T+1 open and exits at T+6 open. All positions
#     are liquidated at each rebalance, even if selected again. Missing opens
#     for selected or held stocks stop the backtest rather than implying a fill.
#     """
#     if top_n < 1 or not 0 <= cost_bps < 10000:
#         raise ValueError("top_n must be positive and cost_bps must be in [0, 10000)")
#     calendar = pd.DatetimeIndex(pd.to_datetime(calendar)).sort_values().unique()
#     opens = opens.copy()
#     opens.index = pd.to_datetime(opens.index)
#     predictions = predictions.copy()
#     predictions["datetime"] = pd.to_datetime(predictions["datetime"])
#     if predictions.duplicated(["datetime", "instrument"]).any():
#         raise ValueError("Duplicate prediction for the same date and instrument")
#     predictions["prediction"] = pd.to_numeric(predictions["prediction"], errors="raise")
#     predictions = predictions[np.isfinite(predictions["prediction"])].copy()
#     signals = {date: group for date, group in predictions.groupby("datetime")}
#     if not signals:
#         raise ValueError("No finite predictions")

#     first = calendar.searchsorted(min(signals))
#     if first >= len(calendar):
#         raise ValueError("Predictions fall outside the trading calendar")
#     # Anchor to the first date with a signal, then use every fifth session.
#     while first < len(calendar) and calendar[first] not in signals:
#         first += 1
#     if first + 6 >= len(calendar):
#         raise ValueError("Not enough future sessions for a complete trade")
#     entries = {}
#     for i in range(first, len(calendar) - 6, 5):
#         signal_date = calendar[i]
#         if signal_date > max(signals):
#             break
#         if signal_date not in signals:
#             raise ValueError(f"Missing predictions for scheduled signal date {signal_date.date()}")
#         chosen = signals[signal_date].sort_values(
#             ["prediction", "instrument"], ascending=[False, True]
#         ).head(top_n)["instrument"].tolist()
#         entries[calendar[i + 1]] = (signal_date, chosen)
#     last_entry = max(entries)
#     last_exit = calendar[calendar.get_loc(last_entry) + 5]
#     rate = cost_bps / 10000
#     cash = 1.0
#     shares = pd.Series(dtype=float)
#     nav_rows, trade_rows = [], []

#     def prices(day, symbols):
#         if not symbols:
#             return pd.Series(dtype=float)
#         values = opens.reindex(index=[day], columns=symbols).iloc[0]
#         if values.isna().any() or (~np.isfinite(values)).any() or (values <= 0).any():
#             bad = values.index[values.isna() | ~np.isfinite(values) | (values <= 0)].tolist()
#             raise ValueError(f"Missing or invalid open on {day.date()}: {bad}")
#         return values

#     for day in calendar[(calendar >= min(entries)) & (calendar <= last_exit)]:
#         held_prices = prices(day, shares.index.tolist())
#         if day in entries or day == last_exit:
#             if not shares.empty:
#                 proceeds = shares * held_prices
#                 cash += proceeds.sum() * (1 - rate)
#                 for symbol, amount in proceeds.items():
#                     trade_rows.append((day, symbol, "sell", amount, amount * rate))
#                 shares = pd.Series(dtype=float)
#             if day in entries:
#                 signal_date, chosen = entries[day]
#                 entry_prices = prices(day, chosen)
#                 # Buy cost is included in cash spent, preventing leverage.
#                 amount = cash / (1 + rate) / len(chosen)
#                 shares = amount / entry_prices
#                 for symbol in chosen:
#                     trade_rows.append((day, symbol, "buy", amount, amount * rate))
#                 cash -= amount * len(chosen) * (1 + rate)
#                 held_prices = entry_prices
#         nav_rows.append((day, cash + (shares * held_prices).sum()))

#     nav = pd.DataFrame(nav_rows, columns=["datetime", "nav"]).set_index("datetime")
#     trades = pd.DataFrame(trade_rows, columns=["datetime", "instrument", "side", "notional", "cost"])
#     return nav, trades


# def main():
#     parser = argparse.ArgumentParser(description=__doc__)
#     parser.add_argument("predictions", type=Path, help="CSV with datetime, instrument, prediction columns")
#     parser.add_argument("--data-dir", type=Path, default=Path("copernicus-dev/qlib_data_us"))
#     parser.add_argument("--top-n", type=int, default=10)
#     parser.add_argument("--cost-bps", type=float, default=10, help="cost per side in basis points")
#     parser.add_argument("--output-dir", type=Path, default=Path("backtest_output"))
#     args = parser.parse_args()

#     predictions = pd.read_csv(args.predictions)
#     required = {"datetime", "instrument", "prediction"}
#     if not required.issubset(predictions.columns):
#         parser.error(f"CSV must contain columns: {', '.join(sorted(required))}")
#     predictions["instrument"] = predictions["instrument"].astype(str).str.upper()
#     calendar = pd.read_csv(args.data_dir / "calendars/day.txt", header=None)[0]
#     qlib.init(provider_uri=str(args.data_dir.resolve()), region="us")
#     raw = D.features(
#         instruments=predictions["instrument"].unique().tolist(),
#         fields=["$open"],
#         start_time=calendar.iloc[0],
#         end_time=calendar.iloc[-1],
#     )
#     opens = raw["$open"].unstack("instrument")
#     nav, trades = backtest(predictions, opens, calendar, args.top_n, args.cost_bps)
#     args.output_dir.mkdir(parents=True, exist_ok=True)
#     nav.to_csv(args.output_dir / "nav.csv")
#     trades.to_csv(args.output_dir / "trades.csv", index=False)
#     # Include initial capital in drawdown so first-day costs are visible.
#     equity = pd.concat([pd.Series([1.0]), nav["nav"].reset_index(drop=True)], ignore_index=True)
#     drawdown = equity / equity.cummax() - 1
#     print(f"Period: {nav.index[0].date()} to {nav.index[-1].date()}")
#     print(f"Total return: {nav['nav'].iloc[-1] - 1:.2%}")
#     print(f"Maximum drawdown: {drawdown.min():.2%}")
#     print(f"Trades: {len(trades)}; costs: {trades['cost'].sum():.4f} of initial capital")
#     print(f"Results: {args.output_dir}")


# if __name__ == "__main__":
#     main()
