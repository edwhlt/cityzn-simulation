#!/bin/bash

echo "=========================================="
echo "🚀 CityZN - Setup & Collect"
echo "=========================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. Vérifier Python
echo -e "${BLUE}1. Vérification de Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 trouvé${NC}"
echo ""

# 2. Créer environnement virtuel
echo -e "${BLUE}2. Création de l'environnement virtuel...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}✅ Environnement virtuel créé${NC}"
else
    echo -e "${GREEN}✅ Environnement virtuel existant${NC}"
fi
echo ""

# 3. Activer environnement
echo -e "${BLUE}3. Activation de l'environnement...${NC}"
source .venv/bin/activate
echo -e "${GREEN}✅ Environnement activé${NC}"
echo ""

# 4. Installer dépendances
echo -e "${BLUE}4. Installation des dépendances...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✅ Dépendances installées${NC}"
echo ""

# 5. Collecter les données
echo -e "${BLUE}5. Collecte des données...${NC}"
python src/data_collection/main_data_collection.py
echo -e "${GREEN}✅ Données collectées${NC}"
echo ""

echo ""
echo "=========================================="
echo "✅ Setup terminé avec succès !"
echo "=========================================="
