import { useState, useCallback, useRef } from 'react';
import axios from 'axios';
import type { AnalysisResult, FinancialCalcResult, ScanStatusResponse } from '../types';
import type { PlacedPanel } from '../components/PanelEditor';

const API_BASE = '/api';

export function useScan() {
    const [isUploading, setIsUploading] = useState(false);
    const [isCalculating, setIsCalculating] = useState(false);
    const [scanId, setScanId] = useState<string | null>(null);
    const [status, setStatus] = useState<ScanStatusResponse | null>(null);
    const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
    const [financialResult, setFinancialResult] = useState<FinancialCalcResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isDemoMode, setIsDemoMode] = useState(false);

    const pollIntervalRef = useRef<number | null>(null);

    const pollStatus = useCallback(async (id: string) => {
        try {
            const res = await axios.get(`${API_BASE}/scan/${id}/status`);
            setStatus(res.data);
            if (res.data.status === 'analyzed') {
                if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
                await fetchAnalysis(id);
            } else if (res.data.status === 'failed') {
                if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
                setError(res.data.error_message || 'Scan failed');
            }
        } catch (err: any) {
            console.error(err);
            if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
            setError('Failed to fetch status');
        }
    }, []);

    const fetchAnalysis = async (id: string) => {
        try {
            const res = await axios.get(`${API_BASE}/scan/${id}/result`);
            setAnalysis(res.data);
        } catch (err: any) {
            console.error(err);
            setError('Failed to fetch analysis result');
        }
    };

    /** Phase 1: Upload image and get roof analysis (depth, shadow, heatmap, panel spec) */
    const uploadPhoto = async (file: File, options: { city: string; monthly_bill: number; lat?: number; lon?: number; isDemo: boolean }) => {
        setIsUploading(true);
        setError(null);
        setScanId(null);
        setStatus(null);
        setAnalysis(null);
        setFinancialResult(null);
        setIsDemoMode(options.isDemo);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('city', options.city);
        formData.append('monthly_bill', options.monthly_bill.toString());
        formData.append('demo', options.isDemo ? 'true' : 'false');
        if (options.lat !== undefined && options.lon !== undefined) {
            formData.append('latitude', options.lat.toString());
            formData.append('longitude', options.lon.toString());
        }

        try {
            const res = await axios.post(`${API_BASE}/scan/upload`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            const id = res.data.scan_id;
            setScanId(id);

            if (res.data.status === 'analyzed') {
                // Synchronous pipeline completed
                setStatus({
                    scan_id: id,
                    status: 'analyzed',
                    progress_percent: 100,
                    current_step: 'ready_for_placement',
                });
                setAnalysis(res.data.result);
            } else {
                // Start polling
                pollIntervalRef.current = window.setInterval(() => pollStatus(id), 1500);
            }
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || 'Failed to start scan');
        } finally {
            setIsUploading(false);
        }
    };

    /** Phase 2: Submit user's panel placement, get financial results */
    const calculateFinancials = async (panels: PlacedPanel[], city?: string, monthlyBill?: number) => {
        if (!scanId) {
            setError('No active scan');
            return;
        }
        setIsCalculating(true);
        setError(null);

        try {
            const payload = {
                scan_id: scanId,
                panels: panels.map(p => ({
                    x: p.xPct,
                    y: p.yPct,
                    width: p.wPct,
                    height: p.hPct,
                })),
                city: city || analysis?.city || 'pune',
                monthly_bill: monthlyBill ?? 3000,
            };

            const res = await axios.post(`${API_BASE}/scan/calculate`, payload);
            setFinancialResult(res.data);
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || 'Financial calculation failed');
        } finally {
            setIsCalculating(false);
        }
    };

    const reset = () => {
        if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
        setIsUploading(false);
        setIsCalculating(false);
        setScanId(null);
        setStatus(null);
        setAnalysis(null);
        setFinancialResult(null);
        setError(null);
        setIsDemoMode(false);
    };

    return {
        isUploading,
        isCalculating,
        scanId,
        status,
        analysis,
        financialResult,
        error,
        isDemoMode,
        uploadPhoto,
        calculateFinancials,
        reset,
    };
}
