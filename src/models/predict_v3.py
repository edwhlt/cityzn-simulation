#!/usr/bin/env python3
"""
Script de prédiction CityZN - Version 3
Prédit le trafic vélo pour une date/heure spécifique sur tous les edges

Usage:
  python predict_v3.py --datetime "2025-11-15 08:00"
  python predict_v3.py --datetime "2025-11-15 17:30" --sample 1000
  python predict_v3.py --datetime "2025-11-15 08:00" --output predictions_rush_hour.csv
"""

import pandas as pd
import numpy as np
import geopandas as gpd
from pathlib import Path
import json
from datetime import datetime
import joblib
import argparse
from tqdm import tqdm

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
DATA_PREDICTIONS_DIR = BASE_DIR / "data" / "predictions"
MODELS_DIR = BASE_DIR / "models"

print("=" * 80)
print("🚴 CITYZN - PRÉDICTION v3 (Architecture Modulaire)")
print("=" * 80)

# =====================================================================
# ARGUMENTS
# =====================================================================

parser = argparse.ArgumentParser(description="Prédire le trafic vélo pour une date/heure spécifique")
parser.add_argument('--datetime', type=str, required=True, 
                    help='Date et heure de prédiction (format: "YYYY-MM-DD HH:MM")')
parser.add_argument('--sample', type=int, default=None,
                    help='Nombre d\'edges à prédire (pour test rapide)')
parser.add_argument('--output', type=str, default=None,
                    help='Nom du fichier de sortie (défaut: predictions_YYYYMMDD_HHMMSS.csv)')
args = parser.parse_args()

# Parser la date
try:
    target_datetime = datetime.strptime(args.datetime, "%Y-%m-%d %H:%M")
except ValueError:
    print(f"❌ Format de date invalide. Utilisez: YYYY-MM-DD HH:MM")
    print(f"   Exemple: 2025-11-15 08:00")
    exit(1)

print(f"\n🎯 Prédiction pour: {target_datetime.strftime('%A %d %B %Y à %H:%M')}")

# =====================================================================
# 1. CHARGER MODÈLE ET MÉTADONNÉES
# =====================================================================

print("\n📂 Étape 1: Chargement du modèle...")

model_path = MODELS_DIR / "best_model.joblib"
if not model_path.exists():
    print(f"   ❌ Modèle non trouvé: {model_path}")
    print(f"   💡 Lancez d'abord: python src/models/train_v3.py")
    exit(1)

model = joblib.load(model_path)
print(f"   ✅ Modèle chargé: {model_path}")

features_path = MODELS_DIR / "feature_columns.json"
with open(features_path, 'r') as f:
    feature_cols = json.load(f)
print(f"   ✅ {len(feature_cols)} features")

encoders_path = MODELS_DIR / "label_encoders.joblib"
label_encoders = joblib.load(encoders_path)
print(f"   ✅ Label encoders chargés")

# Afficher métriques du modèle
metrics_path = MODELS_DIR / "metrics.json"
if metrics_path.exists():
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    print(f"\n   📊 Performance du modèle:")
    print(f"      • Type: {metrics['model_type']}")
    print(f"      • R²: {metrics['metrics']['r2']:.3f}")
    print(f"      • MAE: {metrics['metrics']['mae']:.1f} vélos/h")

# =====================================================================
# 2. CHARGER EDGES STATIQUES
# =====================================================================

print("\n🗺️  Étape 2: Chargement edges statiques...")

edges_static_path = DATA_PROCESSED_DIR / "edges_static_v3.gpkg"
if not edges_static_path.exists():
    print(f"   ❌ Edges statiques non trouvés: {edges_static_path}")
    print(f"   💡 Lancez d'abord: python src/preprocessing/create_ml_dataset_v3.py")
    exit(1)

edges = gpd.read_file(edges_static_path)
print(f"   ✅ {len(edges):,} edges chargés")

# Échantillon si demandé
if args.sample:
    sample_size = min(args.sample, len(edges))
    edges = edges.sample(n=sample_size, random_state=42)
    print(f"   📊 Échantillon: {len(edges):,} edges")

# =====================================================================
# 3. CHARGER DONNÉES MÉTÉO
# =====================================================================

print("\n🌤️  Étape 3: Chargement données météo...")

# Chercher fichier météo (timestamped ou unique)
weather_files = list((DATA_RAW_DIR / "weather").glob("weather_data*.json"))
if not weather_files:
    print(f"   ⚠️  Aucune donnée météo trouvée, utilisation de valeurs par défaut")
    weather_df = pd.DataFrame([{
        'timestamp': target_datetime,
        'temperature_c': 15.0,
        'precipitation_mm': 0.0,
        'wind_speed_kmh': 10.0,
        'is_raining': False
    }])
