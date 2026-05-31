"""
Drug ML Service — loads the trained GIN model, validates SMILES, and runs drug origin prediction.
"""

import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from pathlib import Path
from rdkit import Chem
from torch_geometric.data import Data
from torch_geometric.nn import GINConv, GINEConv, global_add_pool, global_mean_pool

from app.core.exceptions import InvalidSMILES, DrugPredictionFailed

# ── Atom Feature Encoding ──
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
ATOM_FEATURE_DIM = 45 + 8 + 6 + 7 + 6 + 1 + 1  # 74

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
BOND_FEATURE_DIM = 5 + 5 + 1 + 1  # 12


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


def smiles_to_graph(smiles, label=0):
    """
    Convert a SMILES string to a PyG Data object.
    Returns None if the molecule can't be processed.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    if mol.GetNumAtoms() < 2:
        return None

    # Node (Atom) Features
    atom_features_list = []
    for atom in mol.GetAtoms():
        atom_features_list.append(get_atom_features(atom))

    x = torch.tensor(atom_features_list, dtype=torch.float)

    # Edge Index & Edge Features (bidirectional)
    edge_indices = []
    edge_features_list = []

    for bond in mol.GetBonds():
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()
        bond_feat = get_bond_features(bond)

        # Add both directions
        edge_indices.append([i, j])
        edge_indices.append([j, i])
        edge_features_list.append(bond_feat)
        edge_features_list.append(bond_feat)

    if len(edge_indices) == 0:
        return None

    edge_index = torch.tensor(edge_indices, dtype=torch.long).t().contiguous()
    edge_attr = torch.tensor(edge_features_list, dtype=torch.float)
    y = torch.tensor([label], dtype=torch.long)

    return Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)


class GINModel(nn.Module):
    """
    Graph Isomorphism Network for molecular classification.
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

        # GIN Convolutional Layers
        self.convs = nn.ModuleList()
        self.batch_norms = nn.ModuleList()

        for i in range(num_layers):
            in_dim = num_node_features if i == 0 else hidden_dim

            # MLP inside GINConv: Linear → ReLU → Linear
            mlp = nn.Sequential(
                nn.Linear(in_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim),
            )

            if use_edge_features:
                conv = GINEConv(mlp, edge_dim=num_edge_features)
            else:
                conv = GINConv(mlp)

            self.convs.append(conv)
            self.batch_norms.append(nn.BatchNorm1d(hidden_dim))

        # Classification Head
        self.fc1 = nn.Linear(hidden_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, num_classes)

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

        # Message Passing Layers
        for i in range(self.num_layers):
            if self.use_edge_features and edge_attr is not None:
                x = self.convs[i](x, edge_index, edge_attr=edge_attr)
            else:
                x = self.convs[i](x, edge_index)

            x = self.batch_norms[i](x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)

        # Global Pooling
        if self.pooling == 'sum':
            x = global_add_pool(x, batch)
        elif self.pooling == 'mean':
            x = global_mean_pool(x, batch)
        else:
            x = global_add_pool(x, batch)

        # Classification Head
        x = F.relu(self.fc1(x))
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.fc2(x)

        return x


