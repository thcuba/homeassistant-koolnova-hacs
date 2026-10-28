# Descubrimiento de Métodos API de Koolnova

Este documento detalla todos los métodos API de Koolnova investigados, incluyendo los actualmente implementados y los adicionales descubiertos.

## 🔍 Metodología de Investigación

1. **Análisis de código fuente**: Revisión del cliente API existente
2. **Pruebas de endpoints públicos**: Requests sin autenticación para detectar endpoints disponibles
3. **Análisis de patrones**: Búsqueda de endpoints comunes en sistemas HVAC/IoT
4. **Script de testing**: Creación de herramienta para pruebas con credenciales reales

## ✅ MÉTODOS API CONFIRMADOS DISPONIBLES

### Endpoints que Funcionan con Autenticación

Estos endpoints están disponibles y proporcionan datos detallados:

#### 1. `/notifications/` - Gestión de Notificaciones
- **Método**: GET
- **Respuesta**: `{"lastPage": 0, "currentPage": 0, "perPage": 0, "total": 0, "data": []}`
- **Estado**: Funcional - Sin notificaciones activas actualmente
- **Implementación sugerida**: Sensor binario para alertas en HA

#### 2. `/devices/` - Gestión de Dispositivos
- **Método**: GET
- **Respuesta**: Lista paginada con 8 dispositivos detallados
- **Datos por dispositivo**:
  - ID, key, project, room, type, sensor, peripheral
  - Información completa del sensor (temperatura, setpoint, RSSI, configuraciones)
  - Información del topic (modo, estado online, configuraciones avanzadas)
- **Estado**: Totalmente funcional
- **Implementación sugerida**: Entidad device_tracker o sensor adicional

#### 3. `/devices/{id}/` - Detalle de Dispositivo Individual
- **Método**: GET
- **Parámetros**: ID del dispositivo
- **Respuesta**: Información completa del dispositivo
- **Estado**: Funcional
- **Uso**: Obtener detalles específicos de un dispositivo

#### 4. `/topics/{id}/` - Detalle de Topic/Proyecto
- **Método**: GET
- **Parámetros**: ID del topic
- **Campos importantes**: mode, is_online, name, project, configurations
- **Estado**: Funcional
- **Uso**: Información detallada de zonas/proyectos

#### 5. `/projects/{id}/` - Detalle de Proyecto
- **Método**: GET
- **Parámetros**: ID del proyecto
- **Campos importantes**: name, code, is_online, user, topic
- **Estado**: Funcional
- **Uso**: Información completa del proyecto

#### 6. `/users/` - Gestión de Usuarios
- **Método**: GET
- **Estado**: Prohibido (403 Forbidden) - Posiblemente por permisos de usuario
- **Nota**: No disponible para usuarios regulares

## 📋 MÉTODOS API ACTUALMENTE IMPLEMENTADOS

### Autenticación
- `POST /auth/v2/login/` - Login con credenciales

### Gestión de Proyectos
- `GET /projects/` - Lista proyectos con paginación
  - Parámetros: page, page_size, ordering, search, is_oem
  - Respuesta: Lista de proyectos con información de topics

### Gestión de Zonas/Sensores
- `GET /topics/sensors/` - Lista sensores/zonas
  - Respuesta: Temperatura, setpoint, status, velocidad, topic_info
- `PUT /topics/sensors/{sensor_id}/` - Actualizar sensor
  - Payloads: `{"setpoint_temperature": float}`, `{"status": "00|01|02|03"}`, `{"speed": "1|2|3|4"}`

### Gestión de Topics/Proyectos
- `PATCH /topics/{topic_id}/` - Actualizar proyecto/topic
  - Payloads: `{"mode": "1|2|4|6"}`, `{"eco": boolean}`, `{"is_online": boolean}`, `{"is_stop": boolean}`

### Gestión de Dispositivos
- `GET /modules` - Lista todos los dispositivos
  - Clasifica por ModuleType_Id (1=Koolnova, 2=Hub)
