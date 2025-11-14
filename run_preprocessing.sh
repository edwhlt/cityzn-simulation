#!/bin/bash

# Script de preprocessing pour CityZN
# Transforme les données brutes en dataset ML

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  🔧 PREPROCESSING CITYZN - CRÉATION DATASET ML               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Vérifier que l'environnement virtuel existe
if [ ! -d ".venv" ]; then
    echo "❌ Environnement virtuel non trouvé"
    echo "💡 Exécuter: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activer l'environnement virtuel
echo "🔧 Activation environnement virtuel..."
source .venv/bin/activate

# Vérifier que les données brutes existent
echo ""
echo "📂 Vérification données brutes..."

MISSING_DATA=0

if [ ! -f "data/raw/osm/osm_network.json" ]; then
    echo "   ❌ data/raw/osm/osm_network.json manquant"
    MISSING_DATA=1
fi

if [ ! -f "data/raw/bike/bike_infrastructure.json" ]; then
    echo "   ❌ data/raw/bike/bike_infrastructure.json manquant"
    MISSING_DATA=1
fi

if [ ! -f "data/raw/bike/bike_sensors_metadata.json" ]; then
    echo "   ❌ data/raw/bike/bike_sensors_metadata.json manquant"
    MISSING_DATA=1
fi

if [ ! -d "data/raw/bike" ] || [ -z "$(ls -A data/raw/bike/bike_counters_*.json 2>/dev/null)" ]; then
    echo "   ❌ Aucun fichier bike_counters_*.json trouvé"
    MISSING_DATA=1
fi

if [ ! -d "data/raw/weather" ] || [ -z "$(ls -A data/raw/weather/weather_data.json 2>/dev/null)" ]; then
    echo "   ❌ Aucun fichier weather_data.json trouvé"
    MISSING_DATA=1
fi

if [ $MISSING_DATA -eq 1 ]; then
    echo ""
    echo "❌ Données brutes manquantes"
    echo "💡 Exécuter d'abord: python src/data_collection/main_data_collection.py"
    exit 1
fi

echo "   ✅ Toutes les données brutes présentes"

# Lancer le preprocessing
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  📊 LANCEMENT PREPROCESSING                                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

python src/preprocessing/create_ml_dataset_v3.py

# Vérifier le résultat
if [ $? -eq 0 ]; then
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║  ✅ PREPROCESSING TERMINÉ AVEC SUCCÈS                        ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📂 Fichiers générés:"
    echo "   • data/processed/final_dataset_v3.csv"
    echo "   • data/processed/edges_static_v3.gpkg"
    echo ""
    echo "🚀 Prochaine étape:"
    echo "   python src/models/train_predict.py train"
    echo ""
else
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║  ❌ ERREUR PENDANT LE PREPROCESSING                          ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "💡 Vérifier les erreurs ci-dessus"
    exit 1
fi
