#!/usr/bin/env bash
# Organize Spark ML artifacts into models/ layout expected by the streaming job.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p models/preprocessing models/classifiers models/label_decoder

link_or_copy() {
  local src="$1"
  local dst="$2"
  if [[ ! -e "$src" ]]; then
    echo "Missing source: $src" >&2
    exit 1
  fi
  rm -rf "$dst"
  ln -sfn "$(realpath "$src")" "$dst"
  echo "Linked $dst -> $src"
}

link_or_copy feature_pipeline models/preprocessing/feature_pipeline
link_or_copy xgb_cv_model models/classifiers/xgboost_intrusion_detector
link_or_copy rf_cv_model models/classifiers/random_forest_fallback
link_or_copy string_indexer models/label_decoder/string_indexer

if [[ -f models/selected_features.pkl ]]; then
  echo "selected_features.pkl already present"
elif [[ -f /home/helqadiri/Desktop/SP1/notebooks/models/selected_features.pkl ]]; then
  cp /home/helqadiri/Desktop/SP1/notebooks/models/selected_features.pkl models/selected_features.pkl
  echo "Copied selected_features.pkl"
fi

echo "Model layout ready under models/"
