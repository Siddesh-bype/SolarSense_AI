import type { ScanStatusResponse } from '../types';
import { Cpu, Maximize, Sun, CheckCircle } from 'lucide-react';

interface Props {
    status: ScanStatusResponse | null;
}

const STEPS = [
    { id: 'preprocessing', label: 'Analyzing your rooftop photo', icon: <Cpu size={20} /> },
    { id: 'depth_estimation', label: 'Building 3D depth model of your roof', icon: <Maximize size={20} /> },
    { id: 'shadow_simulation', label: 'Simulating sunlight & shadow patterns', icon: <Sun size={20} /> },
];

export function ScanProgress({ status }: Props) {
    // While waiting for the first status update (backend processes synchronously),
    // show a loading screen instead of nothing.
    const currentStep = status?.current_step ?? 'preprocessing';
    const currentStatus = status?.status ?? 'pending';

    const currentIdx = STEPS.findIndex(s => s.id === currentStep);
    const activeIdx = currentIdx >= 0 ? currentIdx : (currentStatus === 'analyzed' || currentStatus === 'complete' ? STEPS.length : 0);

    const percentage = (currentStatus === 'analyzed' || currentStatus === 'complete') ? 100 : (status?.progress_percent ?? 5);

    return (
        <div className="glass-panel animate-in" style={{ padding: '2.5rem', maxWidth: '600px', margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 600, marginBottom: '0.25rem' }}>Analyzing Your Roof</h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>This usually takes a few seconds.</p>
            </div>

            <div style={{ marginBottom: '2.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                    <span style={{ fontWeight: 500 }}>Overall Progress</span>
                    <span style={{ fontWeight: 600, color: 'var(--color-primary)' }}>{percentage}%</span>
                </div>

                {/* Progress Bar Container */}
                <div style={{
                    height: '8px',
                    background: '#f2f4f7',
                    borderRadius: '4px',
                    overflow: 'hidden',
                    border: '1px solid var(--border-subtle)'
                }}>
                    {/* Progress Fill */}
                    <div style={{
                        height: '100%',
                        width: `${percentage}%`,
                        background: 'var(--color-primary)',
                        transition: 'width 0.5s ease-out',
                        position: 'relative',
                        overflow: 'hidden',
                        borderRadius: '4px'
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
                    const done = currentStatus === 'analyzed' || currentStatus === 'complete';
                    const isCompleted = idx < activeIdx || done;
                    const isActive = idx === activeIdx && !done;
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
                            background: isActive ? 'rgba(26, 115, 232, 0.05)' : 'transparent',
                            border: `1px solid ${isActive ? 'rgba(26, 115, 232, 0.15)' : 'transparent'}`,
                            transition: 'all 0.3s ease'
                        }}>
                            <div style={{
                                width: 32, height: 32, borderRadius: '50%',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                background: isCompleted ? 'rgba(26, 115, 232, 0.08)' : (isActive ? '#f2f4f7' : 'transparent'),
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


        </div>
    );
}
