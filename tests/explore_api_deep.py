#!/usr/bin/env python3
"""
Exploración profunda de la API de Koolnova
"""

import json
import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from koolnova_api.client import KoolnovaAPIRestClient

def explore_api_deep():
    """Exploración profunda de endpoints API con credenciales reales"""

    # Credentials come from the environment: never commit an account to this repo.
    #   export KOOLNOVA_USERNAME=... KOOLNOVA_PASSWORD=... [KOOLNOVA_EMAIL=...]
    username = os.environ.get("KOOLNOVA_USERNAME", "")
    password = os.environ.get("KOOLNOVA_PASSWORD", "")
    email = os.environ.get("KOOLNOVA_EMAIL", username)
    if not username or not password:
        print("Set KOOLNOVA_USERNAME and KOOLNOVA_PASSWORD before running this exploration.")
        return

    print("🔬 EXPLORACIÓN PROFUNDA DE LA API DE KOOLNOVA")
    print("=" * 60)

    try:
        client = KoolnovaAPIRestClient(username, password, email)
        print("✅ Autenticación exitosa\n")

        # 1. EXPLORAR NOTIFICATIONS EN DETALLE
        print("📢 1. EXPLORACIÓN DE NOTIFICATIONS")
        print("-" * 40)
        try:
            response = client._get_session().rest_request("GET", "notifications/")
            notifications = response.json()
            print(f"📊 Estructura: {json.dumps(notifications, indent=2, default=str)[:500]}...")
            print(f"📈 Total notificaciones: {notifications.get('total', 0)}")
        except Exception as e:
            print(f"❌ Error: {e}")
        print()

        # 2. EXPLORAR DEVICES EN DETALLE
        print("📱 2. EXPLORACIÓN DE DEVICES")
        print("-" * 40)
        try:
            response = client._get_session().rest_request("GET", "devices/")
            devices = response.json()
            print(f"📊 Total dispositivos: {devices.get('total', 0)}")

            if devices.get('data') and len(devices['data']) > 0:
                device = devices['data'][0]
                print(f"🔍 Primer dispositivo: {device.get('type', 'N/A')} - {device.get('sensor', {}).get('name', 'Sin nombre')}")

                # Analizar estructura del sensor
                sensor = device.get('sensor', {})
                print(f"   🌡️ Temperatura actual: {sensor.get('temperature', 'N/A')}°C")
                print(f"   🎯 Setpoint: {sensor.get('setpoint_temperature', 'N/A')}°C")
                print(f"   📶 RSSI: {sensor.get('topic_info', {}).get('rssi', 'N/A')} dBm")
                print(f"   🔄 Última sync: {sensor.get('topic_info', {}).get('last_sync', 'N/A')}")

                # Analizar configuraciones
                configs = sensor.get('topic_info', {}).get('configurations', [])
                if configs:
                    print(f"   ⚙️ Configuraciones ({len(configs)}):")
                    for config in configs[:3]:  # Mostrar primeras 3
                        print(f"      {config.get('key', 'N/A')}: {config.get('value', 'N/A')}")

        except Exception as e:
            print(f"❌ Error: {e}")
        print()

        # 3. INVESTIGAR POR QUÉ MODULES DA 404
        print("🔧 3. INVESTIGACIÓN DEL ERROR EN /modules")
        print("-" * 40)
        try:
            # Intentar diferentes variaciones
            variations = [
                "modules",
                "modules/",
                "module",
                "module/",
                "devices/modules",
                "devices/modules/"
            ]

            for var in variations:
                try:
                    response = client._get_session().rest_request("GET", var)
                    print(f"✅ {var} -> {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   📊 Tipo: {type(data)}, Longitud: {len(data) if isinstance(data, (list, dict)) and hasattr(data, '__len__') else 'N/A'}")
                        break
                except Exception as e:
                    print(f"❌ {var} -> {str(e)[:50]}...")

        except Exception as e:
            print(f"❌ Error general: {e}")
        print()

        # 4. EXPLORAR ENDPOINTS RELACIONADOS CON DISPOSITIVOS
        print("🔍 4. EXPLORACIÓN DE ENDPOINTS RELACIONADOS")
        print("-" * 40)

        # Obtener un ID de dispositivo para pruebas
        device_id = None
        try:
            response = client._get_session().rest_request("GET", "devices/")
            devices_data = response.json()
            if devices_data.get('data') and len(devices_data['data']) > 0:
                device_id = devices_data['data'][0]['id']
                sensor_id = devices_data['data'][0]['sensor']['id']
                topic_id = devices_data['data'][0]['sensor']['topic_info']['id']

                print(f"🎯 IDs obtenidos - Device: {device_id}, Sensor: {sensor_id}, Topic: {topic_id}")

                # Probar endpoints relacionados
                related_endpoints = [
                    f"devices/{device_id}",
                    f"sensors/{sensor_id}",
                    f"topics/{topic_id}",
                    f"topics/{topic_id}/sensors",
                    f"projects/{devices_data['data'][0]['project']}"
                ]

                for endpoint in related_endpoints:
                    try:
                        response = client._get_session().rest_request("GET", endpoint)
                        print(f"   ✅ {endpoint} -> {response.status_code}")
                        if response.status_code == 200:
                            data = response.json()
                            if isinstance(data, dict):
                                print(f"      🔑 Keys: {list(data.keys())[:5]}...")  # Primeras 5 keys
                    except Exception as e:
                        print(f"   ❌ {endpoint} -> {str(e)[:40]}...")

        except Exception as e:
            print(f"❌ Error obteniendo IDs: {e}")
        print()

        # 5. EXPLORACIÓN DE OTROS ENDPOINTS POTENCIALES
        print("🌐 5. EXPLORACIÓN DE ENDPOINTS ADICIONALES")
        print("-" * 40)

        additional_endpoints = [
            "system/info",
            "system/status",
            "system/health",
            "config",
            "settings",
            "profile",
            "account",
            "dashboard",
            "analytics",
            "reports"
        ]

        for endpoint in additional_endpoints:
            try:
                response = client._get_session().rest_request("GET", endpoint)
                print(f"✅ {endpoint} -> {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict):
                        print(f"   🔑 Keys: {list(data.keys())[:3]}...")
                    elif isinstance(data, list):
                        print(f"   📊 Array con {len(data)} elementos")
            except Exception as e:
                print(f"❌ {endpoint} -> {response.status_code if 'response' in locals() else 'Error'}")

        print("\n" + "=" * 60)
        print("🏁 EXPLORACIÓN COMPLETADA")

    except Exception as e:
        print(f"❌ Error de autenticación: {e}")

if __name__ == "__main__":
    explore_api_deep()
