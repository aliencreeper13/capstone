/**
 * World Map Viewer Component - Comprehensive Visualization
 * Displays: terrain, nodes, paths, and armies with interactive features
 * 
 * This component renders a complete world map visualization with:
 * - Procedurally generated terrain using seeded noise
 * - Game nodes (cities) color-coded by ownership
 * - Paths connecting nodes as brown lines
 * - Army indicators: blue circles for moving armies, blue squares for stationed armies
 * - Interactive selection of armies to view details and move them
 */

import React, { useEffect, useRef, useState } from 'react';
import { GameApiService } from '../services/gameApi';
import { Army } from '../types/gameState';
import './styles/WorldMapViewer.css';

/**
 * MapData interface represents the processed map structure
 * Contains node and path information with coordinate and ownership data
 */
interface MapData {
  seed: number;
  size: [number, number];
  nodes: Array<{
    id: string;
    coords: [number, number];
    is_claimed: boolean;
    city_name?: string;
    claimed_by?: string;
    is_friendly: boolean;
    size: number;
    armies: string[]; // Array of army IDs stationed at this node
  }>;
  paths: Array<{
    id: string;
    from_coords: [number, number];
    to_coords: [number, number];
    distance: number;
  }>;
}

const WorldMapViewer: React.FC = () => {
  // Canvas reference for direct drawing
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  // State management
  const [mapData, setMapData] = useState<MapData | null>(null);
  const [armies, setArmies] = useState<Army[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedArmy, setSelectedArmy] = useState<Army | null>(null);
  const [canMove, setCanMove] = useState(false);
  const [adjacentNodes, setAdjacentNodes] = useState<any[]>([]);
  const [adjacentNodesMap, setAdjacentNodesMap] = useState<Record<string, any[]>>({});

  // Responsive canvas size (fills available container)
  const [canvasSize, setCanvasSize] = useState({ width: 1000, height: 700 });

  // Canvas rendering constants (derived from container)
  const CANVAS_WIDTH = canvasSize.width;
  const CANVAS_HEIGHT = canvasSize.height;

  const PADDING = 50; // Padding from canvas edge
  const NODE_RADIUS = 8; // Radius of node circles
  const ARMY_INDICATOR_SIZE = 10; // Radius of moving army circles
  const STATIONED_SQUARE_SIZE = 36; // size of the blue square for stationed armies

  // Resize observer to keep canvas filling its parent container
  useEffect(() => {
    const resize = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        // ensure minimum sensible sizes
        setCanvasSize({
          width: Math.max(320, Math.floor(rect.width)),
          height: Math.max(240, Math.floor(rect.height))
        });
      }
    };

    resize();
    const ro = new ResizeObserver(resize);
    if (containerRef.current) ro.observe(containerRef.current);
    window.addEventListener("resize", resize);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", resize);
    };
  }, []);

  /**
   * Generates seeded pseudo-random noise using sine-based hash
   * The seed ensures deterministic terrain generation (same seed = same terrain)
   * Coordinates are scaled by dividing by 50 to create larger terrain features
   */
  const generateTerrainNoise = (seed: number, x: number, y: number): number => {
    const n = Math.sin(x * 12.9898 + y * 78.233 + seed) * 43758.5453;
    return n - Math.floor(n);
  };

  /**
   * Renders procedural terrain background on the canvas
   * Uses seeded noise to generate a consistent green-tinted landscape
   * Processes pixels in 4x4 chunks for performance
   */
  const renderTerrain = (ctx: CanvasRenderingContext2D, seed: number) => {
    const imageData = ctx.createImageData(CANVAS_WIDTH, CANVAS_HEIGHT);
    const data = imageData.data;

    // Process in 4-pixel chunks for better performance
    const pixelSize = 4;
    for (let y = 0; y < CANVAS_HEIGHT; y += pixelSize) {
      for (let x = 0; x < CANVAS_WIDTH; x += pixelSize) {
        // Generate noise value between 0 and 1
        const noiseValue = generateTerrainNoise(seed, x / 50, y / 50);
        
        // Create RGB values based on noise (mostly green with variation)
        const greenValue = Math.floor(50 + noiseValue * 80);
        const baseRed = Math.floor(20 + noiseValue * 30);
        const baseGreen = greenValue;
        const baseBlue = Math.floor(20 + noiseValue * 40);

        // Apply color to all pixels in the chunk
        for (let dy = 0; dy < pixelSize && y + dy < CANVAS_HEIGHT; dy++) {
          for (let dx = 0; dx < pixelSize && x + dx < CANVAS_WIDTH; dx++) {
            const idx = ((y + dy) * CANVAS_WIDTH + (x + dx)) * 4;
            data[idx] = baseRed;      // Red channel
            data[idx + 1] = baseGreen; // Green channel
            data[idx + 2] = baseBlue;  // Blue channel
            data[idx + 3] = 255;       // Alpha channel (full opacity)
          }
        }
      }
    }

    // Copy the generated image data to canvas
    ctx.putImageData(imageData, 0, 0);
  };

  /**
   * Converts world coordinates to canvas pixel coordinates
   * Accounts for map size, canvas dimensions, and padding
   * Scales the world map to fit within the canvas drawing area
   */
  const worldToCanvas = (coords: [number, number], mapSize: [number, number]): [number, number] => {
    const scaleX = (CANVAS_WIDTH - 2 * PADDING) / mapSize[0];
    const scaleY = (CANVAS_HEIGHT - 2 * PADDING) / mapSize[1];
    return [
      PADDING + coords[0] * scaleX,
      PADDING + coords[1] * scaleY
    ];
  };

  /**
   * Main rendering function that draws the entire map
   * Called whenever map data or armies change
   * Rendering order: terrain -> paths -> nodes -> moving armies -> stationed armies -> legend
   */
  const drawMap = (ctx: CanvasRenderingContext2D, data: MapData, armiesData: Army[]) => {
    if (!ctx || !data) return;

    // Ensure canvas internal pixels match our size (in case props changed)
    if (canvasRef.current && (canvasRef.current.width !== CANVAS_WIDTH || canvasRef.current.height !== CANVAS_HEIGHT)) {
      canvasRef.current.width = CANVAS_WIDTH;
      canvasRef.current.height = CANVAS_HEIGHT;
    }
    
    // Clear canvas with dark background
    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    
    // Render procedurally generated terrain
    renderTerrain(ctx, data.seed);

    // Draw paths as brown lines connecting nodes
    ctx.strokeStyle = '#8B6F47';
    ctx.lineWidth = 2;
    data.paths.forEach((path) => {
      const [x1, y1] = worldToCanvas(path.from_coords, data.size);
      const [x2, y2] = worldToCanvas(path.to_coords, data.size);
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    });

    // Draw nodes as color-coded circles
    data.nodes.forEach((node) => {
      const [x, y] = worldToCanvas(node.coords, data.size);

      // Color coding: green (friendly), red (hostile), gray (unclaimed)
      if (node.is_friendly) {
        // Friendly: player's own empire
        ctx.fillStyle = '#27ae60';
      } else if (node.is_claimed && node.claimed_by) {
        // Hostile: claimed by another empire
        ctx.fillStyle = '#e74c3c';
      } else {
        // Unclaimed: no city or no owner
        ctx.fillStyle = '#606060';
      }

      // Draw node circle
      ctx.beginPath();
      ctx.arc(x, y, NODE_RADIUS, 0, Math.PI * 2);
      ctx.fill();

      // Draw coordinate labels
      ctx.fillStyle = '#ffffff';
      ctx.font = '19px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      ctx.fillText(`(${node.coords[0]}, ${node.coords[1]})`, x, y - NODE_RADIUS - 8);

      // Draw city name label if node has a city
      if (node.city_name) {
        ctx.fillStyle = '#ffffff';
        ctx.font = '11px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText(node.city_name, x, y + NODE_RADIUS + 5);
      }
    });

    // Draw moving armies as blue circles positioned along paths
    data.paths.forEach((path) => {
      // Filter armies on this specific path by matching coordinates
      const pathArmies = armiesData.filter(
        a => a.is_on_path && 
             a.path_position !== undefined && 
             a.path_node1_coords && 
             a.path_node2_coords &&
             ((a.path_node1_coords[0] === path.from_coords[0] && a.path_node1_coords[1] === path.from_coords[1] &&
               a.path_node2_coords[0] === path.to_coords[0] && a.path_node2_coords[1] === path.to_coords[1]) ||
              (a.path_node1_coords[0] === path.to_coords[0] && a.path_node1_coords[1] === path.to_coords[1] &&
               a.path_node2_coords[0] === path.from_coords[0] && a.path_node2_coords[1] === path.from_coords[1]))
      );
      
      pathArmies.forEach((army) => {
        const [x1, y1] = worldToCanvas(path.from_coords, data.size);
        const [x2, y2] = worldToCanvas(path.to_coords, data.size);

        // Calculate position along path (0 to distance)
        // Need to handle both directions: forward and backward
        let progress = 0;
        if (army.path_node1_coords && army.path_node2_coords) {
          const isForward = 
            army.path_node1_coords[0] === path.from_coords[0] &&
            army.path_node1_coords[1] === path.from_coords[1];
          
          // If moving backwards, flip the progress
          if (isForward) {
            progress = (army.path_position || 0) / (path.distance || 1);
          } else {
            progress = 1 - ((army.path_position || 0) / (path.distance || 1));
          }
        }
        
        // Interpolate between start and end coordinates
        const armyX = x1 + (x2 - x1) * progress;
        const armyY = y1 + (y2 - y1) * progress;

        // Draw blue circle for moving army
        ctx.fillStyle = '#3498db';
        ctx.beginPath();
        ctx.arc(armyX, armyY, ARMY_INDICATOR_SIZE, 0, Math.PI * 2);
        ctx.fill();

        // Highlight selected army with golden outline
        if (selectedArmy && selectedArmy.id === army.id) {
          ctx.strokeStyle = '#f39c12';
          ctx.lineWidth = 2;
          ctx.stroke();
        }
      });
    });

    // Draw stationed armies as blue squares next to nodes
    data.nodes.forEach((node) => {
      const nodeArmyIds = node.armies;
      // Get armies stationed at this node (not on paths, matching by ID)
      const nodeArmies = armiesData.filter(a => !a.is_on_path && nodeArmyIds.includes(a.id));
      
      // Only draw if there are stationed armies
      if (nodeArmies.length > 0) {
        // Also make sure that all stationed armies are not empty
        if (!nodeArmies.every(a => a.unit_count === 0))
        {
            const [x, y] = worldToCanvas(node.coords, data.size);
            const squareSize = STATIONED_SQUARE_SIZE;
 
            // Draw blue square for stationed army
            ctx.fillStyle = '#3498db';
            ctx.fillRect(x + 12, y - 8, squareSize, squareSize);

            // Highlight selected army with golden outline
            if (selectedArmy && nodeArmies.find(a => a.id === selectedArmy.id)) {
              ctx.strokeStyle = '#f39c12';
              ctx.lineWidth = 2;
              ctx.strokeRect(x + 12, y - 8, squareSize, squareSize);
            }
        }
      }
    });

    // Draw legend in bottom right corner
    drawLegend(ctx);
  };

  /**
   * Draws a legend box explaining the map symbols
   * Positioned in the bottom-right corner with semi-transparent background
   */
  const drawLegend = (ctx: CanvasRenderingContext2D) => {
    const legendX = CANVAS_WIDTH - 200;
    const legendY = 10;
    const boxWidth = 190;
    const boxHeight = 130;

    // Semi-transparent black background
    ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
    ctx.fillRect(legendX, legendY, boxWidth, boxHeight);

    // Legend title
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 13px Arial';
    ctx.textAlign = 'left';
    ctx.fillText('Legend:', legendX + 10, legendY + 12);

    // Legend items with symbols and labels
    const items = [
      { color: '#27ae60', label: 'Your City', y: 30 },
      { color: '#e74c3c', label: 'Enemy City', y: 48 },
      { color: '#606060', label: 'Unclaimed', y: 66 },
      { color: '#3498db', label: 'Army (●=moving, ■=stationed)', y: 84 },
      { color: '#8B6F47', label: 'Path', y: 102 },
    ];

    // Draw each legend item with appropriate symbol
    items.forEach((item) => {
      ctx.fillStyle = item.color;
      if (item.label.includes('Path')) {
        // Draw line for paths
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(legendX + 15, legendY + item.y);
        ctx.lineTo(legendX + 25, legendY + item.y);
        ctx.stroke();
      } else if (item.label.includes('moving')) {
        // Draw small circle for moving armies
        ctx.beginPath();
        ctx.arc(legendX + 18, legendY + item.y, 3, 0, Math.PI * 2);
        ctx.fill();
      } else if (item.label.includes('stationed')) {
        // Draw small square for stationed armies
        ctx.fillRect(legendX + 16, legendY + item.y - 2, 4, 4);
      } else {
        // Draw circle for cities/nodes
        ctx.beginPath();
        ctx.arc(legendX + 18, legendY + item.y, 5, 0, Math.PI * 2);
        ctx.fill();
      }

      // Draw label text
      ctx.fillStyle = '#ffffff';
      ctx.font = '11px Arial';
      ctx.fillText(item.label, legendX + 30, legendY + item.y - 5);
    });
  };

  /**
   * Effect hook: Fetches map and army data on component mount
   * Polls for updated data every 2 seconds to keep UI in sync with backend
   * Transforms backend responses to MapData format
   */
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Fetch map structure, armies, and game state in parallel
        const [mapDataRes, armiesRes, gameState] = await Promise.all([
          GameApiService.getMapStructure(),
          GameApiService.getArmies(),
          GameApiService.getGameState(),
        ]);

        const playerEmpireName = gameState.empire.name;
        console.log("Player empire name:", playerEmpireName);
        console.log("Sample nodes from backend:", (mapDataRes as any).nodes.slice(0, 3));

        // Transform backend map data to local MapData format
        const finalMapData: MapData = {
          seed: 42,
          size: [200, 200],
          // Transform nodes: extract relevant fields and ensure armies array exists
          nodes: (mapDataRes as any).nodes.map((n: any) => {
            // Determine if node is friendly based on claimed_by field
            let isFriendly = false;
            if (n.claimed_by === playerEmpireName) {
              isFriendly = true;
            }

            return {
              id: n.id,
              coords: n.coords,
              is_claimed: n.is_claimed,
              city_name: n.city_name,
              claimed_by: n.claimed_by,
              is_friendly: isFriendly,
              size: n.size,
              armies: n.armies || [] // Array of army IDs at this node
            };
          }),
          // Transform paths: normalize field names from backend
          paths: (mapDataRes as any).paths.map((p: any) => ({
            id: p.id,
            from_coords: p.node1_coords || p.from_coords,
            to_coords: p.node2_coords || p.to_coords,
            distance: p.distance
          }))
        };

        // Update state with fetched data
        setMapData(finalMapData);
        setArmies(armiesRes);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load map data');
        console.error('Map loading error:', err);
      } finally {
        setLoading(false);
      }
    };

    // Fetch immediately on mount and poll
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  /**
   * Effect hook: Renders the map whenever data or selected army changes
   * Gets canvas context and calls drawMap with current state
   */
  useEffect(() => {
    if (!canvasRef.current || !mapData) return;

    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;

    drawMap(ctx, mapData, armies);
  }, [mapData, armies, selectedArmy, CANVAS_WIDTH, CANVAS_HEIGHT]);

  /**
   * Effect hook: Fetches adjacent nodes for each non-moving army
   * When an army is at a node, we fetch the neighboring nodes it can move to
   */
  useEffect(() => {
    if (!mapData) return;

    const fetchAdjacentNodesForArmies = async () => {
      const newAdjacentNodesMap: Record<string, any[]> = {};

      for (const army of armies) {
        // Only fetch for non-empty, stationed armies
        if (army.unit_count > 0 && !army.is_on_path) {
          // Find the node where this army is located
          const currentNode = mapData.nodes.find(n => n.armies.includes(army.id));
          if (currentNode) {
            try {
              const adjacentNodes = await GameApiService.getAdjacentNodes(currentNode.id);
              newAdjacentNodesMap[army.id] = adjacentNodes;
            } catch (err) {
              console.error(`Failed to fetch adjacent nodes for army ${army.id}:`, err);
              newAdjacentNodesMap[army.id] = [];
            }
          }
        } else {
          newAdjacentNodesMap[army.id] = [];
        }
      }

      setAdjacentNodesMap(newAdjacentNodesMap);
    };

    fetchAdjacentNodesForArmies();
  }, [armies, mapData]);

  /**
   * Handles army movement from the army list panel
   * Sends movement command to backend and disables dropdown until army reaches destination
   */
  const handleArmyMovement = async (armyId: string, destinationNodeId: string) => {
    try {
      await GameApiService.moveArmy(armyId, destinationNodeId);
    } catch (err) {
      console.error(`Failed to move army ${armyId}:`, err);
    }
  };

  /**
   * Handles canvas click events for selecting armies
   * First checks for moving armies on paths, then checks for stationed armies at nodes
   * Updates selected army and loads adjacent nodes if needed
   */
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!mapData || !canvasRef.current) return;

    // Get click position relative to canvas
    const rect = canvasRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    // Check if click hit a moving army
    mapData.paths.forEach((path) => {
      const pathArmies = armies.filter(a => a.is_on_path);
      pathArmies.forEach((army) => {
        const [x1, y1] = worldToCanvas(path.from_coords, mapData.size);
        const [x2, y2] = worldToCanvas(path.to_coords, mapData.size);
        const progress = (army.position || 0) / (path.distance || 1);
        const armyX = x1 + (x2 - x1) * progress;
        const armyY = y1 + (y2 - y1) * progress;

        // Check if click is within 12 pixels of army circle
        const dist = Math.sqrt((clickX - armyX) ** 2 + (clickY - armyY) ** 2);
        if (dist <= 12) {
          setSelectedArmy(army);
          setCanMove(false); // Moving armies can't be moved via UI
        }
      });
    });

    // Check if click hit a stationed army
    mapData.nodes.forEach((node) => {
      const nodeArmyIds = node.armies;
      const nodeArmies = armies.filter(a => !a.is_on_path && nodeArmyIds.includes(a.id));
      if (nodeArmies.length > 0) {
        const [x, y] = worldToCanvas(node.coords, mapData.size);
        const squareX = x + 12;
        const squareY = y - 8;
        const squareSize = STATIONED_SQUARE_SIZE;
 
        // Check if click is within the square bounds
        if (clickX >= squareX && clickX <= squareX + squareSize &&
            clickY >= squareY && clickY <= squareY + squareSize) {
          // Select first army at this node
          setSelectedArmy(nodeArmies[0]);
          setCanMove(true); // Stationed armies can be moved
          // Load adjacent nodes for movement options
          GameApiService.getAdjacentNodes(node.id).then(setAdjacentNodes);
        }
      }
    });
  };

  // Render loading/error states
  if (loading) {}
  if (error) return <div className="world-map-viewer error"><p>{error}</p></div>;
  if (!mapData) return <div className="world-map-viewer"><p>No map data</p></div>;

  return (
    <div className="world-map-viewer">
      <div className="left-panel">
        {/* Canvas for rendering map */}
        <div ref={containerRef} className="map-container">
          <canvas
            ref={canvasRef}
            width={CANVAS_WIDTH}
            height={CANVAS_HEIGHT}
            onClick={handleCanvasClick}
            className="map-canvas"
            title="Click on army indicators to select them"
          />
        </div>
      </div>

      {/* Right side: armies and selected army details */}
      <div className="right-panel">
        {/* Side panel showing all armies with movement options */}
        <div className="armies-list-panel">
           <h4>Armies</h4>
           <div className="armies-list">
             {armies.filter(a => a.unit_count > 0).length === 0 ? (
               <p className="no-armies">No armies available</p>
             ) : (
               armies
                 .filter(a => a.unit_count > 0)
                 .map((army) => {
                   const currentNode = mapData?.nodes.find(n => n.armies.includes(army.id));
                   const adjacentNodesForArmy = adjacentNodesMap[army.id] || [];
                   const canMoveArmy = !army.is_on_path && adjacentNodesForArmy.length > 0;

                   return (
                     <div key={army.id} className="army-item">
                       <div className="army-header">
                         <h5>{army.name || `Army ${army.id.slice(0, 8)}`}</h5>
                         <span className={`status-badge ${army.is_on_path ? 'moving' : 'stationed'}`}>
                           {army.is_on_path ? 'Moving' : 'Stationed'}
                         </span>
                       </div>
                       <div className="army-details">
                         <p><strong>Units:</strong> {army.unit_count}</p>
                         <p><strong>Position:</strong> ({currentNode?.coords[0]}, {currentNode?.coords[1]})</p>
                         {currentNode?.city_name && (
                           <p><strong>City:</strong> {currentNode.city_name}</p>
                         )}
                       </div>
                       {canMoveArmy && (
                         <div className="movement-dropdown">
                           <label htmlFor={`army-${army.id}`}>Move to:</label>
                           <select
                             id={`army-${army.id}`}
                             defaultValue=""
                             onChange={(e) => {
                               if (e.target.value) {
                                 handleArmyMovement(army.id, e.target.value);
                                 e.target.value = '';
                             }
                           }}
                           className="destination-select"
                         >
                           <option value="">Select destination...</option>
                           {adjacentNodesForArmy.map((node) => (
                             <option key={node.id} value={node.id}>
                               {node.city_name || `(${node.coords[0]}, ${node.coords[1]})`}
                             </option>
                           ))}
                         </select>
                       </div>
                     )}
                   </div>
                 );
               })
             )}
           </div>
         </div>

         {/* Side panel showing selected army details and movement options */}
         {selectedArmy && (
           <div className="selected-army-panel">
           <h4>{selectedArmy.name}</h4>
           <div className="army-info">
             <p><strong>Units:</strong> {selectedArmy.unit_count}</p>
             <p><strong>Location:</strong> {selectedArmy.location}</p>
             {selectedArmy.is_on_path ? (
               <p><strong>Status:</strong> Moving ({selectedArmy.is_halted ? 'Halted' : 'Moving'})</p>
             ) : (
               <p><strong>Status:</strong> Stationed</p>
             )}
             {/* Movement buttons shown only for stationed armies with adjacent nodes */}
             {canMove && adjacentNodes.length > 0 && (
               <div className="movement-options">
                 <p><strong>Move to:</strong></p>
                 <div className="destination-buttons">
                   {adjacentNodes.map((node) => (
                     <button
                       key={node.id}
                       onClick={() => GameApiService.moveArmy(selectedArmy.id, node.id)}
                       className="destination-btn"
                     >
                       {node.city_name || `(${node.coords[0]}, ${node.coords[1]})`}
                     </button>
                   ))}
                 </div>
               </div>
             )}
           </div>
         </div>
         )}
       </div>
     </div>
   );
 };
 
 export default WorldMapViewer;
