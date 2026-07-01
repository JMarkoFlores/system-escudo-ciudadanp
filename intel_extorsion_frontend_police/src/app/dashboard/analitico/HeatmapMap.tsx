'use client';

import React from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { HeatmapPoint } from '@/types';

const alertColor = (nivel: string) => {
  switch (nivel) {
    case 'critico': return '#7f1d1d';
    case 'alto': return '#ef4444';
    case 'medio': return '#f59e0b';
    default: return '#22c55e';
  }
};

interface HeatmapMapProps {
  puntos: HeatmapPoint[];
}

export default function HeatmapMap({ puntos }: HeatmapMapProps) {
  const validPoints = puntos.filter(
    (p) => p && typeof p.lat === 'number' && typeof p.lng === 'number' && !isNaN(p.lat) && !isNaN(p.lng)
  );

  return (
    <MapContainer center={[-8.1, -79.05]} zoom={11} style={{ height: '100%', width: '100%' }}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {validPoints.map((punto, idx) => (
        <CircleMarker
          key={idx}
          center={[punto.lat, punto.lng]}
          radius={12 + punto.intensidad * 20}
          fillColor={alertColor(punto.nivel_alerta_dominante)}
          color={alertColor(punto.nivel_alerta_dominante)}
          fillOpacity={0.6}
          weight={1}
        >
          <Popup>
            <div className="text-sm">
              <strong>{punto.zona}</strong><br/>
              Denuncias: {punto.total_denuncias}<br/>
              Nivel: {punto.nivel_alerta_dominante}<br/>
              Tipo: {punto.tipo_zona}
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
