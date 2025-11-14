# Architecture du Projet - Version 3 (Modulaire)

## 📋 Vue d'Ensemble

Le projet a été réorganisé en architecture modulaire avec des scripts séparés par responsabilité.

## 🗂️ Structure du Projet

```
CityZN/Simulation Python/
├── data/
│   ├── raw/                          # Données brutes collectées
│   │   ├── bike/                     # Données vélo
│   │   │   ├── bike_counters_*.json  # Comptages horaires (timestampés)
│   │   │   ├── bike_sensors_metadata.json
│   │   │   ├── bike_sensors.geojson
│   │   │   ├── bike_infrastructure.json
│   │   │   └── bike_infrastructure_simplified.geojson
│   │   ├── osm/                      # Réseau routier
│   │   │   └── osm_network.json
│   │   └── weather/                  # Données météo
│   │       ├── weather_data_*.json   # Météo horaire (timestampés)
│   │       └── weather_daily_summary.json
│   ├── processed/                    # Données preprocessées
│   │   ├── final_dataset_v3.csv      # Dataset ML training
│   │   └── edges_static_v3.gpkg      # Features edges (GeoPackage)
│   └── predictions/                  # Prédictions du modèle
│       ├── predictions_*.csv
│       └── predictions_*.geojson
├── src/
│   ├── data_collection/              # 📥 Collecte de données
│   │   ├── main_data_collection.py   # 🚀 Orchestrateur
│   │   ├── fetch_bike_counters.py    # 🚴 Compteurs vélo
│   │   ├── fetch_bike_infrastructure.py # 🛤️ Pistes cyclables
│   │   ├── fetch_osm_network.py      # 🗺️ Réseau routier
│   │   └── fetch_weather.py          # 🌤️ Météo
│   ├── preprocessing/                # 🔧 Preprocessing
│   │   └── create_ml_dataset_v3.py   # Dataset ML
│   ├── models/                       # 🤖 Modèles ML
│   │   ├── train_v3.py               # 🎓 Entraînement
│   │   ├── predict_v3.py             # 🔮 Prédiction date/heure
│   │   └── analyze_errors_v3.py      # 📊 Analyse erreurs
│   └── visualization/                # 📊 Visualisation
│       ├── create_visualizations.py
│       ├── export_kepler.py
│       └── export_kepler_geojson.py
├── models/                           # 💾 Modèles entraînés
│   ├── best_model.joblib
│   ├── feature_columns.json
│   ├── label_encoders.joblib
│   └── metrics.json
├── visualizations/                   # 📈 Visualisations générées
└── run.sh                           # 🚀 Script de démarrage rapide
```

## 🔄 Workflow Complet

### 1. Collecte de Données

```bash
# Collecte complète (toutes sources)
python src/data_collection/main_data_collection.py

# Ou individuellement
python src/data_collection/fetch_osm_network.py
python src/data_collection/fetch_bike_infrastructure.py
python src/data_collection/fetch_bike_counters.py
python src/data_collection/fetch_weather.py
```

**Sortie** : Fichiers JSON/GeoJSON dans `data/raw/`

### 2. Preprocessing

```bash
python src/preprocessing/create_ml_dataset_v3.py
```

**Sortie** :
- `data/processed/final_dataset_v3.csv` (dataset training)
- `data/processed/edges_static_v3.gpkg` (features edges)

### 3. Entraînement du Modèle

```bash
python src/models/train_v3.py
```

**Sortie** :
- `models/best_model.joblib`
- `models/feature_columns.json`
- `models/label_encoders.joblib`
- `models/metrics.json`
- `data/predictions/feature_importance.csv`

### 4. Prédiction pour Date/Heure Spécifique

```bash
# Prédire pour demain à 8h
python src/models/predict_v3.py --datetime "2025-11-15 08:00"

# Test rapide sur 1000 edges
python src/models/predict_v3.py --datetime "2025-11-15 08:00" --sample 1000

# Nom personnalisé
python src/models/predict_v3.py --datetime "2025-11-15 17:30" --output rush_soir.csv
```

**Sortie** :
- `data/predictions/predictions_YYYYMMDD_HHMMSS.csv`
- `data/predictions/predictions_YYYYMMDD_HHMMSS.geojson`
- `data/predictions/predictions_YYYYMMDD_HHMMSS_metadata.json`

### 5. Analyse des Erreurs

```bash
python src/models/analyze_errors_v3.py
```

