# Plan Cuadrante PNP - GeoJSON

## Archivo Actual

El archivo `plan_cuadrante_la_libertad.geojson` contiene datos de demo con 8 cuadrantes simplificados del departamento de La Libertad.

## Integración del GeoJSON Oficial

Para integrar el GeoJSON oficial del Plan Cuadrante PNP:

### 1. Obtener el GeoJSON Oficial

El GeoJSON oficial del Plan Cuadrante PNP debe obtenerse de la fuente oficial de la PNP. Los pasos típicos son:

1. Contactar a la DIVINCRI La Libertad para obtener el archivo oficial
2. El archivo debe estar en formato GeoJSON válido
3. Debe contener al menos los siguientes campos en `properties`:
   - `cuadrante`: Código del cuadrante (ej: "C-01")
   - `distrito`: Nombre del distrito
   - `comisaria`: Nombre de la comisaría responsable
   - `riesgo_base`: Nivel de riesgo base ("bajo", "medio", "alto")

### 2. Formato Esperado

```json
{
  "type": "FeatureCollection",
  "name": "Plan Cuadrante PNP - La Libertad",
  "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
  "features": [
    {
      "type": "Feature",
      "properties": {
        "cuadrante": "C-01",
        "distrito": "Trujillo",
        "comisaria": "Comisaría Trujillo Centro",
        "riesgo_base": "medio"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[-79.032, -8.110], [-79.026, -8.110], ...]]
      }
    }
  ]
}
```

### 3. Campos Adicionales Soportados

El sistema también soporta estos campos opcionales en `properties`:
- `provincia`: Nombre de la provincia
- `region`: Nombre de la región/departamento
- `poblacion`: Población estimada del cuadrante
- `area_km2`: Área en kilómetros cuadrados

### 4. Reemplazar el Archivo

Una vez obtenido el GeoJSON oficial:

1. Reemplaza el contenido de `plan_cuadrante_la_libertad.geojson` con el archivo oficial
2. Asegúrate de que el archivo esté codificado en UTF-8
3. Verifica que el JSON sea válido usando un validador de GeoJSON
4. Reconstruye el contenedor `agent-api`:

```bash
docker compose build agent-api
docker compose up -d agent-api
```

### 5. Verificación

Verifica que el GeoJSON se carga correctamente:

```bash
curl http://localhost:8000/v1/heatmap/cuadrantes
```

Debería devolver el GeoJSON con todos los cuadrantes oficiales.

## Notas Técnicas

- El sistema usa `shapely` o `geojson` para procesar el archivo
- Las coordenadas deben estar en WGS84 (CRS84)
- Los polígonos deben ser válidos y cerrados
- El sistema soporta MultiPolygon para cuadrantes complejos
