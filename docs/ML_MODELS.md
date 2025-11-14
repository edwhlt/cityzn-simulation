# Module Machine Learning (ML)

Ce module contient les scripts d'entraînement, prédiction et analyse du modèle ML pour prédire le trafic cycliste.

## 📁 Structure

```
src/models/
├── train_v3.py              # 🎓 Entraînement du modèle
├── predict_v3.py            # 🔮 Prédiction pour une date/heure spécifique
├── analyze_errors_v3.py     # 📊 Analyse détaillée des erreurs
└── README.md                # 📖 Cette documentation
```

## 🚀 Workflow ML Complet

### 1. Entraînement du Modèle

```bash
python src/models/train_v3.py
```

**Prérequis** : Dataset preprocessing terminé (`data/processed/final_dataset_v3.csv`)

**Ce que fait le script** :
- Charge le dataset (~11k lignes, 68 edges avec capteurs)
- Encode les features catégorielles
- Split temporel 80/20 (train/test)
- Compare 3 modèles :
  - RandomForest
  - GradientBoosting
  - Ridge (baseline)
- Sélectionne le meilleur (par R²)
- Analyse feature importance
- Sauvegarde tout

**Sorties** :
- `models/best_model.joblib` - Modèle entraîné (~50 MB)
- `models/feature_columns.json` - Liste des 27 features
- `models/label_encoders.joblib` - Encodeurs catégoriels
- `models/metrics.json` - Métriques de performance
- `data/predictions/feature_importance.csv` - Importance des features

**Performance actuelle** :
- R² = 0.873 (excellent)
- MAE = 28.5 vélos/h
- RMSE = 59.7 vélos/h
- MAPE = ~75% (élevé car beaucoup de valeurs faibles)

### 2. Prédiction pour Date/Heure Spécifique ⭐

```bash
# Prédire pour demain 8h du matin
python src/models/predict_v3.py --datetime "2025-11-15 08:00"

# Prédire pour vendredi 17h30 (rush hour soir)
python src/models/predict_v3.py --datetime "2025-11-22 17:30"

# Test rapide sur 1000 edges (au lieu de 60k)
python src/models/predict_v3.py --datetime "2025-11-15 08:00" --sample 1000

# Nom de fichier personnalisé
python src/models/predict_v3.py --datetime "2025-11-15 08:00" --output rush_vendredi.csv
```

**Prérequis** : Modèle entraîné + edges statiques

**Arguments** :
- `--datetime` (requis) : Date et heure au format `"YYYY-MM-DD HH:MM"`
- `--sample` (optionnel) : Nombre d'edges à prédire (pour tests rapides)
- `--output` (optionnel) : Nom du fichier de sortie

**Ce que fait le script** :
1. Charge le modèle entraîné
2. Charge les edges statiques (60k edges avec features géométriques)
3. Trouve la météo la plus proche de la date/heure cible
4. Génère les features temporelles (heure, jour, weekend, rush hour)
5. Ajoute les features météo (température, pluie, vent + dérivées)
6. Encode les features catégorielles
7. Prédit le trafic pour tous les edges
8. Exporte résultats

**Sorties** :
- `data/predictions/predictions_YYYYMMDD_HHMMSS.csv` - Données tabulaires
- `data/predictions/predictions_YYYYMMDD_HHMMSS.geojson` - Visualisation spatiale
- `data/predictions/predictions_YYYYMMDD_HHMMSS_metadata.json` - Métadonnées

**Exemple de sortie** :
```
🎯 Prédiction pour: Saturday 15 November 2025 à 08:00
📊 Statistiques des prédictions:
   • Moyenne: 6.6 vélos/h
   • Médiane: 5 vélos/h
   • Min: 0 vélos/h
   • Max: 48 vélos/h

🔥 Top 10 edges avec le plus de trafic:
   🚴 Edge 273993960: 48 vélos/h (cycleway)
      Edge 512303723: 41 vélos/h
   ...
```

### 3. Analyse des Erreurs

```bash
python src/models/analyze_errors_v3.py
```

**Prérequis** : Modèle entraîné + dataset