**Sortie** :
- `visualizations/error_analysis_v3.png`
- `visualizations/error_analysis_report_v3.txt`
- `data/predictions/worst_predictions_v3.csv`

## 🔧 Scripts Helper

### Orchestrateur complet

```bash
./run_training.sh
```

Lance automatiquement : entraînement + analyse + prédiction exemple

### 6. Prédictions (Anciennes versions - à migrer)

```bash
# Prédiction sur données de test
python src/models/train_predict.py predict

# Prédiction complète (tous les edges)
python src/models/predict_complete.py

# Prédiction zones grises uniquement
python src/models/predict_gray_zones.py
```

**Sortie** : `data/predictions/predictions_*.csv` et `.geojson`

### 5. Visualisation

```bash
# Export pour Kepler.gl
python src/visualization/export_kepler.py

# Créer visualisations complètes
python src/visualization/create_visualizations.py
```

**Sortie** : `visualizations/*.html`, `.csv`, `.geojson`

## 📊 Types de Données

### Données Brutes

| Source | Format | Fréquence | Timestamp |
|--------|--------|-----------|-----------|
| Compteurs vélo | JSON | Horaire | ✅ Oui |
| Capteurs metadata | JSON | Unique | ❌ Non (mis à jour) |
| Pistes cyclables | JSON/GeoJSON | Unique | ❌ Non (écrasé) |
| Réseau OSM | JSON/GeoJSON | Unique | ❌ Non (écrasé) |
| Météo | JSON | Horaire | ✅ Oui |

### Données Processées

| Fichier | Description | Format |
|---------|-------------|--------|
| `final_dataset_v3.csv` | Dataset training (~10k lignes) | CSV |
| `edges_static_v3.gpkg` | Features edges (~60k edges) | GeoPackage |

### Prédictions

| Fichier | Description | Contenu |
|---------|-------------|---------|
| `predictions_complete_*.csv` | Prédictions tous edges | edge_id, timestamp, prediction |
| `predictions_spatial_*.geojson` | Prédictions géospatialisées | LineString + prédictions |
| `predictions_gray_zones_*.csv` | Prédictions zones sans capteurs | Edges non observés |

## 🎯 Philosophie de l'Architecture

### Séparation des Responsabilités

1. **Collecte** (`data_collection/`) : Un script par source de données
2. **Preprocessing** (`preprocessing/`) : Transformation raw → ML dataset
3. **Modèles** (`models/`) : Training, prédiction, analyse
4. **Visualisation** (`visualization/`) : Export et graphiques

### Stratégie de Stockage

- **Timestampé** : Données temporelles (météo, comptages)
- **Écrasé** : Données structurelles (réseau, infrastructures)

### Scope Training vs Prédiction

- **Training** : Edges avec capteurs uniquement (~62 edges)
- **Prédiction** : Tous les edges (~60k edges)

## 🗑️ Fichiers Supprimés (Migration v3)

### Data Collection
- ❌ `fetch_lyon_data.py` (remplacé par scripts modulaires)

### Preprocessing
- ❌ `create_ml_dataset.py` (v1)
- ❌ `create_ml_dataset_v2.py` (v2)
- ❌ `create_traffic_patterns_from_realtime.py` (non utilisé)

### Models
- ❌ `predict_complete_BROKEN.py` (fichier cassé)

## 📝 Conventions de Nommage

### Fichiers Timestampés

Format : `{nom}_{YYYYMMDD}_{HHMMSS}.{ext}`

Exemple : `bike_counters_20251114_153042.json`

### Versions

Les fichiers avec version incluent le numéro : `final_dataset_v3.csv`

### GeoJSON vs JSON

- `.json` : Données tabulaires avec métadonnées
- `.geojson` : Données géospatiales (GeoJSON standard)
- `.gpkg` : Données géospatiales optimisées (GeoPackage)

## 🚀 Quick Start

```bash
# 1. Tout collecter et traiter
python src/data_collection/main_data_collection.py
python src/preprocessing/create_ml_dataset_v3.py

# 2. Entraîner
python src/models/train_predict.py train

# 3. Prédire
python src/models/train_predict.py predict

# 4. Visualiser
python src/visualization/export_kepler.py
```

Ou utiliser le script de démarrage :

```bash
./run.sh
```

## 📚 Documentation

- `src/data_collection/README.md` : Détails collecte de données
- `src/preprocessing/README.md` : Détails preprocessing
- Ce fichier : Vue d'ensemble architecture
