import { useEffect, useState } from 'react';
import { useScan } from './hooks/useScan';
import { RoofUploader } from './components/RoofUploader';
import { ScanProgress } from './components/ScanProgress';
import { PanelEditor } from './components/PanelEditor';
import type { PlacedPanel } from './components/PanelEditor';
import { FinancialDashboard } from './components/FinancialDashboard';
import { ReportCard } from './components/ReportCard';
import { Sun, X } from 'lucide-react';

type ModalType = 'how-it-works' | 'subsidies' | null;

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
  const [modal, setModal] = useState<ModalType>(null);

  const handleUpload = (file: File, options: { city: string; monthly_bill: number; isDemo: boolean }) => {
    setViewState('progress');
    uploadPhoto(file, options);
  };

  const handlePanelSubmit = (panels: PlacedPanel[]) => {
    calculateFinancials(panels);
  };

  useEffect(() => {
    if (analysis && viewState === 'progress') {
      setViewState('editor');
    }
  }, [analysis, viewState]);

  useEffect(() => {
    if (financialResult && viewState === 'editor') {
      setViewState('financial');
    }
  }, [financialResult, viewState]);

  return (
    <div className="app-wrapper">
      {/* Header */}
      <header style={{
        padding: '0 2rem',
        height: '56px',
        borderBottom: '1px solid var(--border-subtle)',
        background: '#fff',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
          <div
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}
            onClick={() => { reset(); setViewState('upload'); }}
          >
            <Sun size={22} color="#1a73e8" />
            <span style={{ fontSize: '1.1rem', fontWeight: 600, color: '#1a1a1a' }}>SolarSense AI</span>
          </div>

          <nav style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
            <button
              onClick={() => setModal('how-it-works')}
              style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', fontSize: '0.875rem', fontWeight: 500, cursor: 'pointer', padding: '0.25rem 0' }}
            >
              How it works
            </button>
            <button
              onClick={() => setModal('subsidies')}
              style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', fontSize: '0.875rem', fontWeight: 500, cursor: 'pointer', padding: '0.25rem 0' }}
            >
              Subsidies
            </button>
            <button
              className="btn btn-primary"
              style={{ padding: '0.4rem 1rem', fontSize: '0.85rem' }}
              onClick={() => { reset(); setViewState('upload'); }}
            >
              Get Started
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content" style={{ padding: '3rem 1.5rem', position: 'relative' }}>

        {/* Error State */}
        {error && (
          <div style={{ maxWidth: '600px', margin: '0 auto 2rem auto', padding: '1rem 1.5rem', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#991b1b' }}>
            <p style={{ fontWeight: 600, marginBottom: '0.25rem', fontSize: '0.9rem' }}>Something went wrong</p>
            <p style={{ fontSize: '0.85rem', color: '#b91c1c' }}>{error}</p>
            <button className="btn btn-secondary" onClick={() => { reset(); setViewState('upload'); }} style={{ marginTop: '0.75rem', fontSize: '0.8rem', padding: '0.4rem 0.75rem' }}>Try Again</button>
          </div>
        )}

        {(viewState === 'upload' && !error) && (
          <div className="animate-in">
            <RoofUploader onUpload={handleUpload} isUploading={isUploading} />
          </div>
        )}

        {(viewState === 'progress' && !error) && (
          <ScanProgress status={status} />
        )}

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

        {(viewState === 'financial' && financialResult && !error) && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <FinancialDashboard data={financialResult.financial} />
            <ReportCard summary={financialResult.summary} />

            <div style={{ textAlign: 'center', marginTop: '1.5rem', display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
              <button className="btn btn-secondary" onClick={() => setViewState('editor')}>
                Adjust Panels
              </button>
              <button className="btn btn-primary" onClick={() => { reset(); setViewState('upload'); }}>
                New Scan
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer style={{ padding: '1.25rem', textAlign: 'center', borderTop: '1px solid var(--border-subtle)', color: 'var(--text-muted)', fontSize: '0.8rem', background: '#fff' }}>
        Built for AMD Slingshot Hackathon 2026
      </footer>

      {/* Modal Overlay */}
      {modal && (
        <div
          onClick={() => setModal(null)}
          style={{
            position: 'fixed', inset: 0,
            background: 'rgba(0,0,0,0.3)',
            zIndex: 200,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: '1rem',
          }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{
              background: '#fff',
              borderRadius: '12px',
              maxWidth: '560px',
              width: '100%',
              maxHeight: '80vh',
              overflow: 'auto',
              boxShadow: 'var(--shadow-lg)',
              padding: '2rem',
              position: 'relative',
            }}
          >
            <button
              onClick={() => setModal(null)}
              style={{
                position: 'absolute', top: '1rem', right: '1rem',
                background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)',
              }}
            >
              <X size={20} />
            </button>

            {modal === 'how-it-works' && (
              <>
                <h2 style={{ fontSize: '1.25rem', marginBottom: '1.25rem' }}>How SolarSense AI Works</h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                  <div style={{ display: 'flex', gap: '0.875rem', alignItems: 'flex-start' }}>
                    <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'var(--color-primary-light)', color: 'var(--color-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, fontSize: '0.8rem', flexShrink: 0 }}>1</div>
                    <div><strong style={{ color: 'var(--text-primary)' }}>Upload your roof photo</strong><br />Take or upload an aerial/satellite image of your rooftop. Our AI accepts JPEG, PNG, or WebP images.</div>
                  </div>
                  <div style={{ display: 'flex', gap: '0.875rem', alignItems: 'flex-start' }}>
                    <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'var(--color-primary-light)', color: 'var(--color-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, fontSize: '0.8rem', flexShrink: 0 }}>2</div>
                    <div><strong style={{ color: 'var(--text-primary)' }}>AI analyzes your roof</strong><br />Our Depth Anything V2 model estimates 3D structure, roof area, tilt angle, and obstructions. A shadow simulation maps annual sunlight patterns.</div>
                  </div>
                  <div style={{ display: 'flex', gap: '0.875rem', alignItems: 'flex-start' }}>
                    <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'var(--color-primary-light)', color: 'var(--color-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, fontSize: '0.8rem', flexShrink: 0 }}>3</div>
                    <div><strong style={{ color: 'var(--text-primary)' }}>Place panels interactively</strong><br />Click on the heatmap to place solar panels where you prefer. Drag to reposition, rotate, or remove them.</div>
                  </div>
                  <div style={{ display: 'flex', gap: '0.875rem', alignItems: 'flex-start' }}>
                    <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'var(--color-primary-light)', color: 'var(--color-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, fontSize: '0.8rem', flexShrink: 0 }}>4</div>
                    <div><strong style={{ color: 'var(--text-primary)' }}>Get your financial report</strong><br />Receive detailed cost breakdown, subsidy estimates under PM Surya Ghar, payback period, EMI options, and 25-year savings projections.</div>
                  </div>
                </div>
              </>
            )}

            {modal === 'subsidies' && (
              <>
                <h2 style={{ fontSize: '1.25rem', marginBottom: '1.25rem' }}>Government Solar Subsidies</h2>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.7, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div style={{ padding: '1rem', background: 'var(--bg-muted)', borderRadius: '8px' }}>
                    <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>PM Surya Ghar Muft Bijli Yojana</h3>
                    <p>The Government of India provides subsidies for rooftop solar installations under this scheme to promote clean energy adoption.</p>
                  </div>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '2px solid var(--border-subtle)' }}>
                        <th style={{ textAlign: 'left', padding: '0.5rem 0.75rem', color: 'var(--text-primary)' }}>System Size</th>
                        <th style={{ textAlign: 'right', padding: '0.5rem 0.75rem', color: 'var(--text-primary)' }}>Subsidy</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                        <td style={{ padding: '0.5rem 0.75rem' }}>Up to 2 kW</td>
                        <td style={{ padding: '0.5rem 0.75rem', textAlign: 'right', fontWeight: 600 }}>Rs 30,000 / kW</td>
                      </tr>
                      <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                        <td style={{ padding: '0.5rem 0.75rem' }}>2 kW - 3 kW</td>
                        <td style={{ padding: '0.5rem 0.75rem', textAlign: 'right', fontWeight: 600 }}>Rs 18,000 / kW (above 2 kW)</td>
                      </tr>
                      <tr>
                        <td style={{ padding: '0.5rem 0.75rem' }}>3 kW - 10 kW</td>
                        <td style={{ padding: '0.5rem 0.75rem', textAlign: 'right', fontWeight: 600 }}>Rs 78,000 (fixed cap)</td>
                      </tr>
                    </tbody>
                  </table>
                  <p style={{ fontSize: '0.85rem' }}>SolarSense AI automatically calculates applicable subsidies based on your system size and displays the net cost after deduction.</p>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Source: Ministry of New and Renewable Energy (MNRE), Government of India. Subject to eligibility and state-level policies.</p>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
