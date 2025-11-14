"""
Script de collecte des données des compteurs vélo Eco-Counter
Source: API Eco-Visio - Métropole de Lyon
Enregistre:
  - Les données des capteurs (fichier unique mis à jour)
  - Les données de comptage (fichier par timestamp)
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw" / "bike"
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

# Configuration API Eco-Visio
SENSORS_LIST_URL = "https://www.eco-visio.net/api/aladdin/1.0.0/pbl/publicwebpageplus/3902?withNull=true"
API_BASE_URL = "https://www.eco-visio.net/api/aladdin/1.0.0/pbl/publicwebpageplus/data"
ORGANISME_ID = "3902"  # Métropole de Lyon


def save_json(data, filename, timestamped=True):
    """Sauvegarde données JSON avec ou sans timestamp"""
    if timestamped:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = DATA_RAW_DIR / f"{filename}_{timestamp}.json"
    else:
        filepath = DATA_RAW_DIR / f"{filename}.json"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Sauvegardé : {filepath.name}")
    return filepath


def format_date_for_api(date_obj):
    """Formate une date pour l'API Eco-Visio (URL encoded)"""
    return date_obj.strftime("%d%%2F%m%%2F%Y")


def fetch_sensors_list():
    """
    Récupère la liste des capteurs vélo et leurs informations
    Retourne: dict {idPdc: {name, lat, lon, flows, total, lastDay}}
    """
    print("\n🚴 Récupération liste des capteurs Eco-Counter...")
    
    try:
        response = requests.get(SENSORS_LIST_URL, timeout=30)
        response.raise_for_status()
        sensors_raw = response.json()
        
        if not isinstance(sensors_raw, list):
            raise ValueError("Format API inattendu")
        
        # Construire le dictionnaire des capteurs
        sensors_map = {}
        for sensor in sensors_raw:
            if not isinstance(sensor, dict):
                continue
            
            pdc_id = sensor.get('idPdc')
            if not pdc_id:
                continue
            
            # Extraire les flow IDs depuis la clé 'pratique'
            flows = []
            if 'pratique' in sensor and isinstance(sensor['pratique'], list):
                flows = [str(p.get('id')) for p in sensor['pratique'] if p.get('id')]
            
            sensors_map[str(pdc_id)] = {
                'name': sensor.get('nom', 'Sans nom'),
                'lat': sensor.get('lat'),
                'lon': sensor.get('lon'),
                'flows': flows,
                'total': sensor.get('total', 0),
                'lastDay': sensor.get('lastDay', 0)
            }
        
        print(f"   → {len(sensors_map)} capteurs détectés")
        total_flows = sum(len(v['flows']) for v in sensors_map.values())
        print(f"   → {total_flows} flows au total")
        
        return sensors_map
        
    except Exception as e:
        print(f"❌ Erreur récupération liste capteurs: {e}")
        return None


def fetch_counter_data(pdc_id, sensor_info, start_date, end_date):
    """
    Récupère les données de comptage pour un capteur spécifique
    """
    if not sensor_info['flows']:
        return []
    
    try:
        flow_ids_str = ";".join(sensor_info['flows'])
        
        url = (
            f"{API_BASE_URL}/{pdc_id}"
            f"?idOrganisme={ORGANISME_ID}"
            f"&idPdc={pdc_id}"
            f"&debut={format_date_for_api(start_date)}"
            f"&fin={format_date_for_api(end_date)}"
            f"&interval=3"  # 3 = horaire
            f"&flowIds={flow_ids_str}"
        )
        
        response = requests.get(url, timeout=40)
        response.raise_for_status()
        raw_data = response.json()
        
        # Parser les données
        series = []
        if isinstance(raw_data, dict) and 'values' in raw_data:
            raw_list = raw_data['values']
        elif isinstance(raw_data, list):
            raw_list = raw_data
        else:
            raw_list = []
        
        # Reconstituer les timestamps et parser les valeurs
        for i, point in enumerate(raw_list):
            # Extraire date et count selon le format
            if isinstance(point, (list, tuple)) and len(point) >= 2:
                date_str, count_str = point[0], point[1]
            elif isinstance(point, dict):
                date_str = point.get('date') or point.get('time') or point.get('0')
                count_str = point.get('value') or point.get('count') or point.get('1')
            else:
                continue
            
            try:
                hours_from_start = i
                timestamp = start_date + timedelta(hours=hours_from_start)
                count_val = int(count_str) if count_str not in (None, '') else 0
            except Exception:
                continue
            
            series.append({
                "counter_id": pdc_id,
                "counter_name": sensor_info['name'],
                "timestamp": timestamp.isoformat(),
                "date_str": date_str,
                "count": count_val,
                "hour": timestamp.hour,
                "day_of_week": timestamp.weekday(),
                "quality": "real",
                "lat": sensor_info['lat'],
                "lon": sensor_info['lon']
            })
        
        return series
        
    except Exception as e:
        print(f"   ⚠️  Erreur PDC {pdc_id} ({sensor_info['name']}): {e}")
        return []


