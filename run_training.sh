#!/bin/bash
# Script d'orchestration pour l'entraînement et l'analyse du modèle v3

set -e  # Arrêter en cas d'erreur

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🤖 CITYZN - PIPELINE ML COMPLET v3"
echo "════════════════════════════════════════════════════════════════════════════════"

# Vérifier environnement virtuel
if [ ! -d ".venv" ]; then
    echo "❌ Environnement virtuel non trouvé (.venv)"
    echo "💡 Créez-le avec: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

echo ""
echo "✅ Environnement virtuel trouvé"
echo "📦 Activation de l'environnement..."
source .venv/bin/activate

# Vérifier dataset preprocessing
if [ ! -f "data/processed/final_dataset_v3.csv" ]; then
    echo ""
    echo "❌ Dataset v3 non trouvé!"
    echo "💡 Lancez d'abord: ./run_preprocessing.sh"
    exit 1
fi

echo ""
echo "────────────────────────────────────────────────────────────────────────────────"
echo "📊 ÉTAPE 1/3: ENTRAÎNEMENT DU MODÈLE"
echo "────────────────────────────────────────────────────────────────────────────────"
echo ""

python src/models/train_v3.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Erreur lors de l'entraînement!"
    exit 1
fi

echo ""
echo "────────────────────────────────────────────────────────────────────────────────"
echo "📈 ÉTAPE 2/3: ANALYSE DES ERREURS"
echo "────────────────────────────────────────────────────────────────────────────────"
echo ""

python src/models/analyze_errors_v3.py

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Erreur lors de l'analyse (non bloquant)"
fi

echo ""
echo "────────────────────────────────────────────────────────────────────────────────"
echo "🔮 ÉTAPE 3/3: PRÉDICTION EXEMPLE"
echo "────────────────────────────────────────────────────────────────────────────────"
echo ""

# Exemple de prédiction pour demain 8h
TOMORROW=$(date -v+1d '+%Y-%m-%d')
PREDICT_DATETIME="$TOMORROW 08:00"

echo "💡 Génération d'une prédiction exemple pour: $PREDICT_DATETIME"
echo ""

python src/models/predict_v3.py --datetime "$PREDICT_DATETIME" --sample 1000

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Erreur lors de la prédiction (non bloquant)"
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ PIPELINE TERMINÉ!"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📁 Fichiers générés:"
echo "   • models/best_model.joblib          - Modèle entraîné"
echo "   • models/metrics.json               - Métriques de performance"
echo "   • models/feature_columns.json       - Liste des features"
echo "   • visualizations/error_analysis_v3.png - Graphiques d'analyse"
echo "   • data/predictions/predictions_*.csv - Exemple de prédiction"
echo ""
echo "💡 Prochaines étapes:"
echo "   1. Consulter: visualizations/error_analysis_report_v3.txt"
echo "   2. Faire une prédiction:"
echo "      python src/models/predict_v3.py --datetime '2025-11-15 17:30'"
echo "   3. Visualiser dans QGIS: data/predictions/predictions_*.geojson"
echo ""
