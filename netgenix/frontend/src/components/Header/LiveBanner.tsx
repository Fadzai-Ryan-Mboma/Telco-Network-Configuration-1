import { Wifi } from 'lucide-react';

interface LiveBannerProps {
  connected: boolean;
  timestamp?: string | null;
  statusText?: string | null;
}

export default function LiveBanner({ connected, timestamp, statusText }: LiveBannerProps) {
  const label = connected ? 'NETGENIX ONLINE' : 'NETGENIX STATUS LOADING';

  return (
    <div className="bg-bg-card/50 border border-white/5 rounded-xl px-4 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className={`status-dot ${connected ? 'status-dot-success animate-pulse-dot' : 'status-dot-error'}`} />
        <Wifi className={`w-4 h-4 ${connected ? 'text-accent-green' : 'text-status-warning'}`} />
        <span className={`text-sm font-medium ${connected ? 'text-accent-green' : 'text-status-warning'}`}>
          {label}
        </span>
        {statusText && (
          <span className="hidden text-xs text-gray-500 sm:inline">
            Access: {statusText.replace(/[✅❌⚠️]/g, '').trim()}
          </span>
        )}
      </div>
      {timestamp && (
        <span className="text-sm text-gray-500">
          Updated: {new Date(timestamp).toLocaleString()}
        </span>
      )}
    </div>
  );
}
