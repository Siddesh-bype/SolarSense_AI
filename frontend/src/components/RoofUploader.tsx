import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, MapPin, Zap, ArrowRight } from 'lucide-react';

interface Props {
    onUpload: (file: File, options: { city: string; monthly_bill: number, isDemo: boolean }) => void;
    isUploading: boolean;
}

const CITIES = [
    { id: 'pune', name: 'Pune' },
    { id: 'mumbai', name: 'Mumbai' },
    { id: 'delhi', name: 'Delhi' },
    { id: 'jaipur', name: 'Jaipur' },
    { id: 'bangalore', name: 'Bangalore' },
    { id: 'chennai', name: 'Chennai' },
    { id: 'hyderabad', name: 'Hyderabad' },
    { id: 'kolkata', name: 'Kolkata' },
];

export function RoofUploader({ onUpload, isUploading }: Props) {
    const [file, setFile] = useState<File | null>(null);
    const [preview, setPreview] = useState<string | null>(null);
    const [city, setCity] = useState('pune');
    const [bill, setBill] = useState(3000);
    const [isDemo, setIsDemo] = useState(false);

    const onDrop = useCallback((acceptedFiles: File[]) => {
        if (acceptedFiles.length > 0) {
            const selected = acceptedFiles[0];
            setFile(selected);
            setPreview(URL.createObjectURL(selected));
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'image/jpeg': ['.jpg', '.jpeg'],
            'image/png': ['.png'],
            'image/webp': ['.webp']
        },
        maxSize: 20 * 1024 * 1024,
        multiple: false
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) return;
        onUpload(file, { city, monthly_bill: bill, isDemo });
    };

    const loadDemoPhoto = async () => {
        try {
            const canvas = document.createElement('canvas');
            canvas.width = 1280;
            canvas.height = 720;
            const ctx = canvas.getContext('2d');
            if (!ctx) throw new Error('Canvas unavailable');

            ctx.fillStyle = '#c8d0d8';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#98a4ad';
            ctx.fillRect(120, 100, 1040, 520);
            ctx.fillStyle = '#7d8b94';
            for (let i = 0; i < 22; i++) {
                ctx.fillRect(150 + i * 48, 130, 28, 460);
            }
            ctx.fillStyle = '#4f5961';
            ctx.fillRect(210, 220, 180, 120);
            ctx.fillRect(760, 280, 210, 160);

            const blob = await new Promise<Blob>((resolve, reject) => {
                canvas.toBlob(
                    (value) => (value ? resolve(value) : reject(new Error('Failed to create demo image'))),
                    'image/jpeg',
                    0.9
                );
            });

            const demoFile = new File([blob], 'demo-roof.jpg', { type: 'image/jpeg' });
            setFile(demoFile);
            setPreview(URL.createObjectURL(demoFile));
            setCity('pune');
            setBill(5000);
            setIsDemo(true);
        } catch (e) {
            console.warn('Failed to generate demo image, upload manually');
        }
    };

    return (
        <div className="glass-panel" style={{ padding: '2rem', maxWidth: '640px', margin: '0 auto', position: 'relative' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
                <div>
                    <h1 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '0.25rem' }}>Solar Roof Analysis</h1>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Upload a rooftop photo to get your personalized solar plan.</p>
                </div>
                <button
                    onClick={loadDemoPhoto}
                    className="btn btn-secondary"
                    style={{ padding: '0.375rem 0.75rem', fontSize: '0.8rem', whiteSpace: 'nowrap', flexShrink: 0 }}>
                    Try Demo
                </button>
            </div>

            <form onSubmit={handleSubmit}>
                {!file ? (
                    <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`} style={{ marginBottom: '1.5rem' }}>
                        <input {...getInputProps()} />
                        <div className="dropzone-icon">
                            <UploadCloud size={28} />
                        </div>
                        {isDragActive ? (
                            <p style={{ fontSize: '0.95rem', fontWeight: 500 }}>Drop the image here...</p>
                        ) : (
                            <div>
                                <p style={{ fontSize: '0.95rem', fontWeight: 500, marginBottom: '0.25rem' }}>Drag and drop your rooftop photo</p>
                                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>or click to browse (JPEG, PNG, max 20 MB)</p>
                            </div>
                        )}
                    </div>
                ) : (
                    <div style={{ marginBottom: '1.5rem', position: 'relative', borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
                        <img src={preview!} alt="Roof preview" style={{ width: '100%', maxHeight: '260px', objectFit: 'cover', display: 'block' }} />
                        <button
                            type="button"
                            onClick={() => { setFile(null); setPreview(null); }}
                            className="btn btn-secondary"
                            style={{ position: 'absolute', top: '0.5rem', right: '0.5rem', background: 'rgba(255,255,255,0.9)', padding: '0.3rem 0.6rem', fontSize: '0.8rem' }}>
                            Change
                        </button>
                    </div>
                )}

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                    <div className="form-group">
                        <label className="form-label">
                            <MapPin size={14} /> Location
                        </label>
                        <select className="form-select" value={city} onChange={e => setCity(e.target.value)}>
                            {CITIES.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                        </select>
                    </div>

                    <div className="form-group">
                        <label className="form-label">
                            <Zap size={14} /> Monthly Bill (INR)
                        </label>
                        <input
                            type="number"
                            className="form-input"
                            value={bill}
                            onChange={e => setBill(Number(e.target.value))}
                            min={500}
                            step={100}
                        />
                    </div>
                </div>

                <button
                    type="submit"
                    className="btn btn-primary"
                    style={{ width: '100%', padding: '0.75rem', fontSize: '0.95rem' }}
                    disabled={!file || isUploading}
                >
                    {isUploading ? (
                        <><div className="spinner" /> Analyzing...</>
                    ) : (
                        <>Analyze Roof <ArrowRight size={16} /></>
                    )}
                </button>
            </form>
        </div>
    );
}
