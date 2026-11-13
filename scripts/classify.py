#!/usr/bin/env python3
"""classify.py — assign each entry's Function (mach:subcategory) deterministically.

Type (mach:category) comes from the folder. Function is assigned here by ordered,
published rules over the entry's harvested keywords and implemented standards:
a rule fires when the keywords intersect its triggers, or supportsSpec names the
standard. If no rule fires, a small curator table supplies the value (entries the
rules could not decide). Every assignment records how it happened via
`mach:subcategoryBy`:  "rule:keyword" | "rule:spec" | "curator".

The allowed Functions per category are defined in data/taxonomy/categories.yaml
and enforced here, so classification can never drift to a free-text value.

Usage:
    python scripts/classify.py            # apply to all entries
    python scripts/classify.py --check    # report only, write nothing (CI)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ENTRIES_DIR = Path("entries")
TAXONOMY = Path("data/taxonomy/categories.yaml")

# ── Ordered rules: category → [(function, {keyword triggers}, spec substring or None)] ──
RULES: dict[str, list[tuple[str, set[str], str | None]]] = {
    "software": [
        ("medical-imaging", {"dicom", "medical-imaging", "radiology", "whole-slide-imaging",
                             "digital-pathology", "pathology", "computational-pathology",
                             "neuroimaging", "mri", "ct", "pacs", "image-computing",
                             "microscopy", "bioimage-analysis", "image-guided-therapy",
                             "surgical-navigation", "pet", "spect", "nuclear-medicine",
                             "tomographic-reconstruction", "image-reconstruction"}, "dicom"),
        ("interoperability", {"fhir", "interoperability", "hl7", "integration-engine", "openehr"}, "fhir"),
        ("clinical-system", {"ehr", "emr", "his", "clinical-decision-support", "decision-support",
                             "hospital-information-system", "tumor-board"}, None),
        ("privacy-deid", {"de-identification", "deidentification", "pii", "privacy", "redaction",
                          "anonymisation", "anonymization"}, None),
        ("pharmacometrics", {"pharmacometrics", "pk-pd", "pharmacokinetics", "pharmacodynamics", "nlme"}, None),
        ("federated-analytics", {"federated-learning", "federated-analysis"}, None),
        ("bioinformatics-pipeline", {"pipeline", "bioinformatics", "variant-calling", "genomics",
                                     "signal-processing", "ecg", "workflow", "cheminformatics",
                                     "molecular-descriptors", "computational-chemistry"}, None),
        ("clinical-nlp", {"clinical-nlp", "named-entity-recognition", "ner", "nlp"}, None),
        ("research-platform", {"research-platform", "data-platform", "biobank", "data-management"}, None),
        ("mhealth", {"mhealth", "mobile-health", "wearable", "digital-health", "cgm",
                     "continuous-glucose-monitoring", "diabetes", "automated-insulin-delivery",
                     "artificial-pancreas", "closed-loop", "remote-monitoring"}, None),
    ],
    "ai-ml-models": [
        ("imaging-model", {"medical-imaging", "radiology", "pathology", "segmentation",
                           "whole-slide-imaging", "digital-pathology", "neuroimaging"}, None),
        ("genomics-model", {"genomics", "protein", "protein-language-model", "omics", "sequence"}, None),
        ("clinical-nlp", {"nlp", "ner", "clinical-nlp", "text"}, None),
        ("agent-model", {"llm-agent", "tool-use"}, None),
        ("foundation-model", {"foundation-model", "llm", "large-language-model", "pretrained",
                              "vision-language-model"}, None),
    ],
    "datasets": [
        ("benchmark", {"benchmark", "clinical-benchmark", "evaluation", "eval", "leaderboard",
                       "llm-evaluation"}, None),
        ("imaging-dataset", {"medical-imaging", "radiology", "pathology", "whole-slide-imaging",
                             "digital-pathology", "histopathology"}, None),
        ("clinical-dataset", {"ehr", "clinical", "icu", "patient", "cohort", "ecg", "eeg", "waveform"}, None),
    ],
    "data-sources": [
        ("terminology", {"terminology", "ontology", "vocabulary", "snomed", "loinc", "icd"}, None),
        ("surveillance-feed", {"surveillance", "outbreak", "outbreak-surveillance", "adverse-event",
                               "pharmacovigilance", "alert", "infectious-disease", "epidemiology"}, None),
        ("research-database", {"biomedical-literature", "medline", "database", "bioactivity",
                               "citations", "literature"}, None),
        ("registry", {"registry", "trial", "clinical-trials", "clinicaltrials", "coverage-determination",
                      "individual-patient-data"}, None),
        ("open-data-portal", {"open-data", "portal", "api", "rest-api"}, None),
    ],
    "specs": [
        ("research-data-standard", {"cdisc", "analysis-datasets", "data-tabulation", "sdtm", "adam"}, None),
        ("interoperability-standard", {"fhir", "hl7", "dicom", "openehr", "interoperability", "ips"}, None),
        ("terminology", {"terminology", "ontology", "snomed", "loinc"}, None),
        ("quality-standard", {"iso", "quality", "conformance"}, None),
        ("data-governance", {"governance", "consent", "license", "odrl", "dcat"}, None),
    ],
    "catalogs": [
        ("catalog", set(), None),  # every catalogs entry is a catalog
    ],
    "ai-tooling": [],  # already uses a clean controlled vocab — keep the authored value
}

# Curator decisions for entries the rules cannot confidently classify.
CURATOR: dict[str, str] = {
    "synapse": "research-database",
    "pubmed": "research-database",
    "chembl": "research-database",
    "vivli": "registry",
    "cms-coverage": "registry",
    "uai-nexus-medvlm-medgrpo": "foundation-model",
    "tuh-eeg": "clinical-dataset",
    "nlmixr2": "pharmacometrics",
    "openonco": "clinical-system",
    "veil": "privacy-deid",
    "no-show": "clinical-system",  # deployed hospital-operations prediction tool
}


def load_allowed() -> dict[str, set[str]]:
    tax = yaml.safe_load(TAXONOMY.read_text(encoding="utf-8"))
    out = {}
    for c in tax["categories"]:
        out[c["id"]] = {fn["id"] for fn in c.get("functions", [])}
    return out


def classify(entry: dict) -> tuple[str | None, str]:
    """Return (function, how). how ∈ rule:keyword|rule:spec|catalog|existing|curator|unclassified."""
    cat = entry.get("mach:category")
    ident = entry.get("identifier", "")

    if cat == "ai-tooling":
        return entry.get("mach:subcategory"), "existing"

    kws = {k.lower() for k in (entry.get("keywords") or [])}
    specs = " ".join(entry.get("mach:supportsSpec") or []).lower()

    for func, triggers, spec_sub in RULES.get(cat, []):
        if triggers and (kws & triggers):
            return func, "rule:keyword"
        if spec_sub and spec_sub in specs:
            return func, "rule:spec"
        if cat == "catalogs":
            return func, "catalog"

    if ident in CURATOR:
        return CURATOR[ident], "curator"
    return None, "unclassified"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    allowed = load_allowed()
    changed = 0
    unclassified = []
    bad_value = []
    counts = {"rule:keyword": 0, "rule:spec": 0, "catalog": 0, "curator": 0, "existing": 0}

    for path in sorted(ENTRIES_DIR.rglob("*.jsonld")):
        if path.name.startswith("_"):
            continue
        d = json.loads(path.read_text(encoding="utf-8"))
        func, how = classify(d)
        cat = d.get("mach:category")

        if func is None:
            unclassified.append(d.get("identifier"))
            continue
        if cat in allowed and func not in allowed[cat]:
            bad_value.append(f"{d.get('identifier')}: {cat}/{func} not in vocab")
            continue

        counts[how] = counts.get(how, 0) + 1
        if how == "existing":
            continue  # don't rewrite ai-tooling's authored value / lineage

        if d.get("mach:subcategory") != func or d.get("mach:subcategoryBy") != how:
            if not args.check:
                d["mach:subcategory"] = func
                d["mach:subcategoryBy"] = how
                path.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            changed += 1

    print(f"classified: {counts} | changed: {changed}")
    if unclassified:
        print(f"UNCLASSIFIED ({len(unclassified)}): {', '.join(unclassified)}")
    if bad_value:
        print("INVALID VALUES:")
        for b in bad_value:
            print(f"  {b}")

    if args.check and (unclassified or bad_value):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
