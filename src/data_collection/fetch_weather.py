"""
Script de collecte des données météorologiques
Source: Open-Meteo Archive API (gratuit, pas de clé nécessaire)
Enregistre: Données météo horaires avec timestamp
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw" / "weather"
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

# Coordonnées de Lyon
LYON_LAT = 45.764
LYON_LON = 4.8357

# API Open-Meteo
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def save_json(data, filename, timestamped=True):
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


def fetch_weather_data(days=7):
    """
    Récupère les données météo historiques pour Lyon
    
    Args:
        days: Nombre de jours en arrière (défaut: 7)
    
    Returns:
        dict avec métadonnées et données météo horaires
    """
    print(f"\n🌤️  Récupération données météo Open-Meteo ({days} derniers jours)...")
    print(f"   Localisation: Lyon ({LYON_LAT}, {LYON_LON})")
    
    # Période
    end_date = datetime.now().date()
    start_date = (datetime.now() - timedelta(days=days)).date()
    
    try:
        # Construire l'URL avec tous les paramètres météo
        url = (
            f"{OPEN_METEO_ARCHIVE_URL}?"
            f"latitude={LYON_LAT}&longitude={LYON_LON}"
            f"&start_date={start_date}"
            f"&end_date={end_date}"
            f"&hourly=temperature_2m,precipitation,rain,snowfall,snow_depth,"
            f"wind_speed_10m,wind_direction_10m,wind_gusts_10m,"
            f"cloud_cover,relative_humidity_2m,surface_pressure,"
            f"weather_code,visibility,is_day"
            f"&timezone=Europe/Paris"
        )
        
        print("   ⏳ Récupération en cours...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Parser les données horaires
        hourly = data.get("hourly", {})
        timestamps = hourly.get("time", [])
        
        if not timestamps:
            raise ValueError("Aucune donnée reçue de l'API")
        
        print(f"   ✓ {len(timestamps)} mesures horaires reçues")
        
        # Construire le dataset structuré
        weather_data = []
        for i, timestamp_str in enumerate(timestamps):
            dt = datetime.fromisoformat(timestamp_str)
            
            # Extraire toutes les variables
            temp = hourly.get("temperature_2m", [])[i]
            precip = hourly.get("precipitation", [])[i]
            rain = hourly.get("rain", [])[i]
            snowfall = hourly.get("snowfall", [])[i]
            snow_depth = hourly.get("snow_depth", [])[i]
            wind_speed = hourly.get("wind_speed_10m", [])[i]
            wind_dir = hourly.get("wind_direction_10m", [])[i]
            wind_gusts = hourly.get("wind_gusts_10m", [])[i]
            cloud = hourly.get("cloud_cover", [])[i]
            humidity = hourly.get("relative_humidity_2m", [])[i]
            pressure = hourly.get("surface_pressure", [])[i]
            weather_code = hourly.get("weather_code", [])[i]
            visibility = hourly.get("visibility", [])[i]
            is_day = hourly.get("is_day", [])[i]
            
            # Calculer des indicateurs dérivés
            is_raining = (rain or 0) > 0.1
            is_snowing = (snowfall or 0) > 0.1
            is_adverse_weather = (rain or 0) > 0.5 or (wind_speed or 0) > 30
            
            weather_data.append({
                "timestamp": dt.isoformat(),
                "date": dt.date().isoformat(),
                "hour": dt.hour,
                "day_of_week": dt.weekday(),
                "is_weekend": dt.weekday() >= 5,
                "temperature_c": temp,
                "precipitation_mm": precip,
                "rain_mm": rain,
                "snowfall_mm": snowfall,
                "snow_depth_cm": snow_depth,
                "wind_speed_kmh": wind_speed,
                "wind_direction_deg": wind_dir,
                "wind_gusts_kmh": wind_gusts,
                "cloud_cover_pct": cloud,
                "humidity_pct": humidity,
                "pressure_hpa": pressure,
                "weather_code": weather_code,
                "visibility_m": visibility,
                "is_day": is_day,
                "is_raining": is_raining,
                "is_snowing": is_snowing,
                "is_adverse_weather": is_adverse_weather
            })
        
        # Calculer les statistiques
        temps = [d["temperature_c"] for d in weather_data if d["temperature_c"] is not None]
        rains = [d["rain_mm"] for d in weather_data if d["rain_mm"] is not None]
        
        avg_temp = sum(temps) / len(temps) if temps else 0
        total_rain = sum(rains)
        rainy_hours = sum(1 for d in weather_data if d["is_raining"])
        adverse_hours = sum(1 for d in weather_data if d["is_adverse_weather"])
        
        # Métadonnées
        metadata = {
            "source": "Open-Meteo Archive API",
            "api_url": OPEN_METEO_ARCHIVE_URL,
            "location": {
                "city": "Lyon, France",
                "latitude": LYON_LAT,
                "longitude": LYON_LON
            },
            "timestamp": datetime.now().isoformat(),
            "records_count": len(weather_data),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "granularity": "hourly",
            "timezone": "Europe/Paris",
            "variables": [
                "température 2m",
                "précipitations totales",
                "pluie",
                "neige",
                "vitesse du vent 10m",
                "direction du vent",
                "rafales",
                "couverture nuageuse",
                "humidité relative",
                "pression de surface",
                "code météo WMO",
                "visibilité"
            ],
            "licence": "CC BY 4.0",
            "description": "Données météo historiques horaires pour modélisation trafic cycliste",
            "apport": "Impact météo sur mobilité : pluie -40-70%, vent fort -20-30%",
            "summary": {
                "avg_temperature_c": round(avg_temp, 1),
                "total_rain_mm": round(total_rain, 1),
                "rainy_hours": rainy_hours,
                "rainy_hours_pct": round(rainy_hours / len(weather_data) * 100, 1) if weather_data else 0,
                "adverse_weather_hours": adverse_hours,
                "adverse_weather_hours_pct": round(adverse_hours / len(weather_data) * 100, 1) if weather_data else 0
            }
        }
        
        result = {
            "metadata": metadata,
            "weather_data": weather_data
        }
        
        # Afficher statistiques
        print(f"   → Température moyenne: {metadata['summary']['avg_temperature_c']}°C")
        print(f"   → Pluie totale: {metadata['summary']['total_rain_mm']} mm")
        print(f"   → Heures pluvieuses: {rainy_hours} ({metadata['summary']['rainy_hours_pct']}%)")
        print(f"   → Heures météo défavorable: {adverse_hours} ({metadata['summary']['adverse_weather_hours_pct']}%)")
        
        return result
        
    except Exception as e:
        print(f"❌ Erreur récupération météo: {e}")
        return None

def main():
    """
    Point d'entrée principal
    """
    print("="*60)
    print("🌤️  COLLECTE DONNÉES MÉTÉOROLOGIQUES")
    print("="*60)
    
    # Récupérer les données (7 derniers jours par défaut)
    result = fetch_weather_data(days=7)
    
    if not result:
        print("❌ Échec de la collecte")
        return None
    
    # Sauvegarder avec timestamp
    filepath = save_json(result, "weather_data", timestamped=False)
    
    # Résumé
    print("\n" + "="*60)
    print("✅ COLLECTE TERMINÉE")
    print("="*60)
    print(f"Total mesures: {result['metadata']['records_count']}")
    print(f"Période: {result['metadata']['period']['days']} jours")
    print(f"\n📁 Fichiers créés dans: {DATA_RAW_DIR}")
    
    return filepath


if __name__ == "__main__":
    main()
