"""Tests for GCC calibration framework."""

import numpy as np
import pytest

from src.engines.math_core.calibration import (
    compute_backtest_metrics,
    calibrate_weights,
    run_calibration_pipeline,
    CalibrationPhase,
)


class TestBacktestMetrics:
    def test_perfect_prediction(self):
        pred = np.array([0.5, 0.6, 0.7])
        actual = np.array([0.5, 0.6, 0.7])
        bt = compute_backtest_metrics(pred, actual, pred, actual)
        assert bt.risk_mae == pytest.approx(0.0, abs=1e-6)
        assert bt.risk_rmse == pytest.approx(0.0, abs=1e-6)
        assert bt.risk_correlation == pytest.approx(1.0, abs=0.01)

    def test_with_error(self):
        pred = np.array([0.5, 0.6, 0.7])
        actual = np.array([0.6, 0.7, 0.8])
        bt = compute_backtest_metrics(pred, actual, pred, actual)
        assert bt.risk_mae == pytest.approx(0.1, abs=0.01)

    def test_claims_metrics(self):
        pred = np.array([100.0, 200.0])
        actual = np.array([110.0, 190.0])
        bt = compute_backtest_metrics(pred, actual, pred, actual, pred, actual)
        assert bt.claims_mae > 0


class TestWeightCalibration:
    def test_converges(self):
        features = np.random.rand(50, 4)
        true_weights = np.array([0.3, 0.2, 0.3, 0.2])
        actual = features @ true_weights + np.random.normal(0, 0.01, 50)
        initial_weights = [0.25, 0.25, 0.25, 0.25]
        predicted = features @ np.array(initial_weights)

        calibrated, adj = calibrate_weights(
            initial_weights, predicted, actual, features,
            learning_rate=0.01, max_iterations=200,
        )
        assert len(calibrated) == 4
        assert sum(calibrated) == pytest.approx(1.0, abs=0.01)

    def test_weights_stay_positive(self):
        features = np.random.rand(20, 3)
        actual = np.random.rand(20)
        predicted = np.random.rand(20)
        calibrated, _ = calibrate_weights([0.33, 0.33, 0.34], predicted, actual, features)
        assert all(w > 0 for w in calibrated)


class TestCalibrationPipeline:
    def test_full_pipeline(self):
        n = 30
        pred_r = np.random.rand(n) * 0.5
        actual_r = pred_r + np.random.normal(0, 0.05, n)
        pred_d = np.random.rand(n) * 0.3
        actual_d = pred_d + np.random.normal(0, 0.03, n)

        report = run_calibration_pipeline(pred_r, actual_r, pred_d, actual_d)
        assert CalibrationPhase.EXPERT_INIT in report.phases_completed
        assert CalibrationPhase.HISTORICAL_BACKTEST in report.phases_completed
        assert report.backtest_result is not None
        assert len(report.recommendations) > 0

    def test_with_features_does_regional_cal(self):
        n = 30
        features = np.random.rand(n, 4)
        weights = [0.25, 0.25, 0.25, 0.25]
        pred_r = features @ np.array(weights)
        actual_r = pred_r + np.random.normal(0, 0.02, n)
        pred_d = np.random.rand(n) * 0.3
        actual_d = pred_d + np.random.normal(0, 0.02, n)

        report = run_calibration_pipeline(
            pred_r, actual_r, pred_d, actual_d,
            risk_features=features, current_weights=weights,
        )
        assert CalibrationPhase.REGIONAL_CALIBRATION in report.phases_completed
