import type { FinancialReport } from '../types';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { IndianRupee, TrendingUp, Zap, Clock } from 'lucide-react';
import { useEffect, useState } from 'react';

interface Props {
    data: FinancialReport;
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export function FinancialDashboard({ data }: Props) {
    const [animatedSavings, setAnimatedSavings] = useState(0);

    useEffect(() => {
        // Count-up animation for hero metric
        const target = data.savings_25yr_inr;
        const duration = 1500;
        const steps = 60;
        const stepTime = Math.abs(Math.floor(duration / steps));
        let current = 0;

        // Quick ease-out simulation
        const timer = setInterval(() => {
            current += target / steps;
            if (current >= target) {
                setAnimatedSavings(target);
                clearInterval(timer);
            } else {
                setAnimatedSavings(Math.floor(current));
            }
        }, stepTime);

        return () => clearInterval(timer);
    }, [data.savings_25yr_inr]);

    const generationData = data.monthly_generation_kwh.map((value, idx) => ({
        name: MONTHS[idx],
        kWh: value
    }));

    const savingsData = data.cumulative_savings_by_year.map((value, idx) => ({
        year: `Year ${idx}`,
        Savings: value,
        Zero: 0
    }));

    const formatINR = (val: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);

    return (
        <div className="animate-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1000px', margin: '0 auto' }}>

            {/* Hero Metric */}
            <div className="glass-panel" style={{ padding: '2.5rem', textAlign: 'center' }}>
                <h2 style={{ color: 'var(--text-secondary)', fontSize: '1.2rem', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Estimated 25-Year Savings
                </h2>
                <div style={{ fontSize: '3rem', fontWeight: 700, lineHeight: 1, marginBottom: '1rem', color: 'var(--color-primary)' }}>
                    {formatINR(animatedSavings)}
                </div>
                <div style={{ display: 'flex', justifyContent: 'center', gap: '2rem', flexWrap: 'wrap' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#f2f4f7', padding: '0.5rem 1rem', borderRadius: '20px' }}>
                        <Clock size={18} color="var(--color-primary)" />
                        <span>Payback: <strong>{data.payback_years.toFixed(1)} yrs</strong></span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#f2f4f7', padding: '0.5rem 1rem', borderRadius: '20px' }}>
                        <Zap size={18} color="#e8a500" />
                        <span>Bill Offset: <strong>{data.bill_offset_pct.toFixed(0)}%</strong></span>
                    </div>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>

                {/* Cost Breakdown */}
                <div className="glass-panel" style={{ padding: '2rem' }}>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <IndianRupee size={18} color="var(--color-primary)" /> Investment Summary
                    </h3>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Equipment (Panels & Inverter)</span>
                            <span>{formatINR(data.cost_breakdown.panel_cost_inr + data.cost_breakdown.inverter_cost_inr)}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Installation & Wiring</span>
                            <span>{formatINR(data.cost_breakdown.mounting_wiring_inr + data.cost_breakdown.installation_cost_inr)}</span>
                        </div>
                        <div style={{ width: '100%', height: '1px', background: 'var(--border-subtle)' }} />
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600 }}>
                            <span>Gross Cost</span>
                            <span>{formatINR(data.cost_breakdown.gross_cost_inr)}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--color-primary)' }}>
                            <span>PM Surya Ghar Subsidy</span>
                            <span>- {formatINR(data.cost_breakdown.subsidy_inr)}</span>
                        </div>
                        <div style={{ width: '100%', height: '1px', background: 'var(--border-subtle)' }} />
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.2rem', fontWeight: 700 }}>
                            <span>Net Investment</span>
                            <span>{formatINR(data.cost_breakdown.net_cost_inr)}</span>
                        </div>
                    </div>

                    {data.emi && (
                        <div style={{ marginTop: '2rem', padding: '1.2rem', background: '#f0f6ff', borderRadius: '10px', border: '1px solid #c6dafb' }}>
                            <h4 style={{ color: '#1a73e8', marginBottom: '0.5rem', fontSize: '0.95rem', fontWeight: 600 }}>Financing Option (SBI Solar Loan)</h4>
                            <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{formatINR(data.emi.monthly_emi_inr)} <span style={{ fontSize: '1rem', color: 'var(--text-secondary)', fontWeight: 400 }}>/ month</span></div>
                            <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>for {data.emi.tenure_months / 12} years @ {data.emi.annual_rate_pct}% p.a.</div>
                        </div>
                    )}
                </div>

                {/* Charts Container */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

                    {/* Generation Chart */}
                    <div className="glass-panel" style={{ padding: '1.5rem', flex: 1 }}>
                        <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>Monthly Generation (kWh)</h3>
                        <div style={{ height: '200px' }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={generationData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
                                    <XAxis dataKey="name" stroke="var(--text-secondary)" fontSize={12} tickLine={false} axisLine={false} />
                                    <YAxis stroke="var(--text-secondary)" fontSize={12} tickLine={false} axisLine={false} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: 'var(--bg-surface-elevated)', border: 'none', borderRadius: '8px' }}
                                        itemStyle={{ color: 'var(--color-warning)' }}
                                    />
                                    <Bar dataKey="kWh" fill="var(--color-warning)" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Savings Chart */}
                    <div className="glass-panel" style={{ padding: '1.5rem', flex: 1 }}>
                        <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <TrendingUp size={16} color="var(--color-primary)" /> Cumulative Return on Investment
                        </h3>
                        <div style={{ height: '200px' }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={savingsData} margin={{ top: 5, right: 5, left: 10, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
                                    <XAxis dataKey="year" stroke="var(--text-secondary)" fontSize={12} tickLine={false} axisLine={false} tick={false} />
                                    <YAxis stroke="var(--text-secondary)" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `₹${val / 1000}k`} />
                                    <Tooltip
                                        formatter={(val: any) => formatINR(val as number)}
                                        contentStyle={{ backgroundColor: 'var(--bg-surface-elevated)', border: 'none', borderRadius: '8px' }}
                                    />
                                    <Line type="monotone" dataKey="Zero" stroke="var(--text-muted)" strokeWidth={1} dot={false} strokeDasharray="5 5" />
                                    <Line type="monotone" dataKey="Savings" stroke="var(--color-primary)" strokeWidth={3} dot={false} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}
