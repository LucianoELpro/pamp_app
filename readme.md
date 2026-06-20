Cómo se usa en el día a día

  Si el Excel original cambia (alguien actualiza datos):
  1. Correr:  python limpiar_base_datos.py
  2. Listo — la app ya muestra la data nueva (se recarga automático)

  Para abrir la app (si se cerró):
  python -m streamlit run app.py
  → abrir navegador en http://localhost:8501

  Si quieres el Excel de presentación actualizado:
  python generar_reporte_presentacion.py

  ---
  Por qué Python y no solo Excel

  Excel tiene límites: no puede filtrar 3,634 filas en tiempo real desde múltiples dimensiones a la vez, calcular KPIs dinámicos, ni mostrar gráficos interactivos con tooltips. La app hace todo eso en el
  navegador, y cualquier usuario puede usarla sin saber nada de Python.