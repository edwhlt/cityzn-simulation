#!/usr/bin/env python3
"""
Création dataset ML - Version 3 (Architecture modulaire)
Adapté à la nouvelle structure d'ingestion avec scripts séparés par source

Sources:
1. OSM network (data/raw/osm/osm_network.json)
2. Bike counters (data/raw/bike/bike_counters_YYYYMMDD_HHMMSS.json) - fichiers horaires
3. Bike sensors metadata (data/raw/bike/bike_sensors_metadata.json)
4. Bike infrastructure (data/raw/bike/bike_infrastructure.json)
5. Weather (data/raw/weather/weather_data_YYYYMMDD_HHMMSS.json) - fichiers horaires

Dataset de sortie:
- Training: edges avec capteurs uniquement (pour entraînement)
- Les zones grises seront prédites par le script de prédiction
"""

import json
import pandas as pd
import geopandas as gpd
from pathlib import Path
from datetime import datetime
import numpy as np
from shapely.geometry import Point
import warnings
warnings.filterwarnings('ignore')

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
DATA_PROCESSED_DIR.mkdir(exist_ok=True)

print("="*80)
print("🔧 CRÉATION DATASET ML - VERSION 3 (Architecture Modulaire)")
print("="*80)

# =====================================================================
# ÉTAPE 1: CHARGER RÉSEAU OSM
# =====================================================================

print("\n📍 Étape 1: Chargement réseau OSM...")

osm_file = DATA_RAW_DIR / "osm" / "osm_network.json"
if not osm_file.exists():
    print(f"❌ Fichier OSM manquant: {osm_file}")
    print("💡 Exécuter d'abord: python src/data_collection/fetch_osm_network.py")
    exit(1)

with open(osm_file, 'r') as f:
    osm_data = json.load(f)

edges_gdf = gpd.GeoDataFrame.from_features(
    osm_data['geojson']['features'],
    crs="EPSG:4326"
)

print(f"   ✅ {len(edges_gdf)} edges OSM chargés")

# =====================================================================
# ÉTAPE 2: CHARGER MÉTADONNÉES DES CAPTEURS VÉLO
# =====================================================================

print("\n🚴 Étape 2: Chargement métadonnées capteurs vélo...")

sensors_file = DATA_RAW_DIR / "bike" / "bike_sensors_metadata.json"
if not sensors_file.exists():
    print(f"❌ Fichier capteurs manquant: {sensors_file}")
    print("💡 Exécuter d'abord: python src/data_collection/fetch_bike_counters.py")
    exit(1)

with open(sensors_file, 'r') as f:
    sensors_data = json.load(f)

sensors_info = sensors_data['sensors']
print(f"   ✅ {len(sensors_info)} capteurs chargés")

# =====================================================================
# ÉTAPE 3: ASSOCIATION SPATIALE CAPTEURS → EDGES
# =====================================================================

print("\n🗺️  Étape 3: Association spatiale capteurs → edges...")

# Créer GeoDataFrame des capteurs
sensors_list = []
for counter_id, info in sensors_info.items():
    if info['lat'] and info['lon']:
        sensors_list.append({
            'counter_id': counter_id,
            'name': info['name'],
            'geometry': Point(info['lon'], info['lat'])
        })

sensors_gdf = gpd.GeoDataFrame(sensors_list, crs="EPSG:4326")
print(f"   • {len(sensors_gdf)} capteurs avec coordonnées")

# Convertir en Lambert 93 pour calculs de distance
edges_lam = edges_gdf.to_crs("EPSG:2154")
sensors_lam = sensors_gdf.to_crs("EPSG:2154")

# Association capteur → edge (rayon 50m)
sensor_to_edge = {}
MAX_DISTANCE = 50

for idx, sensor in sensors_lam.iterrows():
    distances = edges_lam.geometry.distance(sensor.geometry)
    min_dist_idx = distances.idxmin()
    min_dist = distances[min_dist_idx]
    
    if min_dist <= MAX_DISTANCE:
        edge_osm_id = edges_lam.loc[min_dist_idx, 'osm_id']
        sensor_to_edge[sensor['counter_id']] = {
            'edge_id': edge_osm_id,
            'distance_m': round(min_dist, 1),
            'sensor_name': sensor['name']
        }