**Ce que fait le script** :
- Charge le dataset de validation
- Génère les prédictions
- Calcule métriques multiples :
  - MAE, RMSE, R², MAPE
  - Median AE, P90, P95
- Analyse par catégories :
  - Par heure de la journée
  - Par jour de la semaine
  - Par type de route
  - Par infrastructure cyclable
  - Par météo
- Génère visualisations (4 graphiques)
- Exporte rapport texte

**Sorties** :
- `visualizations/error_analysis_v3.png` - 4 graphiques :
  1. Scatter plot prédictions vs réel
  2. Distribution des résidus
  3. Erreur par heure
  4. Erreur par niveau de trafic
- `visualizations/error_analysis_report_v3.txt` - Rapport complet
- `data/predictions/worst_predictions_v3.csv` - Top 100 pires erreurs

## 📊 Features du Modèle (27)

### Temporelles (5)
- `hour` - Heure de la journée (0-23)
- `day_of_week` - Jour de la semaine (0=lundi, 6=dimanche)
- `is_weekend` - Weekend (0/1)
- `is_rush_hour_morning` - Rush hour matin 7-9h (0/1)
- `is_rush_hour_evening` - Rush hour soir 17-19h (0/1)

### Météo (7)
- `temperature_c` - Température en °C
- `precipitation_mm` - Précipitations en mm
- `wind_speed_kmh` - Vitesse du vent en km/h
- `is_raining` - Pluie (0/1)
- `is_cold` - Froid <5°C (0/1)
- `is_hot` - Chaud >30°C (0/1)
- `is_windy` - Vent fort >30km/h (0/1)

### Infrastructure (10)
- `highway_type` - Type de route (primary, secondary, cycleway, etc.)
- `road_category` - Catégorie (major/minor/local/cycleway)
- `lanes` - Nombre de voies
- `maxspeed_kmh` - Vitesse max en km/h
- `has_cycleway` - Présence d'aménagement cyclable OSM (0/1)
- `has_dedicated_bike_lane` - Piste cyclable dédiée <20m (0/1)
- `bike_lane_distance_m` - Distance à la piste cyclable la plus proche
- `surface_quality` - Qualité de surface (paved/unpaved/unknown)
- `is_lit` - Éclairage public (0/1)
- `edge_length_m` - Longueur du segment en m

### Géométrie (2)
- `distance_to_center_km` - Distance au centre-ville en km
- `orientation` - Orientation (N/S/E/W/NE/NW/SE/SW)

### Historiques (3) - Lag features
- `bike_count_lag_1h` - Trafic 1h avant
- `bike_count_lag_24h` - Trafic 24h avant (même heure veille)
- `bike_count_rolling_7d` - Moyenne mobile 7 jours

> ⚠️ **Note** : Les lag features sont disponibles uniquement pour le training. Pour la prédiction sur edges sans historique, elles sont mises à 0.

## 🎯 Top 10 Features Importantes

D'après l'analyse du modèle Random Forest (feature importance) :

1. **bike_count_lag_1h** (42.4%) - Trafic 1h avant
2. **bike_count_rolling_7d** (16.1%) - Moyenne 7 jours
3. **bike_count_lag_24h** (13.8%) - Trafic même heure veille
4. **hour** (5.3%) - Heure de la journée
5. **distance_to_center_km** (4.1%) - Distance au centre
6. **wind_speed_kmh** (3.2%) - Vitesse du vent
7. **temperature_c** (3.1%) - Température
8. **edge_length_m** (2.3%) - Longueur du segment
9. **bike_lane_distance_m** (1.8%) - Distance piste cyclable
10. **day_of_week** (1.8%) - Jour de la semaine

**Insight** : Les 3 lag features représentent 72% de l'importance totale ! Le trafic passé est le meilleur prédicteur du trafic futur.

## 🔧 Scripts Helper

### Script orchestrateur complet

```bash
./run_training.sh
```

Ce script bash lance automatiquement :
1. Entraînement du modèle
2. Analyse des erreurs
3. Prédiction exemple (demain 8h, échantillon 1000 edges)

## 💡 Cas d'Usage

### Cas 1 : Prédire le trafic pour tous les edges demain matin

```bash
python src/models/predict_v3.py --datetime "2025-11-15 08:00"
```

