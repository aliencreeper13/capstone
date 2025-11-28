/**
 * World Map Viewer Component
 * Unified visualization combining terrain, nodes, paths, and armies
 */

import React, { useEffect, useRef, useState } from 'react';
import { WorldMapData, Army } from '../types/gameState';
import { GameApiService } from '../services/gameApi';
import './styles/WorldMapViewer.css';

interface WorldMapViewerProps {
  selectedArmy?: string | null;
  onArmySelect?: (armyId: string | null) => void;
}

const WorldMapViewer: React.FC<WorldMapViewerProps> = ({ selectedArmy, onArmySelect }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [mapData, setMapData] = useState<WorldMapData | null>(null);
  const [armies, setArmies] = useState<Army[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());

  const CANVAS_WIDTH = 1200;
  const CANVAS_HEIGHT = 800;
  const PADDING = 40;
  const NODE_RADIUS = 6;
  const PATH_WIDTH = 2;

  // Perlin noise-like function for green noise terrain
  const generateTerrainNoise = (seed: number, x: number, y: number, scale: number = 100): number => {
    // Simple hash-based pseudo-random generator seeded with coordinates
    const n = Math.sin(x * 12.9898 + y * 78.233 + seed) * 43758.5453;
    return n - Math.floor(n);
  };

  // Generate terrain pattern on canvas
  const renderTerrain = (ctx: CanvasRenderingContext2D, seed: number) => {
    const imageData = ctx.createImageData(CANVAS_WIDTH, CANVAS_HEIGHT);
    const data = imageData.data;

    // Create green noise pattern
    const pixelSize = 4; // 4x4 pixels per noise sample for efficiency
    for (let y = 0; y < CANVAS_HEIGHT; y += pixelSize) {
      for (let x = 0; x < CANVAS_WIDTH; x += pixelSize) {
        const noiseValue = generateTerrainNoise(seed, x / 50, y / 50);
        // Create various shades of green
        const greenValue = Math.floor(50 + noiseValue * 80);
        const baseRed = Math.floor(20 + noiseValue * 30);
        const baseGreen = greenValue;
        const baseBlue = Math.floor(20 + noiseValue * 40);

        for (let dy = 0; dy < pixelSize && y + dy < CANVAS_HEIGHT; dy++) {
          for (let dx = 0; dx < pixelSize && x + dx < CANVAS_WIDTH; dx++) {
            const idx = ((y + dy) * CANVAS_WIDTH + (x + dx)) * 4;
            data[idx] = baseRed;      // R
            data[idx + 1] = baseGreen; // G
            data[idx + 2] = baseBlue;  // B
            data[idx + 3] = 255;       // A
          }
        }
      }
    }

    ctx.putImageData(imageData, 0, 0);
  };

  // Draw the complete map
  const drawMap = (ctx: CanvasRenderingContext2D, data: WorldMapData, armiesData: Army[]) => {
    if (!ctx) return;

    // Clear canvas
    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

    // Render terrain
    renderTerrain(ctx, data.seed);

    // Calculate scale for node positioning
    const [mapWidth, mapHeight] = data.size;
    const scaleX = (CANVAS_WIDTH - 2 * PADDING) / mapWidth;
    const scaleY = (CANVAS_HEIGHT - 2 * PADDING) / mapHeight;

    // Helper to convert world coords to canvas coords
    const worldToCanvas = (x: number, y: number): [number, number] => [
      PADDING + x * scaleX,
      PADDING + y * scaleY,
    ];

    // Draw paths first (so they appear behind nodes)
    ctx.strokeStyle = '#8B6F47'; // Brown color
    ctx.lineWidth = PATH_WIDTH;
    data.paths.forEach((path) => {
      const [x1, y1] = worldToCanvas(path.from_coords[0], path.from_coords[1]);
      const [x2, y2] = worldToCanvas(path.to_coords[0], path.to_coords[1]);

      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    });

    // Draw nodes
    data.nodes.forEach((node) => {
      const [x, y] = worldToCanvas(node.coords[0], node.coords[1]);
      ctx.fillStyle = node.is_friendly ? '#3B82F6' : node.is_claimed ? '#EF4444' : '#404040'; // Blue, Red, Dark Gray
      ctx.beginPath();
      ctx.arc(x, y, NODE_RADIUS, 0, Math.PI * 2);
      ctx.fill();

      // Highlight effect if hovered or highlighted
      if (hoveredNode === node.id || highlightedNodes.has(node.id)) {
        ctx.strokeStyle = '#FFD700';
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // Draw labels for cities
      if (node.city_name) {
        ctx.fillStyle = '#FFFFFF';
        ctx.font = 'bold 12px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText(node.city_name, x, y + NODE_RADIUS + 5);
      }
    });

    // Draw armies as badges
    armiesData.forEach((army) => {
      // Find army position from map data
      // For now, place armies at their location node
      const nodeId = army.location; // Assuming this matches node id

      const node = data.nodes.find((n) =>
        (n.city_name === nodeId || n.id === nodeId)
      );

      if (node) {
        const [x, y] = worldToCanvas(node.coords[0], node.coords[1]);

        // Draw army badge (small circle with number)
        ctx.fillStyle = selectedArmy === army.id ? '#FFD700' : '#FFA500'; // Gold if selected, Orange otherwise
        ctx.beginPath();
        ctx.arc(x - 10, y - 10, 8, 0, Math.PI * 2);
        ctx.fill();

        // Draw unit count
        ctx.fillStyle = '#000000';
        ctx.font = 'bold 10px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(army.unit_count.toString(), x - 10, y - 10);
      }
    });

    // Draw legend
    drawLegend(ctx);
  };

  // Draw map legend
  const drawLegend = (ctx: CanvasRenderingContext2D) => {
    const legendX = CANVAS_WIDTH - 180;
    const legendY = 10;

    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(legendX, legendY, 170, 110);

    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 12px Arial';
    ctx.textAlign = 'left';
    ctx.fillText('Legend:', legendX + 10, legendY + 10);

    // Friendly
    ctx.fillStyle = '#3B82F6';
    ctx.beginPath();
    ctx.arc(legendX + 15, legendY + 30, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#FFFFFF';
    ctx.font = '11px Arial';
    ctx.fillText('Friendly City', legendX + 25, legendY + 26);

    // Hostile
    ctx.fillStyle = '#EF4444';
    ctx.beginPath();
    ctx.arc(legendX + 15, legendY + 50, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#FFFFFF';
    ctx.fillText('Hostile City', legendX + 25, legendY + 46);

    // Unclaimed
    ctx.fillStyle = '#404040';
    ctx.beginPath();
    ctx.arc(legendX + 15, legendY + 70, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#FFFFFF';
    ctx.fillText('Unclaimed Node', legendX + 25, legendY + 66);

    // Army
    ctx.fillStyle = '#FFA500';
    ctx.beginPath();
    ctx.arc(legendX + 15, legendY + 90, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#FFFFFF';
    ctx.fillText('Army', legendX + 25, legendY + 86);
  };

  // Fetch map data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [mapDataRes, armiesRes] = await Promise.all([
          GameApiService.getWorldMapData(),
          GameApiService.getArmies(),
        ]);
        setMapData(mapDataRes);
        setArmies(armiesRes);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load map data');
        console.error('Map loading error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // Poll for updates every 2 seconds
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  // Render map when data changes
  useEffect(() => {
    if (!canvasRef.current || !mapData) return;

    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;

    drawMap(ctx, mapData, armies);
  }, [mapData, armies, hoveredNode, highlightedNodes, selectedArmy]);

  // Handle canvas mouse events
  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!mapData || !canvasRef.current) return;

    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const [mapWidth, mapHeight] = mapData.size;
    const scaleX = (CANVAS_WIDTH - 2 * PADDING) / mapWidth;
    const scaleY = (CANVAS_HEIGHT - 2 * PADDING) / mapHeight;

    // Check if hovering over any node
    let hoveredId: string | null = null;
    for (const node of mapData.nodes) {
      const canvasX = PADDING + node.coords[0] * scaleX;
      const canvasY = PADDING + node.coords[1] * scaleY;
      const dist = Math.sqrt((x - canvasX) ** 2 + (y - canvasY) ** 2);

      if (dist <= NODE_RADIUS + 5) {
        hoveredId = node.id;
        break;
      }
    }

    setHoveredNode(hoveredId);
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!mapData || !canvasRef.current) return;

    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const [mapWidth, mapHeight] = mapData.size;
    const scaleX = (CANVAS_WIDTH - 2 * PADDING) / mapWidth;
    const scaleY = (CANVAS_HEIGHT - 2 * PADDING) / mapHeight;

    // Check if clicked on any node
    for (const node of mapData.nodes) {
      const canvasX = PADDING + node.coords[0] * scaleX;
      const canvasY = PADDING + node.coords[1] * scaleY;
      const dist = Math.sqrt((x - canvasX) ** 2 + (y - canvasY) ** 2);

      if (dist <= NODE_RADIUS + 5) {
        // Highlight adjacent nodes (future movement feature)
        // For now, just mark this as selected
        setHighlightedNodes(new Set([node.id]));
        return;
      }
    }

    setHighlightedNodes(new Set());
  };

  if (loading) {
    // return <div className="world-map-viewer"><div className="loading">Loading world map...</div></div>;
  }

  if (error) {
    return <div className="world-map-viewer"><div className="error">{error}</div></div>;
  }

  return (
    <div className="world-map-viewer">
      <div className="map-container">
        <canvas
          ref={canvasRef}
          width={CANVAS_WIDTH}
          height={CANVAS_HEIGHT}
          onMouseMove={handleCanvasMouseMove}
          onClick={handleCanvasClick}
          className="map-canvas"
          title="Click nodes to select. Hover for info."
        />
      </div>
      <div className="map-info">
        <h3>World Map</h3>
        <p>
          <strong>Seed:</strong> {mapData?.seed}
        </p>
        <p>
          <strong>Nodes:</strong> {mapData?.nodes.length || 0}
        </p>
        <p>
          <strong>Paths:</strong> {mapData?.paths.length || 0}
        </p>
        <p>
          <strong>Armies:</strong> {armies.length || 0}
        </p>
        {hoveredNode && (
          <div className="hovered-info">
            <p><strong>Selected Node:</strong> {hoveredNode}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorldMapViewer;