"""
Script de collecte des infrastructures cyclables de Lyon
Source: API Grand Lyon - Plan des modes doux (pistes cyclables, voies vertes, etc.)
Enregistre: GeoJSON des infrastructures cyclables
"""

import json
import requests
from datetime import datetime
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw" / "bike"
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

# URL de l'API Grand Lyon pour les pistes cyclables
BIKE_INFRASTRUCTURE_URL = (
    "https://data.grandlyon.com/fr/geoserv/ogc/features/v1/collections/"
    "metropole-de-lyon:pvo_patrimoine_voirie.pvoplanmodesdoux/items?"
    "f=application/geo%2Bjson&crs=EPSG:4171&startIndex=0&sortby=gid"
)


def save_json(data, filename, timestamped=False):
    """Sauvegarde données JSON"""
    if timestamped:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = DATA_RAW_DIR / f"{filename}_{timestamp}.json"
    else:
        filepath = DATA_RAW_DIR / f"{filename}.json"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Sauvegardé : {filepath.name}")
    return filepath


def fetch_bike_infrastructure():
    """
    Récupère les infrastructures cyclables de la Métropole de Lyon
    Retourne: GeoJSON avec pistes cyclables, voies vertes, etc.
    """
    print("\n🚴 Récupération infrastructures cyclables Grand Lyon...")
    
    try:
        # Récupérer les données
        response = requests.get(BIKE_INFRASTRUCTURE_URL, timeout=60)
        response.raise_for_status()
        
        geojson_data = response.json()
        
        # Vérifier le format GeoJSON
        if not isinstance(geojson_data, dict) or geojson_data.get('type') != 'FeatureCollection':
            raise ValueError("Format GeoJSON invalide")
        
        features = geojson_data.get('features', [])
        
        # Analyser les types d'infrastructures
        infra_types = {}
        total_length_km = 0
        
        for feature in features:
            props = feature.get('properties', {})
            
            # Extraire le type d'infrastructure
            infra_type = props.get('type') or props.get('typologie') or props.get('nature') or 'Inconnu'
            infra_types[infra_type] = infra_types.get(infra_type, 0) + 1
            
            # Calculer longueur si disponible
            length = props.get('longueur') or props.get('length') or props.get('shape_length')
            if length:
                try:
                    total_length_km += float(length) / 1000  # Convertir m en km
                except (ValueError, TypeError):
                    pass
        
        # Créer le résultat avec métadonnées enrichies
        result = {
            "metadata": {
                "source": "Grand Lyon - Plan des modes doux",
                "api_url": BIKE_INFRASTRUCTURE_URL,
                "timestamp": datetime.now().isoformat(),
                "total_features": len(features),
                "total_length_km": round(total_length_km, 2),
                "infrastructure_types": infra_types,
                "crs": "EPSG:4171 (RGF93)",
                "licence": "Licence Ouverte / Open Licence",
                "description": "Pistes cyclables, voies vertes, bandes cyclables, zones 30, etc.",
                "apport": "Réseau cyclable complet pour calcul d'accessibilité et routing vélo"
            },
            "geojson": geojson_data
        }
        
        # Statistiques par type
        print(f"   → {len(features)} segments d'infrastructure")
        print(f"   → Longueur totale: {total_length_km:.1f} km")
        print(f"   → Types d'infrastructures:")
        for infra_type, count in sorted(infra_types.items(), key=lambda x: x[1], reverse=True):
            print(f"      • {infra_type}: {count}")
        
        return result
        
    except Exception as e:
        print(f"❌ Erreur récupération infrastructures: {e}")
        return None


def export_simplified_geojson(result):
    """
    Exporte une version simplifiée du GeoJSON (seulement géométries + infos clés)
    """
    print("\n📍 Export GeoJSON simplifié...")
    
    try:
        geojson_data = result['geojson']
        features_simplified = []
        
        for feature in geojson_data.get('features', []):
            props = feature.get('properties', {})
            
            # Garder seulement les propriétés essentielles
            simplified_props = {
                'id': props.get('gid') or props.get('id'),
                'type': props.get('type') or props.get('typologie') or props.get('nature'),
                'name': props.get('nom') or props.get('name'),
                'width': props.get('largeur') or props.get('width'),
                'surface': props.get('revetement') or props.get('surface'),
                'sens': props.get('sens'),
                'statut': props.get('statut'),
            }
            
            features_simplified.append({
                'type': 'Feature',
                'geometry': feature.get('geometry'),
                'properties': {k: v for k, v in simplified_props.items() if v is not None}
            })
        
        geojson_simplified = {
            'type': 'FeatureCollection',
            'metadata': {
                'source': 'Grand Lyon - Plan des modes doux (simplifié)',
                'timestamp': datetime.now().isoformat()
            },
            'features': features_simplified
        }
        
        filepath = DATA_RAW_DIR / "bike_infrastructure_simplified.geojson"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(geojson_simplified, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ Version simplifiée exportée: {filepath.name}")
        return filepath
        
    except Exception as e:
        print(f"   ⚠️  Erreur export simplifié: {e}")
        return None


def main():
    """
    Point d'entrée principal
    """
    print("="*60)
    print("🚴 COLLECTE INFRASTRUCTURES CYCLABLES LYON")
    print("="*60)
    
    # Récupérer les données
    result = fetch_bike_infrastructure()
    
    if not result:
        print("❌ Échec de la collecte")
        return None
    
    # Sauvegarder le fichier complet (pas de timestamp, écrase à chaque collecte)
    filepath = save_json(result, "bike_infrastructure", timestamped=False)
    
    # Exporter version simplifiée pour visualisation
    export_simplified_geojson(result)
    
    # Résumé
    print("\n" + "="*60)
    print("✅ COLLECTE TERMINÉE")
    print("="*60)
    print(f"Total segments: {result['metadata']['total_features']}")
    print(f"Longueur totale: {result['metadata']['total_length_km']} km")
    print(f"\n📁 Fichiers créés dans: {DATA_RAW_DIR}")
    
    return filepath


if __name__ == "__main__":
    main()
