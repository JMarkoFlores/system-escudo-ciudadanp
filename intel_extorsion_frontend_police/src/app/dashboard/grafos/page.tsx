'use client';

import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { useAppStore } from '@/stores/appStore';
import { graphService } from '@/services/api';
import { CriminalGraph } from '@/types';

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false });

export default function GrafosPage() {
  const { grafoActivo, setGrafoActivo, clusters, setClusters } = useAppStore();
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<any>(null);

  useEffect(() => {
    const fetchGraph = async () => {
      try {
        const { data } = await graphService.obtener();
        setGrafoActivo(data);
      } catch {
        console.error('Error cargando grafo criminal');
        setGrafoActivo({ nodes: [], links: [] });
      } finally {
        setLoading(false);
      }
    };
    fetchGraph();
  }, [setGrafoActivo]);

  const groupColors: Record<string, string> = {
    denunciante: '#3b82f6',
    sospechoso: '#ef4444',
    telefono: '#f59e0b',
    cuenta: '#10b981',
    caso: '#8b5cf6',
    evidencia: '#64748b',
  };

  if (loading) return <div className="text-center py-20 text-slate-500">Cargando red criminal...</div>;

  return (
    <div className="space-y-4 h-[calc(100vh-8rem)]">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Redes Criminales</h1>
        <p className="text-slate-500 text-sm">Visualización de grafos de correlación entre denuncias, sospechosos y evidencias</p>
      </div>

      <div className="flex space-x-4 text-xs">
        {Object.entries(groupColors).map(([group, color]) => (
          <div key={group} className="flex items-center">
            <span className="w-3 h-3 rounded-full mr-1" style={{ backgroundColor: color }} />
            <span className="capitalize text-slate-600">{group}</span>
          </div>
        ))}
      </div>

      <div className="bg-white border rounded-xl shadow-sm flex-1 overflow-hidden relative" style={{ height: '600px' }}>
        {grafoActivo && (
          <ForceGraph2D
            graphData={grafoActivo}
            nodeAutoColorBy="group"
            nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
              const label = node.label;
              const fontSize = 12 / globalScale;
              ctx.font = `${fontSize}px Sans-Serif`;
              const textWidth = ctx.measureText(label).width;
              const bckgDimensions = [textWidth, fontSize].map((n) => n + fontSize * 0.2);

              ctx.fillStyle = groupColors[node.group] || '#999';
              ctx.beginPath();
              ctx.arc(node.x, node.y, (node.val || 3) * 2, 0, 2 * Math.PI);
              ctx.fill();

              ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
              ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y + 8, bckgDimensions[0], bckgDimensions[1]);

              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              ctx.fillStyle = '#1e293b';
              ctx.fillText(label, node.x, node.y + 8 + fontSize / 2);
            }}
            linkDirectionalArrowLength={6}
            linkDirectionalArrowRelPos={1}
            linkCurvature={0.1}
            onNodeClick={(node: any) => setSelectedNode(node)}
            width={1200}
            height={600}
          />
        )}
      </div>

      {selectedNode && (
        <div className="bg-white border rounded-xl p-4 shadow-sm">
          <h4 className="font-semibold text-slate-800">{selectedNode.label}</h4>
          <p className="text-xs text-slate-500 capitalize">Tipo: {selectedNode.group}</p>
          {selectedNode.metadata && (
            <div className="mt-2 text-xs space-y-1">
              {selectedNode.metadata.zona_principal && (
                <p><strong>Zona:</strong> {selectedNode.metadata.zona_principal}</p>
              )}
              {selectedNode.metadata.nivel_alerta && (
                <p><strong>Nivel:</strong> {selectedNode.metadata.nivel_alerta}</p>
              )}
              {selectedNode.metadata.total_denuncias !== undefined && (
                <p><strong>Denuncias:</strong> {selectedNode.metadata.total_denuncias}</p>
              )}
              {selectedNode.metadata.monto_min && (
                <p><strong>Monto:</strong> {selectedNode.metadata.monto_min} - {selectedNode.metadata.monto_max}</p>
              )}
            </div>
          )}
          <pre className="text-xs bg-slate-50 p-2 rounded mt-2 overflow-auto">{JSON.stringify(selectedNode, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
