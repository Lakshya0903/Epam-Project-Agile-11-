"""
Provides baseline and classical time-series forecast algorithms implemented in pure Python.
Used to establish benchmark baselines before evaluating complex statistical or deep learning models.

Supported Algorithms:
1. Naive Persistence (y_hat_{t+h} = y_t) - Benchmark baseline
2. Simple Moving Average (SMA)
3. Exponential Smoothing (SES)
4. Linear Trend Extrapolation (Ordinary Least Squares)
"""

from typing import List, Dict, Any, Optional
import math


class BasePricePredictor:
    """Abstract base interface for commodity price forecasting models."""

    def __init__(self, name: str):
        self.name = name
        self.history: List[float] = []

    def fit(self, history: List[float]) -> "BasePricePredictor":
        """Train or fit model with historical price series."""
        if not history:
            raise ValueError(f"[{self.name}] History series cannot be empty.")
        self.history = [float(x) for x in history]
        return self

    def predict(self, horizon_days: int = 1) -> List[float]:
        """Predict modal price for next `horizon_days` periods."""
        raise NotImplementedError("Subclasses must implement predict()")


class NaivePersistencePredictor(BasePricePredictor):
    """
    Naive Baseline (Persistence Model).
    Forecasts future values as equal to the most recently observed value.
    Any proposed model MUST outperform this baseline to be viable for production.
    """

    def __init__(self):
        super().__init__("Naive-Persistence")

    def predict(self, horizon_days: int = 1) -> List[float]:
        if not self.history:
            raise ValueError("Model must be fitted before predict()")
        last_val = self.history[-1]
        return [round(last_val, 2) for _ in range(horizon_days)]


class SimpleMovingAveragePredictor(BasePricePredictor):
    """
    Rolling Window Moving Average Predictor.
    Averages the last `window_size` days to smooth out transient daily volatility.
    """

    def __init__(self, window_size: int = 7):
        super().__init__(f"SMA-{window_size}")
        self.window_size = window_size

    def predict(self, horizon_days: int = 1) -> List[float]:
        if not self.history:
            raise ValueError("Model must be fitted before predict()")
        window = self.history[-self.window_size :] if len(self.history) >= self.window_size else self.history
        mean_val = sum(window) / len(window)
        return [round(mean_val, 2) for _ in range(horizon_days)]


class ExponentialSmoothingPredictor(BasePricePredictor):
    """
    Single Exponential Smoothing (SES).
    Weights recent observations exponentially more than older observations.
    alpha in (0, 1]: smoothing factor (e.g. 0.3).
    """

    def __init__(self, alpha: float = 0.3):
        super().__init__(f"SES-alpha={alpha}")
        self.alpha = max(0.01, min(0.99, alpha))

    def predict(self, horizon_days: int = 1) -> List[float]:
        if not self.history:
            raise ValueError("Model must be fitted before predict()")
        
        # Fit smoothed level recursively
        s = self.history[0]
        for val in self.history[1:]:
            s = self.alpha * val + (1 - self.alpha) * s
            
        return [round(s, 2) for _ in range(horizon_days)]


class LinearTrendPredictor(BasePricePredictor):
    """
    Linear Trend Extrapolator.
    Computes ordinary least squares regression (slope and intercept) over recent history
    to project short-term upward or downward momentum.
    """

    def __init__(self, window_size: int = 14):
        super().__init__(f"LinearTrend-{window_size}")
        self.window_size = window_size
        self.slope = 0.0
        self.intercept = 0.0

    def fit(self, history: List[float]) -> "LinearTrendPredictor":
        super().fit(history)
        subset = self.history[-self.window_size :] if len(self.history) >= self.window_size else self.history
        n = len(subset)
        if n < 2:
            self.slope = 0.0
            self.intercept = subset[0]
            return self

        # x = 0, 1, ..., n-1
        x_mean = (n - 1) / 2.0
        y_mean = sum(subset) / n

        numerator = sum((i - x_mean) * (subset[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        self.slope = numerator / denominator if denominator != 0 else 0.0
        self.intercept = y_mean - self.slope * x_mean
        return self

    def predict(self, horizon_days: int = 1) -> List[float]:
        if not self.history:
            raise ValueError("Model must be fitted before predict()")
        subset_len = min(len(self.history), self.window_size)
        predictions = []
        for step in range(1, horizon_days + 1):
            future_x = (subset_len - 1) + step
            pred = self.intercept + self.slope * future_x
            # Guardrail: agricultural prices cannot be negative
            pred = max(10.0, pred)
            predictions.append(round(pred, 2))
        return predictions


def build_predictor(algorithm: str = "naive", **kwargs) -> BasePricePredictor:
    """Factory function for instantiating predictors."""
    algo = algorithm.lower().strip()
    if algo in ("naive", "persistence"):
        return NaivePersistencePredictor()
    elif algo in ("sma", "moving_average"):
        window = kwargs.get("window_size", 7)
        return SimpleMovingAveragePredictor(window_size=window)
    elif algo in ("ses", "exponential_smoothing"):
        alpha = kwargs.get("alpha", 0.3)
        return ExponentialSmoothingPredictor(alpha=alpha)
    elif algo in ("linear", "trend"):
        window = kwargs.get("window_size", 14)
        return LinearTrendPredictor(window_size=window)
    else:
        raise ValueError(f"Unknown algorithm: '{algorithm}'. Choose 'naive', 'sma', 'ses', or 'linear'.")


if __name__ == "__main__":
    # Test suite executing all predictors
    sample_prices = [2100, 2120, 2150, 2140, 2180, 2220, 2210, 2250, 2270, 2300]
    horizon = 3

    print("=" * 60)
    print("FARMCART COMMODITY PRICE PREDICTOR DEMO")
    print(f"Historical Price Series (10 days): {sample_prices}")
    print(f"Forecast Horizon: {horizon} days")
    print("=" * 60)

    for algo in ["naive", "sma", "ses", "linear"]:
        model = build_predictor(algo)
        model.fit(sample_prices)
        forecasts = model.predict(horizon_days=horizon)
        print(f"Algorithm: {model.name:<22} | Forecasts (Days +1..+{horizon}): {forecasts}")
    print("=" * 60)