- `GET /modules/{koolnova_id}/NewResume` - Mediciones actuales
  - Respuesta: temperature, red_ox, chlorine, ph, battery

### Gestión de Hubs
- `GET /hub/{hub_id}/state` - Estado del hub
  - Respuesta: `{"state": bool, "mode": behavior}`
- `PUT /hub/{hub_id}/mode/{target_mode}` - Cambiar modo
  - Modos: "manual", "auto", "planning"
- `POST /hub/{hub_id}/Manual/{state}` - Cambiar estado manual

## ❌ ENDPOINTS PROBADOS SIN RESPUESTA

Se probaron más de 50 endpoints diferentes que no respondieron:

### Programación/Horarios
- `/schedules/`, `/planning/`, `/programs/`, `/timers/`, `/routines/`, `/automation/`, `/rules/`, `/scenes/`

### Datos Históricos
- `/measurements/`, `/history/`, `/logs/`, `/measurements/latest/`
- `/modules/{id}/history`, `/modules/{id}/logs`, `/modules/{id}/measurements`
- `/topics/{id}/history`, `/topics/{id}/logs`

### Sistema y Diagnósticos
- `/system/`, `/diagnostics/`, `/health/`, `/maintenance/`
- `/system/status/`, `/system/info/`, `/modules/{id}/diagnostics`

### Configuración
- `/config/`, `/calibration/`, `/profiles/`, `/presets/`

### Analytics y Reportes
- `/stats/`, `/analytics/`, `/reports/`, `/dashboard/`, `/summary/`

### Otros
- `/alerts/`, `/events/`, `/activities/`, `/timeline/`, `/energy/`, `/data/`

## 🔧 HERRAMIENTA DE TESTING

Se creó `test_api_methods.py` para investigar endpoints con credenciales reales:

```bash
# Establecer credenciales
export KOOLNOVA_USERNAME='tu_usuario'
export KOOLNOVA_PASSWORD='tu_password'
export KOOLNOVA_EMAIL='tu_email'  # opcional

# Ejecutar pruebas
python test_api_methods.py
```

Esta herramienta:
- Verifica autenticación
- Prueba métodos ya implementados
- Investiga endpoints adicionales descubiertos
- Prueba endpoints relacionados con módulos específicos

## 📊 ANÁLISIS DE LA API

### Fortalezas
- ✅ API RESTful bien estructurada
- ✅ Autenticación robusta con tokens
- ✅ Headers específicos bien documentados
- ✅ Soportes métodos estándar (GET, POST, PUT, PATCH)

### Limitaciones
- ❌ Pocos endpoints disponibles comparado con sistemas HVAC típicos
- ❌ Sin funcionalidad de scheduling/programming real
- ❌ Sin datos históricos
- ❌ Sin diagnósticos avanzados
- ❌ Sin gestión energética

### Comparación con APIs Típicas de HVAC
| Funcionalidad | Koolnova API | APIs Típicas |
|---------------|--------------|---------------|
| Control básico | ✅ | ✅ |
| Scheduling | ❌ | ✅ |
| Datos históricos | ❌ | ✅ |
| Alertas | ⚠️ (sólo notificaciones) | ✅ |
| Diagnósticos | ❌ | ✅ |
| Multi-usuario | ⚠️ (básico) | ✅ |
| Gestión energética | ❌ | ✅ |

## 💡 RECOMENDACIONES PARA IMPLEMENTACIÓN

### Alta Prioridad
1. **`/notifications/`** - Implementar como sensor binario en HA para alertas
2. **`/devices/`** - Crear entidad device_tracker para gestión de dispositivos

### Media Prioridad
3. **`/users/`** - Soporte multi-usuario (si aplica)

### Baja Prioridad
- Los demás endpoints probados no responden, sugiriendo que no existen

## 🔐 REQUERIMIENTOS PARA TESTING REAL

