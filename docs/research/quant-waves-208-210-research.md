---
name: quant-waves-208-210-research
description: Econometric and financial engineering research for Quantitative Waves 208-210 (Semivariance / Downside Risk, Realized Beta / CAPM, Multi-Horizon Term Structure)
metadata:
  type: reference
---

# Quantitative Desk Waves 208–210 Econometric Research

## 1. Wave 208: Barndorff-Nielsen, Kinnebrock & Shephard (2010) Realized Semivariance & Signed Jumps
- **Foundational Paper:** Barndorff-Nielsen, Kinnebrock & Shephard (2010), "Measuring Downside Risk: Realized Semivariance in Financial Econometrics", *Volatility and Time Series Econometrics*.
- **High-Frequency Return Decomposition:**
  For intraday log-returns $r_{t,i} = p_{t,i} - p_{t,i-1}$, decompose into positive and negative returns:
  $$r_{t,i}^+ = \max(r_{t,i}, 0),\quad r_{t,i}^- = \min(r_{t,i}, 0)$$
- **Realized Semivariances:**
  $$RS_t^+ = \sum_{i=1}^M (r_{t,i}^+)^2,\quad RS_t^- = \sum_{i=1}^M (r_{t,i}^-)^2$$
  Note that $RV_t = RS_t^+ + RS_t^-$.
- **Signed Jump Variation:**
  $$\Delta J_t = RS_t^+ - RS_t^-$$
- **Asymmetric Predictability:** Patton & Sheppard (2015) demonstrate that negative semivariance $RS_t^-$ has significantly higher persistence and predictive power for future volatility than positive semivariance $RS_t^+$.

## 2. Wave 209: Andersen, Bollerslev, Diebold & Wu (2006) Realized Beta & Continuous Covariance
- **Foundational Paper:** Andersen, Bollerslev, Diebold & Wu (2006), "Realized Beta: Persistence and Predictability", *Econometric Analysis of Economic and Financial Time Series*.
- **High-Frequency Co-movement:**
  For asset returns $r_{i,t}$ and market index returns $r_{m,t}$:
  $$RCov_{i,m,t} = \sum_{k=1}^M r_{i,t,k} \cdot r_{m,t,k},\quad RV_{m,t} = \sum_{k=1}^M r_{m,t,k}^2$$
- **Realized Beta Formulation:**
  $$\beta_{i,t} = \frac{RCov_{i,m,t}}{RV_{m,t}}$$
- **Continuous vs Jump Beta Decomposition:**
  Using Bipower Co-variation ($BCOV$), isolate continuous systemic beta:
  $$\beta_{i,t}^c = \frac{BCOV_{i,m,t}}{BV_{m,t}}$$
  Eliminates idiosyncratic jump distortions from market beta estimates.

## 3. Wave 210: Bekaert, Hoerova & Lo Duca (2013) Risk Aversion & Uncertainty Decomposition
- **Foundational Paper:** Bekaert, Hoerova & Lo Duca (2013), "Risk, Uncertainty and Monetary Policy", *Journal of Monetary Economics*.
- **VIX Squared Decomposition:**
  $$VIX_t^2 = \mathbb{E}_t[RV_{t+1}] + VRP_t$$
  Where:
  - $\mathbb{E}_t[RV_{t+1}]$ is physical stock market Expected Variance (Economic Uncertainty).
  - $VRP_t = VIX_t^2 - \mathbb{E}_t[RV_{t+1}]$ is Variance Risk Premium (Time-Varying Risk Aversion).
- **Structural Mapping & Policy Stance:**
  - High Uncertainty + High Risk Aversion $\to$ Liquidity Flight / Panic Regime.
  - Low Uncertainty + High Risk Aversion $\to$ Structural Hedge / Deleveraging.
  - Low Uncertainty + Low Risk Aversion $\to$ Complacency / Carry Trade Expansion.
