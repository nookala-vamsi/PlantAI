#!/usr/bin/env python3
"""
=============================================================================
 GIN-based Natural Drug Compound Classification — Kaggle Training Notebook
=============================================================================

 PURPOSE:
   Train a Graph Isomorphism Network (GIN) to classify natural compounds
   into three biological origin classes: Plant, Fungal, or Bacterial.

 DATASET:
   COCONUT database (COCONUT_DB.sdf) — ~400K+ natural compounds.
   After filtering for valid taxonomy and DOI, expect ~60K compounds.

 PLATFORM:
   Kaggle with GPU T4 x2 accelerator.

 HOW TO USE ON KAGGLE:
   1. Upload COCONUT_DB.sdf as a Kaggle dataset
   2. Create a new Kaggle notebook, select GPU T4 x2 accelerator
   3. Copy this entire file into notebook cells (each "# %%  CELL N" is one cell)
   4. Run all cells sequentially
   5. Download the saved model artifact from the output

=============================================================================
"""

# %% CELL 1 — Environment Setup & Library Installation
# =====================================================
# Install required libraries not pre-installed on Kaggle.
# PyTorch is pre-installed on Kaggle GPU instances.
# We need: PyG (torch_geometric), RDKit, and their compiled extensions.

# ── Step 1: Install RDKit ──
# RDKit is NOT pre-installed on Kaggle. Install via pip.
!pip install rdkit

# ── Step 2: Install PyTorch Geometric ──
!pip install torch_geometric

# ── Step 3: Install PyG compiled extensions ──
# These MUST match the exact PyTorch + CUDA version on Kaggle.
# Kaggle has PyTorch 2.10.0+cu128 — the wheel URL below is locked to that.
!pip install pyg_lib torch_scatter torch_sparse -f https://data.pyg.org/whl/torch-2.10.0+cu128.html

# ── Verify installation ──
import torch
import rdkit
from torch_geometric.data import Data
import torch_scatter

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU name: {torch.cuda.get_device_name(0)}")
print(f"RDKit version: {rdkit.__version__}")
print("PyG and dependencies: all good ✅")


# %% CELL 2 — Import All Libraries
# ==================================

import os
import gc
import time
import warnings
import json
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for Kaggle
import seaborn as sns

from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit import RDLogger

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau

import torch_geometric
from torch_geometric.data import Data, InMemoryDataset
from torch_geometric.loader import DataLoader  # Moved in PyG 2.7.0+
from torch_geometric.nn import GINConv, GINEConv, global_add_pool, global_mean_pool
from torch_geometric.nn import BatchNorm as PyGBatchNorm

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    balanced_accuracy_score, matthews_corrcoef, f1_score,
    precision_recall_fscore_support, confusion_matrix,
    classification_report
)

# Suppress RDKit warnings for cleaner output
RDLogger.logger().setLevel(RDLogger.ERROR)
warnings.filterwarnings('ignore')

print(f"PyTorch: {torch.__version__}")
print(f"PyTorch Geometric: {torch_geometric.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")


# %% CELL 3 — Parse COCONUT SDF File & Extract Data
# ====================================================
# The COCONUT_DB.sdf contains ~400K+ natural product records.
# Each record has properties: SMILES, textTaxa, citationDOI, etc.
# We need to:
#   1. Read all records from the SDF
#   2. Extract SMILES and taxonomic annotations (textTaxa)
#   3. Filter for valid taxonomy (not "[notax]")
#   4. Map taxonomic annotations to our 3 classes: Plant, Fungal, Bacterial

print("=" * 70)
print("PHASE 1: Parsing COCONUT SDF Database")
print("=" * 70)

# ── IMPORTANT: Update this path to your Kaggle dataset location ──
# On Kaggle, uploaded datasets are at: /kaggle/input/<dataset-name>/
# Update the path below to match your upload name.
SDF_PATH = "/kaggle/input/coconut-db/COCONUT_DB.sdf"

# Fallback paths (for local testing)
if not os.path.exists(SDF_PATH):
    SDF_PATH = "/kaggle/input/coconut-database/COCONUT_DB.sdf"
if not os.path.exists(SDF_PATH):
    SDF_PATH = "COCONUT_DB.sdf"  # Same directory fallback

print(f"Looking for SDF at: {SDF_PATH}")
assert os.path.exists(SDF_PATH), (
    f"❌ COCONUT_DB.sdf not found at {SDF_PATH}!\n"
    "Please upload COCONUT_DB.sdf as a Kaggle dataset and update SDF_PATH above.\n"
    "Common path: /kaggle/input/<your-dataset-name>/COCONUT_DB.sdf"
)
print(f"✅ Found SDF file: {os.path.getsize(SDF_PATH) / 1e9:.2f} GB")

# ── Parse SDF using RDKit's ForwardSDMolSupplier (streaming, memory efficient) ──
print("\nParsing SDF file (this takes 5-15 minutes for ~400K records)...")

records = []
failed_parse = 0
no_smiles = 0
start_time = time.time()

with open(SDF_PATH, 'rb') as f:
    supplier = Chem.ForwardSDMolSupplier(f, sanitize=True, removeHs=True)

    for idx, mol in enumerate(supplier):
        if mol is None:
            failed_parse += 1
            continue

        # Extract properties
        try:
            smiles = mol.GetProp('SMILES') if mol.HasProp('SMILES') else Chem.MolToSmiles(mol)
            text_taxa = mol.GetProp('textTaxa') if mol.HasProp('textTaxa') else '[notax]'
            citation_doi = mol.GetProp('citationDOI') if mol.HasProp('citationDOI') else '[]'
            coconut_id = mol.GetProp('coconut_id') if mol.HasProp('coconut_id') else f'UNK_{idx}'
        except Exception:
            failed_parse += 1
            continue

        if not smiles or smiles.strip() == '':
            no_smiles += 1
            continue

        records.append({
            'coconut_id': coconut_id,
            'smiles': smiles.strip(),
            'textTaxa': text_taxa.strip(),
            'citationDOI': citation_doi.strip(),
        })

        # Progress reporting every 50K molecules
        if (idx + 1) % 50000 == 0:
            elapsed = time.time() - start_time
            print(f"  Processed {idx + 1:,} molecules... ({elapsed:.0f}s elapsed)")

elapsed = time.time() - start_time
print(f"\n✅ SDF parsing complete in {elapsed:.0f}s")
print(f"  Total molecules parsed: {len(records):,}")
print(f"  Failed to parse: {failed_parse:,}")
print(f"  No SMILES: {no_smiles:,}")

df_raw = pd.DataFrame(records)
del records  # Free memory
gc.collect()
print(f"  DataFrame shape: {df_raw.shape}")
print(f"\nSample textTaxa values:")
print(df_raw['textTaxa'].value_counts().head(20))


