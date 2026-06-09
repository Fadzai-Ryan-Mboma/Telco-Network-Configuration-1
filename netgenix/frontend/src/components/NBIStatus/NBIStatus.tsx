import { AlertTriangle, CheckCircle2, Clock, HelpCircle, ShieldAlert } from 'lucide-react';
import type { NBIDiagnostics, NBIEnvironmentDiagnostic } from '../../services/api';

interface NBIStatusProps {
  diagnostics: NBIDiagnostics | null;
  loading?: boolean;
}

const statusCopy: Record<NBIEnvironmentDiagnostic['classification'], { label: string; className: string }> = {
  success: { label: 'Authenticated', className: 'badge-success' },
  auth_failed: { label: 'Auth failed', className: 'badge-error' },
  timeout: { label: 'Timeout', className: 'badge-warning' },
  endpoint_missing: { label: 'Endpoint missing', className: 'badge-error' },
  method_wrong: { label: 'Endpoint reachable', className: 'badge-warning' },
  unknown: { label: 'Unknown', className: 'badge-warning' },
};

function StatusIcon({ classification }: { classification: NBIEnvironmentDiagnostic['classification'] }) {
  if (classification === 'success') {
    return <CheckCircle2 className="h-5 w-5 text-status-success" />;
  }
  if (classification === 'timeout') {
    return <Clock className="h-5 w-5 text-status-warning" />;
  }
  if (classification === 'unknown' || classification === 'method_wrong') {
    return <HelpCircle className="h-5 w-5 text-status-warning" />;
  }
  return <ShieldAlert className="h-5 w-5 text-status-error" />;
}

function EnvironmentCard({ environment }: { environment: NBIEnvironmentDiagnostic }) {
  const status = statusCopy[environment.classification];

  return (
    <div className="rounded-xl border border-white/5 bg-bg-input p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <StatusIcon classification={environment.classification} />
          <div>
            <h3 className="font-semibold text-white">{environment.name}</h3>
            <p className="text-xs text-gray-500">Huawei iMaster MAE</p>
          </div>
        </div>
        <span className={`badge ${status.className}`}>{status.label}</span>
      </div>

      <div className="mt-4 grid gap-2 text-sm text-gray-300 md:grid-cols-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-gray-500">GUI</p>
          <p>{environment.gui_reachable ? 'Reachable' : 'Unavailable'}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-gray-500">NBI</p>
          <p>{environment.nbi_reachable ? 'Reachable' : 'Unavailable'}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-gray-500">MAE Result</p>
          <p>{environment.ret_code ? `${environment.ret_code} ${environment.ret_message ?? ''}` : 'No login result'}</p>
        </div>
      </div>
    </div>
  );
}

export default function NBIStatus({ diagnostics, loading = false }: NBIStatusProps) {
  return (
    <section className="card">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-lg font-semibold">
            <AlertTriangle className="h-5 w-5 text-accent-orange" />
            Access / Evaluation NBI State
          </h2>
          <p className="text-sm text-gray-500">
            Live platform connection status for Access and Evaluation.
          </p>
        </div>
        {loading && <span className="badge badge-warning">Checking</span>}
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        {(diagnostics?.environments ?? []).map((environment) => (
          <EnvironmentCard key={environment.name} environment={environment} />
        ))}
      </div>

      {!loading && !diagnostics && (
        <p className="text-sm text-gray-500">Connection status is loading.</p>
      )}
    </section>
  );
}
