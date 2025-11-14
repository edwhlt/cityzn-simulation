# CityZN - Prédiction de Trafic Cycliste Urbain

## 🎯 Objectif du Projet

Système de collecte, fusion et prédiction de données de trafic cycliste pour **identifier et combler les zones grises** (zones sans capteurs) à Lyon.

## 🌟 Proposition de Valeur

**Problème** : Les villes ont des données de trafic cycliste fragmentées et incomplètes
- Compteurs vélo uniquement sur certains axes (~74 capteurs pour toute l'agglomération)
- Zones entières sans mesure (zones grises représentant ~99% des edges du réseau)
- Impossible de planifier efficacement les infrastructures cyclables

**Solution** : Notre IA agrège plusieurs sources et prédit les valeurs manquantes
- Fusion intelligente de 4 sources de données (compteurs vélo, réseau OSM, pistes cyclables, météo)
- Prédiction du trafic sur les ~60k edges du réseau
- Cartographie complète du trafic cycliste urbain

## 📊 Sources de Données

### 1. **Compteurs Vélo** (Eco-Counter via API Eco-Visio)
- 🎯 Apport : Flux cyclistes horaires réels
- 📍 Couverture : ~74 capteurs (62 associés à des edges OSM)
- 🔄 Fréquence : Horaire (7 derniers jours)
- 📦 Format : JSON timestampé par heure

### 2. **Infrastructure Cyclable** (Grand Lyon Open Data)
- 🎯 Apport : Pistes cyclables, voies vertes, bandes cyclables
- 📍 Couverture : Métropole de Lyon
- 🔄 Fréquence : Mise à jour régulière
- 📦 Format : GeoJSON

### 3. **Réseau Routier** (OpenStreetMap via Overpass)
- 🎯 Apport : Géométrie complète + attributs (vitesse, voies, sens)
- 📍 Couverture : ~60k edges pour Lyon
- 🔄 Fréquence : Statique (mise à jour à la demande)
- 📦 Format : GeoJSON

### 4. **Météo** (Open-Meteo Archive API)
- 🎯 Apport : Impact majeur sur trafic vélo (-40% à -70% sous la pluie)
- 📊 Variables : température, précipitations, vent
- 🔄 Fréquence : Horaire (7 derniers jours)
- 📦 Format : JSON timestampé

## 🔬 Méthodologie

### Architecture Modulaire v3

Le projet suit une architecture modulaire en 4 étapes :

### 1. Collecte de Données
```bash
python src/data_collection/main_data_collection.py
```

Scripts individuels disponibles :
- `fetch_bike_counters.py` - Compteurs vélo (API Eco-Visio)
- `fetch_bike_infrastructure.py` - Pistes cyclables (Grand Lyon)
- `fetch_osm_network.py` - Réseau routier (Overpass API)
- `fetch_weather.py` - Météo (Open-Meteo)

### 2. Preprocessing
```bash
python src/preprocessing/create_ml_dataset_v3.py
```

Transforme les données brutes en dataset ML :
- Association spatiale capteurs → edges (≤50m)
- Enrichissement infrastructure (pistes cyclables, distance)
- Features temporelles + météo + géométriques
- Lag features (trafic historique)

**Sortie** : 
- `final_dataset_v3.csv` (~11k lignes, 68 edges avec capteurs)
- `edges_static_v3.gpkg` (60k edges avec features)

### 3. Entraînement ML
```bash
python src/models/train_v3.py
```

Compare 3 modèles (RandomForest, GradientBoosting, Ridge) et sélectionne le meilleur.

**Performance actuelle** :
- **R² = 0.873** (87% de variance expliquée)
- **MAE = 28.5 vélos/h**
- Top features : lag_1h (42%), rolling_7d (16%), lag_24h (14%)

### 4. Prédiction pour Date/Heure Spécifique ⭐
```bash
# Prédire pour demain à 8h
python src/models/predict_v3.py --datetime "2025-11-15 08:00"

# Test rapide sur 1000 edges
python src/models/predict_v3.py --datetime "2025-11-15 17:30" --sample 1000
```

Prédit le trafic vélo sur **tous les 60k edges** pour n'importe quelle date/heure

**Sorties** :
- CSV avec prédictions + features
- GeoJSON pour visualisation (QGIS, Kepler.gl)
- Métadonnées JSON (météo, statistiques, contexte)

## 📈 Résultats v3

### Performance du Modèle
- ✅ **R² = 0.873** (excellent)
- ✅ **MAE = 28.5 vélos/h** (erreur moyenne absolue)
- ✅ **RMSE = 59.7 vélos/h**

### Couverture
- 🎓 **Training** : 68 edges avec capteurs réels (~11k mesures)
- 🔮 **Prédiction** : 60,566 edges du réseau complet de Lyon
- 📊 **Features** : 27 features (temporelles, météo, infrastructure, historiques)

### Top Features Importantes
1. **bike_count_lag_1h** (42%) - Trafic 1h avant
2. **bike_count_rolling_7d** (16%) - Moyenne 7 jours
3. **bike_count_lag_24h** (14%) - Même heure veille
4. **hour** (5%) - Heure de la journée
5. **distance_to_center_km** (4%) - Distance au centre

## 🛠️ Installation et Utilisation

### Installation

```bash
# Créer environnement virtuel
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Installer dépendances
pip install -r requirements.txt
```

### Utilisation Rapide - Pipeline Complet

```bash
# 1. Collecter les données (compteurs vélo, réseau OSM, pistes, météo)
python src/data_collection/main_data_collection.py

# 2. Preprocessing (créer dataset ML)
python src/preprocessing/create_ml_dataset_v3.py

# 3. Entraîner le modèle
python src/models/train_v3.py

# 4. Prédire pour une date/heure spécifique
python src/models/predict_v3.py --datetime "2025-11-15 08:00"

# 5. Analyser les erreurs (optionnel)
python src/models/analyze_errors_v3.py
```

### Scripts Helper

```bash
# Preprocessing avec validation
./run_preprocessing.sh

# Pipeline ML complet (entraînement + analyse + prédiction exemple)
./run_training.sh
```

### Exemples de Prédiction

```bash
# Prédire demain matin 8h (rush hour)
python src/models/predict_v3.py --datetime "2025-11-15 08:00"

# Prédire vendredi soir 18h (rush hour)
python src/models/predict_v3.py --datetime "2025-11-22 18:00"

# Test rapide sur 1000 edges
python src/models/predict_v3.py --datetime "2025-11-15 08:00" --sample 1000

# Nom de fichier personnalisé
python src/models/predict_v3.py --datetime "2025-11-15 17:30" --output rush_vendredi_soir.csv
```

**� Documentation complète** : Voir dossier [docs/](docs/)
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Architecture du projet v3
- [DATA_COLLECTION.md](docs/DATA_COLLECTION.md) - Guide collecte de données
- [PREPROCESSING.md](docs/PREPROCESSING.md) - Guide preprocessing
- [ML_MODELS.md](docs/ML_MODELS.md) - Guide ML (entraînement, prédiction, analyse)
- [MIGRATION_V3.md](docs/MIGRATION_V3.md) - Migration vers v3

## � Structure du Projet

```
.
├── README.md                      # Ce fichier
├── QUICKSTART.md                  # Guide de démarrage rapide
├── requirements.txt               # Dépendances Python
├── run.sh                         # Script de lancement
├── docs/                          # 📚 Documentation complète
│   ├── README.md                  # Index de la documentation
│   ├── ARCHITECTURE.md            # Architecture du projet
│   ├── DATA_COLLECTION.md         # Guide collecte de données
│   ├── PREPROCESSING.md           # Guide preprocessing
│   └── MIGRATION_V3.md            # Guide migration v3
├── data/
│   ├── raw/                       # Données brutes collectées
│   │   ├── bike/                  # Compteurs + infrastructure vélo
│   │   ├── osm/                   # Réseau routier OSM
│   │   └── weather/               # Données météo
│   ├── processed/                 # Dataset ML
│   └── predictions/               # Résultats prédictions
├── src/
│   ├── data_collection/           # 📥 Collecte modulaire
│   │   ├── main_data_collection.py      # Orchestrateur
│   │   ├── fetch_bike_counters.py       # Compteurs vélo
│   │   ├── fetch_bike_infrastructure.py # Pistes cyclables
│   │   ├── fetch_osm_network.py         # Réseau OSM
│   │   └── fetch_weather.py             # Météo
│   ├── preprocessing/             # 🔧 Preprocessing
│   │   └── create_ml_dataset_v3.py
│   ├── models/                    # 🤖 ML v3
│   │   ├── train_v3.py            # Entraînement
│   │   ├── predict_v3.py          # Prédiction date/heure
│   │   └── analyze_errors_v3.py   # Analyse erreurs
│   └── visualization/             # 📊 Visualisation
│       └── export_kepler.py
├── models/                        # 💾 Modèles entraînés
│   ├── best_model.joblib          # RandomForest (R²=0.873)
│   ├── feature_columns.json       # 27 features
│   ├── label_encoders.joblib
│   └── metrics.json
└── visualizations/                # 📈 Outputs visuels
```

## 🎓 Cas d'Usage

### Pour les Villes
- 📍 Optimisation déploiement capteurs (où investir ?)
- � Planification infrastructures cyclables
- 📊 Identification des axes à fort potentiel cyclable
- 🌧️ Anticipation impact météo sur le trafic

### Pour les Développeurs
- 🏗️ Architecture modulaire facilement extensible
- � Scripts séparés par responsabilité
- 📚 Documentation complète dans `docs/`
- 🧪 Facile à tester et à adapter

## 📜 Licences & Conformité

- ✅ OpenStreetMap : ODbL (attribution requise)
- ✅ Grand Lyon Open Data : Licence Ouverte 2.0
- ✅ Open-Meteo : CC BY 4.0
- ✅ Eco-Counter : Données ouvertes Métropole de Lyon
- 💰 Études d'impact sans campagnes terrain coûteuses
- 🔮 Scénarios "what-if" (nouvelle piste, ZTL, etc.)
- 📊 Benchmarking inter-villes
- 🗺️ Cartographie complète du trafic multi-modal

### Pour les Développeurs
- 🔌 API trafic prédictif pour apps mobilité
- 🚗 Routage intelligent évitant congestion
- 📱 Analyse multimodale en temps réel
- 🌤️ Prédictions conditionnelles (si pluie demain...)

## 📧 Contact

Projet développé pour TEM - Early Makers Group
