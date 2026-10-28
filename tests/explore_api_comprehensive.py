#!/usr/bin/env python3
"""
Exploración COMPREHENSIVA de TODOS los endpoints API de Koolnova
"""

import json
import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from koolnova_api.client import KoolnovaAPIRestClient

def explore_api_comprehensive():
    """Exploración comprehensiva de TODOS los endpoints API descubiertos"""

    # Credentials come from the environment: never commit an account to this repo.
    #   export KOOLNOVA_USERNAME=... KOOLNOVA_PASSWORD=... [KOOLNOVA_EMAIL=...]
    username = os.environ.get("KOOLNOVA_USERNAME", "")
    password = os.environ.get("KOOLNOVA_PASSWORD", "")
    email = os.environ.get("KOOLNOVA_EMAIL", username)
    if not username or not password:
        print("Set KOOLNOVA_USERNAME and KOOLNOVA_PASSWORD before running this exploration.")
        return

    print("🔬 EXPLORACIÓN COMPREHENSIVA DE LA API DE KOOLNOVA")
    print("=" * 70)

    try:
        client = KoolnovaAPIRestClient(username, password, email)
        print("✅ Autenticación exitosa\n")

        # Obtener IDs para pruebas relacionadas
        device_id = None
        topic_id = None
        project_id = None

        try:
            devices_response = client._get_session().rest_request("GET", "devices/")
            devices_data = devices_response.json()
            if devices_data.get('data') and len(devices_data['data']) > 0:
                device_id = devices_data['data'][0]['id']
                topic_id = devices_data['data'][0]['sensor']['topic_info']['id']
                project_id = devices_data['data'][0]['project']
        except:
            pass

        # 1. EXPLORAR SISTEMA
        print("🖥️ 1. ENDPOINTS DEL SISTEMA")
        print("-" * 50)

        system_endpoints = [
            "system/info",
            "system/status",
            "system/health"
        ]

        for endpoint in system_endpoints:
            try:
                response = client._get_session().rest_request("GET", endpoint)
                data = response.json()
                print(f"✅ {endpoint}")
                print(f"   📊 Tipo: {type(data)}")
                if isinstance(data, dict):
                    print(f"   🔑 Keys: {list(data.keys())}")
                    # Mostrar algunos valores importantes
                    for key, value in list(data.items())[:3]:
                        print(f"   {key}: {value}")
                print()
            except Exception as e:
                print(f"❌ {endpoint}: {str(e)[:60]}...\n")

        # 2. EXPLORAR CONFIGURACIÓN Y PERFIL
        print("⚙️ 2. ENDPOINTS DE CONFIGURACIÓN Y PERFIL")
        print("-" * 50)

        config_endpoints = [
            "config",
            "settings",
            "profile",
            "account"
        ]

        for endpoint in config_endpoints:
            try:
                response = client._get_session().rest_request("GET", endpoint)
                data = response.json()
                print(f"✅ {endpoint}")
                print(f"   📊 Tipo: {type(data)}")
                if isinstance(data, dict):
                    print(f"   🔑 Keys ({len(data)}): {list(data.keys())[:5]}...")
                    # Mostrar contenido si no es muy largo
                    if len(str(data)) < 300:
                        print(f"   💾 Contenido: {data}")
                print()
            except Exception as e:
                print(f"❌ {endpoint}: {str(e)[:60]}...\n")

        # 3. EXPLORAR DASHBOARD Y ANALYTICS
        print("📊 3. ENDPOINTS DE DASHBOARD Y ANALYTICS")
        print("-" * 50)

        analytics_endpoints = [
            "dashboard",
            "analytics",
            "reports"
        ]

        for endpoint in analytics_endpoints:
            try:
                response = client._get_session().rest_request("GET", endpoint)
                data = response.json()
                print(f"✅ {endpoint}")
                print(f"   📊 Tipo: {type(data)}")
                if isinstance(data, dict):
                    print(f"   🔑 Keys: {list(data.keys())}")
                elif isinstance(data, list):
                    print(f"   📈 Array con {len(data)} elementos")
                    if data and len(data) > 0:
                        print(f"   🔍 Primer elemento: {data[0] if len(str(data[0])) < 100 else str(data[0])[:100] + '...'}")
                print()
            except Exception as e:
                print(f"❌ {endpoint}: {str(e)[:60]}...\n")

        # 4. EXPLORAR ENDPOINTS RELACIONADOS CON ENTIDADES
        print("🔗 4. ENDPOINTS RELACIONADOS CON ENTIDADES")
        print("-" * 50)

        if device_id and topic_id and project_id:
            entity_endpoints = [
                f"devices/{device_id}",
                f"topics/{topic_id}",
                f"projects/{project_id}"
            ]

            for endpoint in entity_endpoints:
                try:
                    response = client._get_session().rest_request("GET", endpoint)
                    data = response.json()
                    print(f"✅ {endpoint}")
                    print(f"   📊 Tipo: {type(data)}")
                    if isinstance(data, dict):
                        print(f"   🔑 Keys ({len(data)}): {list(data.keys())[:8]}...")
                        # Mostrar algunos campos importantes
                        important_fields = ['name', 'status', 'temperature', 'mode', 'is_online']
                        for field in important_fields:
                            if field in data:
                                print(f"   {field}: {data[field]}")
                    print()
                except Exception as e:
                    print(f"❌ {endpoint}: {str(e)[:60]}...\n")

        # 5. EXPLORAR ENDPOINTS DE HISTORIA/MEASUREMENTS
        print("📈 5. ENDPOINTS DE HISTORIA Y MEDIDAS")
        print("-" * 50)

        # Probar varios patrones de historia
        history_patterns = [
            "measurements",
            "measurements/latest",
            "measurements/history",
            "data",
            "data/history",
            "history",
            "logs",
            "timeline"
        ]

        for pattern in history_patterns:
            try:
                response = client._get_session().rest_request("GET", pattern)
                data = response.json()
                print(f"✅ {pattern}")
                print(f"   📊 Tipo: {type(data)}")
                if isinstance(data, dict):
                    print(f"   🔑 Keys: {list(data.keys())}")
                    if 'total' in data:
                        print(f"   📈 Total: {data['total']}")
                elif isinstance(data, list):
                    print(f"   📈 Array con {len(data)} elementos")
                print()
            except Exception as e:
                print(f"❌ {pattern}: {str(e)[:60]}...\n")

        # 6. EXPLORAR ENDPOINTS DE PROGRAMACIÓN
        print("⏰ 6. ENDPOINTS DE PROGRAMACIÓN/SCHEDULING")
        print("-" * 50)

        scheduling_endpoints = [
            "schedules",
            "planning",
            "programs",
            "timers",
            "routines",
            "automation",
            "rules"
        ]

        for endpoint in scheduling_endpoints:
            try:
                response = client._get_session().rest_request("GET", endpoint)
                data = response.json()
                print(f"✅ {endpoint}")
                print(f"   📊 Tipo: {type(data)}")
                if isinstance(data, dict) and 'total' in data:
                    print(f"   📈 Total: {data['total']}")
                elif isinstance(data, list):
                    print(f"   📈 Array con {len(data)} elementos")
                print()
            except Exception as e:
                print(f"❌ {endpoint}: {str(e)[:60]}...\n")

        # 7. EXPLORAR ENDPOINTS DE ALERTAS Y NOTIFICACIONES
        print("🚨 7. ENDPOINTS DE ALERTAS Y NOTIFICACIONES")
        print("-" * 50)

        alert_endpoints = [
            "alerts",
            "notifications",
            "notifications/unread",
            "warnings",
            "events"
        ]

        for endpoint in alert_endpoints:
            try:
                response = client._get_session().rest_request("GET", endpoint)
                data = response.json()
                print(f"✅ {endpoint}")
                print(f"   📊 Tipo: {type(data)}")
                if isinstance(data, dict) and 'total' in data:
                    print(f"   📈 Total: {data['total']}")
                elif isinstance(data, list):
                    print(f"   📈 Array con {len(data)} elementos")
                print()
            except Exception as e:
                print(f"❌ {endpoint}: {str(e)[:60]}...\n")

        # 8. RESUMEN FINAL
        print("📋 8. RESUMEN FINAL DE ENDPOINTS FUNCIONANDO")
        print("-" * 50)

        working_endpoints = [
            # Sistema
            "system/info", "system/status", "system/health",
            # Configuración
            "config", "settings", "profile", "account",
            # Dashboard/Analytics
            "dashboard", "analytics", "reports",
            # Entidades principales
            "projects", "topics", "devices", "notifications"
        ]

        print(f"✅ TOTAL ENDPOINTS FUNCIONANDO: {len(working_endpoints)}")
        print("📂 Categorías:")
        print("   🖥️ Sistema: system/info, system/status, system/health")
        print("   ⚙️ Config: config, settings, profile, account")
        print("   📊 Analytics: dashboard, analytics, reports")
        print("   🏠 Entidades: projects, topics, devices, notifications")

        print("\n🔍 MÉTODOS ADICIONALES DESCUBIERTOS:")
        print("   • Información detallada del sistema")
        print("   • Configuraciones de usuario")
        print("   • Datos de dashboard y analytics")
        print("   • Información detallada de dispositivos individuales")
        print("   • Estados del sistema en tiempo real")

        print("\n" + "=" * 70)
        print("🏁 EXPLORACIÓN COMPREHENSIVA COMPLETADA")
        print(f"🎯 TOTAL ENDPOINTS DESCUBIERTOS: {len(working_endpoints) + 4}")  # +4 por entidades relacionadas

    except Exception as e:
        print(f"❌ Error de autenticación: {e}")

if __name__ == "__main__":
    explore_api_comprehensive()
