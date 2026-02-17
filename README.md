# Dashboard de Mantenimiento Predictivo

Este es un dashboard ejecutivo construido en Streamlit para una empresa de transporte terrestre de hidrocarburos.

## Objetivo
Visualizar el riesgo de falla mecánica, costo esperado, y ahorro generado por un modelo de mantenimiento predictivo.

## Funcionalidades
- **Ranking de Unidades**: Clasificación por riesgo de falla.
- **Análisis Financiero**: Comparación de Costo Esperado de Inacción (CEI) vs Costo de Mantenimiento (CEM).
- **Semáforo de Riesgo**: Indicadores visuales claros para la toma de decisiones.
- **KPIs Ejecutivos**: Ahorro acumulado, ROI estimado.

## Instalación y Ejecución

1. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

2. Ejecutar la aplicación:
   ```bash
   streamlit run dashboard.py
   ```

## Estructura del Proyecto
- `dashboard.py`: Aplicación principal de Streamlit.
- `data_generator.py`: Módulo para generar datos simulados.
- `requirements.txt`: Dependencias del proyecto.
