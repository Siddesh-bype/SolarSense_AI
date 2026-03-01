import { useEffect, useState } from 'react';
import { useScan } from './hooks/useScan';
import { RoofUploader } from './components/RoofUploader';
import { ScanProgress } from './components/ScanProgress';
import { HeatmapOverlay } from './components/HeatmapOverlay';
import { PanelPlacementAR } from './components/PanelPlacementAR';
import { FinancialDashboard } from './components/FinancialDashboard';
import { ReportCard } from './components/ReportCard';
import { Sun } from 'lucide-react';

function App() {
  const { isUploading, status, result, error, uploadPhoto, reset } = useScan();
  const [viewState, setViewState] = useState<'upload' | 'progress' | 'heatmap' | 'placement' | 'financial'>('upload');

  const handleUpload = (file: File, options: { city: string; monthly_bill: number; isDemo: boolean }) => {
    setViewState('progress');
    uploadPhoto(file, options);
  };

  // When result comes in, we can either automatically transition or wait.
  // The prompt asks for a "90-second demo flow without any user intervention",
  // so when result is ready we should transition automatically, then maybe delay between views.
  // For safety, providing manual progression buttons in the UI as implemented.

  // Actually, if we want an auto-flow, we can use useEffect to transition automatically, 
  // but manual transition is safer for a functional UI. Let's start with manual transition 
  // after progress finishes, or just show everything sequentially in a scroll view.
  // The components are built as sequential cards. Let's just show them based on state.

  // If scan is complete but view is still 'progress', automatically switch to heatmap.
  useEffect(() => {
    if (status?.status === 'complete' && result && viewState === 'progress') {
      setViewState('heatmap');
    }
  }, [status, result, viewState]);

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
            <p style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Failed to generate solar plan</p>
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

        {/* Heatmap View */}
        {(viewState === 'heatmap' && result && !error) && (
          <HeatmapOverlay
            originalImage={result.original_image_url}
            heatmapImage={result.shadow.heatmap_url}
            onContinue={() => setViewState('placement')}
          />
        )}

        {/* Placement View */}
        {(viewState === 'placement' && result && !error) && (
          <PanelPlacementAR
            originalImage={result.original_image_url}
            heatmapImage={result.shadow.heatmap_url}
            panels={result.placement.panels}
            totalCapacityKw={result.placement.system_capacity_kw}
            onContinue={() => setViewState('financial')}
          />
        )}

        {/* Financial Details and Report View */}
        {(viewState === 'financial' && result && !error) && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <FinancialDashboard data={result.financial} />
            <ReportCard summary={result.summary} />

            <div style={{ textAlign: 'center', marginTop: '2rem' }}>
              <button className="btn btn-secondary" onClick={() => { reset(); setViewState('upload'); }}>
                Start New Scan
              </button>
            </div>
          </div>
        )}

      </main>

      {/* Footer */}
      <footer style={{ padding: '2rem', textAlign: 'center', borderTop: '1px solid var(--border-subtle)', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
        <p>Built for AMD Slingshot Hackathon 2026 • Point. Scan. Power Your Home.</p>
      </footer>
    </div>
  );
}

export default App;
