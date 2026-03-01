import { useState, useRef } from 'react';
import type { PanelPlacement } from '../types';
import { Download, LayoutGrid, Eye, EyeOff } from 'lucide-react';

interface Props {
    originalImage: string;
    heatmapImage: string; // Used for optional blending
    panels: PanelPlacement[];
    totalCapacityKw: number;
    onContinue: () => void;
}

export function PanelPlacementAR({ originalImage, heatmapImage, panels, totalCapacityKw, onContinue }: Props) {
    const [showPanels, setShowPanels] = useState(true);
    const [hoveredPanel, setHoveredPanel] = useState<number | null>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    const handleDownload = () => {
        // Basic download trigger (in reality, we'd draw to canvas and export)
        const link = document.createElement('a');
        link.href = originalImage; // simplified for React demo
        link.download = 'SolarSense-Plan.jpg';
        link.click();
    };

    return (
        <div className="glass-panel animate-in" style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2 style={{ fontSize: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <LayoutGrid className="text-gradient" /> Optimal Layout
                </h2>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                        className="btn btn-secondary"
                        onClick={() => setShowPanels(!showPanels)}
                        title={showPanels ? "Hide Panels" : "Show Panels"}
                        style={{ padding: '0.5rem' }}
                    >
                        {showPanels ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                    <button
                        className="btn btn-secondary"
                        onClick={handleDownload}
                        title="Download Plan"
                        style={{ padding: '0.5rem' }}
                    >
                        <Download size={18} />
                    </button>
                </div>
            </div>

            <div
                ref={containerRef}
                style={{
                    position: 'relative',
                    borderRadius: '16px',
                    overflow: 'hidden',
                    border: '1px solid var(--border-subtle)',
                    lineHeight: 0
                }}
            >
                <img
                    src={originalImage}
                    alt="Original Roof"
                    style={{ width: '100%', display: 'block' }}
                />

                {/* Heatmap subtle blend */}
                <img
                    src={heatmapImage}
                    alt="Heatmap Blend"
                    style={{
                        position: 'absolute',
                        top: 0, left: 0, width: '100%', height: '100%',
                        opacity: 0.3, mixBlendMode: 'multiply', pointerEvents: 'none'
                    }}
                />

                <div style={{
                    position: 'absolute', top: 0, left: 0, width: '100%', height: '100%',
                    opacity: showPanels ? 1 : 0, transition: 'opacity 0.3s ease'
                }}>
                    {panels.map((p) => {
                        // Because original image maps to 1024x1024 internally usually,
                        // we need to scale CSS percentages.
                        // For simplicity, assume image is full width and we use % positioning if we scale.
                        // Alternatively, use a square aspect ratio container
                        return (
                            <div
                                key={p.panel_id}
                                onMouseEnter={() => setHoveredPanel(p.panel_id)}
                                onMouseLeave={() => setHoveredPanel(null)}
                                style={{
                                    position: 'absolute',
                                    left: `${(p.x / 1024) * 100}%`,
                                    top: `${(p.y / 1024) * 100}%`,
                                    width: `${(p.width / 1024) * 100}%`,
                                    height: `${(p.height / 1024) * 100}%`,
                                    backgroundColor: hoveredPanel === p.panel_id ? 'rgba(0, 230, 118, 0.4)' : 'rgba(41, 121, 255, 0.35)',
                                    border: `2px solid ${hoveredPanel === p.panel_id ? '#00E676' : 'white'}`,
                                    borderRadius: '2px',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    color: 'white',
                                    fontSize: '10px',
                                    fontWeight: 'bold',
                                    boxShadow: hoveredPanel === p.panel_id ? '0 0 10px rgba(0, 230, 118, 0.8)' : 'none',
                                    transition: 'all 0.2s'
                                }}
                            >
                                {hoveredPanel === p.panel_id && (
                                    <div style={{
                                        position: 'absolute', bottom: '100%', left: '50%', transform: 'translateX(-50%)',
                                        background: 'var(--bg-surface-elevated)', border: '1px solid var(--color-primary)',
                                        padding: '4px 8px', borderRadius: '4px', whiteSpace: 'nowrap', zIndex: 10,
                                        marginBottom: '4px', fontSize: '12px'
                                    }}>
                                        Yield: {p.irradiance_pct}%
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>

                {/* Badges */}
                <div style={{
                    position: 'absolute', top: '10px', right: '10px',
                    background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)',
                    padding: '8px 12px', borderRadius: '8px', border: '1px solid var(--border-subtle)',
                    color: 'white', fontWeight: 600, fontSize: '0.9rem', textAlign: 'right'
                }}>
                    <div style={{ color: 'var(--color-primary)' }}>{panels.length} Panels</div>
                    <div style={{ fontSize: '0.8rem', opacity: 0.8 }}>{totalCapacityKw.toFixed(1)} kW System</div>
                </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
                <button className="btn btn-primary" onClick={onContinue}>
                    View Financials →
                </button>
            </div>
        </div>
    );
}
