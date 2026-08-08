import { Button } from '@/components/ui/button';

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
  return (
    <div className="flex h-full w-full flex-col items-center justify-center px-6 text-center">
      <WelcomeImage />

      <section className="flex flex-col items-center">
        <h1 className="text-foreground text-3xl font-bold tracking-tight md:text-5xl">
          English Learning Coach
        </h1>

        <p className="text-foreground max-w-prose pt-3 leading-6 font-medium">
          Practice English through friendly voice conversations
        </p>

        <Button
          size="lg"
          onClick={onStartCall}
          className="mt-6 w-64 rounded-full font-mono text-xs font-bold tracking-wider uppercase"
        >
          {startButtonText}
        </Button>
      </section>

      <div className="fixed bottom-5 left-0 flex w-full items-center justify-center px-6">
        <p className="text-muted-foreground max-w-prose pt-1 text-xs leading-5 font-normal text-pretty md:text-sm">
          Your friendly English Learning Coach is ready to help you practice.
        </p>
      </div>
    </div>
  );
};