print(f"   ✅ {len(sensor_to_edge)} capteurs associés à des edges (≤{MAX_DISTANCE}m)")

edges_with_sensors = list(set(info['edge_id'] for info in sensor_to_edge.values()))
print(f"   ✅ {len(edges_with_sensors)} edges uniques avec capteurs")

# =====================================================================
# ÉTAPE 4: CHARGER DONNÉES DE COMPTAGE VÉLO (fichiers horaires)
# =====================================================================

print("\n📊 Étape 4: Chargement données de comptage vélo...")

bike_data_dir = DATA_RAW_DIR / "bike"
bike_counter_files = sorted(bike_data_dir.glob("bike_counters_*.json"))

if not bike_counter_files:
    print(f"❌ Aucun fichier de comptage trouvé dans {bike_data_dir}")
    print("💡 Exécuter d'abord: python src/data_collection/fetch_bike_counters.py")
    exit(1)

print(f"   • {len(bike_counter_files)} fichiers de comptage trouvés")

# Charger tous les fichiers horaires
all_bike_records = []
for bike_file in bike_counter_files:
    try:
        with open(bike_file, 'r') as f:
            data = json.load(f)
            records = data.get('records', [])
            all_bike_records.extend(records)
    except Exception as e:
        print(f"   ⚠️  Erreur lecture {bike_file.name}: {e}")

bike_df = pd.DataFrame(all_bike_records)
bike_df['timestamp'] = pd.to_datetime(bike_df['timestamp'])

# Associer edges
bike_df['edge_id'] = bike_df['counter_id'].map(
    lambda x: sensor_to_edge.get(x, {}).get('edge_id')
)
bike_df = bike_df[bike_df['edge_id'].notna()].copy()

print(f"   ✅ {len(bike_df):,} mesures chargées")
print(f"   📅 Période: {bike_df['timestamp'].min()} → {bike_df['timestamp'].max()}")

# =====================================================================
# ÉTAPE 5: ENRICHIR AVEC INFRASTRUCTURE CYCLABLE
# =====================================================================

print("\n🚲 Étape 5: Enrichissement infrastructure cyclable...")

bike_infra_file = DATA_RAW_DIR / "bike" / "bike_infrastructure.json"

if bike_infra_file.exists():
    with open(bike_infra_file, 'r') as f:
        bike_infra_data = json.load(f)
    
    bike_lines_gdf = gpd.GeoDataFrame.from_features(
        bike_infra_data['geojson']['features'],
        crs="EPSG:4171"  # RGF93
    ).to_crs("EPSG:2154")
    
    print(f"   • Calcul distances pistes cyclables (spatial join optimisé)...")
    
    # Méthode optimisée : spatial join avec buffer
    # Créer un buffer de 20m autour des pistes cyclables
    bike_lines_buffered = bike_lines_gdf.copy()
    bike_lines_buffered['geometry'] = bike_lines_buffered.geometry.buffer(20)
    
    # Spatial join : edges qui intersectent le buffer ont une piste à <20m
    edges_with_lanes = gpd.sjoin(
        edges_lam,
        bike_lines_buffered[['geometry']],
        how='left',
        predicate='intersects'
    )
    
    # Gérer les duplicatas : un edge peut intersecter plusieurs bike lanes
    # On ne garde que l'info binaire (a ou n'a pas de bike lane proche)
    edges_with_bike_lane = edges_with_lanes[edges_with_lanes['index_right'].notna()].index.unique()
    edges_gdf['has_dedicated_bike_lane'] = False
    edges_gdf.loc[edges_with_bike_lane, 'has_dedicated_bike_lane'] = True
    
    # Pour la distance exacte, on le fait seulement pour les edges AVEC capteurs (optimisation)
    edges_with_sensors_set = set(edges_with_sensors)
    edges_gdf['bike_lane_distance_m'] = 999999.0
    
    print(f"   • Calcul distances exactes pour edges avec capteurs...")
    for idx, row in edges_lam[edges_lam['osm_id'].isin(edges_with_sensors_set)].iterrows():
        distances = bike_lines_gdf.geometry.distance(row.geometry)
        if len(distances) > 0:
            edges_gdf.at[idx, 'bike_lane_distance_m'] = distances.min()
    
    bike_lane_count = edges_gdf['has_dedicated_bike_lane'].sum()
    print(f"   ✅ {bike_lane_count} edges avec piste cyclable dédiée (<20m)")
