"""
Pure-Python implementation of regression metrics for commodity price forecasting
and demand modeling. Evaluates predictions against ground truth without external
dependencies (no numpy/scikit-learn required for lightweight portability).
"""

import math
from typing import List, Dict, Any, Union


def mean_absolute_error(y_true: List[float], y_pred: List[float]) -> float:
    """
    Compute Mean Absolute Error (MAE): (1/n) * sum(|y_true - y_pred|)
    Measures average magnitude of forecast errors in price units (INR/quintal).
    """
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true ({len(y_true)}) != y_pred ({len(y_pred)})")
    if not y_true:
        raise ValueError("Cannot calculate MAE on empty lists")
    return sum(abs(t - p) for t, p in zip(y_true, y_pred)) / len(y_true)


def root_mean_squared_error(y_true: List[float], y_pred: List[float]) -> float:
    """
    Compute Root Mean Squared Error (RMSE): sqrt((1/n) * sum((y_true - y_pred)^2))
    Penalizes large outlier forecast errors more heavily than MAE.
    """
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true ({len(y_true)}) != y_pred ({len(y_pred)})")
    if not y_true:
        raise ValueError("Cannot calculate RMSE on empty lists")
    mse = sum((t - p) ** 2 for t, p in zip(y_true, y_pred)) / len(y_true)
    return math.sqrt(mse)


def mean_absolute_percentage_error(y_true: List[float], y_pred: List[float], epsilon: float = 1e-8) -> float:
    """
    Compute Mean Absolute Percentage Error (MAPE): (100 / n) * sum(|(y_true - y_pred) / y_true|)
    Provides scale-independent error metric as a percentage (e.g. 5.4%).
    """
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true ({len(y_true)}) != y_pred ({len(y_pred)})")
    if not y_true:
        raise ValueError("Cannot calculate MAPE on empty lists")
    
    pct_errors = []
    for t, p in zip(y_true, y_pred):
        denom = abs(t) if abs(t) > epsilon else epsilon
        pct_errors.append(abs(t - p) / denom)
    
    return (sum(pct_errors) / len(pct_errors)) * 100.0


def directional_accuracy(y_true: List[float], y_pred: List[float]) -> float:
    """
    Compute Directional Accuracy (%): Percentage of times the forecast
    correctly predicted the direction of price movement compared to previous value.
    Requires at least 2 points.
    """
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true ({len(y_true)}) != y_pred ({len(y_pred)})")
    if len(y_true) < 2:
        return 100.0
    
    correct_directions = 0
    total_steps = len(y_true) - 1
    for i in range(1, len(y_true)):
        actual_delta = y_true[i] - y_true[i - 1]
        pred_delta = y_pred[i] - y_true[i - 1]
        if (actual_delta >= 0 and pred_delta >= 0) or (actual_delta < 0 and pred_delta < 0):
            correct_directions += 1
            
    return (correct_directions / total_steps) * 100.0


def evaluate_forecast(y_true: List[float], y_pred: List[float]) -> Dict[str, float]:
    """
    Comprehensive evaluation summary containing MAE, RMSE, MAPE, and Directional Accuracy.
    """
    mae = mean_absolute_error(y_true, y_pred)
    rmse = root_mean_squared_error(y_true, y_pred)
    mape = mean_absolute_percentage_error(y_true, y_pred)
    da = directional_accuracy(y_true, y_pred)
    
    return {
        "sample_size": len(y_true),
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape_pct": round(mape, 2),
        "directional_accuracy_pct": round(da, 2),
    }


if __name__ == "__main__":
    # Self-test with sample synthetic observations and predictions
    actuals = [2200.0, 2250.0, 2180.0, 2300.0, 2340.0, 2280.0, 2310.0]
    preds =   [2190.0, 2240.0, 2200.0, 2280.0, 2350.0, 2300.0, 2300.0]
    
    metrics = evaluate_forecast(actuals, preds)
    print("=" * 50)
    print("FARMCART ML EVALUATION SUITE TEST")
    print("=" * 50)
    print(f"Sample Count          : {metrics['sample_size']}")
    print(f"MAE (INR/quintal)     : {metrics['mae']}")
    print(f"RMSE (INR/quintal)    : {metrics['rmse']}")
    print(f"MAPE (%)              : {metrics['mape_pct']}%")
    print(f"Directional Accuracy  : {metrics['directional_accuracy_pct']}%")
    print("=" * 50)
    print("All ML evaluation metrics calculated successfully.")