class DrugMLService:
    """Handles model loading and GIN inference for drug origin prediction from SMILES."""

    def __init__(self):
        self._model = None
        self._device = None
        self._label_names = {0: 'Plant', 1: 'Fungal', 2: 'Bacterial'}

    def load_model(self):
        """
        Load the trained GIN model.
        Called once at server startup.
        """
        self._device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Resolve path relative to this file's location: backend/app/drug_classification/service.py
        root_dir = Path(__file__).resolve().parents[3]
        model_path = root_dir / "ml" / "models" / "drug_classification" / "gin_drug_classifier_final.pt"

        if not model_path.exists():
            raise FileNotFoundError(f"GIN Drug Classifier model file not found at: {model_path}")

        print(f"[DrugMLService] Loading Drug GIN model from {model_path}...")
        
        try:
            artifact = torch.load(str(model_path), map_location=self._device, weights_only=False)
            model_config = artifact.get('model_config', {
                'num_node_features': ATOM_FEATURE_DIM,
                'num_edge_features': BOND_FEATURE_DIM,
                'hidden_dim': 128,
                'num_layers': 3,
                'dropout': 0.3,
                'pooling': 'sum',
                'use_edge_features': True,
                'num_classes': 3
            })
            
            # Recreate model
            self._model = GINModel(
                num_node_features=model_config['num_node_features'],
                num_edge_features=model_config['num_edge_features'],
                hidden_dim=model_config['hidden_dim'],
                num_layers=model_config['num_layers'],
                dropout=model_config['dropout'],
                pooling=model_config['pooling'],
                use_edge_features=model_config['use_edge_features'],
                num_classes=model_config['num_classes']
            )
            
            self._model.load_state_dict(artifact['model_state_dict'])
            self._model.to(self._device)
            self._model.eval()
            
            # Load label mapping if present
            if 'label_names' in artifact:
                self._label_names = {int(k): v for k, v in artifact['label_names'].items()}
                
            print("[DrugMLService] GIN Drug Classifier loaded successfully!")
        except Exception as e:
            raise RuntimeError(f"Failed to load GIN model: {str(e)}")

    def predict(self, smiles: str) -> dict:
        """
        Runs GIN drug origin prediction pipeline:
        1. Validates the SMILES string using RDKit (raises InvalidSMILES if bad).
        2. Normalizes the SMILES string.
        3. Converts SMILES into a molecular graph.
        4. Runs GIN model inference.
        5. Formats and returns prediction and confidence scores.
        """
        if self._model is None:
            raise RuntimeError("GIN Drug model not loaded. Call load_model() first.")

        smiles = smiles.strip()
        if not smiles:
            raise InvalidSMILES("SMILES string cannot be empty.")

        # 1. Validate SMILES using RDKit
        try:
            mol = Chem.MolFromSmiles(smiles)
        except Exception as e:
            raise InvalidSMILES("Invalid SMILES string. Please check your input.")

        if mol is None:
            raise InvalidSMILES("Invalid SMILES string. Please check your input.")

        # 2. Normalize SMILES
        try:
            norm_smiles = Chem.MolToSmiles(mol, isomericSmiles=False)
            mol_norm = Chem.MolFromSmiles(norm_smiles)
            if mol_norm is None:
                raise ValueError("SMILES normalization failed.")
        except Exception as e:
            raise InvalidSMILES("Invalid SMILES string. Please check your input.")

        # 3. Convert to Molecular Graph
        try:
            graph_data = smiles_to_graph(norm_smiles)
            if graph_data is None:
                raise ValueError("Graph featurization returned None (molecule likely too small).")
        except Exception as e:
            raise DrugPredictionFailed(f"Failed to featurize SMILES structure: {str(e)}")

        # 4. GIN Model Inference
        try:
            # Assign batch attribute for global pooling (required for batch size 1)
            graph_data.batch = torch.zeros(graph_data.x.size(0), dtype=torch.long, device=self._device)
            graph_data = graph_data.to(self._device)
            
            with torch.no_grad():
                logits = self._model(graph_data)
                probabilities = F.softmax(logits, dim=1).cpu().numpy()[0]
        except Exception as e:
            raise DrugPredictionFailed(f"Inference prediction failed: {str(e)}")

        # 5. Format response
        confidence = {
            "Plant": float(probabilities[0]),
            "Fungal": float(probabilities[1]),
            "Bacterial": float(probabilities[2])
        }

        # Select maximum confidence predicted label
        prediction_label = max(confidence, key=confidence.get)

        # Check for low confidence warning (predicted class confidence < 60%)
        note = None
        if confidence[prediction_label] < 0.60:
            note = "Low confidence prediction — this compound may have ambiguous origin"

        # Provide a backward compatible response that satisfies both Float dict confidence
        # and integer percent confidence, and both predicted_class and prediction keys!
        return {
            "predicted_class": prediction_label,
            "prediction": prediction_label,  # backward compatibility
            "confidence": confidence,
            "note": note,
            "warning": note  # backward compatibility
        }


# Singleton instance
drug_ml_service = DrugMLService()
