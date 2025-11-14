#!/usr/bin/env python3
"""
Analyse détaillée des erreurs du modèle CityZN - Version 3
- Métriques multiples pour évaluer le modèle
- Analyse des résidus par catégorie
- Visualisations des erreurs

Usage:
  python analyze_errors_v3.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error
import joblib
import json

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
DATA_PREDICTIONS_DIR = BASE_DIR / "data" / "predictions"
MODELS_DIR = BASE_DIR / "models"
VISUALIZATIONS_DIR = BASE_DIR / "visualizations"
VISUALIZATIONS_DIR.mkdir(exist_ok=True, parents=True)

# Style pour les graphiques
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 10)

print("=" * 80)
print("📊 ANALYSE DÉTAILLÉE DES ERREURS - CITYZN v3")
print("=" * 80)

# =====================================================================
# 1. CHARGER DONNÉES ET MODÈLE
# =====================================================================

print("\n📂 Étape 1: Chargement des données...")

# Charger dataset
df = pd.read_csv(DATA_PROCESSED_DIR / "final_dataset_v3.csv")
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Filtrer lignes valides (avec bike_count)
df_valid = df[df['bike_count'].notna()].copy()
print(f"   ✅ {len(df_valid):,} lignes valides avec données réelles")

# Charger le modèle entraîné
model_path = MODELS_DIR / "best_model.joblib"
if not model_path.exists():
    print(f"   ❌ Modèle non trouvé: {model_path}")
    print(f"   💡 Lancez d'abord: python src/models/train_v3.py")
    exit(1)

model = joblib.load(model_path)
print(f"   ✅ Modèle chargé: {model_path}")

# Charger encoders et features
label_encoders = joblib.load(MODELS_DIR / "label_encoders.joblib")
with open(MODELS_DIR / "feature_columns.json", 'r') as f:
    feature_cols = json.load(f)

print(f"   ✅ {len(feature_cols)} features chargées")

# =====================================================================
# 2. PRÉPARER DONNÉES POUR PRÉDICTION
# =====================================================================

print("\n🔧 Étape 2: Préparation des données...")

# Encoder features catégorielles (déjà fait pendant training normalement)
# On refait au cas où
categorical_cols = [
    'highway_type', 'road_category', 'cycleway_type',
    'surface_quality', 'bicycle_access', 'orientation'
]

# Extraire X et y
X = df_valid[feature_cols].copy()
y_true = df_valid['bike_count'].copy()

# Remplir NaN (comme dans l'entraînement)
numeric_cols = X.select_dtypes(include=[np.number]).columns
X[numeric_cols] = X[numeric_cols].fillna(X[numeric_cols].median())
X = X.fillna(0)

print(f"   ✅ {len(X):,} échantillons prêts pour prédiction")

# =====================================================================
# 3. PRÉDICTIONS ET CALCUL MÉTRIQUES
# =====================================================================

print("\n🔮 Étape 3: Génération des prédictions...")

y_pred = model.predict(X)
y_pred = np.maximum(y_pred, 0)  # Pas de valeurs négatives

# Calculer résidus
residuals = y_true - y_pred
abs_residuals = np.abs(residuals)
pct_residuals = abs_residuals / (y_true + 1) * 100  # +1 pour éviter division par 0

print(f"   ✅ Prédictions générées")

# =====================================================================
# 4. MÉTRIQUES GLOBALES
# =====================================================================

print("\n📊 Étape 4: Calcul métriques globales...")

metrics = {
    'MAE': mean_absolute_error(y_true, y_pred),
    'RMSE': np.sqrt(mean_squared_error(y_true, y_pred)),
    'R2': r2_score(y_true, y_pred),
    'MAPE': mean_absolute_percentage_error(y_true, y_pred) * 100,
    'Median_AE': np.median(abs_residuals),
    'P90_AE': np.percentile(abs_residuals, 90),
    'P95_AE': np.percentile(abs_residuals, 95)
}

print("\n   🎯 Métriques de performance:")
print(f"      • MAE (Mean Absolute Error):     {metrics['MAE']:.2f} vélos/h")
print(f"      • RMSE (Root Mean Squared Error): {metrics['RMSE']:.2f} vélos/h")
print(f"      • R² (Coefficient de détermination): {metrics['R2']:.3f}")
print(f"      • MAPE (Mean Absolute % Error):   {metrics['MAPE']:.1f}%")
print(f"      • Median AE (Erreur médiane):     {metrics['Median_AE']:.2f} vélos/h")
print(f"      • P90 AE (90e percentile):        {metrics['P90_AE']:.2f} vélos/h")
print(f"      • P95 AE (95e percentile):        {metrics['P95_AE']:.2f} vélos/h")

# =====================================================================
# 5. ANALYSE PAR CATÉGORIES
# =====================================================================

print("\n🔍 Étape 5: Analyse par catégories...")

# Ajouter prédictions au dataframe
df_valid['y_pred'] = y_pred
df_valid['residual'] = residuals
df_valid['abs_residual'] = abs_residuals
df_valid['pct_residual'] = pct_residuals

# 5.1 Par heure de la journée
print("\n   ⏰ Analyse par heure:")
hourly_errors = df_valid.groupby('hour').agg({
    'abs_residual': ['mean', 'median'],
    'bike_count': 'mean'
}).round(2)
print(hourly_errors)

# 5.2 Par jour de la semaine
print("\n   📅 Analyse par jour de la semaine:")
days = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
daily_errors = df_valid.groupby('day_of_week').agg({
    'abs_residual': ['mean', 'median'],
    'bike_count': 'mean'
}).round(2)
daily_errors.index = [days[i] for i in daily_errors.index]
print(daily_errors)

# 5.3 Par type de route
print("\n   🛣️  Analyse par type de route:")
# Décoder highway_type si nécessaire
if 'highway_type' in label_encoders:
    df_valid['highway_type_decoded'] = df_valid['highway_type'].apply(
        lambda x: label_encoders['highway_type'].classes_[int(x)] if x >= 0 else 'unknown'
    )
    highway_errors = df_valid.groupby('highway_type_decoded').agg({
        'abs_residual': ['mean', 'median', 'count'],
        'bike_count': 'mean'
    }).round(2)
    highway_errors = highway_errors.sort_values(('bike_count', 'mean'), ascending=False)
    print(highway_errors.head(10))

# 5.4 Par présence de piste cyclable
print("\n   🚴 Analyse par infrastructure cyclable:")
if 'has_dedicated_bike_lane' in df_valid.columns:
    bike_lane_errors = df_valid.groupby('has_dedicated_bike_lane').agg({
        'abs_residual': ['mean', 'median'],
        'bike_count': 'mean',
        'edge_id': 'count'
    }).round(2)
    bike_lane_errors.index = ['Sans piste', 'Avec piste']
    print(bike_lane_errors)

# 5.5 Par météo
print("\n   🌦️  Analyse par conditions météo:")
if 'is_raining' in df_valid.columns:
    weather_errors = df_valid.groupby('is_raining').agg({
        'abs_residual': ['mean', 'median'],
        'bike_count': 'mean',
        'edge_id': 'count'
    }).round(2)
    weather_errors.index = ['Temps sec', 'Pluie']
    print(weather_errors)

# =====================================================================
# 6. VISUALISATIONS
# =====================================================================

print("\n📈 Étape 6: Génération des visualisations...")

# 6.1 Scatter plot: Prédictions vs Réel
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Plot 1: Scatter avec ligne identité
ax1 = axes[0, 0]
ax1.scatter(y_true, y_pred, alpha=0.3, s=20)
max_val = max(y_true.max(), y_pred.max())
ax1.plot([0, max_val], [0, max_val], 'r--', lw=2, label='Prédiction parfaite')
ax1.set_xlabel('Valeurs réelles (vélos/h)', fontsize=12)
ax1.set_ylabel('Valeurs prédites (vélos/h)', fontsize=12)
ax1.set_title(f'Prédictions vs Réel (R² = {metrics["R2"]:.3f})', fontsize=14, fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Distribution des résidus
ax2 = axes[0, 1]
ax2.hist(residuals, bins=50, edgecolor='black', alpha=0.7)
ax2.axvline(x=0, color='r', linestyle='--', lw=2, label='Résidu = 0')
ax2.set_xlabel('Résidus (réel - prédit)', fontsize=12)
ax2.set_ylabel('Fréquence', fontsize=12)
ax2.set_title(f'Distribution des résidus (MAE = {metrics["MAE"]:.1f})', fontsize=14, fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Plot 3: Erreur par heure
ax3 = axes[1, 0]
hourly_mae = df_valid.groupby('hour')['abs_residual'].mean()
ax3.bar(hourly_mae.index, hourly_mae.values, color='steelblue', edgecolor='black')
ax3.set_xlabel('Heure de la journée', fontsize=12)
ax3.set_ylabel('MAE (vélos/h)', fontsize=12)
ax3.set_title('Erreur moyenne par heure', fontsize=14, fontweight='bold')
ax3.set_xticks(range(24))
ax3.grid(True, alpha=0.3, axis='y')

# Plot 4: Erreur par trafic réel (bins)
ax4 = axes[1, 1]
df_valid['traffic_bin'] = pd.cut(df_valid['bike_count'], bins=[0, 10, 50, 100, 200, 1000, 10000], 
                                   labels=['0-10', '10-50', '50-100', '100-200', '200-1000', '1000+'])
bin_errors = df_valid.groupby('traffic_bin', observed=True)['abs_residual'].mean()
ax4.bar(range(len(bin_errors)), bin_errors.values, color='coral', edgecolor='black')
ax4.set_xticks(range(len(bin_errors)))
ax4.set_xticklabels(bin_errors.index, rotation=45)
ax4.set_xlabel('Trafic réel (vélos/h)', fontsize=12)
ax4.set_ylabel('MAE (vélos/h)', fontsize=12)
ax4.set_title('Erreur moyenne par niveau de trafic', fontsize=14, fontweight='bold')
ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plot_path = VISUALIZATIONS_DIR / "error_analysis_v3.png"
plt.savefig(plot_path, dpi=150, bbox_inches='tight')
print(f"   ✅ Graphiques sauvegardés: {plot_path}")
plt.close()

# =====================================================================
# 7. RAPPORT TEXTE
# =====================================================================

print("\n📝 Étape 7: Génération du rapport...")

report_path = VISUALIZATIONS_DIR / "error_analysis_report_v3.txt"
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("RAPPORT D'ANALYSE DES ERREURS - CITYZN v3\n")
    f.write("=" * 80 + "\n\n")
    
    f.write(f"Date de génération: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Dataset: final_dataset_v3.csv\n")
    f.write(f"Échantillons analysés: {len(df_valid):,}\n")
    f.write(f"Edges uniques: {df_valid['edge_id'].nunique()}\n\n")
    
    f.write("MÉTRIQUES GLOBALES\n")
    f.write("-" * 80 + "\n")
    for metric, value in metrics.items():
        f.write(f"{metric:20s}: {value:.2f}\n")
    
    f.write("\n\nANALYSE PAR HEURE\n")
    f.write("-" * 80 + "\n")
    f.write(hourly_errors.to_string())
    
    f.write("\n\nANALYSE PAR JOUR\n")
    f.write("-" * 80 + "\n")
    f.write(daily_errors.to_string())
    
    if 'highway_type_decoded' in df_valid.columns:
        f.write("\n\nANALYSE PAR TYPE DE ROUTE (Top 10)\n")
        f.write("-" * 80 + "\n")
        f.write(highway_errors.head(10).to_string())
    
    if 'has_dedicated_bike_lane' in df_valid.columns:
        f.write("\n\nANALYSE PAR INFRASTRUCTURE CYCLABLE\n")
        f.write("-" * 80 + "\n")
        f.write(bike_lane_errors.to_string())
    
    if 'is_raining' in df_valid.columns:
        f.write("\n\nANALYSE PAR MÉTÉO\n")
        f.write("-" * 80 + "\n")
        f.write(weather_errors.to_string())
    
    f.write("\n\n" + "=" * 80 + "\n")
    f.write("INTERPRÉTATIONS ET RECOMMANDATIONS\n")
    f.write("=" * 80 + "\n\n")
    
    # Interprétations automatiques
    f.write("1. QUALITÉ GLOBALE DU MODÈLE\n")
    if metrics['R2'] > 0.8:
        f.write(f"   ✅ Excellent: R² = {metrics['R2']:.3f} (>0.8)\n")
    elif metrics['R2'] > 0.6:
        f.write(f"   ⚠️  Bon: R² = {metrics['R2']:.3f} (>0.6)\n")
    else:
        f.write(f"   ❌ À améliorer: R² = {metrics['R2']:.3f} (<0.6)\n")
    
    f.write(f"\n2. PRÉCISION\n")
    avg_traffic = df_valid['bike_count'].mean()
    relative_mae = (metrics['MAE'] / avg_traffic) * 100
    f.write(f"   • Erreur moyenne: {metrics['MAE']:.1f} vélos/h\n")
    f.write(f"   • Trafic moyen: {avg_traffic:.1f} vélos/h\n")
    f.write(f"   • Erreur relative: {relative_mae:.1f}%\n")
    
    f.write(f"\n3. RECOMMANDATIONS\n")
    if metrics['R2'] < 0.7:
        f.write("   • Collecter plus de données (temporelles et spatiales)\n")
        f.write("   • Ajouter features: événements, vacances, météo avancée\n")
    if metrics['MAPE'] > 50:
        f.write("   • Modèle peu fiable pour faible trafic (MAPE élevé)\n")
        f.write("   • Filtrer prédictions < 10 vélos/h ou utiliser classification\n")

print(f"   ✅ Rapport sauvegardé: {report_path}")

# =====================================================================
# 8. EXPORT CSV DES ERREURS
# =====================================================================

print("\n💾 Étape 8: Export des erreurs détaillées...")

# Top 100 pires prédictions
worst_predictions = df_valid.nlargest(100, 'abs_residual')[
    ['edge_id', 'timestamp', 'bike_count', 'y_pred', 'residual', 'abs_residual', 
     'hour', 'day_of_week', 'is_weekend', 'is_rush_hour']
].copy()

worst_path = DATA_PREDICTIONS_DIR / "worst_predictions_v3.csv"
worst_predictions.to_csv(worst_path, index=False)
print(f"   ✅ Top 100 pires prédictions: {worst_path}")

# =====================================================================
# 9. RÉSUMÉ FINAL
# =====================================================================

print("\n" + "=" * 80)
print("✅ ANALYSE TERMINÉE!")
print("=" * 80)

print(f"\n📁 Fichiers générés:")
print(f"   1. {plot_path.relative_to(BASE_DIR)}")
print(f"   2. {report_path.relative_to(BASE_DIR)}")
print(f"   3. {worst_path.relative_to(BASE_DIR)}")

print(f"\n🎯 Performance du modèle:")
print(f"   • R² = {metrics['R2']:.3f}")
print(f"   • MAE = {metrics['MAE']:.1f} vélos/h")
print(f"   • MAPE = {metrics['MAPE']:.1f}%")