Para completar la investigación con datos reales, se necesitan:
- Credenciales válidas de cuenta Koolnova
- Dispositivos activos conectados
- Acceso a diferentes tipos de proyectos/zona

## 📝 CONCLUSIONES

La API de Koolnova es **funcional pero limitada** comparada con sistemas HVAC modernos. Los métodos adicionales disponibles son mínimos:

- **3 endpoints confirmados** no implementados
- **Enfoque en control en tiempo real** más que en analytics/históricos
- **API básica** suficiente para control esencial pero sin funcionalidades avanzadas

La integración actual cubre las necesidades básicas de control HVAC. Los endpoints adicionales descubiertos agregarían valor limitado a la funcionalidad existente.

## 📊 RESULTADOS DE LA INVESTIGACIÓN CON CREDENCIALES REALES

### Configuración del Sistema Analizado
- **Proyecto**: "CASA" (ID: 1174) - Estado: ONLINE
- **Dispositivos**: 8 sensores/zonas activas
- **Estado general**: Todos los dispositivos conectados y funcionales

### Endpoints Funcionando Confirmados
1. **`/notifications/`** ✅ - Sistema funcional, 0 notificaciones activas
2. **`/devices/`** ✅ - 8 dispositivos con información completa y detallada
3. **`/devices/{id}/`** ✅ - Detalles individuales de dispositivos
4. **`/topics/{id}/`** ✅ - Información detallada de topics (modo: 4, online: True)
5. **`/projects/{id}/`** ✅ - Información completa del proyecto

### Estructura de Datos Descubierta

#### Información de Dispositivos (`/devices/`)
Cada dispositivo incluye:
- **Información básica**: id, key, project, room, type, sensor, peripheral
- **Datos del sensor**: temperature (22.0°C), setpoint_temperature (22.0°C), status, zone, speed
- **Información del topic**: mode, is_online, rssi (-65 dBm), last_sync, configurations
- **Configuraciones avanzadas**: AllowEco, AllowAntiFrost, TopicModes, etc.

#### Información de Topics (`/topics/{id}/`)
- **24 campos disponibles** incluyendo configuraciones detalladas
- **Estado en tiempo real**: mode, is_online, last_sync
- **Configuraciones del sistema**: MQTT, seguridad, etc.

## 🔍 DESCUBRIMIENTOS IMPORTANTES

1. **API más rica de lo esperado**: Los endpoints disponibles proporcionan mucha más información que los actualmente utilizados
2. **Datos en tiempo real completos**: Temperaturas, RSSI, estados, configuraciones
3. **Sistema de configuraciones avanzado**: Múltiples parámetros configurables por dispositivo
4. **Información de conectividad**: RSSI, última sincronización, estado online

## 💡 OPORTUNIDADES DE MEJORA PARA LA INTEGRACIÓN

### Funcionalidades Adicionales Posibles
1. **Sensor de conectividad**: RSSI y estado de dispositivos
2. **Información de batería**: Para dispositivos con batería
3. **Configuraciones avanzadas**: Permitir configuración desde HA
4. **Notificaciones del sistema**: Alertas cuando hay problemas
5. **Información detallada del proyecto**: Estados globales

### Valor Agregado
- **Mejor diagnóstico**: Información detallada de conectividad y estado
- **Configuración avanzada**: Acceso a configuraciones no disponibles actualmente
- **Monitoreo mejorado**: Más sensores y estados disponibles

## 📝 CONCLUSIONES FINALES

Después de la investigación exhaustiva con credenciales reales, se confirma que:

1. **La API tiene más funcionalidades disponibles** de las que se pensaba inicialmente
2. **Los endpoints adicionales proporcionan datos valiosos** para mejorar la integración
3. **Hay oportunidades reales de mejora** agregando sensores adicionales y funcionalidades
4. **La integración actual es básica** comparada con lo que la API puede ofrecer

**Recomendación**: Considerar implementar los endpoints `/devices/` y `/notifications/` para agregar valor significativo a la integración de Home Assistant.