# %% CELL 4 — Clean & Filter Dataset: Assign Plant/Fungal/Bacterial Labels
# ===========================================================================
# The textTaxa field contains taxonomic annotations like:
#   "[notax]" — no taxonomy info (skip these)
#   "[Plantae]", "[plants]", "[Viridiplantae]" — Plant origin
#   "[Fungi]", "[Ascomycota]", "[Basidiomycota]" — Fungal origin
#   "[Bacteria]", "[Actinobacteria]", "[Proteobacteria]" — Bacterial origin
#
# We map these to our 3 classes using comprehensive keyword matching.

print("=" * 70)
print("PHASE 2: Cleaning & Labeling Dataset")
print("=" * 70)

# Step 1: Remove entries with no taxonomy
print(f"\nTotal records before filtering: {len(df_raw):,}")
df_filtered = df_raw[df_raw['textTaxa'] != '[notax]'].copy()
df_filtered = df_filtered[df_filtered['textTaxa'] != 'notax'].copy()
df_filtered = df_filtered[df_filtered['textTaxa'] != '[]'].copy()
df_filtered = df_filtered[~df_filtered['textTaxa'].str.strip().isin(['', 'nan', 'None'])].copy()
print(f"After removing [notax]/empty: {len(df_filtered):,}")

# Step 2: Filter for entries with a DOI (verified publication)
# citationDOI field: "[]" means no DOI, otherwise contains DOI strings
df_with_doi = df_filtered[
    (df_filtered['citationDOI'] != '[]') &
    (df_filtered['citationDOI'] != '') &
    (df_filtered['citationDOI'].str.len() > 4)
].copy()
print(f"After requiring DOI: {len(df_with_doi):,}")

# Step 3: Classify textTaxa into Plant / Fungal / Bacterial
# Use keyword-based classification from the taxonomic text

# ── Comprehensive taxonomy keyword mapping ──
# These keywords cover kingdom-level, phylum-level, and common taxa names
PLANT_KEYWORDS = [
    'plantae', 'plant', 'viridiplantae', 'streptophyta', 'embryophyta',
    'tracheophyta', 'magnoliopsida', 'liliopsida', 'pinopsida',
    'eudicots', 'monocots', 'asteraceae', 'fabaceae', 'lamiaceae',
    'poaceae', 'rosaceae', 'solanaceae', 'brassicaceae', 'apiaceae',
    'rutaceae', 'euphorbiaceae', 'rubiaceae', 'lauraceae', 'moraceae',
    'leguminosae', 'compositae', 'umbelliferae', 'cruciferae', 'gramineae',
    'labiatae', 'myrtaceae', 'orchidaceae', 'malvaceae', 'cucurbitaceae',
    'convolvulaceae', 'apocynaceae', 'araceae', 'ranunculaceae',
    'zingiberaceae', 'piperaceae', 'annonaceae', 'menispermaceae',
    'meliaceae', 'sapindaceae', 'thymelaeaceae', 'clusiaceae',
    'guttiferae', 'theaceae', 'ericaceae', 'oleaceae', 'verbenaceae',
    'scrophulariaceae', 'acanthaceae', 'boraginaceae', 'gentianaceae',
    'polygonaceae', 'chenopodiaceae', 'amaranthaceae', 'caryophyllaceae',
    'papaveraceae', 'berberidaceae', 'magnoliaceae', 'aristolochiaceae',
    'piperales', 'magnoliales', 'laurales', 'gymnosperm', 'angiosperm',
    'pteridophyta', 'bryophyta', 'marchantiophyta', 'anthocerotophyta',
    'cycadopsida', 'ginkgopsida', 'gnetopsida', 'lycopodiopsida',
    'polypodiopsida', 'equisetopsida', 'psilotopsida', 'marattiopsida',
    'spermatophyta', 'chlorophyta', 'charophyta',
]

FUNGAL_KEYWORDS = [
    'fungi', 'fungal', 'mycota', 'ascomycota', 'basidiomycota',
    'zygomycota', 'chytridiomycota', 'glomeromycota', 'mucoromycota',
    'eurotiomycetes', 'sordariomycetes', 'dothideomycetes',
    'lecanoromycetes', 'leotiomycetes', 'pezizomycetes',
    'agaricomycetes', 'tremellomycetes', 'ustilaginomycetes',
    'saccharomycetes', 'schizosaccharomycetes', 'taphrinomycetes',
    'aspergillus', 'penicillium', 'fusarium', 'trichoderma',
    'cladosporium', 'alternaria', 'botrytis', 'candida',
    'saccharomyces', 'cryptococcus', 'agaricus', 'pleurotus',
    'ganoderma', 'trametes', 'phoma', 'colletotrichum',
    'endophytic fung', 'mycorrhiz', 'lichen', 'yeast',
    'dikarya', 'opisthokonta',
]

BACTERIAL_KEYWORDS = [
    'bacteria', 'bacterial', 'proteobacteria', 'actinobacteria',
    'firmicutes', 'bacteroidetes', 'cyanobacteria', 'tenericutes',
    'spirochaetes', 'chlamydiae', 'chloroflexi', 'deinococcus',
    'planctomycetes', 'verrucomicrobia', 'acidobacteria',
    'alphaproteobacteria', 'betaproteobacteria', 'gammaproteobacteria',
    'deltaproteobacteria', 'epsilonproteobacteria',
    'streptomyces', 'bacillus', 'pseudomonas', 'escherichia',
    'staphylococcus', 'mycobacterium', 'clostridium', 'lactobacillus',
    'rhizobium', 'agrobacterium', 'burkholderia', 'xanthomonas',
    'erwinia', 'serratia', 'vibrio', 'enterobacter', 'klebsiella',
    'nocardia', 'micromonospora', 'amycolatopsis', 'salinispora',
    'actinomycet', 'myxobacter', 'cyanobacter',
    'prokaryot', 'archaea',
]


def classify_taxa(text_taxa):
    """
    Classify a textTaxa string into Plant, Fungal, or Bacterial.
    Returns the label string or None if unclassifiable.
    """
    text_lower = text_taxa.lower()

    # Score each category by keyword matches
    plant_score = sum(1 for kw in PLANT_KEYWORDS if kw in text_lower)
    fungal_score = sum(1 for kw in FUNGAL_KEYWORDS if kw in text_lower)
    bacterial_score = sum(1 for kw in BACTERIAL_KEYWORDS if kw in text_lower)

    max_score = max(plant_score, fungal_score, bacterial_score)

    if max_score == 0:
        return None  # No matching keywords — can't classify

    # Assign to the category with the highest score
    if plant_score == max_score:
        return 'Plant'
    elif fungal_score == max_score:
        return 'Fungal'
    else:
        return 'Bacterial'


# Apply classification
print("\nClassifying taxonomic annotations...")
df_with_doi['origin_label'] = df_with_doi['textTaxa'].apply(classify_taxa)

