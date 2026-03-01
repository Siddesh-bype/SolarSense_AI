import { useState } from 'react';
import axios from 'axios';
import type { FinancialReport } from '../types';

const API_BASE = '/api';

export function useFinancial() {
    const [data, setData] = useState<FinancialReport | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const getEstimate = async (panels: number, city: string, monthlyBill: number) => {
        setLoading(true);
        setError(null);
        try {
            const res = await axios.get(`${API_BASE}/financial/estimate`, {
                params: { panels, city, monthly_bill: monthlyBill },
            });
            setData(res.data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to fetch estimate');
        } finally {
            setLoading(false);
        }
    };

    return { data, loading, error, getEstimate };
}
