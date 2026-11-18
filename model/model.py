import pandas as pd

from feature import Label

purge_days = {Label.T5: 6}


class Model:
    @staticmethod
    def split_data(
        features: pd.DataFrame,
        labels: pd.DataFrame,
        calendar: pd.Series,
        label_type: Label,
        train_seg: tuple[str, str],
        valid_seg: tuple[str, str],
        test_seg: tuple[str, str],
    ):
        dates = features.index.get_level_values("datetime")
        train_mask = get_segment_mask(
            dates,
            train_seg[0],
            train_seg[1],
            calendar,
            purge_last=purge_days[label_type],
        )
        valid_mask = get_segment_mask(
            dates,
            valid_seg[0],
            valid_seg[1],
            calendar,
            purge_last=purge_days[label_type],
        )
        test_mask = get_segment_mask(dates, test_seg[0], test_seg[1], calendar)
        X_train, y_train = features[train_mask], labels[train_mask]
        X_valid, y_valid = features[valid_mask], labels[valid_mask]
        X_test, y_test = features[test_mask], labels[test_mask]
        return (X_train, y_train), (X_valid, y_valid), (X_test, y_test)


def get_segment_mask(
    dates: pd.Index,
    start: str,
    end: str,
    calendar: pd.Series,
    purge_last: int = 0,
):
    segment_days = calendar[(calendar >= start) & (calendar <= end)]
    if purge_last:
        segment_days = segment_days[:-purge_last]
    if len(segment_days) == 0:
        raise ValueError(f"No trading days in ${start} to ${end}")
    return (dates >= segment_days.iloc[0]) & (dates <= segment_days.iloc[-1])
