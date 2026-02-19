# Dashboard de Mantenimiento Predictivo

Este es un dashboard ejecutivo modular y escalable construido en Streamlit para una empresa de transporte terrestre de hidrocarburos.

## Objetivo
Visualizar el riesgo de falla mecánica, costo esperado, y ahorro generado por un modelo de mantenimiento predictivo, utilizando una arquitectura modular que facilita la escalabilidad y el mantenimiento.

## Funcionalidades
- **Resumen Ejecutivo**: KPIs financieros, ROI, Matriz de Riesgo y Acciones Prioritarias.
- **Inteligencia de Flota**: Mapa general, distribución geográfica y módulo de Optimización de Rutas (VRP) con Google OR-Tools.
- **Diagnóstico de Activos**: Drill-down detallado por unidad, tendencias históricas y análisis de sensores.
- **Motor de Riesgo Logístico**: Módulo independiente para análisis de riesgo en rutas.

## Instalación y Ejecución

1. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

2. Ejecutar la aplicación:
   ```bash
   streamlit run dashboard.py
   ```

## Estructura del Proyecto (Modular)

La aplicación ha sido refactorizada para seguir principios de escalabilidad:

- `dashboard.py`: Punto de entrada principal (Router).
- `src/`: Código fuente organizado.
  - `data/`: Carga de datos, generadores y lógica de negocio (Financials).
  - `ui/`: Componentes reutilizables (KPIs, Charts, Maps) y Estilos (CSS).
  - `views/`: Vistas principales (Summary, Fleet, Asset, Risk).
  - `modules/`: Módulos independientes (ej. Logistic Risk Engine).
  - `utils/`: Utilidades generales (ej. Solver VRP).
