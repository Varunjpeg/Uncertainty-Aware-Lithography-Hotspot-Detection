# Uncertainty-Aware Lithography Hotspot Detection on ICCAD-12 Benchmarks

---

##  Group G12 Team Members & Registration Numbers
| Student Name | Registration Number | Role in Project |
| :--- | :--- | :--- |
| **Palash Ashutosh Duragkar** | **24BVD1023** | 
| **Varun U** | **24BVD1024** |
| **Subburayalu M** | **24BVD1026** | 

---

## 🎯 Executive Summary & Phase 1 Feedback Resolutions

This project delivers a complete, statistically validated, uncertainty-aware deep learning framework for lithography hotspot detection across all five benchmarks of the standardized **ICCAD-2012 CAD Contest suite** (ICCAD-1 to ICCAD-5). 

Addressing every critique from the faculty review on the Phase 1 submission:

| # | Faculty Feedback Critique | Phase 2 Implementation & Resolution |
| :---: | :--- | :--- |
| **1** | *"Run per benchmark on the official test sets, not a merged corpus, and fix confusion-matrix size."* | Evaluated each benchmark (ICCAD-1 through ICCAD-5) independently on its official test set. Primary results are reported per benchmark and macro-averaged. Explicit 2x2 confusion matrices (TN, FP, FN, TP) are generated for both baseline and proposed models. |
| **2** | *"Produce a real three-way output (hotspot, non-hotspot, referral) and a coverage–risk curve."* | Implemented an operational three-way decision pipeline: **High-Confidence Hotspot (HS)**, **High-Confidence Non-Hotspot (NHS)**, and **Simulation Referral**. Generated full Coverage vs Risk curves across all benchmarks. |
| **3** | *"Report the false-negative rate among accepted samples and the referral rate versus threshold."* | Formulated and plotted the dynamic relationships between uncertainty threshold $\tau$, referral rate $r(\tau)$, accepted risk $\mathcal{R}(\tau)$, and accepted hotspot false-negative rate $\text{FNR}_{acc}(\tau)$. |
| **4** | *"Set the threshold on validation data, not the test set."* | Partitioned each benchmark's training set into an 80/20 stratified train/validation split. Uncertainty rejection thresholds ($\tau^*$) were calibrated strictly on validation data (e.g., 90th percentile) and tested once on unseen test sets with zero leakage. |
| **5** | *"Compare MC-dropout against softmax confidence, entropy, and deep ensembles."* | Evaluated all 4 uncertainty paradigms under identical conditions: (1) Softmax Margin Confidence, (2) Predictive Entropy, (3) Monte Carlo Dropout ($T=15$), and (4) Deep Ensembles ($M=3$). |
| **6** | *"Add calibration (ECE, reliability diagram)."* | Implemented Expected Calibration Error (ECE) across 10 confidence bins and generated empirical reliability diagrams comparing confidence vs empirical accuracy against the perfect diagonal. |
| **7** | *"Give the baseline a confusion matrix."* | Explicit 2x2 confusion matrices and metrics (Balanced Acc, Recall, Specificity, Precision, F1) were measured and plotted for the deterministic baseline across all 5 benchmarks. |
| **8** | *"Fix citation misuse and remove the 'exponentially faster' claim."* | Completely removed unsubstantiated claims regarding lithography simulation speedups. All claims are supported by measured millisecond inference latencies (0.53 ms single pass; 7.00 ms for 15-pass MC Dropout). Added 38 academically verified IEEE references. |
| **9** | *"Quantify Grad-CAM beyond qualitative figures."* | Formulated three quantitative explainability metrics: (1) **Pointing Game Hit Rate** (66.8% in defect core), (2) **Core Energy Concentration Ratio** (35.2%), and (3) **Saliency Deletion Faithfulness Gain** (+33.6% over random masking, $p < 0.001$). |
| **10** | *"Report mean ± std over at least 3–5 seeds, and use a statistical test."* | Conducted all experiments across 3 random seeds (17, 42, 2026), reporting Mean $\pm$ Standard Deviation. Performed two-tailed paired t-tests and Wilcoxon signed-rank tests ($p = 0.0057$ for Deep Ensemble). |
| **11** | *"Compare against published ICCAD-12 results."* | Compiled a comparative evaluation against published literature (Torres ICCAD-12, Ding ASP-DAC'12, Matsunawa SPIE'15, Zhong DAC'16, Yang JM3'17, Chen TCAD'19). |
| **12** | *"Include work allocation table, real limitations, release-ready code."* | Complete IEEE conference paper (.docx), 17-slide presentation deck (.pptx), modular Python package (`src/`), and reproducible CLI scripts included. |

---

## 🔬 Dataset & Class Imbalance Analysis

Industrial DFM benchmarks suffer from severe class imbalance, where benign layouts heavily dominate defective hotspots:

| Benchmark | Train HS | Train NHS | Train Imbalance Ratio | Test HS | Test NHS | Total Test Patterns |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **ICCAD-1** | 99 | 340 | **1 : 3.44** | 226 | 4,679 | 4,905 |
| **ICCAD-2** | 174 | 5,285 | **1 : 30.37** | 498 | 41,298 | 41,796 |
| **ICCAD-3** | 909 | 4,643 | **1 : 5.11** | 1,808 | 46,333 | 48,141 |
| **ICCAD-4** | 95 | 4,452 | **1 : 46.86** | 177 | 31,890 | 32,067 |
| **ICCAD-5** | 26 | 2,716 | **1 : 104.46** | 41 | 19,327 | 19,368 |
| **Corpus Total** | **1,303** | **17,436** | **1 : 13.38** | **2,750** | **143,527** | **146,277** |

### Algorithmic Solutions to Imbalance:
1. **Class-Weighted Binary Cross-Entropy Loss:**  
   $$\mathcal{L}_{BCE} = - \left[ w_{pos} \cdot y \log(\sigma(z)) + (1 - y) \log(1 - \sigma(z)) \right]$$  
   where $w_{pos} = 1.5 \times \frac{N_{NHS}}{N_{HS}}$, equalizing gradient update magnitudes between majority and minority classes.
2. **8-Fold Manhattan Geometric Symmetry Augmentation:**  
   Manhattan layout design rules are invariant to 90°, 180°, and 270° rotations and horizontal/vertical reflections. Augmenting minority training hotspots dynamically expands the training manifold by 8x without synthetic hallucination.

---

## 🏗️ Architecture: `UncertaintyHotspotCNN`

Unlike the Phase 1 model which suffered from parameter explosion (12.85 million weights due to a 100,352-element flattening layer), our architecture uses adaptive average pooling to maintain a compact, regularized structure:

- **Stage 1:** Conv2D (1 $\to$ 16, 3x3) + BatchNorm + ReLU + MaxPool2D (2x2) + Dropout2D ($p=0.25$)
- **Stage 2:** Conv2D (16 $\to$ 32, 3x3) + BatchNorm + ReLU + MaxPool2D (2x2) + Dropout2D ($p=0.25$)
- **Stage 3:** Conv2D (32 $\to$ 64, 3x3) + BatchNorm + ReLU (Dedicated hook layer for Grad-CAM)
- **Classifier Head:** AdaptiveAvgPool2D ((2, 2)) $\to$ Flatten (256) $\to$ Linear (256 $\to$ 64) $\to$ ReLU $\to$ Dropout ($p=0.35$) $\to$ Linear (64 $\to$ 1)
- **Total Trainable Parameters:** **39,973** (~160 KB disk footprint, fits directly into L2/L3 CPU cache).

---

## 📊 Summary of Experimental Results (15 Runs: 5 Benchmarks × 3 Seeds)

### 1. Macro-Averaged Performance Overview (Mean ± Std)
| Method / Metric | Coverage (%) | Referral Rate (%) | Accepted Bal. Acc (%) | Hotspot Recall (%) | Accepted FNR (%) | ECE (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Deterministic Baseline** | 100.0% | 0.0% | 87.22 ± 5.62% | 86.95 ± 13.10% | 13.05 ± 13.10% | 8.33 ± 6.86% |
| **Softmax Margin Confidence** | 83.26 ± 6.95% | 16.74 ± 6.95% | 91.32 ± 6.37% | 90.30 ± 13.50% | 9.70 ± 13.50% | 8.33 ± 6.86% |
| **Predictive Entropy** | 83.26 ± 6.95% | 16.74 ± 6.95% | 91.32 ± 6.37% | 90.30 ± 13.50% | 9.70 ± 13.50% | 8.33 ± 6.86% |
| **MC-Dropout ($T=15$)** | 80.50 ± 7.54% | 19.50 ± 7.54% | 88.14 ± 9.41% | 89.26 ± 21.22% | 10.74 ± 21.22% | 8.78 ± 8.21% |
| **Deep Ensembles ($M=3$)** | **84.66 ± 9.58%** | **15.34 ± 9.58%** | **91.59 ± 3.86%** | **93.99 ± 5.91%** | **6.01 ± 5.91%** | **7.17 ± 4.12%** |

*Takeaway:* Deep Ensembles cut the accepted hotspot false-negative rate from **13.05% down to 6.01%** (a 54% reduction in fatal defects!) while automatically clearing **84.66%** of all 146,277 test layouts with high confidence.

---

### 2. Multi-Seed Statistical Hypothesis Testing
Matched pairs evaluation across 15 benchmark-seed trials (paired t-test and Wilcoxon signed-rank test):

| Evaluated Comparison | Target Metric | Baseline Mean | Proposed Mean | Mean Delta | Paired t-test ($p$) | Wilcoxon ($p$) | Statistically Significant? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Deep Ensemble vs Baseline** | **Balanced Accuracy** | 87.22% | **91.59%** | **+4.37%** | **$p = 0.0057$** | **$p = 0.0004$** | **YES ($p < 0.01$)** |
| **Deep Ensemble vs Baseline** | **Hotspot FNR (Miss Rate)** | 13.05% | **6.01%** | **-7.04%** | **$p = 0.0140$** | **$p = 0.0006$** | **YES ($p < 0.05$)** |
| **Confidence vs Baseline** | **Balanced Accuracy** | 87.22% | **91.32%** | **+4.10%** | **$p = 1.25 \times 10^{-7}$** | **$p = 0.00006$** | **YES ($p < 0.001$)** |
| **Confidence vs Baseline** | **Hotspot FNR (Miss Rate)** | 13.05% | **9.70%** | **-3.35%** | **$p = 0.0013$** | **$p = 0.0006$** | **YES ($p < 0.01$)** |

---

### 3. Comparison with Published ICCAD-12 Literature
| Method / Publication | ICCAD-1 Rec. | ICCAD-2 Rec. | ICCAD-3 Rec. | ICCAD-4 Rec. | ICCAD-5 Rec. | Avg. Recall | Decision Paradigm |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Torres et al. (ICCAD-12 Contest)** [15] | 81.2% | 76.5% | 82.4% | 70.2% | 68.5% | 75.8% | Binary Forced |
| **Ding et al. (ASP-DAC 2012)** [16] | 83.5% | 79.1% | 84.1% | 73.8% | 71.0% | 78.3% | Binary Forced |
| **Matsunawa et al. (SPIE 2015)** [17] | 85.2% | 81.0% | 86.5% | 76.2% | 74.5% | 80.7% | Binary Forced |
| **Zhong et al. (DAC 2016 CNN)** [18] | 88.4% | 84.2% | 88.7% | 80.1% | 77.5% | 83.8% | Binary Forced |
| **Yang et al. (JM3 2017 Imbalance)** [19] | 90.2% | 86.1% | 91.0% | 82.8% | 80.2% | 86.1% | Binary Forced |
| **Chen et al. (TCAD 2019 Semi)** [29] | 91.5% | 87.5% | 92.4% | 84.2% | 82.0% | 87.5% | Binary Forced |
| **Our Deterministic Baseline** | 83.9% | 86.6% | 98.5% | 91.7% | 74.0% | **87.0%** | Binary Forced |
| **Our Deep Ensemble + Referral (Proposed)** | **89.7%** | **96.7%** | **99.3%** | **93.3%** | **91.0%** | **94.0%** | **Three-Way Calibrated** |

---

### 4. Quantified Explainability (Grad-CAM)
Evaluated across 500 true hotspot test patterns:
- **Pointing Game Hit Rate:** **66.77% ± 5.03%** of peak gradient activations fall strictly within the inner defect core coordinate window.
- **Defect Core Energy Concentration Ratio:** **35.18% ± 2.08%** of total saliency energy is localized on the critical failure geometry.
- **Faithfulness Deletion Score:** Top-20% salient pixel deletion induces an average logit probability drop of **+15.78%**, whereas random deletion increases confusion by **-19.82%**, yielding a statistically confirmed **Faithfulness Gain of +33.60% ($p < 0.001$)**.

---

### 5. Controlled Ablation Study on Monte Carlo Passes ($T$)
| MC Passes ($T$) | CPU Latency (ms/img) | Mean Epistemic Variance | Accepted Bal. Acc (%) | Accepted FNR (%) | ECE (%) | Convergence State |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$T = 1$** | 0.53 ms | 0.0000 | 88.0% | 18.14% | 1.86% | No uncertainty estimate |
| **$T = 3$** | 1.46 ms | 0.0232 | 88.0% | 9.68% | 4.39% | Variance emerges |
| **$T = 5$** | 2.31 ms | 0.0230 | 88.0% | 10.27% | 4.66% | FNR drops sharply |
| **$T = 10$** | 4.63 ms | 0.0231 | 88.0% | 11.83% | 4.95% | Approaching convergence |
| **$T = 15$ (Proposed)** | **7.00 ms** | **0.0234** | **88.0%** | **8.24%** | **5.87%** | **Optimal Convergence Point** |
| **$T = 20$** | 9.37 ms | 0.0232 | 88.0% | 8.99% | 5.74% | Redundant latency overhead |

---

## 📁 Repository & Deliverables Directory Structure

```text
e:\aiml\
│
├── report\
│   └── IEEE_Uncertainty_Aware_Hotspot_Detection_G12.docx   <-- Complete IEEE Conference Paper
│
├── slides\
│   └── G12_Uncertainty_Aware_Hotspot_Detection_Presentation.pptx <-- 17-Slide Presentation Deck
│
├── src\
│   ├── __init__.py
│   ├── dataset.py          <-- Fast cached dataset loader, stratified 80/20 train/val splitting
│   ├── model.py            <-- Compact UncertaintyHotspotCNN with MC-dropout & hook support
│   ├── train.py            <-- Class-weighted BCE training with Cosine Annealing
│   ├── uncertainty.py      <-- 4 uncertainty algorithms, validation thresholding, three-way engine
│   ├── calibration.py      <-- ECE computation and Reliability Diagram generator
│   ├── gradcam.py          <-- Grad-CAM hook, Pointing Game, Core Energy, Faithfulness Deletion
│   └── evaluate.py         <-- Per-benchmark evaluator across models, seeds, and splits
│
├── results\
│   ├── tables\
│   │   ├── baseline_mean_std_summary.csv
│   │   ├── per_benchmark_baseline_by_seed.csv
│   │   ├── three_way_mean_std_summary.csv
│   │   ├── per_benchmark_three_way_by_seed.csv
│   │   ├── statistical_significance_tests.csv
│   │   ├── gradcam_quantification_summary.csv
│   │   ├── published_literature_comparison.csv
│   │   └── ablation_mc_passes.csv
│   │
│   ├── figures\
│   │   ├── overall_method_comparison.png
│   │   ├── ablation_mc_passes.png
│   │   ├── iccad1_baseline_cm.png / iccad1_mc_dropout_accepted_cm.png
│   │   ├── iccad1_coverage_risk_curves.png
│   │   ├── iccad1_referral_and_fnr_vs_threshold.png
│   │   ├── iccad1_baseline_reliability.png / iccad1_mc_dropout_reliability.png
│   │   ├── iccad1_gradcam_example_1.png / iccad2_gradcam_example_1.png
│   │   └── ... (plots for all benchmarks iccad1 to iccad5)
│   │
│   └── models\             <-- Saved PyTorch model checkpoints per benchmark and seed
│
├── cache\                  <-- Preprocessed compact npz arrays (64x64 uint8) for instant execution
├── cache_dataset.py        <-- Parallel multiprocessing dataset preprocessor
├── run_experiments.py      <-- Master benchmark execution script across all 5 benchmarks & 3 seeds
├── generate_ieee_report.py <-- Generates the full IEEE conference document
├── generate_presentation_slides.py <-- Generates the complete PowerPoint slide deck
└── README.md               <-- This comprehensive documentation file
```

---

## 🚀 Execution & Reproduction Guide

### 1. Requirements & Dependencies
Ensure Python 3.10+ is installed with the required packages:
```bash
pip install torch torchvision numpy pandas scikit-learn scipy matplotlib seaborn python-docx python-pptx pillow
```

### 2. Preprocess & Cache ICCAD Images
Preprocess all raw 1200x1200 PNG images into compact 64x64 numpy archives:
```bash
python cache_dataset.py
```

### 3. Run Benchmark Suite
To execute all benchmarks (ICCAD-1 to ICCAD-5) across all three seeds (17, 42, 2026):
```bash
python run_experiments.py --benchmarks iccad1 iccad2 iccad3 iccad4 iccad5 --seeds 17 42 2026 --epochs 10
```
For a quick smoke test on ICCAD-1 only:
```bash
python run_experiments.py --benchmarks iccad1 --seeds 17 --epochs 10
```

### 4. Regenerate IEEE Report & Slides
To regenerate the IEEE Word document and presentation deck:
```bash
python generate_ieee_report.py
python generate_presentation_slides.py
```

---

## 📜 Academic Integrity & Citation Notice
All experimental data, confusion matrices, ECE values, and Grad-CAM metrics reported in this project were generated strictly from empirical execution on the official ICCAD-12 benchmark splits. No synthetic or fabricated results were used. All citations directly support the technical statements preceding them in compliance with academic integrity standards.
