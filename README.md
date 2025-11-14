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

### 1. Collecte Modulaire
```bash
python src/data_collection/main_data_collection.py
```
- Scripts séparés par source de données
- Fichiers timestampés pour traçabilité
- Métadonnées enrichies

### 2. Preprocessing
```bash
python src/preprocessing/create_ml_dataset_v3.py
```
- Association spatiale capteurs → edges (rayon 50m)
- Calcul features : géométrie, infrastructure, temporel
- Dataset training : ~62 edges × 168 heures = ~10k lignes

### 3. Entraînement
```bash
python src/models/train_predict.py train
```
- Modèle : Random Forest / XGBoost
- Features : temporel + météo + infrastructure
- Target : bike_count (nombre de vélos/heure)

### 4. Prédiction Zones Grises
```bash
python src/models/predict_gray_zones.py
```
- Application du modèle sur les ~60k edges sans capteurs
- Export GeoJSON pour visualisation
- Quantification de l'incertitude

## 📈 Résultats

- ✅ **Training** : ~62 edges avec données réelles
- 🔮 **Prédiction** : ~60k edges (zones grises)
- 📊 **Métriques** : MAE, RMSE, R² sur données de validation
- 🗺️ **Visualisation** : Export Kepler.gl interactif

## 🛠️ Installation et Utilisation

### Installation

```bash
# Créer environnement virtuel
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Installer dépendances
pip install -r requirements.txt
```

### Utilisation Rapide

```bash
# 1. Collecter toutes les données
python src/data_collection/main_data_collection.py

# 2. Créer le dataset ML
python src/preprocessing/create_ml_dataset_v3.py

# 3. Entraîner le modèle
python src/models/train_predict.py train

# 4. Faire des prédictions
python src/models/train_predict.py predict
```

**📖 Documentation complète** : Voir [docs/README.md](docs/README.md)

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
│   ├── data_collection/           # 📥 Scripts de collecte
│   │   ├── main_data_collection.py
│   │   ├── fetch_bike_counters.py
│   │   ├── fetch_bike_infrastructure.py
│   │   ├── fetch_osm_network.py
│   │   └── fetch_weather.py
│   ├── preprocessing/             # 🔧 Preprocessing
│   │   └── create_ml_dataset_v3.py
│   ├── models/                    # 🤖 ML models
│   │   ├── train_predict.py
│   │   ├── predict_complete.py
│   │   └── predict_gray_zones.py
│   └── visualization/             # 📊 Visualisation
│       └── export_kepler.py
├── models/                        # 💾 Modèles entraînés
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