def export_sensors_to_geojson(sensors_map, stats_by_sensor):
    """
    Exporte les capteurs en GeoJSON pour visualisation
    """
    print("\n📍 Export capteurs en GeoJSON...")
    
    try:
        features = []
        
        for sensor_id, sensor_info in sensors_map.items():
            lat = sensor_info.get("lat")
            lon = sensor_info.get("lon")
            
            if lat is None or lon is None:
                continue
            
            stats = stats_by_sensor.get(sensor_id, {})
            avg = stats.get("avg", 0)
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": {
                    "sensor_id": sensor_id,
                    "name": sensor_info.get("name", "Capteur inconnu"),
                    "avg_bikes_per_hour": round(avg, 1),
                    "max_bikes_per_hour": stats.get("max", 0),
                    "min_bikes_per_hour": stats.get("min", 0),
                    "total_records": stats.get("count", 0),
                    "total_passages": stats.get("total", 0),
                    "flows_count": len(sensor_info.get("flows", []))
                }
            }
            features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "metadata": {
                "source": "Eco-Counter bike sensors",
                "timestamp": datetime.now().isoformat(),
                "total_sensors": len(features)
            },
            "features": features
        }
        
        filepath = DATA_RAW_DIR / "bike_sensors.geojson"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ {len(features)} capteurs exportés: {filepath.name}")
        return filepath
        
    except Exception as e:
        print(f"   ⚠️  Erreur export GeoJSON: {e}")
        return None


