'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Clock, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Escalation {
  reference_id: string;
  description: string;
  urgency: string;
  language: string;
  follow_up_method: string;
  created_at: string;
}

function WelcomeImage() {
  return null;
}

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [escalations, setEscalations] = useState<Escalation[]>([]);

  const fetchEscalations = async () => {
    try {
      const res = await fetch('/api/escalations');
      if (res.ok) {
        const data = await res.json();
        setEscalations(data.slice(0, 3)); // show only top 3 most recent
      }
    } catch (err) {
      console.error('Failed to load escalations:', err);
    }
  };

  useEffect(() => {
    fetchEscalations();
    const interval = setInterval(fetchEscalations, 5000);
    return () => clearInterval(interval);
  }, []);

  const getUrgencyColor = (urgency: string) => {
    const u = urgency.toLowerCase();
    if (u === 'high') return 'text-red-500 bg-red-500/10 border-red-500/20';
    if (u === 'medium') return 'text-amber-500 bg-amber-500/10 border-amber-500/20';
    return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20';
  };

  return (
    <div className="flex min-h-screen w-full flex-col items-center justify-between px-6 py-12 md:py-24">
      <div />

      <section className="flex max-w-lg flex-col items-center text-center">
        <WelcomeImage />
        <h1 className="text-foreground text-4xl font-bold tracking-tight md:text-6xl">
          English Learning Coach
        </h1>

        <p className="text-muted-foreground max-w-prose pt-4 text-base leading-6 font-medium">
          Practice English through friendly voice conversations
        </p>

        <Button
          size="lg"
          onClick={onStartCall}
          className="mt-8 w-64 rounded-full font-mono text-xs font-bold tracking-wider uppercase transition-transform hover:scale-105"
        >
          {startButtonText}
        </Button>
      </section>

      {/* Escalation request feed */}
      <div className="mt-12 mb-8 w-full max-w-2xl">
        <div className="border-border/40 mb-4 flex items-center justify-between border-b pb-2">
          <h3 className="text-muted-foreground text-xs font-bold tracking-wider uppercase">
            Open Escalation Requests
          </h3>
          <Link
            href="/dashboard"
            className="text-primary flex items-center gap-1 text-xs font-semibold hover:underline"
          >
            View Full Dashboard <ExternalLink className="size-3" />
          </Link>
        </div>

        {escalations.length === 0 ? (
          <p className="text-muted-foreground border-border/40 rounded-xl border border-dashed py-4 text-center text-xs italic">
            No active escalations. Your learning requests are up to date!
          </p>
        ) : (
          <div className="space-y-3">
            {escalations.map((esc) => (
              <div
                key={esc.reference_id}
                className="border-border bg-card/20 hover:bg-card/40 flex items-start justify-between gap-4 rounded-xl border p-3.5 text-left text-xs backdrop-blur-xs transition-colors"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-primary font-mono font-bold">{esc.reference_id}</span>
                    <span className="text-muted-foreground text-[10px]">•</span>
                    <span className="text-muted-foreground flex items-center gap-1">
                      <Clock className="size-3" />
                      {new Date(esc.created_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>
                  <p className="text-foreground line-clamp-1 font-medium">{esc.description}</p>
                </div>
                <div className="flex shrink-0 flex-col items-end gap-1.5">
                  <span
                    className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${getUrgencyColor(esc.urgency)}`}
                  >
                    {esc.urgency.toUpperCase()}
                  </span>
                  <span className="text-muted-foreground text-[10px] italic">
                    Follow-up: {esc.follow_up_method}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex w-full items-center justify-center">
        <p className="text-muted-foreground max-w-prose text-xs leading-5 font-normal text-pretty">
          Your friendly English Learning Coach is ready to help you practice.
        </p>
      </div>
    </div>
  );
};
