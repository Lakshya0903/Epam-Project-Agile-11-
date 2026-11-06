# FarmCart — Machine Learning Research & Feasibility Framework

**Lead:** Alankrit Purohit (AI/ML Lead)  
**Status:** Phase 1 Feasibility & Benchmark Modeling  

---

## 1. Objective & Problem Framing

The goal of the ML track in FarmCart is to determine whether predictive algorithms can provide **measurable, defensible value** to smallholder farmers and buyers without introducing deployment fragility or blocking core marketplace transactions.

### Key Applications Under Evaluation:
1. **Mandi Price Forecasting**: Predicting 3-day and 7-day terminal wholesale modal prices to guide farmers on optimal harvest timing and listing prices.
2. **Cluster Demand Estimation**: Forecasting regional order density to optimize delivery batch sizes.

---

## 2. Engineering Principles

> [!IMPORTANT]
> **ML is an advisory enhancement, NOT a runtime dependency.**
> - The core marketplace (listing, checkout, batching, delivery, payments) functions 100% deterministically without ML models.
> - No complex external frameworks (PyTorch, TensorFlow) are required for Phase 1; baseline models are implemented in pure Python.
> - We benchmark all predictive models against a strict **Naive (Persistence) Baseline** ($y_t = y_{t-1}$). If a model cannot beat the naive baseline, it is rejected.

---

## 3. Evaluation Criteria

Models are evaluated using three standard regression metrics:

1. **Mean Absolute Error (MAE)**:
   $$\text{MAE} = \frac{1}{n} \sum_{i=1}^n |y_i - \hat{y}_i|$$
   Measures absolute average deviation in INR per quintal.
2. **Root Mean Squared Error (RMSE)**:
   $$\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^n (y_i - \hat{y}_i)^2}$$
   Penalizes large outlier forecast errors.
3. **Mean Absolute Percentage Error (MAPE)**:
   $$\text{MAPE} = \frac{100\%}{n} \sum_{i=1}^n \left| \frac{y_i - \hat{y}_i}{y_i} \right|$$
   Provides scale-independent accuracy across high-value and low-value crops. Target: **MAPE < 8.0%**.

---

## 4. Directory Structure

```text
ml/
├── README.md                          # Machine learning framework documentation (this file)
├── evaluation.py                      # Pure-Python metrics suite (MAE, RMSE, MAPE)
├── price_predictor.py                 # Naive, Moving Average, and Linear Trend Predictors
└── experiments/
    ├── dataset_generator.py           # Synthetic seasonal mandi time-series generator
    └── baseline_experiment.py         # Reproducible benchmark experiment runner
```

---

## 5. Running the Baseline Experiment

To execute the reproducible experiment and evaluate baseline model performance:

```bash
python ml/experiments/baseline_experiment.py
```
