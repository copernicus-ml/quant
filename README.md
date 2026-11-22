# Copernicus

```
uv run ./dump_bin.py dump_all \
  --data_path ./copernicus-prod/qlib_csv \
  --qlib_dir ./copernicus-prod/qlib_data_us \
  --date_field_name date \
  --symbol_field_name symbol \
  --include_fields open,high,low,close,volume,vwap,factor \
  --file_suffix .csv \
  --freq day
```