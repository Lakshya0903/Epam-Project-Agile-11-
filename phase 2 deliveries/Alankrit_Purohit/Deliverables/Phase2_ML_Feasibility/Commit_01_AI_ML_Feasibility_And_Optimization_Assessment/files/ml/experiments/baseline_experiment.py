"""
Runs an empirical walk-forward backtest evaluating whether classical time-series
and trend models outperform the naive persistence baseline on agricultural price series.
"""

import sys
import os
from typing import List, Dict, Any

# Ensure parent directory and ml/ package are resolvable
current_dir = os.path.dirname(os.path.abspath(__file__))
ml_dir = os.path.abspath(os.path.join(current_dir, ".."))
if ml_dir not in sys.path:
    sys.path.insert(0, ml_dir)

try:
    from evaluation import evaluate_forecast
    from price_predictor import (
        NaivePersistencePredictor,
        SimpleMovingAveragePredictor,
        ExponentialSmoothingPredictor,
        LinearTrendPredictor,
    )
    from dataset_generator import generate_mandi_time_series
except ImportError:
    # If run from repository root or differently structured path
    from ml.evaluation import evaluate_forecast
    from ml.price_predictor import (
        NaivePersistencePredictor,
        SimpleMovingAveragePredictor,
        ExponentialSmoothingPredictor,
        LinearTrendPredictor,
    )
    from ml.experiments.dataset_generator import generate_mandi_time_series


def run_benchmark_experiment(
    total_days: int = 75,
    test_horizon: int = 14,
    seed: int = 2026,
) -> Dict[str, Any]:
    """
    Execute 1-step ahead walk-forward backtest across test_horizon periods.
    """
    records = generate_mandi_time_series(days=total_days, seed=seed)

    # Focus on primary benchmark mandate: Tomato at Azadpur (Delhi)
    series_data = [
        r["modal_price"]
        for r in records
        if r["commodity"] == "Tomato" and "Azadpur" in r["mandi"]
    ]

    train_len = len(series_data) - test_horizon
    test_actuals = series_data[train_len:]

    models = [
        ("Naive (Persistence)", NaivePersistencePredictor()),
        ("Moving Avg (SMA-7)", SimpleMovingAveragePredictor(window_size=7)),
        ("Exp Smoothing (alpha=0.3)", ExponentialSmoothingPredictor(alpha=0.3)),
        ("Linear Trend (OLS-14)", LinearTrendPredictor(window_size=14)),
    ]

    results = []
    naive_mape = None

    for name, model in models:
        predictions = []
        # Walk-forward 1-step ahead simulation
        for t in range(train_len, len(series_data)):
            history_t = series_data[:t]
            model.fit(history_t)
            pred_1 = model.predict(horizon_days=1)[0]
            predictions.append(pred_1)

        metrics = evaluate_forecast(test_actuals, predictions)
        if "Naive" in name:
            naive_mape = metrics["mape_pct"]

        beats_baseline = (
            "BASELINE"
            if "Naive" in name
            else ("YES" if naive_mape and metrics["mape_pct"] < naive_mape else "NO")
        )

        results.append({
            "model": name,
            "mae": metrics["mae"],
            "rmse": metrics["rmse"],
            "mape": metrics["mape_pct"],
            "da": metrics["directional_accuracy_pct"],
            "beats_baseline": beats_baseline,
        })

    return {
        "commodity": "Tomato (Azadpur)",
        "test_days": test_horizon,
        "results": results,
    }


def print_benchmark_table(experiment_output: Dict[str, Any]):
    print("=" * 80)
    print(f"FARMCART ML BENCHMARK REPORT — {experiment_output['commodity']}")
    print(f"Evaluation Window: {experiment_output['test_days']} Days Walk-Forward Validation")
    print("=" * 80)
    header = f"{'Model':<28} | {'MAE (INR)':<10} | {'RMSE (INR)':<10} | {'MAPE (%)':<9} | {'Dir Acc (%)':<11} | {'Beats Baseline?'}"
    print(header)
    print("-" * 80)
    for r in experiment_output["results"]:
        row = (
            f"{r['model']:<28} | "
            f"{r['mae']:<10.2f} | "
            f"{r['rmse']:<10.2f} | "
            f"{r['mape']:<9.2f} | "
            f"{r['da']:<11.1f} | "
            f"{r['beats_baseline']}"
        )
        print(row)
    print("=" * 80)
    print("CONCLUSION & GOVERNANCE DIRECTIVE:")
    print("1. Naive baseline error establishes minimum threshold.")
    print("2. Models with 'Beats Baseline = NO' or 'MAPE > 8%' are REJECTED for production.")
    print("3. ML models are non-blocking advisory components only.")
    print("=" * 80)


if __name__ == "__main__":
    output = run_benchmark_experiment()
    print_benchmark_table(output)