else:
    # Charger toutes les données météo
    weather_data = []
    for file in weather_files:
        with open(file, 'r') as f:
            data = json.load(f)
            # Structure: {metadata: {...}, weather_data: [...]}
            if isinstance(data, dict) and 'weather_data' in data:
                weather_data.extend(data['weather_data'])
            elif isinstance(data, dict) and 'data' in data:
                weather_data.extend(data['data'])
            elif isinstance(data, list):
                weather_data.extend(data)
            else:
                weather_data.append(data)
    
    weather_df = pd.DataFrame(weather_data)
    if 'timestamp' in weather_df.columns:
        weather_df['timestamp'] = pd.to_datetime(weather_df['timestamp'])
    print(f"   ✅ {len(weather_df)} mesures météo chargées")

# Trouver la mesure météo la plus proche de target_datetime
weather_df['time_diff'] = abs((weather_df['timestamp'] - target_datetime).dt.total_seconds())
closest_weather = weather_df.loc[weather_df['time_diff'].idxmin()]

print(f"   📅 Météo pour {closest_weather['timestamp']}:")
print(f"      • Température: {closest_weather['temperature_c']:.1f}°C")
print(f"      • Précipitations: {closest_weather['precipitation_mm']:.1f}mm")
print(f"      • Vent: {closest_weather['wind_speed_kmh']:.1f}km/h")
print(f"      • Pluie: {'Oui' if closest_weather['is_raining'] else 'Non'}")

# =====================================================================
# 4. CRÉER FEATURES TEMPORELLES
# =====================================================================

print("\n⏰ Étape 4: Génération features temporelles...")

# Features temporelles
edges['hour'] = target_datetime.hour
edges['day_of_week'] = target_datetime.weekday()
edges['is_weekend'] = int(target_datetime.weekday() >= 5)
edges['is_rush_hour_morning'] = int(target_datetime.hour in [7, 8, 9])
edges['is_rush_hour_evening'] = int(target_datetime.hour in [17, 18, 19])

print(f"   ✅ Features temporelles:")
print(f"      • Heure: {target_datetime.hour}h")
print(f"      • Jour: {['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][target_datetime.weekday()]}")
print(f"      • Weekend: {'Oui' if edges['is_weekend'].iloc[0] else 'Non'}")
print(f"      • Rush hour matin: {'Oui' if edges['is_rush_hour_morning'].iloc[0] else 'Non'}")
print(f"      • Rush hour soir: {'Oui' if edges['is_rush_hour_evening'].iloc[0] else 'Non'}")

# =====================================================================
# 5. AJOUTER FEATURES MÉTÉO
# =====================================================================

print("\n🌦️  Étape 5: Ajout features météo...")

edges['temperature_c'] = closest_weather['temperature_c']
edges['precipitation_mm'] = closest_weather['precipitation_mm']
edges['wind_speed_kmh'] = closest_weather['wind_speed_kmh']
edges['is_raining'] = int(closest_weather['is_raining'])

# Features météo dérivées (comme dans training)
edges['is_cold'] = int(closest_weather['temperature_c'] < 5)
edges['is_hot'] = int(closest_weather['temperature_c'] > 30)
edges['is_windy'] = int(closest_weather['wind_speed_kmh'] > 30)

print(f"   ✅ Features météo ajoutées")

# =====================================================================
# 6. ENCODER FEATURES CATÉGORIELLES
# =====================================================================

print("\n🔧 Étape 6: Encodage features catégorielles...")

categorical_cols = [
    'highway_type', 'road_category', 'cycleway_type',
    'surface_quality', 'bicycle_access', 'orientation'
]

for col in categorical_cols:
    if col in edges.columns and col in label_encoders:
        # Gérer valeurs inconnues
        edges[col] = edges[col].fillna('unknown')
        
        # Encoder (gérer les valeurs non vues pendant training)
        le = label_encoders[col]
        edges[col] = edges[col].apply(
            lambda x: le.transform([str(x)])[0] if str(x) in le.classes_ else -1
        )

print(f"   ✅ {len(categorical_cols)} colonnes encodées")

# =====================================================================
# 7. PRÉPARER FEATURES POUR PRÉDICTION
# =====================================================================

print("\n📋 Étape 7: Préparation features finales...")

# Vérifier que toutes les features requises sont présentes
missing_features = set(feature_cols) - set(edges.columns)
if missing_features:
    print(f"   ⚠️  Features manquantes: {missing_features}")
    # Ajouter avec valeurs par défaut
    for feat in missing_features:
        if 'lag' in feat or 'rolling' in feat:
            edges[feat] = 0  # Pas de données historiques pour prédiction future
        else:
            edges[feat] = 0

# Extraire X dans le bon ordre
X = edges[feature_cols].copy()

# Remplir NaN
numeric_cols = X.select_dtypes(include=[np.number]).columns
X[numeric_cols] = X[numeric_cols].fillna(X[numeric_cols].median())
X = X.fillna(0)

print(f"   ✅ {len(X):,} lignes × {len(feature_cols)} features prêtes")

# =====================================================================
# 8. PRÉDICTION
# =====================================================================

print("\n🔮 Étape 8: Prédiction en cours...")

predictions = model.predict(X)
edges['bike_count_predicted'] = predictions

# Arrondir et s'assurer que c'est positif
edges['bike_count_predicted'] = edges['bike_count_predicted'].clip(lower=0).round(0).astype(int)

