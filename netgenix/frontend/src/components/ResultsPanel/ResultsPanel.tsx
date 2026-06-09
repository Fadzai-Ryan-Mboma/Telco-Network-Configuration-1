import { BarChart3, AlertTriangle, Zap, TrendingUp, Check, X } from 'lucide-react';
import type { OptimizationResult } from '../../services/api';
import RiskGauge from './RiskGauge';
import ParameterChange from './ParameterChange';
import MMLCommands from './MMLCommands';

interface ResultsPanelProps {
  result: OptimizationResult | null;
  onApprove: () => void;
  onReject: () => void;
  isExecuting?: boolean;
}

export default function ResultsPanel({
  result,
  onApprove,
  onReject,
  isExecuting
}: ResultsPanelProps) {
  // Empty state
  if (!result) {
    return (
      <div className="card h-full flex flex-col items-center justify-center text-center py-16">
        <div className="w-16 h-16 bg-accent-teal/20 rounded-2xl flex items-center justify-center mb-4">
          <BarChart3 className="w-8 h-8 text-accent-teal" />
        </div>
        <h3 className="text-xl font-semibold text-white mb-2">Ready to Optimize</h3>
        <p className="text-gray-400 max-w-sm">
          Use the AI assistant to describe your network optimization goals.
          I'll analyze the situation and provide detailed recommendations.
        </p>
      </div>
    );
  }

  // Error state
  if (result.status === 'error') {
    return (
      <div className="card h-full flex flex-col items-center justify-center text-center py-16">
        <div className="w-16 h-16 bg-status-error/20 rounded-2xl flex items-center justify-center mb-4">
          <AlertTriangle className="w-8 h-8 text-status-error" />
        </div>
        <h3 className="text-xl font-semibold text-white mb-2">Analysis Failed</h3>
        <p className="text-gray-400 max-w-sm">
          {result.error_message || 'An error occurred during analysis.'}
        </p>
      </div>
    );
  }

  return (
    <div className="card h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-accent-green/20 rounded-lg flex items-center justify-center">
          <AlertTriangle className="w-5 h-5 text-accent-green" />
        </div>
        <div>
          <h3 className="font-semibold text-white">Analysis Complete</h3>
          <p className="text-xs text-gray-500">AI-powered recommendations ready for review</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Left Column - Issue Analysis */}
        <div className="col-span-2 space-y-6">
          {/* Issue Analysis */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="w-4 h-4 text-status-warning" />
              <h4 className="font-medium text-white">Issue Analysis</h4>
            </div>
            <div className="bg-bg-card-hover rounded-lg p-4">
              <p className="text-gray-300 mb-3">{result.issue}</p>
              {result.detailed_issue && (
                <div className="text-sm text-gray-400 space-y-1">
                  {result.detailed_issue.split('\n').filter(line => line.trim()).map((line, i) => (
                    <p key={i}>{line.startsWith('•') || line.startsWith('-') ? line : `• ${line}`}</p>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Recommended Changes */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Zap className="w-4 h-4 text-accent-teal" />
              <h4 className="font-medium text-white">Recommended Changes</h4>
            </div>
            <div className="space-y-3">
              {result.recommendations.map((rec, index) => (
                <ParameterChange
                  key={index}
                  parameter={rec.parameter}
                  currentValue={rec.current_value}
                  newValue={rec.recommended_value}
                  unit={rec.unit}
                />
              ))}
            </div>
          </div>

          {/* MML Commands */}
          {result.mml_commands.length > 0 && (
            <MMLCommands commands={result.mml_commands} />
          )}
        </div>

        {/* Right Column - Risk & Impact */}
        <div className="space-y-6">
          {/* Risk Assessment */}
          <RiskGauge
            score={result.risk_score}
            level={result.risk_level}
            details={result.detailed_risk}
          />

          {/* Expected Impact */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-4 h-4 text-accent-green" />
              <h4 className="font-medium text-white">Expected Impact</h4>
            </div>
            <div className="bg-bg-card-hover rounded-lg p-4 space-y-2">
              <p className="text-sm text-gray-300">{result.expected_impact}</p>
              {result.detailed_impact && (
                <div className="text-sm text-gray-400 space-y-1 mt-2">
                  {result.detailed_impact.split('\n').filter(line => line.trim()).map((line, i) => (
                    <div key={i} className="flex items-start gap-2">
                      <TrendingUp className="w-3 h-3 text-accent-green mt-1 flex-shrink-0" />
                      <span>{line.replace(/^[•\-]\s*/, '')}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            <div className="rounded-lg border border-status-warning/30 bg-status-warning/10 p-3 text-xs text-status-warning">
              Safe mode is active. Approval performs a dry-run unless backend live MML is explicitly enabled.
            </div>
            <button
              onClick={onApprove}
              disabled={isExecuting}
              className="btn-primary w-full"
            >
              <Check className="w-4 h-4" />
              <span>Approve & Execute</span>
            </button>
            <button
              onClick={onReject}
              disabled={isExecuting}
              className="btn-secondary w-full"
            >
              <X className="w-4 h-4" />
              <span>Reject Changes</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
