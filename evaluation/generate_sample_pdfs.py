import os
import fitz  # PyMuPDF

def create_pdf(filename: str, pages_data: list, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    
    doc = fitz.open()
    
    for page_info in pages_data:
        # Create standard A4 page (595 x 842 points)
        page = doc.new_page(width=595, height=842)
        
        # Header banner
        page.draw_rect(fitz.Rect(40, 40, 555, 80), color=(0.1, 0.2, 0.4), fill=(0.92, 0.95, 0.98))
        page.insert_text(fitz.Point(50, 65), page_info["header"], fontsize=14, fontname="helv", color=(0.1, 0.2, 0.5))
        
        # Section Title
        page.insert_text(fitz.Point(40, 115), page_info["title"], fontsize=18, fontname="hebo", color=(0.05, 0.1, 0.2))
        
        # Content paragraphs
        y_cursor = 145
        for paragraph in page_info["paragraphs"]:
            rect = fitz.Rect(40, y_cursor, 555, y_cursor + 120)
            page.insert_textbox(rect, paragraph, fontsize=10.5, fontname="helv", color=(0.15, 0.15, 0.2))
            y_cursor += 110

        # Footer
        footer_text = f"DocuMind Research Benchmark Dataset | {filename} | Page {page_info['page_num']}"
        page.insert_text(fitz.Point(40, 810), footer_text, fontsize=8.5, fontname="helv", color=(0.5, 0.5, 0.5))
        page.draw_line(fitz.Point(40, 795), fitz.Point(555, 795), color=(0.8, 0.8, 0.8))

    doc.save(filepath)
    doc.close()
    return filepath

def generate_all_samples(output_dir: str):
    samples = {}
    
    # 1. Quantum Computing
    qc_pages = [
        {
            "page_num": 1,
            "header": "Quantum Computing Advances - Annual Review 2026",
            "title": "1. Superconducting Qubits & Processor Architecture",
            "paragraphs": [
                "The 2026 Hyperion-X quantum processor demonstrates a landmark achievement in superconducting qubit architectures, scaling to 1,024 physical qubits with average coherence times (T1 and T2) surpassing 320 microseconds.",
                "Cross-talk mitigation is achieved through 3D coaxial wiring and tunable couplers, yielding single-qubit gate fidelities of 99.94% and two-qubit CZ gate fidelities of 99.65%. This architecture provides the necessary gate depth to execute deep quantum circuits prior to decoherence.",
                "Thermal dissipation remains under 12 milliwatts at the 15 millikelvin stage of dilution refrigerators, validating scalable cryogenic modular interconnects."
            ]
        },
        {
            "page_num": 2,
            "header": "Quantum Computing Advances - Annual Review 2026",
            "title": "2. Surface Code Error Correction Benchmarks",
            "paragraphs": [
                "Fault-tolerant quantum computing requires continuous syndrome measurement. Implementing a distance-7 surface code on the Hyperion-X architecture demonstrated a suppressed logical error rate of 1.2 x 10^-6 per syndrome cycle.",
                "The physical error threshold remained well below the critical 0.75% limit. Real-time neural decoder chips integrated at the 4 Kelvin stage decoded syndromes in under 450 nanoseconds, outperforming classical FPGA pipelines by 4.2x.",
                "This marks the first empirical proof of exponential error suppression with increasing code distance across superconducting physical lattices."
            ]
        },
        {
            "page_num": 3,
            "header": "Quantum Computing Advances - Annual Review 2026",
            "title": "3. Quantum Advantage & Computational Chemistry",
            "paragraphs": [
                "Simulations of the FeMo-cofactor nitrogenase active site were completed in 184 seconds on the 1,024-qubit system. Classical tensor-network approximations on the Frontier supercomputer required 4,200 years of equivalent compute.",
                "Energy ground states were determined to within 0.8 kcal/mol chemical accuracy, unlocking novel catalyst pathways for low-temperature synthetic ammonia production.",
                "Future iterations aim to deploy 4,096 physical qubits with photonic quantum repeaters for distributed cluster execution by Q4 2027."
            ]
        }
    ]
    samples["Quantum_Computing_2026_Advancements.pdf"] = create_pdf(
        "Quantum_Computing_2026_Advancements.pdf", qc_pages, output_dir
    )

    # 2. Renewable Energy
    energy_pages = [
        {
            "page_num": 1,
            "header": "Global Clean Tech Energy Briefing 2026",
            "title": "1. Solid-State Lithium-Sulfur Batteries",
            "paragraphs": [
                "Solid-state Lithium-Sulfur (Li-S) battery architectures achieved gravimetric energy densities of 650 Wh/kg and volumetric densities of 980 Wh/L in standardized pouch-cell testing.",
                "Polysulfide shuttle suppression is maintained via a 15-micrometer lithium-conducting ceramic-polymer composite electrolyte. The cells exhibit over 85% capacity retention after 1,500 full charge-discharge cycles at 1C rate.",
                "Manufacturing economics indicate a projected bill-of-materials cost of $48 per kWh at 50 GWh gigafactory scale, significantly displacing traditional nickel-manganese-cobalt chemistries."
            ]
        },
        {
            "page_num": 2,
            "header": "Global Clean Tech Energy Briefing 2026",
            "title": "2. Utility-Scale Vanadium Redox Flow Systems",
            "paragraphs": [
                "Grid-scale multi-hour energy storage deployments reached 100 MW / 800 MWh capacity in high-desert solar installations. Vanadium redox flow batteries (VRFB) demonstrated an overall round-trip AC-to-AC efficiency of 82.4%.",
                "Electrolyte degradation remained virtually zero over a continuous 20-year simulated duty cycle, since active vanadium species exist entirely in liquid phase with no phase transitions.",
                "Automated thermal and state-of-charge rebalancing algorithms reduced parasitic pumping losses by 18.5%, increasing seasonal plant availability to 99.8%."
            ]
        },
        {
            "page_num": 3,
            "header": "Global Clean Tech Energy Briefing 2026",
            "title": "3. Levelized Cost of Storage (LCOS) Economics",
            "paragraphs": [
                "The Levelized Cost of Storage (LCOS) for 8-to-12 hour grid storage dropped to $68 per MWh in 2026, representing a 45% reduction compared to 2022 benchmarks.",
                "Federal clean energy tax credits and automated cathode recycling loops are projected to compress LCOS further to $42 per MWh by 2030.",
                "Grid interconnection queue delays remain the primary non-technical bottleneck, averaging 22 months across regional transmission organizations."
            ]
        }
    ]
    samples["Renewable_Energy_Storage_Breakthroughs.pdf"] = create_pdf(
        "Renewable_Energy_Storage_Breakthroughs.pdf", energy_pages, output_dir
    )

    # 3. Medical AI Diagnostics
    med_pages = [
        {
            "page_num": 1,
            "header": "Clinical Oncology & AI Diagnostics Report",
            "title": "1. Deep Learning Mammography Screening",
            "paragraphs": [
                "Clinical multi-center trials evaluating the OmniVision-Med transformer model across 45,000 screening mammograms achieved a diagnostic sensitivity of 98.4% and a specificity of 96.1%.",
                "The AI assistant successfully detected occult microcalcifications and invasive ductal carcinomas up to 14 months earlier than conventional radiologist double-reading protocols.",
                "False-positive recall rates decreased by 34.2%, reducing patient anxiety and unnecessary biopsy procedures by an estimated $140 million across participating hospital networks."
            ]
        },
        {
            "page_num": 2,
            "header": "Clinical Oncology & AI Diagnostics Report",
            "title": "2. Multimodal Whole-Slide Histopathology",
            "paragraphs": [
                "Integrating gigapixel whole-slide imaging with patient genomic variant profiles yielded an AUC of 0.978 for predicting immunotherapy response in non-small cell lung cancer (NSCLC).",
                "Self-supervised vision foundation models trained on 2.4 million tissue slides identified novel spatial tumor-infiltrating lymphocyte (TIL) architectural patterns correlated with 5-year survival.",
                "Inference latency on edge hospital workstation clusters averaged 3.2 seconds per slide, meeting real-time intraoperative frozen section workflow constraints."
            ]
        },
        {
            "page_num": 3,
            "header": "Clinical Oncology & AI Diagnostics Report",
            "title": "3. Regulatory Clearance & Ethical Governance",
            "paragraphs": [
                "The US FDA granted 510(k) clearance for OmniVision-Med in Q3 2025 as a Class II Computer-Aided Diagnostic Device across 14 radiological indications.",
                "Model explainability is guaranteed via integrated gradient heatmaps and confidence calibration curves verified against expert pathologist consensus panels.",
                "Demographic parity audits confirmed equal diagnostic performance across diverse ethnic and age cohorts with variance under 1.2%."
            ]
        }
    ]
    samples["AI_in_Medical_Diagnostics_Report.pdf"] = create_pdf(
        "AI_in_Medical_Diagnostics_Report.pdf", med_pages, output_dir
    )

    return samples

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data", "sample_docs")
    created = generate_all_samples(out_dir)
    print(f"Generated {len(created)} sample PDFs in {out_dir}:")
    for name, path in created.items():
        print(f" - {name} ({os.path.getsize(path)} bytes)")
