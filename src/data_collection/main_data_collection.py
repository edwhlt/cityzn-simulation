"""
Script orchestrateur de collecte de données Lyon
Lance tous les scripts de collecte dans l'ordre optimal
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire src au path
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

# Importer les modules de collecte
from data_collection import (
    fetch_bike_counters,
    fetch_bike_infrastructure,
    fetch_osm_network,
    fetch_weather
)


def print_header(title):
    """Affiche un en-tête formaté"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_section(icon, title):
    """Affiche un titre de section"""
    print(f"\n{icon} {title}")
    print("-" * 70)


def main():
    """
    Exécute la collecte complète de toutes les sources de données
    """
    start_time = datetime.now()
    
    print_header("🚀 COLLECTE COMPLÈTE DES DONNÉES - LYON")
    print(f"\n📅 Date: {start_time.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"📍 Zone: Lyon et Métropole")
    
    results = {
        "execution_start": start_time.isoformat(),
        "sources": {}
    }
    
    # ========================================================================
    # 1. RÉSEAU ROUTIER OSM (prioritaire - structure de base)
    # ========================================================================
    print_section("🗺️", "1/4 - Réseau routier OpenStreetMap")
    try:
        osm_result = fetch_osm_network.main()
        results["sources"]["osm_network"] = {
            "status": "success" if osm_result else "failed",
            "file": str(osm_result) if osm_result else None
        }
        if osm_result:
            print("✅ Réseau OSM collecté avec succès")
        else:
            print("⚠️  Échec collecte réseau OSM")
    except Exception as e:
        print(f"❌ Erreur réseau OSM: {e}")
        results["sources"]["osm_network"] = {"status": "error", "error": str(e)}
    
    time.sleep(2)  # Rate limiting respectueux
    
    # ========================================================================
    # 2. INFRASTRUCTURE CYCLABLE (Grand Lyon)
    # ========================================================================
    print_section("🚴", "2/4 - Infrastructures cyclables Grand Lyon")
    try:
        bike_infra_result = fetch_bike_infrastructure.main()
        results["sources"]["bike_infrastructure"] = {
            "status": "success" if bike_infra_result else "failed",
            "file": str(bike_infra_result) if bike_infra_result else None
        }
        if bike_infra_result:
            print("✅ Infrastructures cyclables collectées avec succès")
        else:
            print("⚠️  Échec collecte infrastructures cyclables")
    except Exception as e:
        print(f"❌ Erreur infrastructures cyclables: {e}")
        results["sources"]["bike_infrastructure"] = {"status": "error", "error": str(e)}
    
    time.sleep(2)
    
    # ========================================================================
    # 3. COMPTEURS VÉLO ECO-COUNTER
    # ========================================================================
    print_section("🚴‍♂️", "3/4 - Compteurs vélo Eco-Counter")
    try:
        bike_counters_result = fetch_bike_counters.main()
        results["sources"]["bike_counters"] = {
            "status": "success" if bike_counters_result else "failed",
            "file": str(bike_counters_result) if bike_counters_result else None
        }
        if bike_counters_result:
            print("✅ Compteurs vélo collectés avec succès")
        else:
            print("⚠️  Échec collecte compteurs vélo")
    except Exception as e:
        print(f"❌ Erreur compteurs vélo: {e}")
        results["sources"]["bike_counters"] = {"status": "error", "error": str(e)}
    
    time.sleep(2)
    
    # ========================================================================
    # 4. DONNÉES MÉTÉO
    # ========================================================================
    print_section("🌤️", "4/4 - Données météorologiques Open-Meteo")
    try:
        weather_result = fetch_weather.main()
        results["sources"]["weather"] = {
            "status": "success" if weather_result else "failed",
            "file": str(weather_result) if weather_result else None
        }
        if weather_result:
            print("✅ Données météo collectées avec succès")
        else:
            print("⚠️  Échec collecte données météo")
    except Exception as e:
        print(f"❌ Erreur données météo: {e}")
        results["sources"]["weather"] = {"status": "error", "error": str(e)}
    
    # ========================================================================
    # RÉSUMÉ FINAL
    # ========================================================================
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    results["execution_end"] = end_time.isoformat()
    results["duration_seconds"] = duration
    
    print_header("📊 RÉSUMÉ DE LA COLLECTE")
    
    # Compter les succès/échecs
    success_count = sum(1 for s in results["sources"].values() if s["status"] == "success")
    total_count = len(results["sources"])
    
    print(f"\n✅ Sources collectées avec succès: {success_count}/{total_count}")
    print(f"⏱️  Durée totale: {duration:.1f} secondes")
    print(f"\n📁 Dossier de sortie: {BASE_DIR / 'data' / 'raw'}")
    
    # Détail par source
    print("\n📋 Détail par source:")
    for source_name, source_info in results["sources"].items():
        status_icon = "✅" if source_info["status"] == "success" else "❌"
        print(f"   {status_icon} {source_name}: {source_info['status']}")
        if source_info.get("file"):
            print(f"      → {Path(source_info['file']).name}")
    
    # Sauvegarder le résumé
    summary_file = BASE_DIR / "data" / "raw" / "collection_summary.json"
    import json
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Résumé sauvegardé: {summary_file.name}")
    
    # Message de fin
    if success_count == total_count:
        print("\n🎉 Collecte complète terminée avec succès!")
    elif success_count > 0:
        print(f"\n⚠️  Collecte partielle: {success_count}/{total_count} sources récupérées")
    else:
        print("\n❌ Échec de la collecte: aucune source récupérée")
    
    print("\n" + "="*70)
    
    return results


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Collecte interrompue par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
