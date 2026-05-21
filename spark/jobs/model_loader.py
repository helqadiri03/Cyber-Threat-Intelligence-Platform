"""Load Spark ML models with XGBoost → Random Forest fallback."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from pyspark.ml import PipelineModel
from pyspark.ml.classification import RandomForestClassificationModel
from pyspark.ml.feature import StringIndexerModel
from pyspark.ml.tuning import CrossValidatorModel

LOG = logging.getLogger(__name__)


@dataclass
class ModelBundle:
    feature_pipeline: PipelineModel
    classifier: object
    classifier_name: str
    label_map: dict[float, str]


def load_label_map(label_indexer_path: str) -> dict[float, str]:
    indexer = StringIndexerModel.load(label_indexer_path)
    return {float(i): name for i, name in enumerate(indexer.labels)}


def load_models(
    feature_pipeline_path: str,
    xgb_path: str,
    rf_path: str,
    label_indexer_path: str,
) -> ModelBundle:
    LOG.info("Loading feature pipeline from %s", feature_pipeline_path)
    feature_pipeline = PipelineModel.load(feature_pipeline_path)
    label_map = load_label_map(label_indexer_path)

    classifier = None
    classifier_name = "unknown"

    try:
        LOG.info("Loading XGBoost classifier from %s", xgb_path)
        xgb_cv = CrossValidatorModel.load(xgb_path)
        classifier = xgb_cv.bestModel
        classifier_name = "xgboost"
        LOG.info("XGBoost model loaded")
    except Exception as exc:
        LOG.warning("XGBoost load failed (%s) — falling back to Random Forest", exc)
        try:
            rf_cv = CrossValidatorModel.load(rf_path)
            classifier = rf_cv.bestModel
            classifier_name = "random_forest"
            LOG.info("Random Forest fallback loaded")
        except Exception as rf_exc:
            LOG.warning("CrossValidator RF load failed (%s) — loading bestModel directly", rf_exc)
            classifier = RandomForestClassificationModel.load(f"{rf_path}/bestModel")
            classifier_name = "random_forest"

    if classifier is None:
        raise RuntimeError("No classifier could be loaded")

    return ModelBundle(
        feature_pipeline=feature_pipeline,
        classifier=classifier,
        classifier_name=classifier_name,
        label_map=label_map,
    )
