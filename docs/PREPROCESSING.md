# Module de Preprocessing

Ce module transforme les données brutes collectées en dataset ML prêt pour l'entraînement.

## 📁 Structure

```
src/preprocessing/
├── create_ml_dataset_v3.py    # 🔧 Script principal de preprocessing
└── README.md                  # 📖 Cette documentation
```

## 🚀 Utilisation

### Prérequis

Assurez-vous d'avoir collecté les données d'abord :

```bash
python src/data_collection/main_data_collection.py
```

### Exécution

```bash
python src/preprocessing/create_ml_dataset_v3.py
```

## 📊 Pipeline de Preprocessing

### 1. Chargement du réseau OSM
- Source : `data/raw/osm/osm_network.json`
- Conversion en GeoDataFrame
- ~60k edges pour Lyon

### 2. Chargement métadonnées capteurs
- Source : `data/raw/bike/bike_sensors_metadata.json`
- Liste des capteurs avec positions GPS
- ~74 capteurs Eco-Counter

### 3. Association spatiale capteurs → edges
- Recherche de l'edge le plus proche pour chaque capteur
- Rayon maximum : 50 mètres
- ~62 edges associés à des capteurs

### 4. Chargement données de comptage
- Source : `data/raw/bike/bike_counters_YYYYMMDD_HHMMSS.json` (fichiers horaires)
- Agrégation de tous les fichiers timestampés
- 7 jours × 24 heures = 168 timestamps

### 5. Enrichissement infrastructure cyclable
- Source : `data/raw/bike/bike_infrastructure.json`
- Calcul distance aux pistes cyclables
- Flag `has_dedicated_bike_lane` si < 20m

### 6. Chargement données météo
- Source : `data/raw/weather/weather_data_YYYYMMDD_HHMMSS.json` (fichier le plus récent)
- Données horaires : température, pluie, vent
- Indicateurs dérivés : `is_raining`, `is_cold`, `is_windy`

### 7. Calcul features edges
- **Géométriques** : longueur, orientation, distance au centre
- **Infrastructure** : type de voie, nb voies, vitesse max, sens unique
- **Cyclable** : pistes dédiées, cycleway OSM, surface, éclairage
- Sauvegarde : `edges_static_v3.gpkg` (GeoPackage)

### 8. Création dataset temporel
- **Scope** : Uniquement edges avec capteurs (training)
- **Dimensions** : ~62 edges × 168 heures = ~10k lignes
- **Features** : temporelles + météo + infrastructure + target

### 9. Lag features
- `bike_count_lag_1h` : comptage 1 heure avant
- `bike_count_lag_24h` : comptage 24 heures avant (même heure J-1)
- `bike_count_rolling_7d` : moyenne mobile 7 jours

### 10. Sauvegarde
- **Dataset final** : `data/processed/final_dataset_v3.csv`
- **Edges statiques** : `data/processed/edges_static_v3.gpkg`

## 📂 Fichiers de Sortie

### final_dataset_v3.csv

Dataset d'entraînement avec colonnes :

**Identifiants**
- `edge_id` : ID unique de l'edge OSM
- `timestamp` : Datetime de la mesure

**Temporel**
- `hour`, `day_of_week`, `is_weekend`
- `is_rush_hour_morning`, `is_rush_hour_evening`

**Météo**
- `temperature_c`, `precipitation_mm`, `wind_speed_kmh`
- `is_raining`, `is_cold`, `is_hot`, `is_windy`

**Infrastructure**
- `highway_type`, `road_category`, `lanes`, `maxspeed_kmh`
- `has_cycleway`, `has_dedicated_bike_lane`, `bike_lane_distance_m`
- `surface_quality`, `is_lit`, `edge_length_m`, `distance_to_center_km`

**Lag features**
- `bike_count_lag_1h`, `bike_count_lag_24h`, `bike_count_rolling_7d`

**Target**
- `bike_count` : Nombre de vélos comptés (target pour ML)

### edges_static_v3.gpkg

GeoPackage avec géométries et features statiques de tous les edges :
- Utilisé pour les prédictions sur zones grises
- Format spatial optimisé pour GeoPandas
- Contient flag `has_real_sensor` pour distinguer training/prédiction

## 🎯 Stratégie Training/Prédiction

### Training (ce script)
- **Edges** : Uniquement ceux avec capteurs (~62)
- **Lignes** : ~10k (manageable)
- **But** : Entraîner le modèle ML

### Prédiction (script séparé)
- **Edges** : Tous les ~60k edges
- **But** : Prédire zones grises sans capteurs
- **Méthode** : Charger modèle + appliquer sur edges_static_v3.gpkg

## 📊 Statistiques Typiques

```
📏 Dimensions:
   • Lignes: ~10,000
   • Colonnes: ~30
   • Edges: ~62
   • Timestamps: 168

🚴 Bike count:
   • Moyenne: ~50-100 vélos/heure
   • Médiane: ~30-60
   • Max: ~400-800 (heures de pointe)

🌦️ Météo:
   • Temp moyenne: ~12-15°C (novembre)
   • % pluie: ~10-20%

🛣️ Infrastructure:
   • ~30-40% edges avec piste cyclable
```

## 🔄 Workflow Complet

```bash
# 1. Collecte des données
python src/data_collection/main_data_collection.py

# 2. Preprocessing
python src/preprocessing/create_ml_dataset_v3.py

# 3. Entraînement (étape suivante)
python src/models/train_model.py

# 4. Prédiction zones grises (étape suivante)
python src/models/predict_gray_zones.py
```

## 🗑️ Fichiers Supprimés

Les anciens scripts ont été supprimés lors de la migration :
- ❌ `create_ml_dataset.py` (v1 - monolithique)
- ❌ `create_ml_dataset_v2.py` (v2 - partiellement modulaire)
- ❌ `create_traffic_patterns_from_realtime.py` (patterns trafic voiture - non utilisé)