# Remove unclassifiable entries
df_labeled = df_with_doi[df_with_doi['origin_label'].notna()].copy()
print(f"After taxonomic classification: {len(df_labeled):,}")
unclassified_count = len(df_with_doi) - len(df_labeled)
print(f"  Unclassifiable (removed): {unclassified_count:,}")

# Step 4: Validate all SMILES with RDKit
print("\nValidating SMILES strings with RDKit...")
valid_mask = []
for smi in df_labeled['smiles']:
    mol = Chem.MolFromSmiles(smi)
    valid_mask.append(mol is not None)

df_labeled = df_labeled[valid_mask].copy()
invalid_smiles = sum(1 for v in valid_mask if not v)
print(f"Invalid SMILES removed: {invalid_smiles:,}")
print(f"Final cleaned dataset: {len(df_labeled):,}")

# Step 5: Remove duplicates by canonical SMILES
print("\nRemoving duplicate SMILES...")
df_labeled['canonical_smiles'] = df_labeled['smiles'].apply(
    lambda s: Chem.MolToSmiles(Chem.MolFromSmiles(s), isomericSmiles=False)
)
before_dedup = len(df_labeled)
df_labeled = df_labeled.drop_duplicates(subset='canonical_smiles', keep='first').copy()
print(f"Duplicates removed: {before_dedup - len(df_labeled):,}")
print(f"Final unique compounds: {len(df_labeled):,}")

# Step 6: Create numeric labels
label_map = {'Plant': 0, 'Fungal': 1, 'Bacterial': 2}
label_names = {0: 'Plant', 1: 'Fungal', 2: 'Bacterial'}
df_labeled['label'] = df_labeled['origin_label'].map(label_map)

# Print final class distribution
print("\n" + "=" * 50)
print("FINAL DATASET CLASS DISTRIBUTION")
print("=" * 50)
class_counts = df_labeled['origin_label'].value_counts()
for cls_name in ['Plant', 'Fungal', 'Bacterial']:
    count = class_counts.get(cls_name, 0)
    pct = count / len(df_labeled) * 100
    print(f"  {cls_name:12s}: {count:>7,} ({pct:5.1f}%)")
print(f"  {'TOTAL':12s}: {len(df_labeled):>7,}")

# Save cleaned CSV for future use
CLEANED_CSV_PATH = "coconut_cleaned.csv"
df_labeled[['coconut_id', 'smiles', 'canonical_smiles', 'origin_label', 'label']].to_csv(
    CLEANED_CSV_PATH, index=False
)
print(f"\n✅ Cleaned dataset saved to: {CLEANED_CSV_PATH}")

# Free memory
del df_raw, df_filtered, df_with_doi
gc.collect()


# %% CELL 5 — Molecule-to-Graph Conversion (Featurization)
# ===========================================================
# Convert each SMILES string into a PyTorch Geometric Data object:
#   - Node features: atom properties (element, degree, Hs, charge, ring, aromatic, hybridization)
#   - Edge index: bond connectivity (bidirectional)
#   - Edge features: bond properties (type, ring, conjugated, stereo)
#   - Graph label: origin class (0=Plant, 1=Fungal, 2=Bacterial)

print("\n" + "=" * 70)
print("PHASE 3: Molecule-to-Graph Conversion")
print("=" * 70)

# ── Atom Feature Encoding ──
# One-hot encodings for categorical atom properties

ATOM_FEATURES = {
    'element': [
        'C', 'N', 'O', 'S', 'F', 'Cl', 'Br', 'I', 'P', 'Si',
        'B', 'Se', 'Te', 'As', 'Ge', 'Sn', 'Sb', 'Bi',
        'Na', 'K', 'Ca', 'Mg', 'Fe', 'Zn', 'Cu', 'Mn',
        'Co', 'Ni', 'Mo', 'Cr', 'V', 'Ti', 'Al', 'Ga',
        'Li', 'Be', 'Pd', 'Pt', 'Au', 'Ag', 'Hg', 'Cd',
        'Pb', 'W',
    ],  # 44 elements + 1 "other" = 45
    'degree': [0, 1, 2, 3, 4, 5, 6],         # 7 + 1 other = 8
    'num_Hs': [0, 1, 2, 3, 4],               # 5 + 1 other = 6
    'formal_charge': [-2, -1, 0, 1, 2, 3],   # 6 + 1 other = 7
    'hybridization': [
        Chem.rdchem.HybridizationType.SP,
        Chem.rdchem.HybridizationType.SP2,
        Chem.rdchem.HybridizationType.SP3,
        Chem.rdchem.HybridizationType.SP3D,
        Chem.rdchem.HybridizationType.SP3D2,
    ],  # 5 + 1 other = 6
}

# Total atom feature dimensions:
# element(45) + degree(8) + num_Hs(6) + formal_charge(7) + hybridization(6)
# + is_aromatic(1) + is_in_ring(1) = 74
ATOM_FEATURE_DIM = 45 + 8 + 6 + 7 + 6 + 1 + 1  # = 74

# ── Bond Feature Encoding ──
BOND_FEATURES = {
    'bond_type': [
        Chem.rdchem.BondType.SINGLE,
        Chem.rdchem.BondType.DOUBLE,
        Chem.rdchem.BondType.TRIPLE,
        Chem.rdchem.BondType.AROMATIC,
    ],  # 4 + 1 other = 5
    'stereo': [
        Chem.rdchem.BondStereo.STEREONONE,
        Chem.rdchem.BondStereo.STEREOANY,
        Chem.rdchem.BondStereo.STEREOZ,
        Chem.rdchem.BondStereo.STEREOE,
    ],  # 4 + 1 other = 5
}

# Total bond feature dimensions:
# bond_type(5) + stereo(5) + is_conjugated(1) + is_in_ring(1) = 12
BOND_FEATURE_DIM = 5 + 5 + 1 + 1  # = 12

print(f"Atom feature dimensions: {ATOM_FEATURE_DIM}")
print(f"Bond feature dimensions: {BOND_FEATURE_DIM}")


def one_hot(value, allowable_set):
    """One-hot encode a value. If value not in set, last position is 1 (unknown)."""
    encoding = [0] * (len(allowable_set) + 1)
    try:
        idx = allowable_set.index(value)
        encoding[idx] = 1
    except ValueError:
        encoding[-1] = 1  # "other" category
    return encoding


def get_atom_features(atom):
    """Extract feature vector for a single atom."""
    features = []
    features += one_hot(atom.GetSymbol(), ATOM_FEATURES['element'])
    features += one_hot(atom.GetTotalDegree(), ATOM_FEATURES['degree'])
    features += one_hot(atom.GetTotalNumHs(), ATOM_FEATURES['num_Hs'])
    features += one_hot(atom.GetFormalCharge(), ATOM_FEATURES['formal_charge'])
    features += one_hot(atom.GetHybridization(), ATOM_FEATURES['hybridization'])
    features.append(1 if atom.GetIsAromatic() else 0)
    features.append(1 if atom.IsInRing() else 0)
    return features


