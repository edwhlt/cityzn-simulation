# Module de Collecte de Données

Ce module contient les scripts de collecte de données pour le projet Lyon.

## 📁 Architecture

Chaque source de données possède son propre script autonome :

```
src/data_collection/
├── main_data_collection.py          # 🚀 Script orchestrateur (lance tout)
├── fetch_bike_counters.py           # 🚴 Compteurs vélo Eco-Counter
├── fetch_bike_infrastructure.py     # 🛤️  Pistes cyclables Grand Lyon
├── fetch_osm_network.py             # 🗺️  Réseau routier OpenStreetMap
├── fetch_weather.py                 # 🌤️  Données météo Open-Meteo
└── README.md                        # 📖 Cette documentation
```

## 🚀 Utilisation

### Collecte complète (recommandé)

Lance tous les scripts de collecte dans l'ordre optimal :

```bash
python src/data_collection/main_data_collection.py
```

### Collecte individuelle

Vous pouvez aussi exécuter chaque script séparément :

```bash
# Compteurs vélo
python src/data_collection/fetch_bike_counters.py

# Infrastructures cyclables
python src/data_collection/fetch_bike_infrastructure.py

# Réseau routier OSM
python src/data_collection/fetch_osm_network.py

# Données météo
python src/data_collection/fetch_weather.py
```

## 📊 Sources de Données

### 1. Compteurs Vélo Eco-Counter
- **Source** : API Eco-Visio (Métropole de Lyon)
- **Données** : Passages horaires des cyclistes (7 derniers jours)
- **Fichiers générés** :
  - `data/raw/bike/bike_counters_data_YYYYMMDD_HHMMSS.json` (timestampé)
  - `data/raw/bike/bike_sensors_metadata.json` (liste des capteurs)
  - `data/raw/bike/bike_sensors.geojson` (positions des capteurs)

### 2. Infrastructures Cyclables
- **Source** : API Grand Lyon (Plan des modes doux)
- **Données** : Pistes cyclables, voies vertes, bandes cyclables
- **Fichiers générés** :
  - `data/raw/bike/bike_infrastructure.json` (complet)
  - `data/raw/bike/bike_infrastructure_simplified.geojson` (simplifié)

### 3. Réseau Routier OSM
- **Source** : API Overpass (OpenStreetMap)
- **Données** : Réseau routier complet avec attributs (vitesse, voies, etc.)
- **Fichiers générés** :
  - `data/raw/osm/osm_network.json` (format GeoJSON)

### 4. Données Météo
- **Source** : API Open-Meteo Archive
- **Données** : Température, précipitations, vent, etc. (7 derniers jours)
- **Fichiers générés** :
  - `data/raw/weather/weather_data_YYYYMMDD_HHMMSS.json` (timestampé)
  - `data/raw/weather/weather_daily_summary.json` (résumé journalier)

## 🗂️ Organisation des Fichiers

```
data/raw/
├── bike/
│   ├── bike_counters_data_YYYYMMDD_HHMMSS.json    # Données de comptage (timestampé)
│   ├── bike_sensors_metadata.json                  # Métadonnées capteurs (mis à jour)
│   ├── bike_sensors.geojson                        # Positions capteurs
│   ├── bike_infrastructure.json                    # Infrastructures (complet)
│   └── bike_infrastructure_simplified.geojson      # Infrastructures (simplifié)
├── osm/
│   └── osm_network.json                            # Réseau routier
└── weather/
    ├── weather_data_YYYYMMDD_HHMMSS.json          # Données météo (timestampé)
    └── weather_daily_summary.json                  # Résumé journalier
```

## ⚙️ Configuration

Les paramètres sont définis dans chaque script :

- **Zone géographique** : Bbox de Lyon (45.7-45.8°N, 4.78-4.9°E)
- **Période par défaut** : 7 derniers jours
- **Granularité** : Horaire

## 📝 Notes

- **Rate limiting** : Pauses de 2 secondes entre chaque collecte
- **Timestamps** : Les données temporelles sont timestampées, les données structurelles (réseau, capteurs) sont écrasées à chaque collecte
- **Format** : Tout est en JSON/GeoJSON pour interopérabilité
- **Licence** : Vérifier les licences dans les métadonnées de chaque fichier

## 🔄 Migration

**Ancien fichier** : `fetch_lyon_data.py` (monolithique) ❌  
**Nouveaux fichiers** : Scripts modulaires ci-dessus ✅

Le fichier `fetch_lyon_data.py` peut être supprimé en toute sécurité.
