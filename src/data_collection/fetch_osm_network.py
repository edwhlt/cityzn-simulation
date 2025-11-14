"""
Script de collecte du réseau routier OpenStreetMap
Source: API Overpass (OpenStreetMap)
Enregistre: GeoJSON du réseau routier complet avec attributs
"""

import json
import requests
from datetime import datetime
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw" / "osm"
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

# Coordonnées de Lyon (bounding box)
LYON_BBOX = {
    "south": 45.7,
    "west": 4.78,
    "north": 45.8,
    "east": 4.9
}

# URL de l'API Overpass
OVERPASS_URL = "http://overpass-api.de/api/interpreter"


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


def fetch_osm_network():
    """
    Récupère le réseau routier de Lyon via Overpass API
    Retourne: GeoJSON avec LineString complètes et attributs détaillés
    """
    print("\n🗺️  Récupération réseau routier OpenStreetMap...")
    print(f"   Zone: Lyon ({LYON_BBOX['south']}, {LYON_BBOX['west']}) - ({LYON_BBOX['north']}, {LYON_BBOX['east']})")
    
    # Requête Overpass avec out geom pour avoir les géométries complètes
    overpass_query = f"""
    [out:json][timeout:120];
    (
      way["highway"~"^(motorway|trunk|primary|secondary|tertiary|residential|unclassified|cycleway|path|footway|pedestrian)$"]
        ({LYON_BBOX['south']},{LYON_BBOX['west']},{LYON_BBOX['north']},{LYON_BBOX['east']});
    );
    out geom;
    """
    
    try:
        print("   ⏳ Envoi requête Overpass (peut prendre 1-2 min)...")
        
        response = requests.post(
            OVERPASS_URL, 
            data={'data': overpass_query}, 
            timeout=150
        )
        response.raise_for_status()
        osm_data = response.json()
        
        print("   ✓ Données OSM reçues, conversion en GeoJSON...")
        
        # Convertir en GeoJSON
        features = []
        ways_count = 0
        highway_types = {}
        
        for element in osm_data.get('elements', []):
            if element.get('type') == 'way' and 'geometry' in element:
                ways_count += 1
                
                # Extraire les coordonnées
                coordinates = [[node['lon'], node['lat']] for node in element['geometry']]
                
                # Extraire les tags/propriétés
                tags = element.get('tags', {})
                highway_type = tags.get('highway', 'unknown')
                highway_types[highway_type] = highway_types.get(highway_type, 0) + 1
                
                properties = {
                    'osm_id': element.get('id'),
                    'highway': highway_type,
                    'name': tags.get('name', 'Sans nom'),
                    'maxspeed': tags.get('maxspeed'),
                    'lanes': tags.get('lanes'),
                    'oneway': tags.get('oneway', 'no'),
                    'surface': tags.get('surface'),
                    'lit': tags.get('lit'),
                    'cycleway': tags.get('cycleway'),
                    'foot': tags.get('foot'),
                    'bicycle': tags.get('bicycle'),
                    'width': tags.get('width'),
                    'access': tags.get('access'),
                    'service': tags.get('service'),
                }
                
                # Créer la feature GeoJSON
                feature = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': coordinates
                    },
                    'properties': {k: v for k, v in properties.items() if v is not None}
                }
                
                features.append(feature)
        
        # Créer le GeoJSON complet
        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        # Métadonnées
        metadata = {
            "source": "OpenStreetMap via Overpass API",
            "api_url": OVERPASS_URL,
            "bbox": LYON_BBOX,
            "timestamp": datetime.now().isoformat(),
            "ways_count": ways_count,
            "features_count": len(features),
            "highway_types": highway_types,
            "crs": "EPSG:4326 (WGS84)",
            "licence": "ODbL (Open Database License)",
            "description": "Réseau routier complet avec géométries LineString et attributs détaillés",
            "apport": "Géométrie du réseau, vitesse max, nb voies, sens unique, type de voie",
            "usage": "GeoPandas: gdf = gpd.GeoDataFrame.from_features(data['geojson']['features'])"
        }
        
        result = {
            "metadata": metadata,
            "geojson": geojson
        }
        
        # Afficher statistiques
        print(f"   ✓ {ways_count} segments routiers récupérés")
        print(f"   → Types de voies:")
        for highway_type, count in sorted(highway_types.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"      • {highway_type}: {count}")
        
        return result
        
    except requests.exceptions.Timeout:
        print("❌ Timeout - L'API Overpass met trop de temps à répondre")
        print("   💡 Essayez de réduire la zone ou réessayez plus tard")
        return None
    except Exception as e:
        print(f"❌ Erreur récupération OSM: {e}")
        return None


def export_by_highway_type(result):
    """
    Exporte des fichiers séparés par type de voie (optionnel)
    """
    print("\n📦 Export par type de voie...")
    
    try:
        geojson_data = result['geojson']
        features_by_type = {}
        
        # Grouper par type de voie
        for feature in geojson_data.get('features', []):
            highway_type = feature['properties'].get('highway', 'unknown')
            
            if highway_type not in features_by_type:
                features_by_type[highway_type] = []
            
            features_by_type[highway_type].append(feature)
        
        # Sauvegarder les types principaux
        main_types = ['primary', 'secondary', 'tertiary', 'residential', 'cycleway']
        
        for highway_type in main_types:
            if highway_type in features_by_type:
                type_geojson = {
                    'type': 'FeatureCollection',
                    'features': features_by_type[highway_type]
                }
                
                filepath = DATA_RAW_DIR / f"osm_network_{highway_type}.geojson"
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(type_geojson, f, indent=2, ensure_ascii=False)
                
                print(f"   ✅ {highway_type}: {len(features_by_type[highway_type])} segments")
        
    except Exception as e:
        print(f"   ⚠️  Erreur export par type: {e}")


def main():
    """
    Point d'entrée principal
    """
    print("="*60)
    print("🗺️  COLLECTE RÉSEAU ROUTIER OPENSTREETMAP")
    print("="*60)
    
    # Récupérer les données
    result = fetch_osm_network()
    
    if not result:
        print("❌ Échec de la collecte")
        return None
    
    # Sauvegarder le fichier complet
    filepath = save_json(result, "osm_network", timestamped=False)
    
    # Exporter par type (optionnel, utile pour analyses spécifiques)
    # export_by_highway_type(result)
    
    # Résumé
    print("\n" + "="*60)
    print("✅ COLLECTE TERMINÉE")
    print("="*60)
    print(f"Total segments: {result['metadata']['ways_count']}")
    print(f"Format: GeoJSON avec LineString")
    print(f"\n📁 Fichier créé dans: {DATA_RAW_DIR}")
    
    return filepath


if __name__ == "__main__":
    main()
