import { useState, useRef, useCallback } from 'react';
import { LayoutGrid, Plus, Trash2, RotateCw, Send } from 'lucide-react';

interface PanelSpec {
    width_px: number;
    height_px: number;
    wattage: number;
    width_m: number;
    height_m: number;
}

interface PlacedPanel {
    id: number;
    xPct: number;   // % position from left
    yPct: number;   // % position from top
    wPct: number;   // % width
    hPct: number;   // % height
    rotated: boolean;
}

interface Props {
    originalImage: string;
    heatmapImage: string;
    panelSpec: PanelSpec;
    imageWidth: number;
    imageHeight: number;
    roofAreaM2: number;
    onSubmit: (panels: PlacedPanel[]) => void;
    isCalculating: boolean;
}

export type { PlacedPanel };

export function PanelEditor({
    originalImage,
    heatmapImage,
    panelSpec,
    imageWidth,
    imageHeight,
    roofAreaM2,
    onSubmit,
    isCalculating,
}: Props) {
    const [panels, setPanels] = useState<PlacedPanel[]>([]);
    const [selectedPanel, setSelectedPanel] = useState<number | null>(null);
    const [showHeatmap, setShowHeatmap] = useState(true);
    const [dragInfo, setDragInfo] = useState<{ id: number; offsetX: number; offsetY: number } | null>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const nextId = useRef(1);

    // Panel size as percentage of image
    const panelWPct = (panelSpec.width_px / imageWidth) * 100;
    const panelHPct = (panelSpec.height_px / imageHeight) * 100;

    const totalCapacityKw = (panels.length * panelSpec.wattage) / 1000;
    const totalAreaM2 = panels.length * panelSpec.width_m * panelSpec.height_m;

    const handleContainerClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
        if (dragInfo) return;
        const rect = containerRef.current?.getBoundingClientRect();
        if (!rect) return;

        // Only place if clicking on the image area (not on an existing panel)
        const target = e.target as HTMLElement;
        if (target.dataset.panel) return;

        const xPct = ((e.clientX - rect.left) / rect.width) * 100 - panelWPct / 2;
        const yPct = ((e.clientY - rect.top) / rect.height) * 100 - panelHPct / 2;

        // Clamp within bounds
        const clampedX = Math.max(0, Math.min(100 - panelWPct, xPct));
        const clampedY = Math.max(0, Math.min(100 - panelHPct, yPct));

        const newPanel: PlacedPanel = {
            id: nextId.current++,
            xPct: clampedX,
            yPct: clampedY,
            wPct: panelWPct,
            hPct: panelHPct,
            rotated: false,
        };

        setPanels(prev => [...prev, newPanel]);
        setSelectedPanel(newPanel.id);
    }, [panelWPct, panelHPct, dragInfo]);

    const handlePanelMouseDown = useCallback((e: React.MouseEvent, panelId: number) => {
        // Don't start drag if clicking on action buttons
        const target = e.target as HTMLElement;
        if (target.closest('[data-action]')) return;

        e.stopPropagation();
        e.preventDefault();
        const rect = containerRef.current?.getBoundingClientRect();
        if (!rect) return;

        const panel = panels.find(p => p.id === panelId);
        if (!panel) return;

        const panelLeftPx = (panel.xPct / 100) * rect.width;
        const panelTopPx = (panel.yPct / 100) * rect.height;

        setDragInfo({
            id: panelId,
            offsetX: e.clientX - rect.left - panelLeftPx,
            offsetY: e.clientY - rect.top - panelTopPx,
        });
        setSelectedPanel(panelId);
    }, [panels]);

    const handleMouseMove = useCallback((e: React.MouseEvent) => {
        if (!dragInfo || !containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        const panel = panels.find(p => p.id === dragInfo.id);
        if (!panel) return;

        let xPct = ((e.clientX - rect.left - dragInfo.offsetX) / rect.width) * 100;
        let yPct = ((e.clientY - rect.top - dragInfo.offsetY) / rect.height) * 100;

        xPct = Math.max(0, Math.min(100 - panel.wPct, xPct));
        yPct = Math.max(0, Math.min(100 - panel.hPct, yPct));

        setPanels(prev => prev.map(p => p.id === dragInfo.id ? { ...p, xPct, yPct } : p));
    }, [dragInfo, panels]);

    const handleMouseUp = useCallback(() => {
        setDragInfo(null);
    }, []);

    const removePanel = (id: number) => {
        setPanels(prev => prev.filter(p => p.id !== id));
        if (selectedPanel === id) setSelectedPanel(null);
    };

    const rotatePanel = (id: number) => {
        setPanels(prev => prev.map(p => {
            if (p.id !== id) return p;
            return {
                ...p,
                wPct: p.hPct,
                hPct: p.wPct,
                rotated: !p.rotated,
            };
        }));
    };

    const clearAll = () => {
        setPanels([]);
        setSelectedPanel(null);
    };

    return (
        <div className="animate-in" style={{ maxWidth: '900px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

            {/* Header */}
            <div className="glass-panel" style={{ padding: '1.5rem 2rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h2 style={{ fontSize: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                            <LayoutGrid className="text-gradient" /> Place Your Solar Panels
                        </h2>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                            Click on the roof to place panels. Drag to reposition. Click a panel to select it.
                        </p>
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button
                            className="btn btn-secondary"
                            onClick={() => setShowHeatmap(!showHeatmap)}
                            style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
                        >
                            {showHeatmap ? 'Hide' : 'Show'} Heatmap
                        </button>
                        <button
                            className="btn btn-secondary"
                            onClick={clearAll}
                            style={{ padding: '0.5rem', color: 'var(--color-danger)' }}
                            title="Clear all panels"
                        >
                            <Trash2 size={18} />
                        </button>
                    </div>
                </div>
            </div>

            {/* Interactive Image Area */}
            <div className="glass-panel" style={{ padding: '1rem', overflow: 'hidden' }}>
                <div
                    ref={containerRef}
                    onClick={handleContainerClick}
                    onMouseMove={handleMouseMove}
                    onMouseUp={handleMouseUp}
                    onMouseLeave={handleMouseUp}
                    style={{
                        position: 'relative',
                        borderRadius: '12px',
                        overflow: 'hidden',
                        cursor: dragInfo ? 'grabbing' : 'crosshair',
                        userSelect: 'none',
                        lineHeight: 0,
                    }}
                >
                    {/* Base Image */}
                    <img
                        src={originalImage}
                        alt="Roof"
                        draggable={false}
                        style={{ width: '100%', display: 'block', pointerEvents: 'none' }}
                    />

                    {/* Heatmap Overlay */}
                    {showHeatmap && (
                        <img
                            src={heatmapImage}
                            alt="Heatmap"
                            draggable={false}
                            style={{
                                position: 'absolute',
                                top: 0, left: 0, width: '100%', height: '100%',
                                opacity: 0.5,
                                mixBlendMode: 'multiply',
                                pointerEvents: 'none',
                            }}
                        />
                    )}

                    {/* Placed Panels */}
                    {panels.map((p) => {
                        const isSelected = selectedPanel === p.id;
                        return (
                            <div
                                key={p.id}
                                data-panel="true"
                                onMouseDown={(e) => handlePanelMouseDown(e, p.id)}
                                onClick={(e) => { e.stopPropagation(); setSelectedPanel(p.id); }}
                                style={{
                                    position: 'absolute',
                                    left: `${p.xPct}%`,
                                    top: `${p.yPct}%`,
                                    width: `${p.wPct}%`,
                                    height: `${p.hPct}%`,
                                    backgroundColor: isSelected
                                        ? 'rgba(26, 115, 232, 0.45)'
                                        : 'rgba(26, 115, 232, 0.3)',
                                    border: `2px solid ${isSelected ? '#1a73e8' : 'rgba(26, 115, 232, 0.6)'}`,
                                    borderRadius: '2px',
                                    cursor: dragInfo?.id === p.id ? 'grabbing' : 'grab',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    color: 'white',
                                    fontSize: '11px',
                                    fontWeight: 700,
                                    textShadow: '0 1px 3px rgba(0,0,0,0.8)',
                                    boxShadow: isSelected
                                        ? '0 0 12px rgba(26, 115, 232, 0.5)'
                                        : '0 1px 4px rgba(0,0,0,0.2)',
                                    transition: dragInfo ? 'none' : 'box-shadow 0.2s, border-color 0.2s',
                                    zIndex: isSelected ? 10 : 1,
                                }}
                            >
                                {p.id}

                                {/* Panel action buttons */}
                                {isSelected && !dragInfo && (
                                    <div
                                        data-action="true"
                                        style={{
                                            position: 'absolute',
                                            top: '-32px',
                                            left: '50%',
                                            transform: 'translateX(-50%)',
                                            display: 'flex',
                                            gap: '4px',
                                            zIndex: 20,
                                        }}
                                        onMouseDown={e => e.stopPropagation()}
                                        onClick={e => e.stopPropagation()}
                                    >
                                        <button
                                            data-action="true"
                                            onClick={(e) => { e.stopPropagation(); rotatePanel(p.id); }}
                                            style={{
                                                background: '#ffffff',
                                                border: '1px solid #d0d5dd',
                                                borderRadius: '6px',
                                                padding: '3px 6px',
                                                cursor: 'pointer',
                                                color: '#344054',
                                                display: 'flex',
                                                alignItems: 'center',
                                                boxShadow: '0 1px 3px rgba(0,0,0,0.15)'
                                            }}
                                            title="Rotate"
                                        >
                                            <RotateCw size={14} />
                                        </button>
                                        <button
                                            data-action="true"
                                            onClick={(e) => { e.stopPropagation(); removePanel(p.id); }}
                                            style={{
                                                background: '#ffffff',
                                                border: '1px solid #fda29b',
                                                borderRadius: '6px',
                                                padding: '3px 6px',
                                                cursor: 'pointer',
                                                color: '#d92d20',
                                                display: 'flex',
                                                alignItems: 'center',
                                                boxShadow: '0 1px 3px rgba(0,0,0,0.15)'
                                            }}
                                            title="Remove"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                )}
                            </div>
                        );
                    })}

                    {/* Instruction overlay when no panels */}
                    {panels.length === 0 && (
                        <div style={{
                            position: 'absolute',
                            top: '50%', left: '50%',
                            transform: 'translate(-50%, -50%)',
                            background: 'rgba(255,255,255,0.95)',
                            boxShadow: '0 4px 24px rgba(0,0,0,0.12)',
                            padding: '1.5rem 2rem',
                            borderRadius: '12px',
                            textAlign: 'center',
                            pointerEvents: 'none',
                            border: '1px solid #e4e7ec',
                        }}>
                            <Plus size={32} style={{ color: 'var(--color-primary)', marginBottom: '0.5rem' }} />
                            <p style={{ fontWeight: 600, fontSize: '1.1rem' }}>Click anywhere on the roof</p>
                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                                to place a {panelSpec.width_m}m × {panelSpec.height_m}m ({panelSpec.wattage}W) solar panel
                            </p>
                        </div>
                    )}

                    {/* Legend bar */}
                    {showHeatmap && (
                        <div style={{
                            position: 'absolute',
                            bottom: '10px', left: '10px',
                            display: 'flex', alignItems: 'center', gap: '0.5rem',
                            background: 'rgba(255,255,255,0.92)',
                            boxShadow: '0 1px 4px rgba(0,0,0,0.12)',
                            padding: '6px 12px',
                            borderRadius: '8px',
                            fontSize: '0.8rem',
                        }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Low Sun</span>
                            <div style={{ width: '80px', height: '6px', background: 'linear-gradient(90deg, #D50000, #FFD600, #00C853)', borderRadius: '3px' }} />
                            <span style={{ color: 'var(--text-secondary)' }}>High Sun</span>
                        </div>
                    )}
                </div>
            </div>

            {/* Stats Bar + Submit */}
            <div className="glass-panel" style={{ padding: '1.5rem 2rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                    {/* Stats */}
                    <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
                        <div>
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Panels</div>
                            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-primary)' }}>{panels.length}</div>
                        </div>
                        <div>
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Capacity</div>
                            <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{totalCapacityKw.toFixed(1)} kW</div>
                        </div>
                        <div>
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Area</div>
                            <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{totalAreaM2.toFixed(1)} m²</div>
                        </div>
                        <div>
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Roof</div>
                            <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{roofAreaM2.toFixed(0)} m²</div>
                        </div>
                    </div>

                    {/* Submit */}
                    <button
                        className="btn btn-primary"
                        onClick={() => onSubmit(panels)}
                        disabled={panels.length === 0 || isCalculating}
                        style={{ padding: '0.875rem 2rem', fontSize: '1.05rem' }}
                    >
                        {isCalculating ? (
                            <><div className="spinner" /> Calculating...</>
                        ) : (
                            <><Send size={18} /> Calculate Savings ({panels.length} panels)</>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