print(f"   ✅ Prédictions effectuées")
print(f"\n   📊 Statistiques des prédictions:")
print(f"      • Moyenne: {edges['bike_count_predicted'].mean():.1f} vélos/h")
print(f"      • Médiane: {edges['bike_count_predicted'].median():.0f} vélos/h")
print(f"      • Min: {edges['bike_count_predicted'].min():.0f} vélos/h")
print(f"      • Max: {edges['bike_count_predicted'].max():.0f} vélos/h")

# =====================================================================
# 9. SAUVEGARDE RÉSULTATS
# =====================================================================

print("\n💾 Étape 9: Sauvegarde des résultats...")

# Timestamp pour fichier
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Nom fichier de sortie
if args.output:
    output_filename = args.output
else:
    output_filename = f"predictions_{timestamp}.csv"

# CSV avec colonnes essentielles
output_cols = [
    'osm_id', 'bike_count_predicted', 'highway_type', 'road_category',
    'edge_length_m', 'has_dedicated_bike_lane', 'bike_lane_distance_m',
    'distance_to_center_km', 'hour', 'day_of_week', 'is_weekend', 'is_rush_hour_morning', 'is_rush_hour_evening',
    'temperature_c', 'precipitation_mm', 'is_raining'
]

# Filtrer colonnes existantes
output_cols_existing = [col for col in output_cols if col in edges.columns]

predictions_csv = DATA_PREDICTIONS_DIR / output_filename
edges[output_cols_existing].to_csv(predictions_csv, index=False)
print(f"   ✅ CSV sauvegardé: {predictions_csv}")

# GeoJSON pour visualisation
output_geojson = output_filename.replace('.csv', '.geojson')
predictions_geojson = DATA_PREDICTIONS_DIR / output_geojson

# Préparer GeoDataFrame pour export
edges_export = edges[output_cols_existing + ['geometry']].copy()
edges_export.to_file(predictions_geojson, driver='GeoJSON')
print(f"   ✅ GeoJSON sauvegardé: {predictions_geojson}")

# Métadonnées
metadata = {
    'prediction_datetime': target_datetime.isoformat(),
    'generated_at': datetime.now().isoformat(),
    'model_path': str(model_path.relative_to(BASE_DIR)),
    'n_edges': len(edges),
    'weather': {
        'temperature_c': float(closest_weather['temperature_c']),
        'precipitation_mm': float(closest_weather['precipitation_mm']),
        'wind_speed_kmh': float(closest_weather['wind_speed_kmh']),
        'is_raining': bool(closest_weather['is_raining'])
    },
    'temporal': {
        'hour': int(target_datetime.hour),
        'day_of_week': int(target_datetime.weekday()),
        'is_weekend': bool(target_datetime.weekday() >= 5),
        'is_rush_hour_morning': bool(target_datetime.hour in [7, 8, 9]),
        'is_rush_hour_evening': bool(target_datetime.hour in [17, 18, 19])
    },
    'statistics': {
        'mean': float(edges['bike_count_predicted'].mean()),
        'median': float(edges['bike_count_predicted'].median()),
        'min': int(edges['bike_count_predicted'].min()),
        'max': int(edges['bike_count_predicted'].max()),
        'total': int(edges['bike_count_predicted'].sum())
    }
}

metadata_filename = output_filename.replace('.csv', '_metadata.json')
metadata_path = DATA_PREDICTIONS_DIR / metadata_filename
with open(metadata_path, 'w') as f:
    json.dump(metadata, f, indent=2)
print(f"   ✅ Métadonnées sauvegardées: {metadata_path}")

# =====================================================================
# 10. RÉSUMÉ FINAL
# =====================================================================

print("\n" + "=" * 80)
print("✅ PRÉDICTION TERMINÉE!")
print("=" * 80)

print(f"\n🎯 Résumé:")
print(f"   • Date/heure: {target_datetime.strftime('%d/%m/%Y à %H:%M')}")
print(f"   • Edges prédits: {len(edges):,}")
print(f"   • Trafic total prédit: {edges['bike_count_predicted'].sum():,} vélos/h")
print(f"   • Trafic moyen: {edges['bike_count_predicted'].mean():.1f} vélos/h/edge")

print(f"\n📁 Fichiers générés:")
print(f"   1. {predictions_csv.relative_to(BASE_DIR)}")
print(f"   2. {predictions_geojson.relative_to(BASE_DIR)}")
print(f"   3. {metadata_path.relative_to(BASE_DIR)}")

print(f"\n🔥 Top 10 edges avec le plus de trafic:")
top_edges = edges.nlargest(10, 'bike_count_predicted')[['osm_id', 'bike_count_predicted', 'highway_type', 'has_dedicated_bike_lane']]
for idx, row in top_edges.iterrows():
    bike_lane = "🚴" if row['has_dedicated_bike_lane'] else "  "
    print(f"   {bike_lane} Edge {row['osm_id']}: {row['bike_count_predicted']:4d} vélos/h ({row['highway_type']})")

print(f"\n💡 Visualisation:")
print(f"   Ouvrir {predictions_geojson.name} dans QGIS ou kepler.gl")
