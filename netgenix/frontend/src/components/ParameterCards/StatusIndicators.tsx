import type {
  EvaluationStatus,
  NBIDiagnostics,
  NBIEnvironmentDiagnostic,
  SystemStatus,
} from '../../services/api';

interface StatusIndicatorsProps {
  status: SystemStatus | null;
  nbiDiagnostics?: NBIDiagnostics | null;
  evaluationStatus?: EvaluationStatus | null;
}

function getNBIIndicator(environment?: NBIEnvironmentDiagnostic) {
  if (!environment) {
    return {
      connected: false,
      warning: true,
    };
  }

  return {
    connected: environment.classification === 'success',
    warning: ['timeout', 'method_wrong', 'unknown'].includes(environment.classification),
  };
}

export default function StatusIndicators({
  status,
  nbiDiagnostics,
  evaluationStatus,
}: StatusIndicatorsProps) {
  const access = nbiDiagnostics?.environments.find((environment) => environment.name === 'Access');

  const indicators = [
    {
      label: 'API Connection',
      connected: status?.api_connected ?? false,
    },
    {
      label: 'Network Elements',
      connected: status?.ne_connected ?? false,
      warning: status?.ne_status?.includes('Unknown'),
    },
    {
      label: 'Database',
      connected: status?.db_connected ?? false,
    },
    {
      label: 'Access NBI',
      ...getNBIIndicator(access),
    },
    {
      label: 'Evaluation GUI',
      connected: evaluationStatus?.connected ?? false,
      warning: !evaluationStatus,
    },
  ];

  return (
    <div className="flex flex-wrap gap-4">
      {indicators.map((indicator) => (
        <div
          key={indicator.label}
          className="flex items-center gap-2 bg-bg-card rounded-full px-4 py-2 border border-white/5"
        >
          <div
            className={`status-dot ${
              indicator.warning
                ? 'status-dot-warning'
                : indicator.connected
                ? 'status-dot-success'
                : 'status-dot-error'
            }`}
          />
          <span className="text-sm text-gray-300">{indicator.label}</span>
        </div>
      ))}
    </div>
  );
}
