import { Share2, FileDown } from 'lucide-react';

interface Props {
    summary: string;
}

export function ReportCard({ summary }: Props) {
    const paragraphs = summary.split('\n\n').filter(p => p.trim() !== '');

    return (
        <div className="glass-panel animate-in" style={{ padding: '2.5rem', maxWidth: '800px', margin: '2rem auto 4rem auto' }}>
            <div style={{ display: 'flex', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1.5rem', marginBottom: '1.5rem', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                    <h2 style={{ fontSize: '1.5rem', color: 'var(--color-primary)' }}>SolarSense Report</h2>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Powered by AI</p>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button className="btn btn-secondary" style={{ padding: '0.6rem' }} title="Share">
                        <Share2 size={18} />
                    </button>
                    <button className="btn btn-secondary" style={{ padding: '0.6rem' }} title="Download PDF">
                        <FileDown size={18} />
                    </button>
                </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', lineHeight: 1.7, fontSize: '1.05rem', color: 'rgba(255,255,255,0.9)' }}>
                {paragraphs.map((p, i) => (
                    <p key={i}>{p}</p>
                ))}
            </div>
        </div>
    );
}
