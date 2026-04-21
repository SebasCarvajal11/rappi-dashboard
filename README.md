# Rappi Availability Dashboard

Dashboard interactivo en Streamlit para monitorear la disponibilidad de tiendas y consultar los datos con un asistente IA (Gemini + LangChain).

## Tabla de contenidos

- [Descripción](#descripción)
- [Características principales](#características-principales)
- [Arquitectura del proyecto](#arquitectura-del-proyecto)
- [Stack tecnológico](#stack-tecnológico)

## Descripción

Este proyecto permite:

- visualizar evolución histórica de `Tiendas_Disponibles`,
- filtrar por fecha, día de semana y rango horario,
- identificar momentos críticos (caídas),
- consultar insights en lenguaje natural mediante un chatbot IA contextualizado con los filtros activos.

El chatbot incluye:

- inyección de contexto de interfaz (filtros actuales),
- estadísticas resumidas del dataset filtrado,
- fallback ante errores de parsing del agente,
- manejo amigable de errores de cuota de Gemini (HTTP 429).

## Características principales

- **KPIs en tiempo real** según filtros aplicados.
- **Gráficos interactivos** (serie temporal y agregados por hora/día).
- **Tabla de incidentes** (top momentos críticos).
- **Widget de chat flotante** con minimizar/abrir.
- **Tema dark por defecto** con Streamlit config.
- **Modelo IA configurable por variable de entorno** (`GEMINI_MODEL`).

## Arquitectura del proyecto

```text
rappi_dashboard/
├── app.py
├── master_data.csv
├── requirements.txt
├── .gitignore
├── .streamlit/
│   └── config.toml
└── dashboard/
    ├── __init__.py
    ├── config.py
    ├── data.py
    ├── ui.py
    └── chatbot.py
```

### Responsabilidades por módulo

- `app.py`: orquestación general de la app.
- `dashboard/config.py`: constantes de configuración.
- `dashboard/data.py`: carga, enriquecimiento y filtrado de datos.
- `dashboard/ui.py`: sidebar, KPIs y visualizaciones.
- `dashboard/chatbot.py`: lógica del asistente IA y UI flotante del chat.

## Stack tecnológico

- Python 3.10+
- Streamlit
- Pandas
- Plotly
- LangChain + LangChain Experimental
- LangChain Google GenAI
- streamlit-float

Dependencias exactas en `requirements.txt`.