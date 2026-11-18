# Alpha158 Feature Reference

Yes. These are the standard **158 Alpha158 features**: 13 single-day features and 29 rolling feature families × 5 windows.

For your frontend, you can group them into **8 sections**. In the tables below, `N` represents `5`, `10`, `20`, `30`, or `60` trading days. For example, `MA20` and `MA60` have the same meaning, but use different lookback windows. The definitions follow the [Qlib Alpha158 implementation](https://github.com/microsoft/qlib/blob/main/qlib/contrib/data/loader.py).

## 1. Daily candlestick shape

These describe the current trading day's price range and where the open and close sit within it.

| Feature | Frontend label | What it indicates |
|---|---|---|
| `KMID` | Candle body / open | `(close − open) / open`. Positive means the stock closed above its open; negative means it closed below. |
| `KLEN` | Daily range / open | `(high − low) / open`. Measures the day's price range relative to the opening price. |
| `KMID2` | Candle body / range | `(close − open) / (high − low)`. Measures the direction and size of the candle body relative to the day's range. |
| `KUP` | Upper shadow / open | Distance from the higher of open and close to the high, divided by open. |
| `KUP2` | Upper shadow / range | The same upper shadow, divided by the day's range. |
| `KLOW` | Lower shadow / open | Distance from the low to the lower of open and close, divided by open. |
| `KLOW2` | Lower shadow / range | The same lower shadow, divided by the day's range. |
| `KSFT` | Close position shift / open | `(2 × close − high − low) / open`. Positive when the close is above the day's midpoint, negative when below. |
| `KSFT2` | Close position shift / range | The same midpoint displacement divided by the day's range. |

**Visualization:** a candlestick chart is the most intuitive view. Show the selected factor's value beside the chart and highlight the relevant body, shadow, or range.

## 2. Current prices relative to close

All four are ratios. A value of `1` means the referenced price equals the close.

| Feature | Frontend label | What it indicates |
|---|---|---|
| `OPEN0` | Open / close | Current open relative to current close. |
| `HIGH0` | High / close | Current high relative to current close. |
| `LOW0` | Low / close | Current low relative to current close. |
| `VWAP0` | VWAP / close | Current VWAP relative to current close. Above `1` means VWAP was above the close. |

**Visualization:** use `1` as a reference line and plot each ratio around it.

## 3. Price trend and volatility

| Feature family | Frontend label | What it indicates |
|---|---|---|
| `ROC{N}` | Past close / current close | Close `N` trading days ago divided by current close. A value below `1` means the current close is higher than the past close. **This is not the conventional `(current / past) − 1` ROC.** |
| `MA{N}` | Moving average / close | Average close over the window divided by current close. Below `1` means the current close is above that average. |
| `STD{N}` | Price volatility / close | Standard deviation of closing prices over the window, divided by current close. Higher values indicate greater dispersion of price levels. |
| `BETA{N}` | Price trend slope / close | Linear regression slope of closing prices over the window, divided by current close. Positive indicates an upward fitted trend; negative indicates downward. |
| `RSQR{N}` | Trend fit R² | R-squared of the closing-price regression against time. Higher values indicate that a straight line fits the price path more closely; it does not indicate direction. |
| `RESI{N}` | Regression residual / close | Current regression residual divided by current close. Indicates how far the current price is from the fitted trend line. |

**Visualization:** line charts work well for each family, with separate lines or a window selector for 5/10/20/30/60. Use reference lines at `1` for `ROC` and `MA`, and at `0` for `BETA` and `RESI`.

## 4. Price range and position

| Feature family | Frontend label | What it indicates |
|---|---|---|
| `MAX{N}` | Window high / close | Highest high in the window divided by current close. Shows the recent high relative to today's close. |
| `MIN{N}` | Window low / close | Lowest low in the window divided by current close. Shows the recent low relative to today's close. |
| `QTLU{N}` | Upper price quantile / close | The 80th percentile of closes in the window divided by current close. |
| `QTLD{N}` | Lower price quantile / close | The 20th percentile of closes in the window divided by current close. |
| `RANK{N}` | Close percentile rank | The current close's percentile rank among closes in the window. Higher means the close is nearer the top of its recent range. |
| `RSV{N}` | Close position in range | `(close − window low) / (window high − window low)`. Near `1` means close is near the window high; near `0` means near the window low. |

**Visualization:** show `RANK` and `RSV` as lines or gauges, and show high/low bands on a price chart for context.

## 5. Timing of highs and lows

These describe the **positions of the high and low within a rolling window**, scaled by the window length.

| Feature family | Frontend label | What it indicates |
|---|---|---|
| `IMAX{N}` | High position in window | The position of the highest high within the last `N` days, divided by `N`. |
| `IMIN{N}` | Low position in window | The position of the lowest low within the last `N` days, divided by `N`. |
| `IMXD{N}` | High–low position difference | `(position of high − position of low) / N`. Indicates the relative ordering and separation of the window's high and low. |

**Visualization:** plot `IMAX` and `IMIN` together. Before labeling an end of the scale as “recent” or “old” in the UI, verify Qlib's `IdxMax`/`IdxMin` indexing behavior against a small known price sequence.

## 6. Price direction and movement

| Feature family | Frontend label | What it indicates |
|---|---|---|
| `CNTP{N}` | Up-day fraction | Fraction of days in the window when close was above the previous close. |
| `CNTN{N}` | Down-day fraction | Fraction of days when close was below the previous close. |
| `CNTD{N}` | Up–down day difference | `CNTP − CNTN`. Positive means more up days; negative means more down days. |
| `SUMP{N}` | Share of upward movement | Sum of positive close-to-close price changes divided by the sum of absolute changes. |
| `SUMN{N}` | Share of downward movement | Sum of negative close-to-close changes, expressed as positive magnitudes, divided by the sum of absolute changes. |
| `SUMD{N}` | Net movement balance | Upward movement minus downward movement, divided by total absolute movement. Positive means gains dominated; negative means losses dominated. |

**Visualization:** use stacked areas or bars for up/down pairs, and a diverging chart centered at `0` for `CNTD` and `SUMD`. `CNTP + CNTN` can be less than `1` when there are unchanged days.

## 7. Price–volume relationship

| Feature family | Frontend label | What it indicates |
|---|---|---|
| `CORR{N}` | Price–volume correlation | Rolling correlation between close and `log(volume + 1)`. Positive means the two tended to move together within the window. |
| `CORD{N}` | Price-change–volume-change correlation | Rolling correlation between the close-price ratio and a log-transformed volume-change ratio. Positive means these changes tended to move together. |
| `WVMA{N}` | Volume-weighted movement variation | Standard deviation divided by mean of `abs(daily return) × volume` over the window. Measures how variable that volume-weighted movement is relative to its average. |

**Visualization:** use a zero-centered line chart for correlations. Treat `WVMA` as a relative variability measure, rather than labeling it as a directional signal.

## 8. Volume trend and movement

| Feature family | Frontend label | What it indicates |
|---|---|---|
| `VMA{N}` | Average volume / current volume | Mean volume over the window divided by current volume. Below `1` means current volume is above the window average. |
| `VSTD{N}` | Volume dispersion / current volume | Standard deviation of volume over the window divided by current volume. |
| `VSUMP{N}` | Share of volume increases | Sum of positive day-to-day volume changes divided by the sum of absolute volume changes. |
| `VSUMN{N}` | Share of volume decreases | Sum of decreases, expressed as positive magnitudes, divided by the sum of absolute volume changes. |
| `VSUMD{N}` | Net volume-change balance | Volume increases minus decreases, divided by total absolute volume change. |

**Visualization:** show `VMA` against a reference line at `1`; show `VSUMP`/`VSUMN` as a pair and `VSUMD` around `0`.

For the frontend, I would store metadata **by family**, then generate the five window variants from it. That avoids maintaining 145 separate descriptions. Keep unavailable values as “—”: `NaN` can occur from insufficient history, missing data, or an undefined calculation, and should not be displayed as zero.
