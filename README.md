# Copernicus

```
uv run ./dump_bin.py dump_all \
  --data_path ./copernicus-dev/qlib_csv \
  --qlib_dir ./copernicus-dev/qlib_data_us \
  --date_field_name date \
  --symbol_field_name symbol \
  --include_fields open,high,low,close,volume,vwap,factor \
  --file_suffix .csv \
  --freq day
```