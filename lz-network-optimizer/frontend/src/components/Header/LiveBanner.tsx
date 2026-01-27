import { Wifi } from 'lucide-react';

interface LiveBannerProps {
  connected: boolean;
  timestamp?: string | null;
}

export default function LiveBanner({ connected, timestamp }: LiveBannerProps) {
  return (
    <div className="bg-bg-card/50 border border-white/5 rounded-xl px-4 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className={`status-dot ${connected ? 'status-dot-success animate-pulse-dot' : 'status-dot-error'}`} />
        <Wifi className={`w-4 h-4 ${connected ? 'text-accent-green' : 'text-status-error'}`} />
        <span className={`text-sm font-medium ${connected ? 'text-accent-green' : 'text-status-error'}`}>
          {connected ? 'CONNECTED TO HUAWEI IMASTER MAE' : 'DISCONNECTED'}
        </span>
      </div>
      {timestamp && (
        <span className="text-sm text-gray-500">
          Updated: {new Date(timestamp).toLocaleString()}
        </span>
      )}
    </div>
  );
}