def get_bond_features(bond):
    """Extract feature vector for a single bond."""
    features = []
    features += one_hot(bond.GetBondType(), BOND_FEATURES['bond_type'])
    features += one_hot(bond.GetStereo(), BOND_FEATURES['stereo'])
    features.append(1 if bond.GetIsConjugated() else 0)
    features.append(1 if bond.IsInRing() else 0)
    return features


def smiles_to_graph(smiles, label):
    """
    Convert a SMILES string to a PyG Data object.

    Returns None if the molecule can't be processed (too small, etc.).
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    # Skip molecules with fewer than 2 atoms (can't form bonds)
    if mol.GetNumAtoms() < 2:
        return None

    # ── Node (Atom) Features ──
    atom_features_list = []
    for atom in mol.GetAtoms():
        atom_features_list.append(get_atom_features(atom))

    x = torch.tensor(atom_features_list, dtype=torch.float)

    # ── Edge Index & Edge Features (bidirectional) ──
    edge_indices = []
    edge_features_list = []

    for bond in mol.GetBonds():
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()
        bond_feat = get_bond_features(bond)

        # Add both directions (A→B and B→A)
        edge_indices.append([i, j])
        edge_indices.append([j, i])
        edge_features_list.append(bond_feat)
        edge_features_list.append(bond_feat)

    if len(edge_indices) == 0:
        # Molecule with atoms but no bonds — skip
        return None

    edge_index = torch.tensor(edge_indices, dtype=torch.long).t().contiguous()
    edge_attr = torch.tensor(edge_features_list, dtype=torch.float)

    # ── Graph Label ──
    y = torch.tensor([label], dtype=torch.long)

    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)
    return data


# ── Convert all molecules to graphs ──
print(f"\nConverting {len(df_labeled):,} molecules to graphs...")
start_time = time.time()

graph_data_list = []
conversion_failures = 0

for idx, row in df_labeled.iterrows():
    graph = smiles_to_graph(row['canonical_smiles'], row['label'])
    if graph is not None:
        graph_data_list.append(graph)
    else:
        conversion_failures += 1

    # Progress reporting
    if (len(graph_data_list) + conversion_failures) % 10000 == 0:
        done = len(graph_data_list) + conversion_failures
        elapsed = time.time() - start_time
        print(f"  Processed {done:,} / {len(df_labeled):,} ({elapsed:.0f}s)")

elapsed = time.time() - start_time
print(f"\n✅ Graph conversion complete in {elapsed:.0f}s")
print(f"  Successful conversions: {len(graph_data_list):,}")
print(f"  Failed conversions: {conversion_failures:,}")

# Print graph statistics
num_nodes = [g.num_nodes for g in graph_data_list]
num_edges = [g.num_edges for g in graph_data_list]
print(f"\nGraph statistics:")
print(f"  Atoms per molecule — min: {min(num_nodes)}, max: {max(num_nodes)}, "
      f"mean: {np.mean(num_nodes):.1f}, median: {np.median(num_nodes):.1f}")
print(f"  Bonds per molecule — min: {min(num_edges)//2}, max: {max(num_edges)//2}, "
      f"mean: {np.mean(num_edges)/2:.1f}, median: {np.median(num_edges)/2:.1f}")

# Verify feature dimensions
sample = graph_data_list[0]
print(f"\nSample graph:")
print(f"  Node feature shape: {sample.x.shape} (expected [n_atoms, {ATOM_FEATURE_DIM}])")
print(f"  Edge index shape: {sample.edge_index.shape}")
print(f"  Edge attr shape: {sample.edge_attr.shape} (expected [n_edges, {BOND_FEATURE_DIM}])")
print(f"  Label: {sample.y.item()} ({label_names[sample.y.item()]})")


# %% CELL 6 — Stratified Train/Validation/Test Split
# =====================================================
# Split: 70% train, 15% validation, 15% test
# Stratified to maintain class distribution across splits.

print("\n" + "=" * 70)
print("PHASE 4: Data Splitting (70/15/15 Stratified)")
print("=" * 70)

# Extract labels for stratification
all_labels = [g.y.item() for g in graph_data_list]

# First split: 70% train, 30% temp
train_data, temp_data, train_labels, temp_labels = train_test_split(
    graph_data_list, all_labels,
    test_size=0.30,
    random_state=42,
    stratify=all_labels
)

# Second split: 50% of temp = 15% val, 50% of temp = 15% test
val_data, test_data, val_labels, test_labels = train_test_split(
    temp_data, temp_labels,
    test_size=0.50,
    random_state=42,
    stratify=temp_labels
)

del temp_data, temp_labels
gc.collect()

# Print split distributions
for name, labels in [("Train", train_labels), ("Validation", val_labels), ("Test", test_labels)]:
    counts = Counter(labels)
    total = len(labels)
    print(f"\n{name} set: {total:,} molecules")
    for cls_idx in sorted(counts.keys()):
        cls_name = label_names[cls_idx]
        count = counts[cls_idx]
        pct = count / total * 100
        print(f"  {cls_name:12s}: {count:>6,} ({pct:5.1f}%)")


# %% CELL 7 — Compute Class Weights for Imbalanced Loss
# ========================================================
# The three classes are imbalanced (~34K Plant vs ~11K Bacterial).
# Use inverse frequency weighting for CrossEntropyLoss.

print("\n" + "=" * 70)
print("PHASE 5: Computing Class Weights")
print("=" * 70)

train_label_counts = Counter(train_labels)
n_samples = len(train_labels)
n_classes = 3

# Inverse frequency weighting: weight_i = n_samples / (n_classes * count_i)
class_weights = []
for i in range(n_classes):
    count = train_label_counts[i]
    weight = n_samples / (n_classes * count)
    class_weights.append(weight)
    print(f"  {label_names[i]:12s}: count={count:>6,}, weight={weight:.4f}")

class_weights_tensor = torch.tensor(class_weights, dtype=torch.float).to(device)
print(f"\nClass weights tensor: {class_weights_tensor}")


# %% CELL 8 — GIN Model Architecture
# =====================================
# Graph Isomorphism Network (GIN) with:
#   - Multiple GINConv layers with BatchNorm + ReLU + Dropout
#   - Optional edge feature integration via GINEConv
#   - Global pooling (sum, mean, or attention)
#   - Fully connected classification head

print("\n" + "=" * 70)
print("PHASE 6: Defining GIN Architecture")
print("=" * 70)


class GINModel(nn.Module):
    """
    Graph Isomorphism Network for molecular classification.

    Architecture:
        Input atom features → [GINConv → BatchNorm → ReLU → Dropout] × N
        → Global Pooling → FC → ReLU → Dropout → FC(3) → output logits

    Args:
        num_node_features: Dimension of input node features (74)
        num_edge_features: Dimension of input edge features (12)
        hidden_dim: Hidden layer dimension (default 128)
        num_layers: Number of GIN convolutional layers (default 3)
        dropout: Dropout probability (default 0.3)
        pooling: Global pooling method — 'sum', 'mean', or 'attention' (default 'sum')
        use_edge_features: Whether to use edge features via GINEConv (default True)
        num_classes: Number of output classes (default 3)
    """

    def __init__(
        self,
        num_node_features=ATOM_FEATURE_DIM,
        num_edge_features=BOND_FEATURE_DIM,
        hidden_dim=128,
        num_layers=3,
        dropout=0.3,
        pooling='sum',
        use_edge_features=True,
        num_classes=3,
    ):
        super(GINModel, self).__init__()

        self.num_layers = num_layers
        self.dropout = dropout
        self.pooling = pooling
        self.use_edge_features = use_edge_features

        # ── GIN Convolutional Layers ──
        self.convs = nn.ModuleList()
        self.batch_norms = nn.ModuleList()

        for i in range(num_layers):
            in_dim = num_node_features if i == 0 else hidden_dim

            # MLP inside each GINConv: Linear → ReLU → Linear
            mlp = nn.Sequential(
                nn.Linear(in_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim),
            )

            if use_edge_features:
                # GINEConv incorporates edge features into message passing
                # Edge features must be projected to match node feature dim
                conv = GINEConv(mlp, edge_dim=num_edge_features)
            else:
                conv = GINConv(mlp)

            self.convs.append(conv)
            self.batch_norms.append(nn.BatchNorm1d(hidden_dim))

        # ── Attention Pooling (optional) ──
        if pooling == 'attention':
            from torch_geometric.nn import GlobalAttention
            gate_nn = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, 1),
            )
            self.attention_pool = GlobalAttention(gate_nn)

        # ── Classification Head ──
        self.fc1 = nn.Linear(hidden_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, num_classes)

        # Store config for saving/loading
        self.config = {
            'num_node_features': num_node_features,
            'num_edge_features': num_edge_features,
            'hidden_dim': hidden_dim,
            'num_layers': num_layers,
            'dropout': dropout,
            'pooling': pooling,
            'use_edge_features': use_edge_features,
            'num_classes': num_classes,
        }

    def forward(self, data):
        x, edge_index, batch = data.x, data.edge_index, data.batch
        edge_attr = data.edge_attr if self.use_edge_features else None

        # ── Message Passing Layers ──
        for i in range(self.num_layers):
            if self.use_edge_features and edge_attr is not None:
                x = self.convs[i](x, edge_index, edge_attr=edge_attr)
            else:
                x = self.convs[i](x, edge_index)

            x = self.batch_norms[i](x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)

        # ── Global Pooling ──
        if self.pooling == 'sum':
            x = global_add_pool(x, batch)
        elif self.pooling == 'mean':
            x = global_mean_pool(x, batch)
        elif self.pooling == 'attention':
            x = self.attention_pool(x, batch)
        else:
            x = global_add_pool(x, batch)  # Default fallback

        # ── Classification Head ──
        x = F.relu(self.fc1(x))
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.fc2(x)

        return x


# ── Hyperparameters (GIN Baseline) ──
HYPERPARAMS = {
    'hidden_dim': 128,
    'num_layers': 3,
    'dropout': 0.3,
    'learning_rate': 0.001,
    'batch_size': 64,
    'pooling': 'sum',
    'use_edge_features': True,
    'patience': 20,
    'max_epochs': 200,
}

print("Baseline Hyperparameters:")
for k, v in HYPERPARAMS.items():
    print(f"  {k}: {v}")

# Create model
model = GINModel(
    num_node_features=ATOM_FEATURE_DIM,
    num_edge_features=BOND_FEATURE_DIM,
    hidden_dim=HYPERPARAMS['hidden_dim'],
    num_layers=HYPERPARAMS['num_layers'],
    dropout=HYPERPARAMS['dropout'],
    pooling=HYPERPARAMS['pooling'],
    use_edge_features=HYPERPARAMS['use_edge_features'],
    num_classes=3,
).to(device)

# Count parameters
total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"\nModel Parameters:")
print(f"  Total: {total_params:,}")
print(f"  Trainable: {trainable_params:,}")
print(f"\nModel Architecture:")
print(model)


# %% CELL 9 — Training Loop with Early Stopping
# ================================================

print("\n" + "=" * 70)
print("PHASE 7: Training GIN Model")
print("=" * 70)

# ── Create DataLoaders ──
train_loader = DataLoader(
    train_data,
    batch_size=HYPERPARAMS['batch_size'],
    shuffle=True,
    num_workers=2,
    pin_memory=True,
)
val_loader = DataLoader(
    val_data,
    batch_size=HYPERPARAMS['batch_size'],
    shuffle=False,
    num_workers=2,
    pin_memory=True,
)
test_loader = DataLoader(
    test_data,
    batch_size=HYPERPARAMS['batch_size'],
    shuffle=False,
    num_workers=2,
    pin_memory=True,
)

print(f"Train batches: {len(train_loader)}")
print(f"Val batches: {len(val_loader)}")
print(f"Test batches: {len(test_loader)}")

# ── Loss, Optimizer, Scheduler ──
criterion = nn.CrossEntropyLoss(weight=class_weights_tensor)
optimizer = Adam(model.parameters(), lr=HYPERPARAMS['learning_rate'], weight_decay=1e-5)
scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=10)


def train_one_epoch(model, loader, optimizer, criterion, device):
    """Train for one epoch. Returns average loss and balanced accuracy."""
    model.train()
    total_loss = 0
    all_preds = []
    all_labels = []

    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()

        out = model(batch)
        loss = criterion(out, batch.y)

        loss.backward()
        # Gradient clipping to prevent exploding gradients
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
        optimizer.step()

        total_loss += loss.item() * batch.num_graphs
        preds = out.argmax(dim=1).cpu().numpy()
        labels = batch.y.cpu().numpy()
        all_preds.extend(preds)
        all_labels.extend(labels)

    avg_loss = total_loss / len(loader.dataset)
    bal_acc = balanced_accuracy_score(all_labels, all_preds)
    return avg_loss, bal_acc


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    """Evaluate model on a dataset. Returns avg loss, balanced accuracy, all preds, all labels."""
    model.eval()
    total_loss = 0
    all_preds = []
    all_labels = []
    all_probs = []

    for batch in loader:
        batch = batch.to(device)
        out = model(batch)
        loss = criterion(out, batch.y)

        total_loss += loss.item() * batch.num_graphs
        probs = F.softmax(out, dim=1).cpu().numpy()
        preds = out.argmax(dim=1).cpu().numpy()
        labels = batch.y.cpu().numpy()

        all_preds.extend(preds)
        all_labels.extend(labels)
        all_probs.extend(probs)

    avg_loss = total_loss / len(loader.dataset)
    bal_acc = balanced_accuracy_score(all_labels, all_preds)
    return avg_loss, bal_acc, np.array(all_preds), np.array(all_labels), np.array(all_probs)


# ── Training Loop with Early Stopping ──
print(f"\nStarting training for up to {HYPERPARAMS['max_epochs']} epochs...")
print(f"Early stopping patience: {HYPERPARAMS['patience']} epochs")
print("-" * 90)
print(f"{'Epoch':>6} | {'Train Loss':>11} | {'Train BAcc':>11} | "
      f"{'Val Loss':>11} | {'Val BAcc':>11} | {'LR':>10} | {'Status':>10}")
print("-" * 90)

best_val_loss = float('inf')
best_val_bacc = 0.0
best_epoch = 0
patience_counter = 0
training_history = []

CHECKPOINT_PATH = "best_gin_model.pt"
training_start = time.time()

for epoch in range(1, HYPERPARAMS['max_epochs'] + 1):
    epoch_start = time.time()

    # Train
    train_loss, train_bacc = train_one_epoch(model, train_loader, optimizer, criterion, device)

    # Validate
    val_loss, val_bacc, _, _, _ = evaluate(model, val_loader, criterion, device)

    # Learning rate scheduling
    scheduler.step(val_loss)
    current_lr = optimizer.param_groups[0]['lr']

    # Track history
    training_history.append({
        'epoch': epoch,
        'train_loss': train_loss,
        'train_bacc': train_bacc,
        'val_loss': val_loss,
        'val_bacc': val_bacc,
        'lr': current_lr,
    })

    # Early stopping check
    status = ""
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        best_val_bacc = val_bacc
        best_epoch = epoch
        patience_counter = 0
        status = "✅ BEST"

        # Save checkpoint
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'val_loss': val_loss,
            'val_bacc': val_bacc,
            'model_config': model.config,
            'hyperparams': HYPERPARAMS,
            'label_names': label_names,
            'atom_feature_dim': ATOM_FEATURE_DIM,
            'bond_feature_dim': BOND_FEATURE_DIM,
        }, CHECKPOINT_PATH)
    else:
        patience_counter += 1
        if patience_counter >= HYPERPARAMS['patience']:
            status = "⛔ STOP"
        else:
            status = f"⏳ {patience_counter}/{HYPERPARAMS['patience']}"

    # Print epoch summary
    print(f"{epoch:>6} | {train_loss:>11.6f} | {train_bacc:>11.4f} | "
          f"{val_loss:>11.6f} | {val_bacc:>11.4f} | {current_lr:>10.6f} | {status:>10}")

    # Early stopping
    if patience_counter >= HYPERPARAMS['patience']:
        print(f"\n⛔ Early stopping triggered at epoch {epoch}")
        print(f"   Best epoch: {best_epoch} with val_loss={best_val_loss:.6f}, val_bacc={best_val_bacc:.4f}")
        break

training_time = time.time() - training_start
print(f"\n✅ Training completed in {training_time/60:.1f} minutes")
print(f"Best model saved at epoch {best_epoch}")


# %% CELL 10 — Plot Training Curves
# =====================================

print("\n" + "=" * 70)
print("PHASE 8: Training Curves Visualization")
print("=" * 70)

history_df = pd.DataFrame(training_history)

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Loss curves
axes[0].plot(history_df['epoch'], history_df['train_loss'], label='Train Loss', color='#2196F3', linewidth=2)
axes[0].plot(history_df['epoch'], history_df['val_loss'], label='Val Loss', color='#F44336', linewidth=2)
axes[0].axvline(x=best_epoch, color='green', linestyle='--', alpha=0.7, label=f'Best (epoch {best_epoch})')
axes[0].set_xlabel('Epoch', fontsize=12)
axes[0].set_ylabel('Loss', fontsize=12)
axes[0].set_title('Training & Validation Loss', fontsize=14, fontweight='bold')
axes[0].legend(fontsize=10)
axes[0].grid(True, alpha=0.3)

# Balanced Accuracy curves
axes[1].plot(history_df['epoch'], history_df['train_bacc'], label='Train BAcc', color='#2196F3', linewidth=2)
axes[1].plot(history_df['epoch'], history_df['val_bacc'], label='Val BAcc', color='#F44336', linewidth=2)
axes[1].axvline(x=best_epoch, color='green', linestyle='--', alpha=0.7, label=f'Best (epoch {best_epoch})')
axes[1].axhline(y=0.919, color='orange', linestyle=':', alpha=0.7, label='MAP4+SVM Benchmark (0.919)')
axes[1].set_xlabel('Epoch', fontsize=12)
axes[1].set_ylabel('Balanced Accuracy', fontsize=12)
axes[1].set_title('Balanced Accuracy', fontsize=14, fontweight='bold')
axes[1].legend(fontsize=10)
axes[1].grid(True, alpha=0.3)

# Learning rate
axes[2].plot(history_df['epoch'], history_df['lr'], color='#9C27B0', linewidth=2)
axes[2].set_xlabel('Epoch', fontsize=12)
axes[2].set_ylabel('Learning Rate', fontsize=12)
axes[2].set_title('Learning Rate Schedule', fontsize=14, fontweight='bold')
axes[2].set_yscale('log')
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('training_curves.png', dpi=150, bbox_inches='tight')
plt.show()
print("✅ Training curves saved to: training_curves.png")


# %% CELL 11 — Comprehensive Evaluation on Test Set
# =====================================================
# Load best model checkpoint and evaluate on held-out test set.
# Compute all required metrics:
#   - Balanced Accuracy
#   - MCC (Matthews Correlation Coefficient)
#   - Macro F1 Score
#   - Per-class Precision, Recall, F1
#   - 3×3 Confusion Matrix

print("\n" + "=" * 70)
print("PHASE 9: Final Evaluation on Test Set")
print("=" * 70)

# Load best checkpoint
print("Loading best model checkpoint...")
checkpoint = torch.load(CHECKPOINT_PATH, map_location=device, weights_only=False)
model.load_state_dict(checkpoint['model_state_dict'])
print(f"Loaded model from epoch {checkpoint['epoch']} "
      f"(val_loss={checkpoint['val_loss']:.6f}, val_bacc={checkpoint['val_bacc']:.4f})")

# Evaluate on test set
test_loss, test_bacc, test_preds, test_true, test_probs = evaluate(
    model, test_loader, criterion, device
)

# ── Core Metrics ──
test_mcc = matthews_corrcoef(test_true, test_preds)
test_macro_f1 = f1_score(test_true, test_preds, average='macro')
test_weighted_f1 = f1_score(test_true, test_preds, average='weighted')

print("\n" + "=" * 60)
print("         TEST SET RESULTS (vs. MAP4+SVM Benchmark)")
print("=" * 60)
print(f"{'Metric':<25} {'GIN':>10} {'MAP4+SVM':>10} {'Status':>10}")
print("-" * 60)
print(f"{'Balanced Accuracy':<25} {test_bacc:>10.4f} {'0.9190':>10} "
      f"{'✅ BEAT' if test_bacc >= 0.919 else '❌ BELOW':>10}")
print(f"{'MCC':<25} {test_mcc:>10.4f} {'0.8790':>10} "
      f"{'✅ BEAT' if test_mcc >= 0.879 else '❌ BELOW':>10}")
print(f"{'Macro F1':<25} {test_macro_f1:>10.4f} {'0.9290':>10} "
      f"{'✅ BEAT' if test_macro_f1 >= 0.929 else '❌ BELOW':>10}")
print(f"{'Weighted F1':<25} {test_weighted_f1:>10.4f} {'—':>10} {'':>10}")
print(f"{'Test Loss':<25} {test_loss:>10.6f} {'—':>10} {'':>10}")
print("=" * 60)

# ── Per-class Metrics ──
print("\nPer-Class Detailed Metrics:")
print("-" * 65)
precision, recall, f1, support = precision_recall_fscore_support(
    test_true, test_preds, average=None, labels=[0, 1, 2]
)

print(f"{'Class':<12} {'Precision':>10} {'Recall':>10} {'F1-Score':>10} {'Support':>10}")
print("-" * 65)
for i in range(3):
    print(f"{label_names[i]:<12} {precision[i]:>10.4f} {recall[i]:>10.4f} "
          f"{f1[i]:>10.4f} {support[i]:>10}")
print("-" * 65)

# Also print full classification report
print("\nFull Classification Report:")
print(classification_report(
    test_true, test_preds,
    target_names=[label_names[i] for i in range(3)],
    digits=4
))


# %% CELL 12 — Confusion Matrix Visualization
# ===============================================

print("Generating confusion matrix...")

cm = confusion_matrix(test_true, test_preds, labels=[0, 1, 2])
cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

class_names = [label_names[i] for i in range(3)]

# Raw counts
sns.heatmap(
    cm, annot=True, fmt='d', cmap='Blues',
    xticklabels=class_names, yticklabels=class_names,
    ax=axes[0], cbar_kws={'label': 'Count'}
)
axes[0].set_xlabel('Predicted', fontsize=12)
axes[0].set_ylabel('True', fontsize=12)
axes[0].set_title('Confusion Matrix (Counts)', fontsize=14, fontweight='bold')

# Normalized (percentages)
sns.heatmap(
    cm_normalized, annot=True, fmt='.2%', cmap='Oranges',
    xticklabels=class_names, yticklabels=class_names,
    ax=axes[1], cbar_kws={'label': 'Proportion'}
)
axes[1].set_xlabel('Predicted', fontsize=12)
axes[1].set_ylabel('True', fontsize=12)
axes[1].set_title('Confusion Matrix (Normalized)', fontsize=14, fontweight='bold')

plt.tight_layout()
plt.savefig('confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.show()
print("✅ Confusion matrix saved to: confusion_matrix.png")


# %% CELL 13 — Error Analysis
# ==============================
# Examine misclassified compounds for patterns.
# Particularly interesting: Plant compounds classified as Fungal/Bacterial
# could indicate endophytic origin.

print("\n" + "=" * 70)
print("PHASE 10: Error Analysis")
print("=" * 70)

# Identify misclassified indices
misclassified_mask = test_preds != test_true
n_misclassified = misclassified_mask.sum()
n_correct = (~misclassified_mask).sum()

print(f"Total test samples: {len(test_true):,}")
print(f"Correctly classified: {n_correct:,} ({n_correct/len(test_true)*100:.1f}%)")
print(f"Misclassified: {n_misclassified:,} ({n_misclassified/len(test_true)*100:.1f}%)")

# Analyze confusion patterns
print("\n── Confusion Patterns ──")
confusion_patterns = Counter()
for true, pred in zip(test_true[misclassified_mask], test_preds[misclassified_mask]):
    pattern = f"{label_names[true]} → {label_names[pred]}"
    confusion_patterns[pattern] += 1

for pattern, count in confusion_patterns.most_common():
    pct = count / n_misclassified * 100
    print(f"  {pattern:<25s}: {count:>5,} ({pct:5.1f}% of errors)")

# Analyze confidence of misclassifications
print("\n── Confidence Analysis ──")
correct_probs = test_probs[~misclassified_mask]
wrong_probs = test_probs[misclassified_mask]

if len(correct_probs) > 0:
    correct_max_conf = correct_probs.max(axis=1)
    print(f"Correct predictions — avg max confidence: {correct_max_conf.mean():.4f}")
    print(f"  Median: {np.median(correct_max_conf):.4f}, Min: {correct_max_conf.min():.4f}")

if len(wrong_probs) > 0:
    wrong_max_conf = wrong_probs.max(axis=1)
    print(f"Wrong predictions   — avg max confidence: {wrong_max_conf.mean():.4f}")
    print(f"  Median: {np.median(wrong_max_conf):.4f}, Min: {wrong_max_conf.min():.4f}")

# Flag potential endophytic compounds
# (Plant compounds misclassified as Fungal or Bacterial)
print("\n── Potential Endophytic Compounds ──")
endophyte_count = 0
for true, pred in zip(test_true[misclassified_mask], test_preds[misclassified_mask]):
    if label_names[true] == 'Plant' and label_names[pred] in ['Fungal', 'Bacterial']:
        endophyte_count += 1

plant_total = (test_true == 0).sum()
print(f"Plant → Fungal/Bacterial misclassifications: {endophyte_count:,}")
print(f"  This is {endophyte_count/plant_total*100:.2f}% of all Plant compounds in test set")
print(f"  These could be compounds actually produced by endophytic organisms!")

# Low confidence predictions analysis
print("\n── Low Confidence Predictions (max prob < 60%) ──")
low_conf_mask = test_probs.max(axis=1) < 0.60
n_low_conf = low_conf_mask.sum()
n_low_conf_wrong = (low_conf_mask & misclassified_mask).sum()
print(f"Total low-confidence predictions: {n_low_conf:,}")
if n_low_conf > 0:
    print(f"  Of which misclassified: {n_low_conf_wrong:,} ({n_low_conf_wrong/n_low_conf*100:.1f}%)")
    print(f"  These ambiguous compounds are candidates for endophytic analysis")

# Confidence distribution plot
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].hist(correct_max_conf, bins=50, alpha=0.7, color='#4CAF50', label='Correct', density=True)
if len(wrong_max_conf) > 0:
    axes[0].hist(wrong_max_conf, bins=50, alpha=0.7, color='#F44336', label='Wrong', density=True)
axes[0].set_xlabel('Max Class Probability', fontsize=12)
axes[0].set_ylabel('Density', fontsize=12)
axes[0].set_title('Confidence Distribution', fontsize=14, fontweight='bold')
axes[0].legend(fontsize=11)
axes[0].grid(True, alpha=0.3)

# Per-class accuracy
class_acc = cm.diagonal() / cm.sum(axis=1)
colors = ['#4CAF50', '#FF9800', '#F44336']
bars = axes[1].bar(class_names, class_acc, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
axes[1].axhline(y=test_bacc, color='blue', linestyle='--', alpha=0.7, label=f'Balanced Acc: {test_bacc:.4f}')
for bar, acc in zip(bars, class_acc):
    axes[1].text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.005,
                 f'{acc:.3f}', ha='center', va='bottom', fontweight='bold', fontsize=12)
axes[1].set_xlabel('Class', fontsize=12)
axes[1].set_ylabel('Accuracy', fontsize=12)
axes[1].set_title('Per-Class Accuracy', fontsize=14, fontweight='bold')
axes[1].set_ylim(0, 1.05)
axes[1].legend(fontsize=11)
axes[1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('error_analysis.png', dpi=150, bbox_inches='tight')
plt.show()
print("✅ Error analysis plots saved to: error_analysis.png")


# %% CELL 14 — Save Final Model Artifact for Deployment
# ========================================================
# Save everything needed to reconstruct and run the model on new SMILES:
#   - Model architecture config
#   - Trained weights (state_dict)
#   - Feature encoding specifications
#   - Label mapping
#   - Training hyperparameters and results

print("\n" + "=" * 70)
print("PHASE 11: Saving Final Model Artifact")
print("=" * 70)

FINAL_MODEL_PATH = "gin_drug_classifier_final.pt"

# Compile all results
final_results = {
    'balanced_accuracy': float(test_bacc),
    'mcc': float(test_mcc),
    'macro_f1': float(test_macro_f1),
    'weighted_f1': float(test_weighted_f1),
    'test_loss': float(test_loss),
    'per_class_precision': precision.tolist(),
    'per_class_recall': recall.tolist(),
    'per_class_f1': f1.tolist(),
    'per_class_support': support.tolist(),
    'confusion_matrix': cm.tolist(),
    'best_epoch': best_epoch,
    'total_training_time_minutes': training_time / 60,
}

# Save complete artifact
artifact = {
    # ── Model ──
    'model_state_dict': model.state_dict(),
    'model_config': model.config,

    # ── Feature Encoding Specs ──
    'atom_features': {
        'element_list': ATOM_FEATURES['element'],
        'degree_list': ATOM_FEATURES['degree'],
        'num_Hs_list': ATOM_FEATURES['num_Hs'],
        'formal_charge_list': ATOM_FEATURES['formal_charge'],
        # Hybridization types are stored as string names for portability
        'hybridization_list': [str(h) for h in ATOM_FEATURES['hybridization']],
    },
    'bond_features': {
        'bond_type_list': [str(bt) for bt in BOND_FEATURES['bond_type']],
        'stereo_list': [str(s) for s in BOND_FEATURES['stereo']],
    },
    'atom_feature_dim': ATOM_FEATURE_DIM,
    'bond_feature_dim': BOND_FEATURE_DIM,

    # ── Labels ──
    'label_names': label_names,  # {0: 'Plant', 1: 'Fungal', 2: 'Bacterial'}
    'label_map': label_map,      # {'Plant': 0, 'Fungal': 1, 'Bacterial': 2}

    # ── Training Info ──
    'hyperparams': HYPERPARAMS,
    'results': final_results,
    'training_history': training_history,

    # ── Class Weights ──
    'class_weights': class_weights,
}

torch.save(artifact, FINAL_MODEL_PATH)
file_size_mb = os.path.getsize(FINAL_MODEL_PATH) / 1e6
print(f"✅ Final model saved to: {FINAL_MODEL_PATH} ({file_size_mb:.1f} MB)")

# Also save results as human-readable JSON
results_json = {
    'model': 'GIN (Graph Isomorphism Network)',
    'dataset': 'COCONUT (filtered)',
    'dataset_size': len(graph_data_list),
    'train_size': len(train_data),
    'val_size': len(val_data),
    'test_size': len(test_data),
    'hyperparameters': HYPERPARAMS,
    'results': final_results,
    'benchmark_comparison': {
        'balanced_accuracy': {
            'GIN': float(test_bacc),
            'MAP4+SVM': 0.919,
            'beat_benchmark': bool(test_bacc >= 0.919),
        },
        'MCC': {
            'GIN': float(test_mcc),
            'MAP4+SVM': 0.879,
            'beat_benchmark': bool(test_mcc >= 0.879),
        },
        'macro_F1': {
            'GIN': float(test_macro_f1),
            'MAP4+SVM': 0.929,
            'beat_benchmark': bool(test_macro_f1 >= 0.929),
        },
    },
}

with open('gin_results.json', 'w') as f:
    json.dump(results_json, f, indent=2)
print("✅ Results saved to: gin_results.json")


# %% CELL 15 — Summary & Next Steps
# =====================================

print("\n" + "=" * 70)
print("TRAINING COMPLETE — SUMMARY")
print("=" * 70)
print(f"""
Model:            GIN (Graph Isomorphism Network)
Dataset:          COCONUT ({len(graph_data_list):,} compounds, 3 classes)
Split:            Train {len(train_data):,} / Val {len(val_data):,} / Test {len(test_data):,}
Best Epoch:       {best_epoch}
Training Time:    {training_time/60:.1f} minutes

═══ TEST SET RESULTS ═══
Balanced Accuracy:  {test_bacc:.4f}  (benchmark: 0.919)
MCC:                {test_mcc:.4f}  (benchmark: 0.879)
Macro F1:           {test_macro_f1:.4f}  (benchmark: 0.929)

═══ FILES SAVED ═══
  • gin_drug_classifier_final.pt  — Full model artifact for deployment
  • best_gin_model.pt             — Best checkpoint
  • gin_results.json              — Results summary
  • coconut_cleaned.csv           — Cleaned dataset
  • training_curves.png           — Loss & accuracy plots
  • confusion_matrix.png          — Confusion matrix visualization
  • error_analysis.png            — Error analysis plots

═══ NEXT STEPS ═══
  1. Download 'gin_drug_classifier_final.pt' from Kaggle output
  2. Place it in: ML_PROJECT/ml/models/drug_classification/
  3. If results are good, proceed to AttentiveFP training
  4. If results need improvement, run hyperparameter tuning
""")

print("🎉 Done! Download your model artifacts from the Kaggle output tab.")
