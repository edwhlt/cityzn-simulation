#!/usr/bin/env python3
"""
Script d'entraînement du modèle ML CityZN - Version 3
Entraîne sur les 68 edges avec capteurs réels (~11k lignes)

Usage:
  python train_v3.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime

# ML libraries
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error
from sklearn.preprocessing import LabelEncoder
import joblib
from tqdm import tqdm

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
DATA_PREDICTIONS_DIR = BASE_DIR / "data" / "predictions"
MODELS_DIR = BASE_DIR / "models"

# Créer dossiers
DATA_PREDICTIONS_DIR.mkdir(exist_ok=True, parents=True)
MODELS_DIR.mkdir(exist_ok=True, parents=True)

print("=" * 80)
print("🤖 CITYZN - TRAINING v3 (Architecture Modulaire)")
print("=" * 80)

# =====================================================================
# 1. CHARGEMENT DONNÉES TRAINING
# =====================================================================

print("\n📂 Étape 1: Chargement dataset training...")

df = pd.read_csv(DATA_PROCESSED_DIR / "final_dataset_v3.csv")
df['timestamp'] = pd.to_datetime(df['timestamp'])

print(f"   ✅ Dataset chargé: {df.shape}")
print(f"   • Lignes: {len(df):,}")
print(f"   • Colonnes: {len(df.columns)}")
print(f"   • Edges uniques: {df['edge_id'].nunique()}")
print(f"   • Période: {df['timestamp'].min().date()} → {df['timestamp'].max().date()}")

# Statistiques sur les données
print(f"\n📊 Statistiques bike_count:")
print(f"   • Lignes avec données: {df['bike_count'].notna().sum():,}")
print(f"   • Moyenne: {df['bike_count'].mean():.1f} vélos/h")
print(f"   • Médiane: {df['bike_count'].median():.1f}")
print(f"   • Max: {df['bike_count'].max():.0f}")
print(f"   • Min: {df['bike_count'].min():.0f}")

# =====================================================================
# 2. PRÉPARATION FEATURES  
# =====================================================================

print("\n🔧 Étape 2: Préparation des features...")

# Features à encoder (catégorielles)
categorical_cols = [
    'highway_type', 'road_category', 'cycleway_type',
    'surface_quality', 'bicycle_access', 'orientation'
]

# Features à exclure
exclude_cols = [
    'edge_id', 'timestamp', 'bike_count'
]

# Label encoding pour les features catégorielles
label_encoders = {}
for col in categorical_cols:
    if col in df.columns:
        le = LabelEncoder()
        # Gérer les valeurs manquantes
        df[col] = df[col].fillna('unknown')
        df[col] = le.fit_transform(df[col].astype(str))
        label_encoders[col] = le

# Sauvegarder les encoders
encoders_path = MODELS_DIR / "label_encoders.joblib"
joblib.dump(label_encoders, encoders_path)
print(f"   ✅ Label encoders sauvegardés: {encoders_path}")

# Sélectionner features pour ML
feature_cols = [col for col in df.columns if col not in exclude_cols]

print(f"   ✅ Features préparées: {len(feature_cols)} colonnes")
print(f"\n📋 Liste des features:")
for i, col in enumerate(feature_cols, 1):
    print(f"      {i:2d}. {col}")

# =====================================================================
# 3. TRAIN/TEST SPLIT
# =====================================================================

print("\n✂️  Étape 3: Création train/test split...")

# Filtrer lignes avec bike_count (enlever les NaN)
df_valid = df[df['bike_count'].notna()].copy()
print(f"   • Lignes valides: {len(df_valid):,}")

# Préparer X et y
X = df_valid[feature_cols].copy()
y = df_valid['bike_count'].copy()

# Remplir NaN dans X
numeric_cols = X.select_dtypes(include=[np.number]).columns
X[numeric_cols] = X[numeric_cols].fillna(X[numeric_cols].median())

print(f"   • Données préparées: {len(X):,} lignes × {len(feature_cols)} features")

# Split temporel: 80% train, 20% test
split_idx = int(len(X) * 0.8)

X_train = X.iloc[:split_idx]
X_test = X.iloc[split_idx:]
y_train = y.iloc[:split_idx]
y_test = y.iloc[split_idx:]

print(f"   ✅ Split effectué:")
print(f"      • Train: {len(X_train):,} lignes ({len(X_train)/len(X)*100:.1f}%)")
print(f"      • Test:  {len(X_test):,} lignes ({len(X_test)/len(X)*100:.1f}%)")

# =====================================================================
# 4. ENTRAÎNEMENT MODÈLES
# =====================================================================

print("\n🎓 Étape 4: Entraînement des modèles...")

models = {}
results = {}

# 4.1 Random Forest
print("\n   🌲 Random Forest...")
rf_model = RandomForestRegressor(
    n_estimators=200,
    max_depth=20,
    min_samples_split=5,
    min_samples_leaf=2,
    max_features='sqrt',
    n_jobs=-1,
    random_state=42,
    verbose=0
)
rf_model.fit(X_train, y_train)
y_pred_rf = rf_model.predict(X_test)

results['RandomForest'] = {
    'MAE': mean_absolute_error(y_test, y_pred_rf),
    'RMSE': np.sqrt(mean_squared_error(y_test, y_pred_rf)),
    'R2': r2_score(y_test, y_pred_rf),
    'MAPE': mean_absolute_percentage_error(y_test, y_pred_rf) * 100
}
models['RandomForest'] = rf_model

print(f"      • MAE:  {results['RandomForest']['MAE']:.2f}")
print(f"      • RMSE: {results['RandomForest']['RMSE']:.2f}")
print(f"      • R²:   {results['RandomForest']['R2']:.3f}")
print(f"      • MAPE: {results['RandomForest']['MAPE']:.1f}%")

# 4.2 Gradient Boosting
print("\n   🚀 Gradient Boosting...")
gb_model = GradientBoostingRegressor(
    n_estimators=200,
    max_depth=10,
    learning_rate=0.1,
    min_samples_split=5,
    min_samples_leaf=2,
    subsample=0.8,
    random_state=42,
    verbose=0
)
gb_model.fit(X_train, y_train)
y_pred_gb = gb_model.predict(X_test)

results['GradientBoosting'] = {
    'MAE': mean_absolute_error(y_test, y_pred_gb),
    'RMSE': np.sqrt(mean_squared_error(y_test, y_pred_gb)),
    'R2': r2_score(y_test, y_pred_gb),
    'MAPE': mean_absolute_percentage_error(y_test, y_pred_gb) * 100
}
models['GradientBoosting'] = gb_model

print(f"      • MAE:  {results['GradientBoosting']['MAE']:.2f}")
print(f"      • RMSE: {results['GradientBoosting']['RMSE']:.2f}")
print(f"      • R²:   {results['GradientBoosting']['R2']:.3f}")
print(f"      • MAPE: {results['GradientBoosting']['MAPE']:.1f}%")

# 4.3 Ridge Regression (baseline)
print("\n   📈 Ridge Regression (baseline)...")
ridge_model = Ridge(alpha=1.0, random_state=42)
ridge_model.fit(X_train, y_train)
y_pred_ridge = ridge_model.predict(X_test)

results['Ridge'] = {
    'MAE': mean_absolute_error(y_test, y_pred_ridge),
    'RMSE': np.sqrt(mean_squared_error(y_test, y_pred_ridge)),
    'R2': r2_score(y_test, y_pred_ridge),
    'MAPE': mean_absolute_percentage_error(y_test, y_pred_ridge) * 100
}
models['Ridge'] = ridge_model

print(f"      • MAE:  {results['Ridge']['MAE']:.2f}")
print(f"      • RMSE: {results['Ridge']['RMSE']:.2f}")
print(f"      • R²:   {results['Ridge']['R2']:.3f}")
print(f"      • MAPE: {results['Ridge']['MAPE']:.1f}%")

# =====================================================================
# 5. SÉLECTION MEILLEUR MODÈLE
# =====================================================================

print("\n🏆 Étape 5: Sélection du meilleur modèle...")

# Comparer par R²
best_model_name = max(results.keys(), key=lambda k: results[k]['R2'])
best_model = models[best_model_name]

print(f"   ✅ Meilleur modèle: {best_model_name}")
print(f"      • R²:   {results[best_model_name]['R2']:.3f}")
print(f"      • MAE:  {results[best_model_name]['MAE']:.2f} vélos/h")
print(f"      • RMSE: {results[best_model_name]['RMSE']:.2f} vélos/h")
print(f"      • MAPE: {results[best_model_name]['MAPE']:.1f}%")

# =====================================================================
# 6. FEATURE IMPORTANCE
# =====================================================================

print("\n📊 Étape 6: Analyse feature importance...")

if hasattr(best_model, 'feature_importances_'):
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': best_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n   Top 10 features:")
    for idx, row in feature_importance.head(10).iterrows():
        print(f"      {row['feature']:30s} {row['importance']:.4f}")
    
    # Sauvegarder
    feature_importance.to_csv(DATA_PREDICTIONS_DIR / "feature_importance.csv", index=False)
    print(f"\n   ✅ Feature importance sauvegardée")

# =====================================================================
# 7. SAUVEGARDE MODÈLE ET MÉTADONNÉES
# =====================================================================

print("\n💾 Étape 7: Sauvegarde du modèle...")

# Sauvegarder modèle
model_path = MODELS_DIR / "best_model.joblib"
joblib.dump(best_model, model_path)
print(f"   ✅ Modèle sauvegardé: {model_path}")

# Sauvegarder feature columns
features_path = MODELS_DIR / "feature_columns.json"
with open(features_path, 'w') as f:
    json.dump(feature_cols, f, indent=2)
print(f"   ✅ Features sauvegardées: {features_path}")

# Sauvegarder métriques
metrics = {
    'model_type': best_model_name,
    'trained_at': datetime.now().isoformat(),
    'dataset': 'final_dataset_v3.csv',
    'n_samples_train': len(X_train),
    'n_samples_test': len(X_test),
    'n_features': len(feature_cols),
    'n_edges': df_valid['edge_id'].nunique(),
    'metrics': {
        'mae': float(results[best_model_name]['MAE']),
        'rmse': float(results[best_model_name]['RMSE']),
        'r2': float(results[best_model_name]['R2']),
        'mape': float(results[best_model_name]['MAPE'])
    },
    'all_models_comparison': {
        name: {k.lower(): float(v) for k, v in metrics.items()}
        for name, metrics in results.items()
    }
}

metrics_path = MODELS_DIR / "metrics.json"
with open(metrics_path, 'w') as f:
    json.dump(metrics, f, indent=2)
print(f"   ✅ Métriques sauvegardées: {metrics_path}")

# =====================================================================
# 8. RÉSUMÉ FINAL
# =====================================================================

print("\n" + "=" * 80)
print("✅ TRAINING TERMINÉ!")
print("=" * 80)

print(f"\n📁 Fichiers générés:")
print(f"   1. {model_path.relative_to(BASE_DIR)}")
print(f"   2. {features_path.relative_to(BASE_DIR)}")
print(f"   3. {encoders_path.relative_to(BASE_DIR)}")
print(f"   4. {metrics_path.relative_to(BASE_DIR)}")

print(f"\n🎯 Performance:")
print(f"   • Modèle: {best_model_name}")
print(f"   • R²: {results[best_model_name]['R2']:.3f}")
print(f"   • Erreur moyenne: {results[best_model_name]['MAE']:.1f} vélos/h")

print(f"\n💡 Prochaine étape:")
print(f"   python src/models/predict_v3.py --datetime '2025-11-15 08:00'")
