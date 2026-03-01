import { useState } from 'react';
import { Layers } from 'lucide-react';

interface Props {
    originalImage: string;
    heatmapImage: string;
    onContinue: () => void;
}

export function HeatmapOverlay({ originalImage, heatmapImage, onContinue }: Props) {
    const [showHeatmap, setShowHeatmap] = useState(true);

    return (
        <div className="glass-panel animate-in" style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2 style={{ fontSize: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Layers className="text-gradient" /> Solar Irradiance Heatmap
                </h2>
                <button
                    className="btn btn-secondary"
                    onClick={() => setShowHeatmap(!showHeatmap)}
                    style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}
                >
                    {showHeatmap ? 'Hide Heatmap' : 'Show Heatmap'}
                </button>
            </div>

            <div style={{ position: 'relative', borderRadius: '16px', overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
                {/* Base Image */}
                <img
                    src={originalImage}
                    alt="Original Roof"
                    style={{ width: '100%', display: 'block' }}
                />

                {/* Heatmap Overlay (using mix-blend-mode for integration) */}
                <img
                    src={heatmapImage}
                    alt="Irradiance Heatmap"
                    className={showHeatmap ? 'animate-pulse-glow' : ''}
                    style={{
                        position: 'absolute',
                        top: 0, left: 0, width: '100%', height: '100%',
                        opacity: showHeatmap ? 0.75 : 0,
                        mixBlendMode: 'multiply',
                        transition: 'opacity 0.4s ease',
                        pointerEvents: 'none'
                    }}
                />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Low Sun</span>
                    <div style={{ width: '120px', height: '8px', background: 'linear-gradient(90deg, #D50000, #FFD600, #00C853)', borderRadius: '4px' }} />
                    <span style={{ color: 'var(--text-secondary)' }}>High Sun</span>
                </div>

                <button className="btn btn-primary" onClick={onContinue}>
                    View Panel Placement →
                </button>
            </div>
        </div>
    );
}
