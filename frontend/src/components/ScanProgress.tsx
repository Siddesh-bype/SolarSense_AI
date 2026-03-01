import type { ScanStatusResponse } from '../types';
import { Cpu, Maximize, Sun, LayoutGrid, Calculator, BookOpenText, CheckCircle } from 'lucide-react';

interface Props {
    status: ScanStatusResponse | null;
}

const STEPS = [
    { id: 'preprocessing', label: 'Analyzing your rooftop photo', icon: <Cpu size={20} /> },
    { id: 'depth_estimation', label: 'Building 3D model of your roof', icon: <Maximize size={20} /> },
    { id: 'shadow_simulation', label: 'Simulating sunlight across seasons', icon: <Sun size={20} /> },
    { id: 'panel_placement', label: 'Finding the best spots for panels', icon: <LayoutGrid size={20} /> },
    { id: 'financial_calculation', label: 'Calculating your savings', icon: <Calculator size={20} /> },
    { id: 'generating_report', label: 'Preparing personalized report', icon: <BookOpenText size={20} /> },
];

export function ScanProgress({ status }: Props) {
    if (!status) return null;

    const currentIdx = STEPS.findIndex(s => s.id === status.current_step);
    const activeIdx = currentIdx >= 0 ? currentIdx : (status.status === 'complete' ? STEPS.length : 0);

    const percentage = status.status === 'complete' ? 100 : status.progress_percent;

    return (
        <div className="glass-panel animate-in" style={{ padding: '2.5rem', maxWidth: '600px', margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <h2 style={{ fontSize: '1.8rem', marginBottom: '0.5rem' }}>AI Processing Engine</h2>
                <p style={{ color: 'var(--text-muted)' }}>SolarSense is analyzing your roof structure...</p>
            </div>

            <div style={{ marginBottom: '2.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                    <span style={{ fontWeight: 500 }}>Overall Progress</span>
                    <span style={{ fontWeight: 600, color: 'var(--color-primary)' }}>{percentage}%</span>
                </div>

                {/* Progress Bar Container */}
                <div style={{
                    height: '12px',
                    background: 'rgba(255,255,255,0.05)',
                    borderRadius: '6px',
                    overflow: 'hidden',
                    border: '1px solid var(--border-subtle)'
                }}>
                    {/* Progress Fill */}
                    <div style={{
                        height: '100%',
                        width: `${percentage}%`,
                        background: 'var(--gradient-primary)',
                        boxShadow: 'var(--glow-primary)',
                        transition: 'width 0.5s ease-out',
                        position: 'relative',
                        overflow: 'hidden'
                    }}>
                        {/* Shimmer effect inside loader */}
                        <div style={{
                            position: 'absolute',
                            top: 0, left: 0, right: 0, bottom: 0,
                            background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)',
                            animation: 'shimmer 1.5s infinite',
                            transform: 'translateX(-100%)'
                        }} />
                    </div>
                </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {STEPS.map((step, idx) => {
                    const isCompleted = idx < activeIdx || status.status === 'complete';
                    const isActive = idx === activeIdx && status.status !== 'complete';
                    const isPending = idx > activeIdx;

                    let color = 'var(--text-primary)';
                    if (isCompleted) color = 'var(--color-primary)';
                    if (isPending) color = 'var(--text-muted)';

                    return (
                        <div key={step.id} style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '1rem',
                            padding: '1rem',
                            borderRadius: '12px',
                            background: isActive ? 'rgba(0, 230, 118, 0.05)' : 'transparent',
                            border: `1px solid ${isActive ? 'rgba(0, 230, 118, 0.2)' : 'transparent'}`,
                            transition: 'all 0.3s ease'
                        }}>
                            <div style={{
                                width: 32, height: 32, borderRadius: '50%',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                background: isCompleted ? 'rgba(0, 230, 118, 0.1)' : (isActive ? 'rgba(0,0,0,0.5)' : 'transparent'),
                                color: color
                            }}>
                                {isCompleted ? <CheckCircle size={20} /> : step.icon}
                            </div>
                            <span style={{
                                fontWeight: isActive ? 600 : 400,
                                color: color,
                                flex: 1
                            }}>
                                {step.label}
                            </span>
                            {isActive && <div className="spinner" style={{ width: 16, height: 16, borderLeftColor: 'transparent', borderTopColor: 'var(--color-primary)', borderRightColor: 'var(--color-primary)', borderBottomColor: 'var(--color-primary)' }} />}
                        </div>
                    )
                })}
            </div>

            <style>{`
        @keyframes shimmer {
          100% { transform: translateX(100%); }
        }
      `}</style>
        </div>
    );
}
