import { useState, useCallback, useRef } from 'react';
import axios from 'axios';
import type { CompleteScanResult, ScanStatusResponse } from '../types';

const API_BASE = '/api';

export function useScan() {
    const [isUploading, setIsUploading] = useState(false);
    const [scanId, setScanId] = useState<string | null>(null);
    const [status, setStatus] = useState<ScanStatusResponse | null>(null);
    const [result, setResult] = useState<CompleteScanResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isDemoMode, setIsDemoMode] = useState(false);

    const pollIntervalRef = useRef<number | null>(null);

    const pollStatus = useCallback(async (id: string) => {
        try {
            const res = await axios.get(`${API_BASE}/scan/${id}/status`);
            setStatus(res.data);
            if (res.data.status === 'complete') {
                if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
                await fetchResult(id);
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

    const fetchResult = async (id: string) => {
        try {
            const res = await axios.get(`${API_BASE}/scan/${id}/result`);
            setResult(res.data);
        } catch (err: any) {
            console.error(err);
            setError('Failed to fetch result');
        }
    };

    const uploadPhoto = async (file: File, options: { city: string; monthly_bill: number; lat?: number; lon?: number; isDemo: boolean }) => {
        setIsUploading(true);
        setError(null);
        setScanId(null);
        setStatus(null);
        setResult(null);
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
            // For demo mode, we still upload but maybe we simulate polling quickly or the backend returns instantly. 
            // The backend router handles actually running the pipeline synchronously for demo.
            const res = await axios.post(`${API_BASE}/scan/upload`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            const id = res.data.scan_id;
            setScanId(id);

            if (res.data.status === 'complete') {
                // Synchronous pipeline completed instantly
                setStatus({
                    scan_id: id,
                    status: 'complete',
                    progress_percent: 100,
                    current_step: 'complete'
                });
                setResult(res.data.result);
            } else {
                // Start polling (in case we switch back to celery later)
                pollIntervalRef.current = window.setInterval(() => pollStatus(id), 1500);
            }
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || 'Failed to start scan');
        } finally {
            setIsUploading(false);
        }
    };

    const reset = () => {
        if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
        setIsUploading(false);
        setScanId(null);
        setStatus(null);
        setResult(null);
        setError(null);
        setIsDemoMode(false);
    }

    return {
        isUploading,
        scanId,
        status,
        result,
        error,
        isDemoMode,
        uploadPhoto,
        reset
    };
}