else:
    print("   ⚠️  Infrastructure cyclable non trouvée, skip")
    edges_gdf['has_dedicated_bike_lane'] = False
    edges_gdf['bike_lane_distance_m'] = 999999.0

# =====================================================================
# ÉTAPE 6: CHARGER DONNÉES MÉTÉO (fichiers horaires)
# =====================================================================

print("\n🌤️  Étape 6: Chargement données météo...")

weather_data_dir = DATA_RAW_DIR / "weather"

# Chercher d'abord fichiers timestampés, sinon fichier unique
weather_files = sorted(weather_data_dir.glob("weather_data_*.json"))

if weather_files:
    # Prendre le fichier le plus récent (timestampé)
    weather_file = weather_files[-1]
    print(f"   • Utilisation: {weather_file.name}")
else:
    # Essayer fichier unique (ancien format)
    weather_file = weather_data_dir / "weather_data.json"
    if not weather_file.exists():
        print(f"❌ Aucun fichier météo trouvé dans {weather_data_dir}")
        print("💡 Exécuter d'abord: python src/data_collection/fetch_weather.py")
        exit(1)
    print(f"   • Utilisation: {weather_file.name}")

with open(weather_file, 'r') as f:
    weather_data = json.load(f)

weather_df = pd.DataFrame(weather_data['weather_data'])
weather_df['timestamp'] = pd.to_datetime(weather_df['timestamp'])

print(f"   ✅ {len(weather_df)} mesures météo horaires")

# =====================================================================
# ÉTAPE 7: CALCULER FEATURES EDGES (TOUS)
# =====================================================================

print("\n🔧 Étape 7: Calcul features edges...")

# Marquer edges avec capteurs
edges_gdf['has_real_sensor'] = edges_gdf['osm_id'].isin(edges_with_sensors)

# Convertir en Lambert 93
edges_lam = edges_gdf.to_crs("EPSG:2154")

# Distance au centre (Place Bellecour)
center_point = gpd.GeoDataFrame(
    geometry=[Point(4.8320, 45.7578)],
    crs="EPSG:4326"
).to_crs("EPSG:2154").iloc[0].geometry

edges_gdf['distance_to_center_km'] = (
    edges_lam.geometry.distance(center_point) / 1000
)

# Longueur edge
edges_gdf['edge_length_m'] = edges_lam.geometry.length

# Orientation
def calc_orientation(geom):
    coords = list(geom.coords)
    if len(coords) < 2:
        return None
    dx = coords[-1][0] - coords[0][0]
    dy = coords[-1][1] - coords[0][1]
    angle = np.degrees(np.arctan2(dy, dx))
    if angle < 0:
        angle += 360
    
    # Catégoriser
    if angle < 22.5 or angle >= 337.5:
        return 'E'
    elif angle < 67.5:
        return 'NE'
    elif angle < 112.5:
        return 'N'
    elif angle < 157.5:
        return 'NW'
    elif angle < 202.5:
        return 'W'
    elif angle < 247.5:
        return 'SW'
    elif angle < 292.5:
        return 'S'
    else:
        return 'SE'

edges_gdf['orientation'] = edges_lam.geometry.apply(calc_orientation)

# Attributs OSM
edges_gdf['highway_type'] = edges_gdf['highway'].fillna('unknown')

def categorize_road(highway_type):
    if highway_type in ['motorway', 'trunk']:
        return 'major'
    elif highway_type in ['primary', 'secondary']:
        return 'arterial'
    elif highway_type in ['tertiary', 'residential']:
        return 'local'
    elif highway_type in ['cycleway', 'path']:
        return 'bike_path'
    else:
        return 'other'

edges_gdf['road_category'] = edges_gdf['highway_type'].apply(categorize_road)

