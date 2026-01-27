interface RiskGaugeProps {
  score: number;
  level: 'LOW' | 'MEDIUM' | 'HIGH';
}

export default function RiskGauge({ score, level }: RiskGaugeProps) {
  const getColor = () => {
    switch (level) {
      case 'LOW':
        return {
          bg: 'bg-status-success',
          text: 'text-status-success',
          glow: 'shadow-status-success/50',
        };
      case 'MEDIUM':
        return {
          bg: 'bg-status-warning',
          text: 'text-status-warning',
          glow: 'shadow-status-warning/50',
        };
      case 'HIGH':
        return {
          bg: 'bg-status-error',
          text: 'text-status-error',
          glow: 'shadow-status-error/50',
        };
    }
  };

  const colors = getColor();
  const percentage = Math.min(100, (score / 10) * 100);

  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <div className="w-3 h-3 rounded-full border-2 border-current" style={{ borderColor: colors.text.replace('text-', '') }} />
        <h4 className="font-medium text-white">Risk Assessment</h4>
      </div>
      <div className="bg-bg-card-hover rounded-lg p-4 flex flex-col items-center">
        {/* Circular Gauge */}
        <div className="relative w-24 h-24 mb-3">
          <div className={`absolute inset-0 rounded-full ${colors.bg} opacity-20`} />
          <div
            className={`absolute inset-2 rounded-full ${colors.bg} shadow-lg ${colors.glow}`}
            style={{
              background: `conic-gradient(currentColor ${percentage}%, transparent ${percentage}%)`,
            }}
          />
          <div className="absolute inset-4 rounded-full bg-bg-card flex items-center justify-center">
            <div className={`w-8 h-8 rounded-full ${colors.bg}`} />
          </div>
        </div>

        {/* Label */}
        <span className={`text-lg font-bold ${colors.text}`}>{level} RISK</span>
        <span className="text-sm text-gray-500">Score: {score.toFixed(1)}/10</span>

        {/* Progress bar */}
        <div className="w-full h-1.5 bg-white/10 rounded-full mt-3 overflow-hidden">
          <div
            className={`h-full ${colors.bg} rounded-full transition-all duration-500`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    </div>
  );
}
