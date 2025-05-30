
# Estrategia PAC-MCMV v1.0

## 1. Estado Actual
- ✅ MVP funcional en AWS EC2 con datos sintéticos
- ✅ Dashboard Streamlit con visualizaciones básicas
- ✅ PostgreSQL dockerizado
- ✅ ETL preparado para recibir datos reales

## 2. Roadmap de Producción

### Fase A: Requisitos de Datos (1 semana)
- [ ] Mapeo de fuentes de datos del banco
- [ ] Definición de esquema de datos obligatorios
- [ ] SLA de actualización de datos

### Fase B: Ingesta Inicial (2 semanas)
- [ ] ETL para archivos reales (CSV/XLSX)
- [ ] Validación de esquema
- [ ] Manejo de errores y logs

### Fase C: Modelo de Datos (1 semana)
- [ ] Esquema normalizado en PostgreSQL
- [ ] Catálogos de UF y municipios
- [ ] Índices para performance

### Fase D: Seguridad (1 semana)
- [ ] AWS Secrets Manager para credenciales
- [ ] SSL para base de datos
- [ ] Autenticación de usuarios

### Fase E: Dashboards v2 (2 semanas)
- [ ] KPIs de atraso
- [ ] Métricas de desembolso
- [ ] Exportación a Excel/PDF

### Fase F: Text Analytics 2.0 (3 semanas)
- [ ] Motor de reglas para clasificación
- [ ] Integración con LLM (Ollama)
- [ ] Análisis de causas de atraso

### Fase G: QA & Release (1 semana)
- [ ] Pruebas con usuarios del banco
- [ ] Checklist de producción
- [ ] Documentación de deployment

## 3. Preguntas Pendientes para el Banco

### Datos
- Formato de archivos fuente (CSV, XLSX, API?)
- Frecuencia de actualización
- Campos obligatorios y opcionales
- Volumen estimado de registros

### Infraestructura
- Acceso: VPN vs Internet con login
- Requisitos de backup y retención
- SLA esperado

### Funcionalidades
- Top 3 insights prioritarios
- Casos de uso del chat/LLM
- Necesidades de exportación

### Compliance
- Datos personales (LGPD)
- Auditoría y logs
- Seguridad de acceso

## 4. Arquitectura Propuesta

```mermaid
graph TB
    A[Fuentes de Datos] --> B[ETL Python]
    B --> C[PostgreSQL]
    C --> D[Streamlit Dashboard]
    C --> E[API FastAPI]
    E --> F[LLM Ollama]
    D --> G[Usuarios Banco]
