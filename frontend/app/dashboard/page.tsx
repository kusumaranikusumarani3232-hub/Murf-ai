'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle,
  Clock,
  Globe,
  MessageSquare,
  Phone,
  ShieldAlert,
  Activity,
  XCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Escalation {
  reference_id: string;
  user_id: string;
  description: string;
  checked_actions: string;
  urgency: string;
  language: string;
  follow_up_method: string;
  status: string;
  created_at: string;
}

export default function DashboardPage() {
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState<{
    summary: { total_calls: number; successful_calls: number; failed_calls: number };
    calls: Array<{ session_id: string; timestamp: string; channel: string; outcome: string; duration?: number }>;
  }>({
    summary: { total_calls: 0, successful_calls: 0, failed_calls: 0 },
    calls: [],
  });

  const fetchEscalations = async () => {
    try {
      const res = await fetch('/api/escalations');
      if (res.ok) {
        const data = await res.json();
        setEscalations(data);
      }
    } catch (err) {
      console.error('Failed to load escalations:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const res = await fetch('/api/analytics');
      if (res.ok) {
        const data = await res.json();
        setAnalytics(data);
      }
    } catch (err) {
      console.error('Failed to load analytics:', err);
    }
  };

  useEffect(() => {
    fetchEscalations();
    fetchAnalytics();
    // Poll every 5 seconds to show new data in real-time
    const interval = setInterval(() => {
      fetchEscalations();
      fetchAnalytics();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const getUrgencyBadge = (urgency: string) => {
    const u = urgency.toLowerCase();
    if (u === 'high') {
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-red-500/20 bg-red-500/10 px-2.5 py-0.5 text-xs font-semibold text-red-500">
          <ShieldAlert className="size-3.5" /> High
        </span>
      );
    }
    if (u === 'medium') {
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/20 bg-amber-500/10 px-2.5 py-0.5 text-xs font-semibold text-amber-500">
          <AlertTriangle className="size-3.5" /> Medium
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-500">
        <CheckCircle className="size-3.5" /> Low
      </span>
    );
  };

  return (
    <div className="bg-background text-foreground min-h-screen p-6 md:p-12">
      <div className="mx-auto max-w-5xl">
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/">
              <Button variant="outline" size="icon" className="rounded-full">
                <ArrowLeft className="size-4" />
              </Button>
            </Link>
            <div>
              <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Teacher Dashboard</h1>
              <p className="text-muted-foreground text-sm">
                Review open support and escalation requests from learners.
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              fetchEscalations();
              fetchAnalytics();
            }}
            className="rounded-full"
          >
            Refresh
          </Button>
        </div>

        {/* Call Analytics Cards */}
        <div className="mb-8 grid gap-4 grid-cols-1 sm:grid-cols-3">
          <div className="border-border bg-card/40 flex items-center justify-between overflow-hidden rounded-2xl border p-6 shadow-xs backdrop-blur-sm">
            <div>
              <span className="text-muted-foreground text-xs font-semibold tracking-wider uppercase">
                Total Calls
              </span>
              <h2 className="mt-2 text-3xl font-extrabold tracking-tight text-foreground md:text-4xl">
                {analytics.summary.total_calls}
              </h2>
            </div>
            <div className="bg-primary/10 rounded-full p-3 text-primary">
              <Activity className="size-6" />
            </div>
          </div>

          <div className="border-border bg-card/40 flex items-center justify-between overflow-hidden rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-6 shadow-xs backdrop-blur-sm">
            <div>
              <span className="text-emerald-500 text-xs font-semibold tracking-wider uppercase">
                Successful Calls
              </span>
              <h2 className="mt-2 text-3xl font-extrabold tracking-tight text-emerald-500 md:text-4xl">
                {analytics.summary.successful_calls}
              </h2>
            </div>
            <div className="bg-emerald-500/10 rounded-full p-3 text-emerald-500">
              <CheckCircle className="size-6" />
            </div>
          </div>

          <div className="border-border bg-card/40 flex items-center justify-between overflow-hidden rounded-2xl border border-red-500/20 bg-red-500/5 p-6 shadow-xs backdrop-blur-sm">
            <div>
              <span className="text-red-500 text-xs font-semibold tracking-wider uppercase">
                Failed Calls
              </span>
              <h2 className="mt-2 text-3xl font-extrabold tracking-tight text-red-500 md:text-4xl">
                {analytics.summary.failed_calls}
              </h2>
            </div>
            <div className="bg-red-500/10 rounded-full p-3 text-red-500">
              <XCircle className="size-6" />
            </div>
          </div>
        </div>

        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <div className="border-primary h-8 w-8 animate-spin rounded-full border-4 border-t-transparent"></div>
          </div>
        ) : escalations.length === 0 ? (
          <div className="border-border bg-card/30 flex h-64 flex-col items-center justify-center rounded-2xl border border-dashed p-8 text-center backdrop-blur-sm">
            <MessageSquare className="text-muted-foreground mb-4 size-12 opacity-50" />
            <h3 className="text-lg font-semibold">No escalations yet</h3>
            <p className="text-muted-foreground mt-1 max-w-sm text-sm">
              When a learner expresses distress or requests a teacher during the voice call, they
              will appear here.
            </p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {escalations.map((item) => (
              <div
                key={item.reference_id}
                className="group border-border bg-card/40 hover:bg-card/70 relative flex flex-col justify-between overflow-hidden rounded-2xl border p-6 shadow-xs backdrop-blur-sm transition-all hover:shadow-md"
              >
                <div>
                  <div className="border-border/50 mb-4 flex items-center justify-between gap-2 border-b pb-3">
                    <span className="text-primary font-mono text-sm font-bold tracking-wider">
                      {item.reference_id}
                    </span>
                    {getUrgencyBadge(item.urgency)}
                  </div>

                  <div className="space-y-3">
                    <div>
                      <h4 className="text-muted-foreground text-xs font-semibold tracking-wider uppercase">
                        Problem Description
                      </h4>
                      <p className="mt-0.5 text-sm font-medium">{item.description}</p>
                    </div>

                    {item.checked_actions && (
                      <div>
                        <h4 className="text-muted-foreground text-xs font-semibold tracking-wider uppercase">
                          What the Agent Checked
                        </h4>
                        <p className="text-muted-foreground mt-0.5 text-xs">
                          {item.checked_actions}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="border-border/30 mt-6 grid grid-cols-2 gap-x-4 gap-y-2 border-t pt-4 text-xs">
                  <div className="text-muted-foreground flex items-center gap-1.5">
                    <Globe className="size-3.5" />
                    <span>
                      Language: <strong className="text-foreground">{item.language}</strong>
                    </span>
                  </div>
                  <div className="text-muted-foreground flex items-center gap-1.5">
                    <Phone className="size-3.5" />
                    <span>
                      Follow-up:{' '}
                      <strong className="text-foreground">{item.follow_up_method}</strong>
                    </span>
                  </div>
                  <div className="text-muted-foreground col-span-2 flex items-center gap-1.5">
                    <Clock className="size-3.5" />
                    <span>
                      Created:{' '}
                      <strong className="text-foreground">
                        {new Date(item.created_at).toLocaleString()}
                      </strong>
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