def main():
    """
    Point d'entrée principal
    """
    print("="*60)
    print("🚴 COLLECTE COMPTEURS VÉLO ECO-COUNTER")
    print("="*60)
    
    # Configuration de la période (7 derniers jours)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    print(f"\nPériode: {start_date.strftime('%d/%m/%Y')} → {end_date.strftime('%d/%m/%Y')}")
    
    # 1. Récupérer la liste des capteurs
    sensors_map = fetch_sensors_list()
    if not sensors_map:
        print("❌ Impossible de récupérer la liste des capteurs")
        return None
    
    # 2. Sauvegarder la liste des capteurs (fichier unique, pas de timestamp)
    sensors_metadata = {
        "source": "Eco-Counter via API Eco-Visio",
        "api_url": SENSORS_LIST_URL,
        "timestamp": datetime.now().isoformat(),
        "total_sensors": len(sensors_map),
        "sensors": sensors_map
    }
    save_json(sensors_metadata, "bike_sensors_metadata", timestamped=False)
    
    # 3. Récupérer les données de comptage pour chaque capteur
    print("\n📊 Récupération données de comptage...")
    all_time_series = []
    successful_counters = 0
    
    for pdc_id, sensor_info in sorted(sensors_map.items()):
        if not sensor_info['flows']:
            continue
        
        print(f"   Capteur {pdc_id}: {sensor_info['name'][:40]}...", end=" ")
        
        series = fetch_counter_data(pdc_id, sensor_info, start_date, end_date)
        
        if series:
            all_time_series.extend(series)
            successful_counters += 1
            print(f"✓ {len(series)} mesures")
        else:
            print("✗")
    
    if not all_time_series:
        print("❌ Aucune donnée de comptage récupérée")
        return None
    
    # 4. Calculer les statistiques
    stats_by_sensor = {}
    for record in all_time_series:
        sensor_id = record["counter_id"]
        count = record["count"]
        
        if sensor_id not in stats_by_sensor:
            stats_by_sensor[sensor_id] = {
                "total": 0,
                "count": 0,
                "max": 0,
                "min": float('inf')
            }
        
        stats_by_sensor[sensor_id]["total"] += count
        stats_by_sensor[sensor_id]["count"] += 1
        stats_by_sensor[sensor_id]["max"] = max(stats_by_sensor[sensor_id]["max"], count)
        stats_by_sensor[sensor_id]["min"] = min(stats_by_sensor[sensor_id]["min"], count)
    
    # Calculer moyennes
    for sensor_id, stats in stats_by_sensor.items():
        stats["avg"] = stats["total"] / stats["count"] if stats["count"] > 0 else 0
        if stats["min"] == float('inf'):
            stats["min"] = 0
    
    # 5. Grouper les données par timestamp (heure)
    print("\n💾 Sauvegarde des données par timestamp...")
    
    data_by_timestamp = {}
    for record in all_time_series:
        timestamp = record["timestamp"]
        if timestamp not in data_by_timestamp:
            data_by_timestamp[timestamp] = []
        data_by_timestamp[timestamp].append(record)
    
    # Sauvegarder un fichier par timestamp
    saved_files = []
    for timestamp_iso, records in sorted(data_by_timestamp.items()):
        # Convertir timestamp ISO en format pour nom de fichier
        dt = datetime.fromisoformat(timestamp_iso)
        timestamp_str = dt.strftime("%Y%m%d_%H%M%S")
        
        hourly_data = {
            "metadata": {
                "source": "Eco-Counter via API Eco-Visio (DONNÉES RÉELLES)",
                "api_url": API_BASE_URL,
                "organisme": f"Métropole de Lyon (ID: {ORGANISME_ID})",
                "collection_timestamp": datetime.now().isoformat(),
                "data_timestamp": timestamp_iso,
                "counters_count": len(records),
                "licence": "Données ouvertes Eco-Counter / Métropole de Lyon"
            },
            "records": records,
            "summary": {
                "total_passages": sum(r["count"] for r in records),
                "avg_passages": round(sum(r["count"] for r in records) / len(records), 1) if records else 0
            }
        }
        
        # Sauvegarder avec le timestamp dans le nom
        filepath = DATA_RAW_DIR / f"bike_counters_{timestamp_str}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            import json
            json.dump(hourly_data, f, indent=2, ensure_ascii=False)
        
        saved_files.append(filepath)
    
    print(f"   ✅ {len(saved_files)} fichiers créés (un par heure)")
    
    # Créer aussi un fichier de résumé global
    summary_result = {
        "metadata": {
            "source": "Eco-Counter via API Eco-Visio (DONNÉES RÉELLES)",
            "collection_timestamp": datetime.now().isoformat(),
            "detected_counters": len(sensors_map),
            "successful_counters": successful_counters,
            "records_count": len(all_time_series),
            "files_count": len(saved_files),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": 7
            }
        },
        "summary": {
            "total_passages": sum(t["count"] for t in all_time_series),
            "avg_per_hour": round(sum(t["count"] for t in all_time_series) / len(all_time_series), 1),
            "max_hour": max(all_time_series, key=lambda x: x["count"]),
            "min_hour": min(all_time_series, key=lambda x: x["count"])
        }
    }
    
    filepath = save_json(summary_result, "bike_counters_summary", timestamped=False)
    
    # 6. Exporter les capteurs en GeoJSON
    export_sensors_to_geojson(sensors_map, stats_by_sensor)
    
    # Afficher le résumé
    print("\n" + "="*60)
    print("✅ COLLECTE TERMINÉE")
    print("="*60)
    print(f"Capteurs réussis: {successful_counters}/{len(sensors_map)}")
    print(f"Fichiers horaires créés: {len(saved_files)}")
    print(f"Total passages: {summary_result['summary']['total_passages']:,}")
    print(f"Moyenne par heure: {summary_result['summary']['avg_per_hour']:.1f}")
    print(f"\n📁 Fichiers créés dans: {DATA_RAW_DIR}")
    
    return filepath


if __name__ == "__main__":
    main()
