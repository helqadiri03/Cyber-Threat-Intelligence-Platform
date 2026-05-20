# Parquet → Kafka Schema Contract

_Generated: 2026-05-20T22:17:48.940335+00:00_

## Dataset summary

| Property | Value |
|----------|-------|
| Source | `/data/stream_holdout` |
| Parquet files | 20 |
| Rows | 30,564 |
| Columns | 60 |
| Contract valid | **True** |

## Critical fields (must be non-null)

- `Label` — nulls: **0**
- `Destination Port` — nulls: **0**
- `Flow Duration` — nulls: **0**

## Label distribution (unique values)

`Botnet`, `BruteForce`, `DoS/DDoS`, `Heartbleed`, `Infiltration`, `Normal`, `Recon`, `WebAttack`

## Selected features check

- Expected (model): **41** features
- Missing in Parquet: _none_

## Column names & types

```json
{
  "Destination Port": "int32",
  "Flow Duration": "int32",
  "Total Fwd Packets": "int32",
  "Total Backward Packets": "int32",
  "Total Length of Fwd Packets": "int32",
  "Total Length of Bwd Packets": "int32",
  "Fwd Packet Length Max": "int32",
  "Fwd Packet Length Min": "int32",
  "Fwd Packet Length Mean": "double",
  "Fwd Packet Length Std": "double",
  "Bwd Packet Length Max": "int32",
  "Bwd Packet Length Min": "int32",
  "Bwd Packet Length Mean": "double",
  "Bwd Packet Length Std": "double",
  "Flow Bytes/s": "double",
  "Flow Packets/s": "double",
  "Flow IAT Mean": "double",
  "Flow IAT Std": "double",
  "Flow IAT Max": "int32",
  "Flow IAT Min": "int32",
  "Fwd IAT Total": "int32",
  "Fwd IAT Mean": "double",
  "Fwd IAT Std": "double",
  "Fwd IAT Max": "int32",
  "Fwd IAT Min": "int32",
  "Bwd IAT Total": "int32",
  "Bwd IAT Mean": "double",
  "Bwd IAT Std": "double",
  "Bwd IAT Max": "int32",
  "Bwd IAT Min": "int32",
  "Fwd Header Length34": "int64",
  "Bwd Header Length": "int32",
  "Fwd Packets/s": "double",
  "Bwd Packets/s": "double",
  "Min Packet Length": "int32",
  "Max Packet Length": "int32",
  "Packet Length Mean": "double",
  "Packet Length Std": "double",
  "Packet Length Variance": "double",
  "FIN Flag Count": "int32",
  "SYN Flag Count": "int32",
  "RST Flag Count": "int32",
  "PSH Flag Count": "int32",
  "ACK Flag Count": "int32",
  "Down/Up Ratio": "int32",
  "Average Packet Size": "double",
  "Avg Fwd Segment Size": "double",
  "Avg Bwd Segment Size": "double",
  "Fwd Header Length55": "int64",
  "act_data_pkt_fwd": "int32",
  "min_seg_size_forward": "int32",
  "Active Mean": "double",
  "Active Std": "double",
  "Active Max": "int32",
  "Active Min": "int32",
  "Idle Mean": "double",
  "Idle Std": "double",
  "Idle Max": "int32",
  "Idle Min": "int32",
  "Label": "string"
}
```

## Kafka contract

- Topic: `cyber_events_raw`
- Encoding: JSON (one row per message)
- Producer and Spark consumer **must** preserve column names exactly.
