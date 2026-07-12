'use client';

import { useEffect, useRef, useState } from 'react';
import { Loader2 } from 'lucide-react';

interface Node {
  id: string;
  title: string;
  year: string;
  citations: string;
  source: string;
  url: string;
}

interface Edge {
  source: string;
  target: string;
  type: string;
}

interface CitationGraphData {
  nodes: Node[];
  edges: Edge[];
  stats: {
    total_nodes: number;
    total_edges: number;
    papers_analyzed: number;
  };
}

interface CitationGraphProps {
  projectId: string;
}

export default function CitationGraph({ projectId }: CitationGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<CitationGraphData | null>(null);
  const [error, setError] = useState('');
  const [token, setToken] = useState('');

  useEffect(() => {
    try {
      const stored = localStorage.getItem('research-ide-auth');
      if (stored) setToken(JSON.parse(stored)?.state?.accessToken || '');
    } catch {}
  }, []);

  useEffect(() => {
    const fetchGraph = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const res = await fetch(`${apiUrl}/api/agents/${projectId}/citation-graph`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        
        if (!res.ok) throw new Error('Failed to fetch citation graph');
        
        const graphData = await res.json();
        setData(graphData);
        drawGraph(graphData);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };

    fetchGraph();
  }, [projectId, token]);

  const drawGraph = (graphData: CitationGraphData) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Simple force-directed layout (simplified)
    const nodes = graphData.nodes.map((node, i) => ({
      ...node,
      x: width / 2 + Math.cos(i * 2 * Math.PI / graphData.nodes.length) * 200,
      y: height / 2 + Math.sin(i * 2 * Math.PI / graphData.nodes.length) * 200,
    }));

    // Draw edges
    ctx.strokeStyle = '#4B5563';
    ctx.lineWidth = 1;
    graphData.edges.forEach(edge => {
      const sourceNode = nodes.find(n => n.id === edge.source);
      const targetNode = nodes.find(n => n.id === edge.target);
      if (sourceNode && targetNode) {
        ctx.beginPath();
        ctx.moveTo(sourceNode.x, sourceNode.y);
        ctx.lineTo(targetNode.x, targetNode.y);
        ctx.stroke();
      }
    });

    // Draw nodes
    nodes.forEach(node => {
      // Node circle
      ctx.beginPath();
      ctx.arc(node.x, node.y, 20, 0, 2 * Math.PI);
      ctx.fillStyle = node.source === 'semantic_scholar' ? '#3B82F6' : '#10B981';
      ctx.fill();
      ctx.strokeStyle = '#1F2937';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Node label
      ctx.fillStyle = '#F9FAFB';
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'center';
      const title = node.title.length > 20 ? node.title.substring(0, 20) + '...' : node.title;
      ctx.fillText(title, node.x, node.y - 25);
      ctx.fillText(`(${node.year})`, node.x, node.y + 35);
    });

    // Draw legend
    ctx.fillStyle = '#6B7280';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Legend:', 10, height - 60);
    
    ctx.beginPath();
    ctx.arc(60, height - 60, 8, 0, 2 * Math.PI);
    ctx.fillStyle = '#3B82F6';
    ctx.fill();
    ctx.fillStyle = '#6B7280';
    ctx.fillText('Semantic Scholar', 75, height - 57);
    
    ctx.beginPath();
    ctx.arc(60, height - 40, 8, 0, 2 * Math.PI);
    ctx.fillStyle = '#10B981';
    ctx.fill();
    ctx.fillStyle = '#6B7280';
    ctx.fillText('Other Sources', 75, height - 37);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-brand-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="card text-center py-8">
        <p className="text-sm text-red-400">{error}</p>
      </div>
    );
  }

  return (
    <div className="card p-4">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-[var(--text-primary)]">Citation Graph</h3>
        <p className="text-xs text-[var(--text-muted)]">
          {data?.stats.total_nodes} nodes, {data?.stats.total_edges} edges
        </p>
      </div>
      <canvas
        ref={canvasRef}
        width={800}
        height={400}
        className="w-full border border-[var(--border)] rounded-lg bg-[var(--bg-secondary)]"
      />
      <p className="text-xs text-[var(--text-muted)] mt-2 text-center">
        Visualization shows citations between papers. Blue nodes = Semantic Scholar, Green = Other sources.
      </p>
    </div>
  );
}
