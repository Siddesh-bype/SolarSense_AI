import { useEffect, useState } from 'react';
import { useScan } from './hooks/useScan';
import { RoofUploader } from './components/RoofUploader';
import { ScanProgress } from './components/ScanProgress';
import { PanelEditor } from './components/PanelEditor';
import type { PlacedPanel } from './components/PanelEditor';
import { FinancialDashboard } from './components/FinancialDashboard';
import { ReportCard } from './components/ReportCard';
import { Sun } from 'lucide-react';

function App() {
  const {
    isUploading,
    isCalculating,
    status,
    analysis,
    financialResult,
    error,
    uploadPhoto,
    calculateFinancials,
    reset,
  } = useScan();

  const [viewState, setViewState] = useState<'upload' | 'progress' | 'editor' | 'financial'>('upload');

  const handleUpload = (file: File, options: { city: string; monthly_bill: number; isDemo: boolean }) => {
    setViewState('progress');
    uploadPhoto(file, options);
  };

  const handlePanelSubmit = (panels: PlacedPanel[]) => {
    calculateFinancials(panels);
  };

  // Auto-transition: progress → editor when analysis is ready
  useEffect(() => {
    if (analysis && viewState === 'progress') {
      setViewState('editor');
    }
  }, [analysis, viewState]);

  // Auto-transition: editor → financial when financial result comes in
  useEffect(() => {
    if (financialResult && viewState === 'editor') {
      setViewState('financial');
    }
  }, [financialResult, viewState]);

  return (
    <div className="app-wrapper">
      {/* Header */}
      <header style={{ padding: '1.5rem 2rem', borderBottom: '1px solid var(--border-subtle)', background: 'rgba(10, 10, 11, 0.8)', backdropFilter: 'blur(12px)', position: 'sticky', top: 0, zIndex: 100 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }} onClick={() => { reset(); setViewState('upload'); }}>
            <div style={{ background: 'var(--gradient-primary)', borderRadius: '50%', padding: '0.4rem', color: '#000' }}>
              <Sun size={24} />
            </div>
            <span style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.02em', fontFamily: 'Outfit' }}>SolarSense AI</span>
          </div>

          <nav style={{ display: 'flex', gap: '1.5rem' }}>
            <a href="#" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500 }}>How it works</a>
            <a href="#" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500 }}>Subsidies</a>
            <a href="#" style={{ color: 'var(--color-primary)', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 600 }}>Get Started</a>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content" style={{ padding: '4rem 2rem', position: 'relative' }}>

        {/* Error State */}
        {error && (
          <div style={{ maxWidth: '800px', margin: '0 auto 2rem auto', padding: '1rem', background: 'rgba(213, 0, 0, 0.1)', border: '1px solid var(--color-danger)', borderRadius: '12px', color: '#ffaaaa', textAlign: 'center' }}>
            <p style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Something went wrong</p>
            <p style={{ fontSize: '0.9rem' }}>{error}</p>
            <button className="btn btn-secondary" onClick={() => { reset(); setViewState('upload'); }} style={{ marginTop: '1rem' }}>Try Again</button>
          </div>
        )}

        {/* Upload View */}
        {(viewState === 'upload' && !error) && (
          <div className="animate-in">
            <RoofUploader onUpload={handleUpload} isUploading={isUploading} />
          </div>
        )}

        {/* Progress View */}
        {(viewState === 'progress' && !error) && (
          <ScanProgress status={status} />
        )}

        {/* Interactive Panel Editor */}
        {(viewState === 'editor' && analysis && !error) && (
          <PanelEditor
            originalImage={analysis.original_image_url}
            heatmapImage={analysis.shadow.heatmap_url}
            panelSpec={analysis.panel_spec}
            imageWidth={analysis.image_width}
            imageHeight={analysis.image_height}
            roofAreaM2={analysis.depth.estimated_roof_area_m2}
            onSubmit={handlePanelSubmit}
            isCalculating={isCalculating}
          />
        )}

        {/* Financial Results */}
        {(viewState === 'financial' && financialResult && !error) && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <FinancialDashboard data={financialResult.financial} />
            <ReportCard summary={financialResult.summary} />

            <div style={{ textAlign: 'center', marginTop: '2rem', display: 'flex', gap: '1rem', justifyContent: 'center' }}>
              <button className="btn btn-secondary" onClick={() => setViewState('editor')}>
                Adjust Panels
              </button>
              <button className="btn btn-secondary" onClick={() => { reset(); setViewState('upload'); }}>
                Start New Scan
              </button>
            </div>
          </div>
        )}

      </main>

      {/* Footer */}
      <footer style={{ padding: '2rem', textAlign: 'center', borderTop: '1px solid var(--border-subtle)', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
        <p>Built for AMD Slingshot Hackathon 2026 &bull; Point. Scan. Power Your Home.</p>
      </footer>
    </div>
  );
}

export default App;