**Temps** : ~2-3 minutes pour 60k edges  
**Taille** : ~30 MB (GeoJSON)

### Cas 2 : Test rapide sur un échantillon

```bash
python src/models/predict_v3.py --datetime "2025-11-15 17:30" --sample 1000
```

**Temps** : ~10 secondes  
**Usage** : Validation rapide avant prédiction complète

### Cas 3 : Comparer rush hour matin vs soir

```bash
# Matin
python src/models/predict_v3.py --datetime "2025-11-15 08:00" --output rush_matin.csv

# Soir
python src/models/predict_v3.py --datetime "2025-11-15 18:00" --output rush_soir.csv

# Comparer ensuite les 2 fichiers dans QGIS ou Python
```

### Cas 4 : Analyser l'impact d'une météo défavorable

```bash
# Hypothèse : journée pluvieuse et froide
# Modifier data/raw/weather/weather_data.json manuellement
# Puis relancer prédiction
python src/models/predict_v3.py --datetime "2025-11-20 08:00"
```

## 🐛 Troubleshooting

### Erreur: "Modèle non trouvé"
```bash
# Solution: Entraîner le modèle d'abord
python src/models/train_v3.py
```

### Erreur: "Edges statiques non trouvés"
```bash
# Solution: Relancer le preprocessing
python src/preprocessing/create_ml_dataset_v3.py
```

### Erreur: "Données météo non trouvées"
```bash
# Solution: Récupérer les données météo
python src/data_collection/fetch_weather.py
```

### Prédictions anormalement basses/hautes

**Causes possibles** :
- Date weekend vs semaine (trafic différent)
- Heure de nuit (trafic très faible normal)
- Météo extrême (pluie forte, froid intense)
- Lag features à 0 pour edges sans historique (normal)

**Solution** :
- Vérifier le contexte dans les métadonnées JSON
- Comparer avec d'autres heures/jours similaires
- Consulter `visualizations/error_analysis_report_v3.txt` pour comprendre les patterns d'erreur

### Script bloqué

Si le script freeze ou prend trop de temps :
- Vérifier qu'on utilise bien les versions v3 (optimisées)
- Essayer avec `--sample 100` d'abord
- Vérifier les logs pour identifier l'étape bloquante

## 📈 Amélioration Continue

### Métriques à surveiller

- **R²** : Doit être > 0.7 (actuellement 0.873 ✅)
- **MAE** : Erreur absolue moyenne (actuellement 28.5 vélos/h)
- **Erreur par heure** : Identifier les heures problématiques
- **Erreur par type de route** : Identifier les types problématiques

### Pistes d'amélioration

1. **Plus de données** :
   - Collecter sur plus de 7 jours (actuellement)
   - Ajouter événements (concerts, manifestations)
   - Ajouter vacances scolaires

2. **Features supplémentaires** :
   - Comptages automobiles (trafic automobile)
   - Qualité de l'air
   - Événements météo extrêmes
   - Présence de commerces/services à proximité

3. **Modèles avancés** :
   - Modèles séparés weekend/semaine
   - Modèles séparés par type de route
   - Deep Learning (LSTM pour séries temporelles)
   - Graph Neural Networks (pour capturer la structure spatiale du réseau)

4. **Post-processing** :
   - Lissage spatial (prédictions cohérentes entre edges voisins)
   - Intervalles de confiance (prédictions probabilistes)
   - Détection d'anomalies

## 📚 Ressources

### Fichiers de configuration

- `models/metrics.json` - Historique des performances
- `models/feature_columns.json` - Liste des features utilisées

### Métadonnées de prédiction

Chaque prédiction génère un fichier `*_metadata.json` avec :
- Date/heure de prédiction
- Météo utilisée
- Features temporelles
- Statistiques des prédictions
- Contexte d'exécution

### Visualisations

- QGIS : Ouvrir les `.geojson` pour voir la distribution spatiale
- Kepler.gl : Visualisation interactive dans le navigateur
- Python/Jupyter : Analyser les `.csv` avec pandas/geopandas

---

**Version** : 3.0  
**Dernière mise à jour** : 14 novembre 2025