edges_gdf['maxspeed_kmh'] = edges_gdf['maxspeed'].apply(
    lambda x: int(x) if pd.notna(x) and str(x).isdigit() else 50
)

edges_gdf['lanes'] = edges_gdf['lanes'].apply(
    lambda x: int(x) if pd.notna(x) and str(x).isdigit() else 2
)

edges_gdf['is_oneway'] = edges_gdf['oneway'] == 'yes'
edges_gdf['cycleway_type'] = edges_gdf['cycleway'].fillna('none')

def categorize_surface(surface):
    if pd.isna(surface):
        return 'unknown'
    surface = str(surface).lower()
    if surface in ['asphalt', 'paved']:
        return 'good'
    elif surface in ['concrete', 'paving_stones']:
        return 'medium'
    else:
        return 'poor'

edges_gdf['surface_quality'] = edges_gdf['surface'].apply(categorize_surface)
edges_gdf['bicycle_access'] = edges_gdf['bicycle'].fillna('yes')
edges_gdf['is_lit'] = edges_gdf['lit'] == 'yes'
edges_gdf['has_cycleway'] = edges_gdf['cycleway'].notna()

print(f"   ✅ Features calculées pour {len(edges_gdf)} edges")

# Sauvegarder edges statiques
edges_static = edges_gdf[[
    'osm_id', 'name', 'highway_type', 'road_category', 'lanes', 'maxspeed_kmh',
    'is_oneway', 'has_cycleway', 'cycleway_type', 'has_dedicated_bike_lane',
    'bike_lane_distance_m', 'surface_quality', 'bicycle_access', 'is_lit',
    'edge_length_m', 'distance_to_center_km', 'orientation', 'geometry', 'has_real_sensor'
]].copy()

edges_static_path = DATA_PROCESSED_DIR / "edges_static_v3.gpkg"
edges_static.to_file(edges_static_path, driver="GPKG")
print(f"   ✅ Edges statiques sauvegardés: {edges_static_path.name}")

# =====================================================================
# ÉTAPE 8: CRÉER DATASET TEMPOREL (edges avec capteurs uniquement)
# =====================================================================

print("\n📊 Étape 8: Création dataset temporel (training)...")

# Obtenir timestamps uniques
timestamps = sorted(bike_df['timestamp'].unique())
print(f"   • {len(timestamps)} timestamps uniques")
print(f"   • {len(edges_with_sensors)} edges avec capteurs")
print(f"   • Dataset: {len(edges_with_sensors)} × {len(timestamps)} = {len(edges_with_sensors) * len(timestamps):,} lignes")

# Lookup dictionnaires pour optimisation
edges_dict = {}
for idx, row in edges_gdf.iterrows():
    edges_dict[row['osm_id']] = row.to_dict()

bike_lookup = {}
for _, row in bike_df.iterrows():
    key = (row['edge_id'], row['timestamp'])
    if key not in bike_lookup:
        bike_lookup[key] = 0
    bike_lookup[key] += row['count']

# Générer dataset
dataset_rows = []

print(f"   • Génération en cours...")

