"""Historical data calibration hooks."""
import numpy as np


def calibrate_weights(predicted: list[float], actual: list[float], learning_rate: float = 0.01) -> list[float]:
    pred = np.array(predicted)
    act = np.array(actual)
    error = act - pred
    adjustment = learning_rate * error
    return (pred + adjustment).tolist()


def compute_calibration_score(predicted: list[float], actual: list[float]) -> dict:
    pred = np.array(predicted)
    act = np.array(actual)
    mse = float(np.mean((pred - act)**2))
    mae = float(np.mean(np.abs(pred - act)))
    correlation = float(np.corrcoef(pred, act)[0, 1]) if len(pred) > 1 else 0.0
    return {"mse": mse, "mae": mae, "correlation": correlation, "r_squared": correlation**2}
