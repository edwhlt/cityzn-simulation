# 🚀 Guide de Démarrage Rapide - CityZN

## 📋 Prérequis

- Python 3.9+
- ~2 GB d'espace disque
- Connexion Internet (pour collecte de données)

## ⚡ Installation

```bash
# 1. Cloner le projet
cd "CityZN/Simulation Python"

# 2. Créer environnement virtuel
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux

# 3. Installer dépendances
pip install -r requirements.txt
```

## 🚀 Workflow Complet (5 minutes)

### Étape 1 : Collecter les Données

```bash
python src/data_collection/main_data_collection.py
```

**Ce script va récupérer** :
- ✅ Réseau routier OSM (~60k edges)
- ✅ Compteurs vélo Eco-Counter (7 jours, ~74 capteurs)
- ✅ Infrastructure cyclable Grand Lyon
- ✅ Données météo Open-Meteo (7 jours)

**Durée** : ~2-3 minutes  
**Résultat** : Fichiers dans `data/raw/bike/`, `data/raw/osm/`, `data/raw/weather/`

---

### Étape 2 : Créer le Dataset ML

```bash
python src/preprocessing/create_ml_dataset_v3.py
```

**Ce script va** :
- ✅ Associer capteurs → edges OSM (spatial join)
- ✅ Calculer features (géométrie, infrastructure, météo)
- ✅ Créer dataset training (~10k lignes)

**Durée** : ~1 minute  
**Résultat** : `data/processed/final_dataset_v3.csv` + `edges_static_v3.gpkg`

---

### Étape 3 : Entraîner le Modèle

```bash
python src/models/train_predict.py train
```

**Ce script va** :
- ✅ Charger le dataset
- ✅ Entraîner Random Forest / XGBoost
- ✅ Sauvegarder le modèle + métriques

**Durée** : ~1 minute  
**Résultat** : `models/best_model.joblib` + métriques

---

### Étape 4 : Faire des Prédictions

```bash
# Prédiction sur données de test
python src/models/train_predict.py predict

# OU prédiction complète (tous les edges)
python src/models/predict_complete.py
```

**Ce script va** :
- ✅ Charger le modèle entraîné
- ✅ Prédire le trafic sur les zones grises
- ✅ Exporter en CSV + GeoJSON

**Durée** : ~1-2 minutes  
**Résultat** : `data/predictions/*.csv` et `.geojson`

---

### Étape 5 : Visualiser (Optionnel)

```bash
python src/visualization/export_kepler.py
```

**Ouvre** : Carte interactive Kepler.gl avec les prédictions

Si vous voulez tout lancer d'un coup (attention, prend ~5 minutes) :

```bash
./run.sh
```

## 📊 Résultats Attendus

### Dataset Training
- **Lignes** : ~10,000 (62 edges × 168 heures)
- **Features** : ~30 (temporel + météo + infrastructure)
- **Target** : bike_count (nombre de vélos/heure)

### Prédictions
- **Zones grises** : ~60,000 edges sans capteurs
- **Format** : CSV + GeoJSON (pour visualisation)
- **Métriques** : MAE, RMSE, R² sur données de validation

### Visualisation
- Carte interactive Kepler.gl
- Heatmap du trafic cycliste prédit
- Comparaison zones mesurées vs prédites

## 📂 Fichiers Générés

```
data/
├── raw/                           # Données brutes
│   ├── bike/
│   │   ├── bike_counters_*.json   # Fichiers horaires
│   │   ├── bike_sensors_metadata.json
│   │   └── bike_infrastructure.json
│   ├── osm/
│   │   └── osm_network.json
│   └── weather/
│       └── weather_data_*.json
├── processed/                     # Dataset ML
│   ├── final_dataset_v3.csv
│   └── edges_static_v3.gpkg
└── predictions/                   # Résultats
    ├── predictions_*.csv
    └── predictions_*.geojson
```

## 🎯 Prochaines Étapes

### Pour un POC réel :

1. **Remplacer les données MOCK** par vraies API :
   - `data.grandlyon.com` pour compteurs vélo et trafic
   - API TCL pour transports en commun
   - Données mobiles agrégées (Orange Flux, etc.)

2. **Améliorer le modèle** :
   - Graph Neural Networks (ST-GNN) pour utiliser la topologie du réseau
   - Prédiction temporelle (séries temporelles)
   - Quantification d'incertitude (zones grises moins fiables)

3. **Déploiement** :
   - API REST pour servir les prédictions
   - Dashboard interactif (Streamlit/Dash)
   - Pipeline automatisé (Airflow)

## 💡 Points Clés pour la Présentation

### Problème
- Les villes ont des données fragmentées (8 compteurs vélo, 10 boucles trafic)
- **>90% du territoire = zones grises** (pas de mesure)
- Impossibilité de planifier efficacement

### Solution
- **Fusion** de 4 sources hétérogènes
- **IA** pour prédire les zones grises
- **Carte complète** du trafic urbain

### Valeur Ajoutée
1. **Pour la ville** :
   - Identification exhaustive des hotspots
   - Meilleure planification (pistes cyclables, travaux)
   - Optimisation placement capteurs

2. **Pour la vente de données** :
   - Carte complète vs points isolés
   - +300-500% de données valorisables
   - Différenciation concurrentielle

3. **ROI** :
   - Pas besoin d'installer des centaines de capteurs (€€€)
   - Économie sur études terrain
   - Valorisation des données existantes

## 📞 Support

Consultez le README.md principal pour plus de détails.