for idx, ts in enumerate(timestamps):
    if idx % 24 == 0:
        print(f"      Jour {idx//24 + 1}/{len(timestamps)//24}...")
    
    # Météo pour ce timestamp
    weather_row = weather_df[weather_df['timestamp'] == ts]
    if len(weather_row) == 0:
        weather_row = weather_df.iloc[weather_df['timestamp'].searchsorted(ts) - 1]
    else:
        weather_row = weather_row.iloc[0]
    
    # Pour chaque edge avec capteur
    for edge_id in edges_with_sensors:
        bike_count = bike_lookup.get((edge_id, ts), None)
        edge_row = edges_dict[edge_id]
        
        row = {
            # Identifiants
            'edge_id': edge_id,
            'timestamp': ts,
            
            # Temporel
            'hour': ts.hour,
            'day_of_week': ts.weekday(),
            'is_weekend': ts.weekday() >= 5,
            'is_rush_hour_morning': 7 <= ts.hour <= 9,
            'is_rush_hour_evening': 17 <= ts.hour <= 19,
            
            # Météo
            'temperature_c': weather_row['temperature_c'],
            'precipitation_mm': weather_row['precipitation_mm'],
            'wind_speed_kmh': weather_row['wind_speed_kmh'],
            'is_raining': weather_row['is_raining'],
            'is_cold': weather_row['temperature_c'] < 10 if pd.notna(weather_row['temperature_c']) else False,
            'is_hot': weather_row['temperature_c'] > 25 if pd.notna(weather_row['temperature_c']) else False,
            'is_windy': weather_row['wind_speed_kmh'] > 20 if pd.notna(weather_row['wind_speed_kmh']) else False,
            
            # Infrastructure edge
            'highway_type': edge_row['highway_type'],
            'road_category': edge_row['road_category'],
            'lanes': edge_row['lanes'],
            'maxspeed_kmh': edge_row['maxspeed_kmh'],
            'has_cycleway': edge_row['has_cycleway'],
            'has_dedicated_bike_lane': edge_row['has_dedicated_bike_lane'],
            'bike_lane_distance_m': edge_row['bike_lane_distance_m'],
            'surface_quality': edge_row['surface_quality'],
            'is_lit': edge_row['is_lit'],
            'edge_length_m': edge_row['edge_length_m'],
            'distance_to_center_km': edge_row['distance_to_center_km'],
            'orientation': edge_row['orientation'],
            
            # Target
            'bike_count': bike_count
        }
        
        dataset_rows.append(row)

final_df = pd.DataFrame(dataset_rows)

print(f"   ✅ Dataset créé: {len(final_df):,} lignes")

# =====================================================================
# ÉTAPE 9: LAG FEATURES
# =====================================================================

print("\n🔁 Étape 9: Calcul lag features...")

final_df = final_df.sort_values(['edge_id', 'timestamp'])

final_df['bike_count_lag_1h'] = final_df.groupby('edge_id')['bike_count'].shift(1)
final_df['bike_count_lag_24h'] = final_df.groupby('edge_id')['bike_count'].shift(24)
final_df['bike_count_rolling_7d'] = (
    final_df.groupby('edge_id')['bike_count']
    .transform(lambda x: x.rolling(window=168, min_periods=1).mean())
)

print(f"   ✅ Lag features calculés")

# =====================================================================
# ÉTAPE 10: SAUVEGARDER
# =====================================================================

print("\n💾 Étape 10: Sauvegarde...")

output_path = DATA_PROCESSED_DIR / "final_dataset_v3.csv"
final_df.to_csv(output_path, index=False)

print(f"   ✅ Dataset sauvegardé: {output_path.name}")

# Statistiques finales
print("\n" + "="*80)
print("📊 STATISTIQUES FINALES")
print("="*80)

print(f"\n📏 Dimensions:")
print(f"   • Lignes: {len(final_df):,}")
print(f"   • Colonnes: {len(final_df.columns)}")
print(f"   • Edges: {final_df['edge_id'].nunique()}")
print(f"   • Timestamps: {final_df['timestamp'].nunique()}")

print(f"\n🚴 Bike count:")
rows_with_data = final_df['bike_count'].notna().sum()
print(f"   • Lignes avec données: {rows_with_data:,}")
if rows_with_data > 0:
    print(f"   • Moyenne: {final_df['bike_count'].mean():.1f} vélos/heure")
    print(f"   • Médiane: {final_df['bike_count'].median():.1f}")
    print(f"   • Max: {final_df['bike_count'].max():.0f}")

print(f"\n🌦️  Météo:")
print(f"   • Temp moyenne: {final_df['temperature_c'].mean():.1f}°C")
print(f"   • % pluie: {final_df['is_raining'].mean() * 100:.1f}%")

print(f"\n🛣️  Infrastructure:")
print(f"   • Edges avec piste cyclable: {final_df['has_dedicated_bike_lane'].sum():,} lignes")

print("\n" + "="*80)
print("✅ PREPROCESSING TERMINÉ!")
print("="*80)
print(f"\nFichiers générés:")
print(f"   1. {output_path.name}")
print(f"   2. {edges_static_path.name}")
