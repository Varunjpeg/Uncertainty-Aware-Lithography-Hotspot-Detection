import os
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def build_presentation():
    prs = Presentation()
    # 16:9 Widescreen layout
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Color Palette: Clean IEEE Academic Navy
    NAVY = RGBColor(0x0F, 0x2A, 0x4A)
    LIGHT_BG = RGBColor(0xF8, 0xFA, 0xFC)
    WHITE = RGBColor(0xFF, 0xFF, 0xFF)
    TEXT_DARK = RGBColor(0x1E, 0x29, 0x3B)
    TEXT_MUTED = RGBColor(0x64, 0x74, 0x8B)
    BLUE_ACCENT = RGBColor(0x02, 0x84, 0xC7)
    GREEN_ACCENT = RGBColor(0x05, 0x96, 0x69)
    RED_ACCENT = RGBColor(0xDC, 0x26, 0x26)

    def set_slide_background(slide, color):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = color

    def add_header(slide, title_text, category_text="BEVD402L — AI & ML FOR IC DESIGN | GROUP G12"):
        # Header banner
        header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.9))
        tf = header_box.text_frame
        tf.word_wrap = True
        tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
        
        p_cat = tf.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(9.5)
        p_cat.font.bold = True
        p_cat.font.color.rgb = BLUE_ACCENT
        
        p_title = tf.add_paragraph()
        p_title.text = title_text
        p_title.font.size = Pt(20)
        p_title.font.bold = True
        p_title.font.color.rgb = NAVY

    # -------------------------------------------------------------
    # SLIDE 1: TITLE SLIDE
    # -------------------------------------------------------------
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, NAVY)

    # Accent decorative shape
    accent = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.2), Inches(0.2), Inches(5.1))
    accent.fill.solid()
    accent.fill.fore_color.rgb = BLUE_ACCENT
    accent.line.fill.background()

    tb1 = s1.shapes.add_textbox(Inches(1.2), Inches(1.2), Inches(11.3), Inches(5.1))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p0 = tf1.paragraphs[0]
    p0.text = "DIGITAL ASSIGNMENT II — PHASE 2 FINAL SUBMISSION"
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = BLUE_ACCENT

    p1 = tf1.add_paragraph()
    p1.text = "Uncertainty-Aware Lithography Hotspot Detection"
    p1.font.size = Pt(30)
    p1.font.bold = True
    p1.font.color.rgb = WHITE
    p1.space_before = Pt(8)

    p2 = tf1.add_paragraph()
    p2.text = "Three-Way Classification, Probability Calibration & Quantified Explainability on ICCAD-12 Benchmarks"
    p2.font.size = Pt(16)
    p2.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)
    p2.space_before = Pt(6)

    p3 = tf1.add_paragraph()
    p3.text = "\nTeam G12 Members:\n• Palash Ashutosh Duragkar (24BVD1023)\n• Varun U (24BVD1024)\n• Subburayalu M (24BVD1026)"
    p3.font.size = Pt(13)
    p3.font.color.rgb = RGBColor(0xE2, 0xE8, 0xF0)
    p3.space_before = Pt(14)

    p4 = tf1.add_paragraph()
    p4.text = "\nCourse: BEVD402L — AI and Machine Learning for IC | Slot: D1+TD1\nFaculty: Dr. G. Lakshmi Priya | School of Electronics Engineering (SENSE), VIT Chennai"
    p4.font.size = Pt(11)
    p4.font.italic = True
    p4.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)

    # Helper for 2-column content slide
    def make_content_slide(title, cat="BEVD402L — RESEARCH METHODOLOGY"):
        s = prs.slides.add_slide(blank_layout)
        set_slide_background(s, LIGHT_BG)
        add_header(s, title, cat)
        return s

    # -------------------------------------------------------------
    # SLIDE 2: RESEARCH CONTEXT & THE DFM HOTSPOT PROBLEM
    # -------------------------------------------------------------
    s2 = make_content_slide("Lithography Hotspot Detection in Sub-Wavelength Regime")
    tb2 = s2.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.4))
    tf2 = tb2.text_frame
    tf2.word_wrap = True

    bullets_s2 = [
        ("Sub-Wavelength Lithography Scaling", "In 193nm immersion lithography, geometric features (<20nm) are far smaller than illumination wavelength, leading to severe optical diffraction, interference, and resist chemical blur."),
        ("Physical Hotspots as Fatal Defects", "Complex 2D topological configurations suffer bridging (shorts), necking (opens), and line-end shortening, severely degrading parametric wafer yield."),
        ("The Verification Dilemma: Speed vs Accuracy", "Rigorous numerical lithography simulation (Hopkins optical modeling + resist dissolution) requires thousands of CPU hours for full-chip verification. Pattern matching is fast but fails on unseen geometries."),
        ("The Pitfall of Deterministic Deep Learning", "Standard CNNs provide rapid inference (~1ms) but output deterministic, overconfident probabilities. On ambiguous or out-of-distribution (OOD) layout clips, false negatives cause fatal yield loss, while false positives overwhelm OPC teams.")
    ]
    for i, (head, desc) in enumerate(bullets_s2):
        p = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
        p.text = f"•  {head}: "
        p.font.bold = True
        p.font.size = Pt(13)
        p.font.color.rgb = NAVY
        p.space_before = Pt(8)
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.size = Pt(12)
        run.font.color.rgb = TEXT_DARK

    # -------------------------------------------------------------
    # SLIDE 3: PHASE 1 FEEDBACK RESOLUTION
    # -------------------------------------------------------------
    s3 = make_content_slide("Comprehensive Resolution of Faculty Phase 1 Feedback")
    tb3 = s3.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.4))
    tf3 = tb3.text_frame
    tf3.word_wrap = True

    feedback_items = [
        ("1. Benchmark Independence", "Eliminated merged corpus. Every benchmark (ICCAD 1 to 5) is trained and evaluated independently on official test sets."),
        ("2. Calibrated 3-Way Decisions", "Implemented a full three-way decision pipeline: High-confidence HS, High-confidence NHS, and Simulation Referral with Coverage–Risk curves."),
        ("3. Validation Thresholding", "Uncertainty thresholds are calibrated strictly on a stratified 20% validation split, ensuring zero test data leakage."),
        ("4. Multi-Paradigm Comparison", "Rigorously benchmarked Softmax Confidence, Predictive Entropy, MC-Dropout (T=15), and Deep Ensembles (M=3)."),
        ("5. Probability Calibration", "Computed Expected Calibration Error (ECE) and generated empirical reliability diagrams across all models."),
        ("6. Baseline Confusion Matrices", "Reported full 2x2 confusion matrices (TN, FP, FN, TP) for both baseline and proposed models per benchmark."),
        ("7. Quantified Explainability", "Grad-CAM is evaluated quantitatively using Pointing Game Hit Rate, Core Energy Concentration, and Faithfulness Deletion Scores."),
        ("8. Statistical Rigor", "Conducted multi-seed evaluations (seeds 17, 42, 2026) with paired t-tests and Wilcoxon signed-rank significance tests.")
    ]
    for i, (head, desc) in enumerate(feedback_items):
        p = tf3.paragraphs[0] if i == 0 else tf3.add_paragraph()
        p.text = f"{head}: "
        p.font.bold = True
        p.font.size = Pt(11.5)
        p.font.color.rgb = NAVY
        p.space_before = Pt(4)
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.size = Pt(11)
        run.font.color.rgb = TEXT_DARK

    # -------------------------------------------------------------
    # SLIDE 4: DATASET DISTRIBUTION & CLASS IMBALANCE MITIGATION
    # -------------------------------------------------------------
    s4 = make_content_slide("ICCAD-12 Benchmark Statistics & Optimization Bias")
    # Add table on left
    t_shape = s4.shapes.add_table(6, 6, Inches(0.8), Inches(1.6), Inches(7.2), Inches(3.2))
    table = t_shape.table
    headers = ["Benchmark", "Train HS", "Train NHS", "Train Imbalance", "Test HS", "Test NHS"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        p = cell.text_frame.paragraphs[0]
        p.font.bold = True
        p.font.size = Pt(10)
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER

    rows_data = [
        ["ICCAD-1", "99", "340", "1 : 3.44", "226", "4,679"],
        ["ICCAD-2", "174", "5,285", "1 : 30.37", "498", "41,298"],
        ["ICCAD-3", "909", "4,643", "1 : 5.11", "1,808", "46,333"],
        ["ICCAD-4", "95", "4,452", "1 : 46.86", "177", "31,890"],
        ["ICCAD-5", "26", "2,716", "1 : 104.46", "41", "19,327"],
    ]
    for i, r in enumerate(rows_data):
        for j, val in enumerate(r):
            cell = table.cell(i+1, j)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if i % 2 == 0 else RGBColor(0xF1, 0xF5, 0xF9)
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(9.5)
            p.font.color.rgb = TEXT_DARK
            p.alignment = PP_ALIGN.CENTER

    # Text box on right
    tb4 = s4.shapes.add_textbox(Inches(8.3), Inches(1.5), Inches(4.2), Inches(5.2))
    tf4 = tb4.text_frame
    tf4.word_wrap = True
    p = tf4.paragraphs[0]
    p.text = "The Imbalance Collapse Problem:"
    p.font.bold = True
    p.font.size = Pt(13)
    p.font.color.rgb = RED_ACCENT
    
    p = tf4.add_paragraph()
    p.text = "In ICCAD-5 (1:104.5), a degenerate model predicting NHS for all inputs achieves 99.05% accuracy but 0.0% hotspot recall."
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_DARK
    p.space_before = Pt(6)

    p = tf4.add_paragraph()
    p.text = "\nOur Algorithmic Mitigations:"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = NAVY
    
    p = tf4.add_paragraph()
    p.text = "1. Class-Weighted Loss:\nBCE loss scaled by pos_weight = w * (N_NHS / N_HS) to equalize minority class gradient updates.\n\n2. 8-Fold Manhattan Augmentation:\nRotations (90°, 180°, 270°) and horizontal/vertical flips of minority training hotspots prevent overfitting and enrich geometric diversity."
    p.font.size = Pt(10.5)
    p.font.color.rgb = TEXT_DARK
    p.space_before = Pt(4)

    # -------------------------------------------------------------
    # SLIDE 5: COMPACT CALIBRATED ARCHITECTURE
    # -------------------------------------------------------------
    s5 = make_content_slide("Proposed Model Architecture: UncertaintyHotspotCNN")
    tb5 = s5.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.4))
    tf5 = tb5.text_frame
    tf5.word_wrap = True

    arch_bullets = [
        ("Parameter Explosion Eliminated", "Phase 1 contained 12.85M parameters due to a 100,352-node dense layer. Our architecture contains only 39,973 parameters (~160 KB memory footprint), preventing severe overfitting."),
        ("Stage 1 (Low-level Edges)", "Conv2D (1->16, 3x3) -> BatchNorm2D -> ReLU -> MaxPool2D (2x2) -> Dropout2D (p=0.25). Captures wire boundaries."),
        ("Stage 2 (Topological Features)", "Conv2D (16->32, 3x3) -> BatchNorm2D -> ReLU -> MaxPool2D (2x2) -> Dropout2D (p=0.25). Captures wire proximity and jogs."),
        ("Stage 3 & Explainability Hook", "Conv2D (32->64, 3x3) -> BatchNorm2D -> ReLU. Dedicated forward/backward hook layer for Grad-CAM."),
        ("Adaptive Average Pooling", "AdaptiveAvgPool2D((2, 2)) compresses feature maps to 2x2 regardless of input scale, feeding Dense(256->64) -> Dropout(0.35) -> Dense(64->1)."),
        ("Principled MC-Dropout Mode", "During inference, Dropout layers are activated while BatchNorm is strictly kept in evaluation mode to use true population running statistics.")
    ]
    for i, (head, desc) in enumerate(arch_bullets):
        p = tf5.paragraphs[0] if i == 0 else tf5.add_paragraph()
        p.text = f"•  {head}: "
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = NAVY
        p.space_before = Pt(6)
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.size = Pt(11.5)
        run.font.color.rgb = TEXT_DARK

    # -------------------------------------------------------------
    # SLIDE 6: 4 UNCERTAINTY QUANTIFICATION PARADIGMS
    # -------------------------------------------------------------
    s6 = make_content_slide("Four Evaluated Uncertainty Estimation Paradigms")
    # 4 Cards Layout
    cards = [
        ("Softmax Confidence", "Measures distance from certainty boundary:\nu_conf = 1 - max(p, 1 - p)\nRange: [0, 0.5]\nFastest, single forward pass, but prone to overconfidence on OOD samples.", Inches(0.8)),
        ("Predictive Entropy", "Quantifies total information ambiguity:\nu_ent = - [p log2 p + (1-p) log2(1-p)]\nRange: [0, 1.0 bit]\nPeaks at p=0.5; captures aleatoric prediction ambiguity.", Inches(3.8)),
        ("Monte Carlo Dropout", "Bayesian epistemic variance over T=15 stochastic passes:\nu_MC = (1/(T-1)) sum (p_t - mean_p)^2\nQuantifies network weight parameter uncertainty on unfamiliar geometries.", Inches(6.8)),
        ("Deep Ensembles", "Independent models (M=3) with distinct weight initializations:\nu_Ens = (1/(M-1)) sum (p_m - mean_p)^2\nCaptures epistemic model diversity and multi-modal posterior distributions.", Inches(9.8))
    ]
    for title, text, left_pos in cards:
        shape = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, Inches(1.6), Inches(2.7), Inches(5.0))
        shape.fill.solid()
        shape.fill.fore_color.rgb = WHITE
        shape.line.color.rgb = BLUE_ACCENT
        shape.line.width = Pt(1.5)
        
        tb = s6.shapes.add_textbox(left_pos + Inches(0.15), Inches(1.8), Inches(2.4), Inches(4.5))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.bold = True
        p.font.size = Pt(13)
        p.font.color.rgb = NAVY
        
        p = tf.add_paragraph()
        p.text = text
        p.font.size = Pt(10.5)
        p.font.color.rgb = TEXT_DARK
        p.space_before = Pt(8)

    # -------------------------------------------------------------
    # SLIDE 7: THREE-WAY CLASSIFICATION & DECISION ENGINE
    # -------------------------------------------------------------
    s7 = make_content_slide("Calibrated Three-Way Decision Pipeline")
    tb7 = s7.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.4))
    tf7 = tb7.text_frame
    tf7.word_wrap = True

    dec_steps = [
        ("Step 1: Threshold Calibration on Validation Split", "The rejection threshold tau is set to the 90th percentile of uncertainty on the 20% validation split: tau = Percentile(U_val, 90.0). No test set peeking."),
        ("Step 2: Operational Three-Way Routing", "For unseen test layout crop x with mean probability p(x) and uncertainty u(x):\n   • If u(x) > tau  ==>  REFERRAL (Sent to detailed lithography simulation / DRC specialist)\n   • If u(x) <= tau and p(x) >= 0.5  ==>  HIGH-CONFIDENCE HOTSPOT (Automated HS detection)\n   • If u(x) <= tau and p(x) < 0.5  ==>  HIGH-CONFIDENCE NON-HOTSPOT (Automated safe pattern)"),
        ("Step 3: Coverage vs Risk Metrics", "Coverage C = N_accepted / N_total. Risk R = N_errors_accepted / N_accepted.\nAccepted Hotspot False-Negative Rate FNR = FN_accepted / (TP_accepted + FN_accepted)."),
        ("DFM Practical Benefit", "Missing a hotspot causes catastrophic chip death on silicon. By referring ambiguous boundary cases to simulation, the model prevents fatal false negatives while automatically clearing 84.7% of safe layouts.")
    ]
    for i, (head, desc) in enumerate(dec_steps):
        p = tf7.paragraphs[0] if i == 0 else tf7.add_paragraph()
        p.text = f"{head}:\n"
        p.font.bold = True
        p.font.size = Pt(12.5)
        p.font.color.rgb = NAVY
        p.space_before = Pt(6)
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.size = Pt(11.5)
        run.font.color.rgb = TEXT_DARK

    # -------------------------------------------------------------
    # SLIDE 8: PRIMARY EXPERIMENTAL RESULTS (MACRO SUMMARY)
    # -------------------------------------------------------------
    s8 = make_content_slide("Overall Macro Performance Comparison Across All Benchmarks")
    # Add overall comparison plot
    if os.path.exists("e:/aiml/results/figures/overall_method_comparison.png"):
        s8.shapes.add_picture("e:/aiml/results/figures/overall_method_comparison.png", Inches(0.8), Inches(1.6), Inches(7.5), Inches(5.2))

    tb8 = s8.shapes.add_textbox(Inches(8.6), Inches(1.6), Inches(4.0), Inches(5.2))
    tf8 = tb8.text_frame
    tf8.word_wrap = True

    p = tf8.paragraphs[0]
    p.text = "Key Quantitative Findings:"
    p.font.bold = True
    p.font.size = Pt(14)
    p.font.color.rgb = NAVY

    findings = [
        ("Balanced Accuracy", "Deep Ensemble achieves 91.59% ± 3.86% (vs 87.22% ± 5.62% baseline)."),
        ("Missed Hotspot Reduction", "Accepted Hotspot FNR drops from 13.05% down to 6.01% (a 54% reduction in fatal defects!)."),
        ("Automated Clearance", "84.66% of the 146,277 test layouts are automatically processed with high confidence."),
        ("Calibration Gain", "ECE drops from 8.33% to 7.17% under Deep Ensembles.")
    ]
    for h, d in findings:
        p = tf8.add_paragraph()
        p.text = f"• {h}: "
        p.font.bold = True
        p.font.size = Pt(11)
        p.font.color.rgb = NAVY
        p.space_before = Pt(6)
        run = p.add_run()
        run.text = d
        run.font.bold = False
        run.font.color.rgb = TEXT_DARK

    # -------------------------------------------------------------
    # SLIDE 9: BENCHMARK-WISE METRICS TABLE
    # -------------------------------------------------------------
    s9 = make_content_slide("Benchmark-Wise Detailed Results Across ICCAD 1–5")
    t9_shape = s9.shapes.add_table(7, 7, Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.0))
    t9 = t9_shape.table
    h9 = ["Benchmark", "Method", "Coverage (%)", "Referral (%)", "Accepted Bal. Acc (%)", "Hotspot Recall (%)", "Accepted FNR (%)"]
    for j, h in enumerate(h9):
        cell = t9.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        p = cell.text_frame.paragraphs[0]
        p.font.bold = True
        p.font.size = Pt(9.5)
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER

    data_s9 = [
        ["ICCAD-1", "Baseline\nMC-Dropout\nDeep Ensemble", "100.0%\n83.3 ± 4.5%\n84.1 ± 17.1%", "0.0%\n16.7 ± 4.5%\n15.9 ± 17.1%", "84.6 ± 1.9%\n88.3 ± 3.6%\n87.8 ± 1.3%", "83.9 ± 11.7%\n95.7 ± 2.7%\n89.7 ± 9.2%", "16.1 ± 11.7%\n4.3 ± 2.7%\n10.3 ± 9.2%"],
        ["ICCAD-2", "Baseline\nMC-Dropout\nDeep Ensemble", "100.0%\n78.2 ± 3.7%\n87.1 ± 5.8%", "0.0%\n21.8 ± 3.7%\n12.9 ± 5.8%", "88.1 ± 5.4%\n92.6 ± 4.2%\n94.8 ± 3.6%", "86.6 ± 9.1%\n97.0 ± 2.1%\n96.7 ± 3.9%", "13.4 ± 9.1%\n3.0 ± 2.1%\n3.3 ± 3.9%"],
        ["ICCAD-3", "Baseline\nMC-Dropout\nDeep Ensemble", "100.0%\n69.3 ± 5.0%\n74.9 ± 2.2%", "0.0%\n30.7 ± 5.0%\n25.1 ± 2.2%", "92.4 ± 1.1%\n94.2 ± 1.9%\n95.9 ± 1.1%", "98.5 ± 0.3%\n99.4 ± 0.0%\n99.3 ± 0.1%", "1.5 ± 0.3%\n0.6 ± 0.0%\n0.7 ± 0.1%"],
        ["ICCAD-4", "Baseline\nMC-Dropout\nDeep Ensemble", "100.0%\n83.2 ± 2.2%\n89.6 ± 4.4%", "0.0%\n16.8 ± 2.2%\n10.4 ± 4.4%", "87.4 ± 1.2%\n88.4 ± 2.3%\n87.9 ± 0.5%", "91.7 ± 1.4%\n93.6 ± 0.5%\n93.3 ± 2.8%", "8.3 ± 1.4%\n6.4 ± 0.5%\n6.7 ± 2.8%"],
        ["ICCAD-5", "Baseline\nMC-Dropout\nDeep Ensemble", "100.0%\n88.5 ± 4.2%\n87.5 ± 9.5%", "0.0%\n11.5 ± 4.2%\n12.5 ± 9.5%", "83.6 ± 10.7%\n77.1 ± 17.7%\n91.6 ± 1.8%", "74.0 ± 21.9%\n60.5 ± 39.6%\n91.0 ± 6.5%", "26.0 ± 21.9%\n39.5 ± 39.6%\n9.0 ± 6.5%"],
        ["Macro Average", "Baseline\nMC-Dropout\nDeep Ensemble", "100.0%\n80.5 ± 7.5%\n84.7 ± 9.6%", "0.0%\n19.5 ± 7.5%\n15.3 ± 9.6%", "87.2 ± 5.6%\n88.1 ± 9.4%\n91.6 ± 3.9%", "87.0 ± 13.1%\n89.3 ± 21.2%\n94.0 ± 5.9%", "13.0 ± 13.1%\n10.7 ± 21.2%\n6.0 ± 5.9%"]
    ]
    for i, row in enumerate(data_s9):
        for j, val in enumerate(row):
            cell = t9.cell(i+1, j)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(0xEB, 0xF3, 0xFB) if i == 5 else (WHITE if i % 2 == 0 else RGBColor(0xF8, 0xFA, 0xFC))
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(8.5)
            p.font.bold = (i == 5)
            p.font.color.rgb = TEXT_DARK
            p.alignment = PP_ALIGN.CENTER

    # -------------------------------------------------------------
    # SLIDE 10: CONFUSION MATRIX RESCUE DYNAMICS
    # -------------------------------------------------------------
    s10 = make_content_slide("Baseline vs MC-Dropout Confusion Matrix Rescue")
    if os.path.exists("e:/aiml/results/figures/iccad1_baseline_cm.png"):
        s10.shapes.add_picture("e:/aiml/results/figures/iccad1_baseline_cm.png", Inches(0.8), Inches(1.8), Inches(3.6), Inches(4.5))
    if os.path.exists("e:/aiml/results/figures/iccad1_mc_dropout_accepted_cm.png"):
        s10.shapes.add_picture("e:/aiml/results/figures/iccad1_mc_dropout_accepted_cm.png", Inches(4.7), Inches(1.8), Inches(3.6), Inches(4.5))

    tb10 = s10.shapes.add_textbox(Inches(8.6), Inches(1.8), Inches(4.0), Inches(4.5))
    tf10 = tb10.text_frame
    tf10.word_wrap = True
    p = tf10.paragraphs[0]
    p.text = "How Uncertainty Saves Yield:"
    p.font.bold = True
    p.font.size = Pt(13)
    p.font.color.rgb = NAVY

    p = tf10.add_paragraph()
    p.text = "• Baseline Catastrophic Misses:\nForced binary classification misses 60 true hotspots (FN=60) on ICCAD-1 alone.\n\n• Uncertainty Rejection Rescue:\nMC-Dropout flags 59 ambiguous hotspots and 665 boundary NHS patterns as uncertain, referring them to lithography simulation.\n\n• Pristine Accepted Decisions:\nMissed hotspots among accepted layouts drop from 60 to 18 (a 70% reduction in missed defects!), while accepted balanced accuracy improves to 88.7%."
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_DARK
    p.space_before = Pt(8)

    # -------------------------------------------------------------
    # SLIDE 11: COVERAGE-RISK DYNAMICS
    # -------------------------------------------------------------
    s11 = make_content_slide("Coverage–Risk Curves & Operational Thresholding")
    if os.path.exists("e:/aiml/results/figures/iccad1_coverage_risk_curves.png"):
        s11.shapes.add_picture("e:/aiml/results/figures/iccad1_coverage_risk_curves.png", Inches(0.8), Inches(1.6), Inches(5.8), Inches(4.8))
    if os.path.exists("e:/aiml/results/figures/iccad1_referral_and_fnr_vs_threshold.png"):
        s11.shapes.add_picture("e:/aiml/results/figures/iccad1_referral_and_fnr_vs_threshold.png", Inches(6.9), Inches(1.6), Inches(5.8), Inches(4.8))

    # -------------------------------------------------------------
    # SLIDE 12: PROBABILITY CALIBRATION (ECE & RELIABILITY)
    # -------------------------------------------------------------
    s12 = make_content_slide("Probability Calibration Analysis (ECE & Reliability Diagrams)")
    if os.path.exists("e:/aiml/results/figures/iccad1_baseline_reliability.png"):
        s12.shapes.add_picture("e:/aiml/results/figures/iccad1_baseline_reliability.png", Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.0))
    if os.path.exists("e:/aiml/results/figures/iccad1_mc_dropout_reliability.png"):
        s12.shapes.add_picture("e:/aiml/results/figures/iccad1_mc_dropout_reliability.png", Inches(6.8), Inches(1.6), Inches(5.6), Inches(5.0))

    # -------------------------------------------------------------
    # SLIDE 13: QUANTIFIED GRAD-CAM EXPLAINABILITY
    # -------------------------------------------------------------
    s13 = make_content_slide("Quantified Explainability: Beyond Visual Heatmaps")
    t13_shape = s13.shapes.add_table(7, 5, Inches(0.8), Inches(1.6), Inches(6.6), Inches(3.0))
    t13 = t13_shape.table
    h13 = ["Benchmark", "Pointing Hit Rate", "Core Energy Ratio", "Grad-CAM Drop", "Faithfulness Gain"]
    for j, h in enumerate(h13):
        cell = t13.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        p = cell.text_frame.paragraphs[0]
        p.font.bold = True
        p.font.size = Pt(8.5)
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER

    data_s13 = [
        ["ICCAD-1", "65.7% ± 4.5%", "33.5% ± 2.3%", "+0.099", "+0.337 ± 0.171"],
        ["ICCAD-2", "66.7% ± 6.4%", "36.3% ± 1.6%", "+0.438", "+0.574 ± 0.090"],
        ["ICCAD-3", "68.7% ± 2.1%", "33.1% ± 0.6%", "+0.143", "+0.189 ± 0.059"],
        ["ICCAD-4", "59.7% ± 1.5%", "35.1% ± 1.3%", "+0.020", "+0.259 ± 0.030"],
        ["ICCAD-5", "73.2% ± 4.9%", "38.1% ± 2.0%", "+0.089", "+0.321 ± 0.195"],
        ["Macro Average", "66.8% ± 5.0%", "35.2% ± 2.1%", "+0.158", "+0.336 ± 0.148"]
    ]
    for i, r in enumerate(data_s13):
        for j, val in enumerate(r):
            cell = t13.cell(i+1, j)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(0xEB, 0xF3, 0xFB) if i == 5 else WHITE
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(8.5)
            p.font.bold = (i == 5)
            p.alignment = PP_ALIGN.CENTER

    if os.path.exists("e:/aiml/results/figures/iccad1_gradcam_example_1.png"):
        s13.shapes.add_picture("e:/aiml/results/figures/iccad1_gradcam_example_1.png", Inches(7.7), Inches(1.6), Inches(4.8), Inches(2.5))
    if os.path.exists("e:/aiml/results/figures/iccad2_gradcam_example_1.png"):
        s13.shapes.add_picture("e:/aiml/results/figures/iccad2_gradcam_example_1.png", Inches(7.7), Inches(4.3), Inches(4.8), Inches(2.5))

    # -------------------------------------------------------------
    # SLIDE 14: MULTI-SEED STATISTICAL SIGNIFICANCE
    # -------------------------------------------------------------
    s14 = make_content_slide("Multi-Seed Statistical Hypothesis Testing")
    t14_shape = s14.shapes.add_table(5, 7, Inches(0.8), Inches(1.6), Inches(11.7), Inches(3.6))
    t14 = t14_shape.table
    h14 = ["Evaluated Method", "Target Metric", "Baseline Mean", "Proposed Mean", "Delta (Mean)", "Paired t-test (p)", "Wilcoxon (p)"]
    for j, h in enumerate(h14):
        cell = t14.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        p = cell.text_frame.paragraphs[0]
        p.font.bold = True
        p.font.size = Pt(9)
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER

    data_s14 = [
        ["Deep Ensemble", "Balanced Accuracy", "87.22%", "91.59%", "+4.37%", "p = 0.0057 **", "p = 0.0004 ***"],
        ["Deep Ensemble", "Hotspot FNR (Miss Rate)", "13.05%", "6.01%", "-7.04%", "p = 0.0140 *", "p = 0.0006 ***"],
        ["Softmax Confidence", "Balanced Accuracy", "87.22%", "91.32%", "+4.10%", "p = 1.25e-7 ***", "p = 0.00006 ***"],
        ["Softmax Confidence", "Hotspot FNR (Miss Rate)", "13.05%", "9.70%", "-3.35%", "p = 0.0013 **", "p = 0.0006 ***"]
    ]
    for i, r in enumerate(data_s14):
        for j, val in enumerate(r):
            cell = t14.cell(i+1, j)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if i % 2 == 0 else RGBColor(0xF8, 0xFA, 0xFC)
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(9)
            p.font.color.rgb = TEXT_DARK
            p.alignment = PP_ALIGN.CENTER

    tb14 = s14.shapes.add_textbox(Inches(0.8), Inches(5.4), Inches(11.7), Inches(1.5))
    tf14 = tb14.text_frame
    tf14.word_wrap = True
    p = tf14.paragraphs[0]
    p.text = "Interpretation: Deep Ensemble delivers statistically significant gains in Balanced Accuracy (p=0.0057) and False-Negative Rate reduction (p=0.014) with large Cohen's d effect sizes (>0.72), proving genuine algorithmic improvement beyond random variation."
    p.font.size = Pt(11)
    p.font.italic = True
    p.font.color.rgb = TEXT_DARK

    # -------------------------------------------------------------
    # SLIDE 15: CONTROLLED ABLATION STUDY
    # -------------------------------------------------------------
    s15 = make_content_slide("Controlled Ablation Study on Monte Carlo Passes (T)")
    if os.path.exists("e:/aiml/results/figures/ablation_mc_passes.png"):
        s15.shapes.add_picture("e:/aiml/results/figures/ablation_mc_passes.png", Inches(0.8), Inches(1.6), Inches(7.5), Inches(5.0))

    tb15 = s15.shapes.add_textbox(Inches(8.6), Inches(1.6), Inches(4.0), Inches(5.0))
    tf15 = tb15.text_frame
    tf15.word_wrap = True
    p = tf15.paragraphs[0]
    p.text = "Bayesian Convergence:"
    p.font.bold = True
    p.font.size = Pt(13)
    p.font.color.rgb = NAVY

    abl_pts = [
        ("T = 1 (Deterministic)", "0.53 ms/img latency, but epistemic variance is null; cannot distinguish ambiguous patterns."),
        ("T = 3 to 5", "Variance rapidly rises to ~0.0230; accepted FNR drops sharply from 18.1% to 9.7%."),
        ("T = 15 (Proposed)", "Variance fully converges (0.0234); accepted FNR reaches 8.24% with 7.00 ms/img latency."),
        ("T = 20", "Negligible variance change (0.0232) while latency scales to 9.37 ms with zero further accuracy gain."),
        ("Conclusion", "T=15 is Pareto-optimal for CAD-oriented physical verification.")
    ]
    for h, d in abl_pts:
        p = tf15.add_paragraph()
        p.text = f"• {h}: "
        p.font.bold = True
        p.font.size = Pt(10.5)
        p.font.color.rgb = NAVY
        p.space_before = Pt(4)
        run = p.add_run()
        run.text = d
        run.font.bold = False
        run.font.color.rgb = TEXT_DARK

    # -------------------------------------------------------------
    # SLIDE 16: WORK ALLOCATION TABLE
    # -------------------------------------------------------------
    s16 = make_content_slide("Group G12 Individual Work Allocation")
    t16_shape = s16.shapes.add_table(4, 4, Inches(0.8), Inches(1.6), Inches(11.7), Inches(4.5))
    t16 = t16_shape.table
    h16 = ["Student Name", "Register No.", "Assigned Responsibilities", "Key Deliverables"]
    for j, h in enumerate(h16):
        cell = t16.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        p = cell.text_frame.paragraphs[0]
        p.font.bold = True
        p.font.size = Pt(10)
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER

    data_s16 = [
        ["Palash Ashutosh Duragkar", "24BVD1023", "Literature survey, ICCAD-12 class distribution analysis, baseline CNN implementation, and hyperparameter tuning.", "Sections I, II, III; Baseline model codebase; Hyperparameter grid search."],
        ["Varun U", "24BVD1024", "Phase 2 lead, uncertainty-aware framework architecture, MC-dropout and Deep Ensemble pipelines, three-way decision engine, calibration analysis (ECE), statistical significance testing, and paper integration.", "Sections IV, V, VI, VII; Complete uncertainty quantification and evaluation pipeline; Multi-seed statistical tests; Final IEEE report."],
        ["Subburayalu M", "24BVD1026", "Explainable AI (Grad-CAM) implementation, quantitative XAI metric design (pointing game, energy, faithfulness), presentation slides development, and repository README.", "Sections VIII, IX, X; Grad-CAM quantification script; Presentation slide deck; Codebase documentation."]
    ]
    for i, r in enumerate(data_s16):
        for j, val in enumerate(r):
            cell = t16.cell(i+1, j)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if i % 2 == 0 else RGBColor(0xF8, 0xFA, 0xFC)
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(9.5)
            p.font.color.rgb = TEXT_DARK
            if j < 2:
                p.font.bold = True
                p.alignment = PP_ALIGN.CENTER

    # -------------------------------------------------------------
    # SLIDE 17: CONCLUSION & SUMMARY
    # -------------------------------------------------------------
    s17 = prs.slides.add_slide(blank_layout)
    set_slide_background(s17, NAVY)

    tb17 = s17.shapes.add_textbox(Inches(1.0), Inches(1.2), Inches(11.3), Inches(5.2))
    tf17 = tb17.text_frame
    tf17.word_wrap = True

    p = tf17.paragraphs[0]
    p.text = "CONCLUSIONS & KEY TAKEAWAYS"
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = WHITE

    takeaways = [
        ("Principled Uncertainty-Aware DFM", "Replaced forced binary decisions with an operational three-way classification pipeline, cutting accepted hotspot false negatives by 54%."),
        ("Rigorously Validated Across ICCAD 1–5", "Evaluated independently on all five official benchmarks across three random seeds with paired t-test and Wilcoxon significance."),
        ("Quantified Explainability", "Demonstrated a 66.8% pointing game hit rate in defect cores and +33.6% faithfulness gain, providing actionable coordinates for DRC engineers."),
        ("Reproducible & Release-Ready", "Complete codebase, pretrained checkpoints, CSV metric logs, high-resolution figures, and IEEE conference paper packaged in repository.")
    ]
    for h, d in takeaways:
        p = tf17.add_paragraph()
        p.text = f"✓  {h}: "
        p.font.bold = True
        p.font.size = Pt(13)
        p.font.color.rgb = BLUE_ACCENT
        p.space_before = Pt(10)
        run = p.add_run()
        run.text = d
        run.font.bold = False
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(0xE2, 0xE8, 0xF0)

    p_end = tf17.add_paragraph()
    p_end.text = "\nThank you! Questions & Discussion."
    p_end.font.size = Pt(16)
    p_end.font.italic = True
    p_end.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)
    p_end.space_before = Pt(14)

    out_file = Path("e:/aiml/slides/G12_Uncertainty_Aware_Hotspot_Detection_Presentation.pptx")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_file))
    print(f"Presentation slides successfully created at: {out_file.resolve()}")

if __name__ == '__main__':
    build_presentation()
