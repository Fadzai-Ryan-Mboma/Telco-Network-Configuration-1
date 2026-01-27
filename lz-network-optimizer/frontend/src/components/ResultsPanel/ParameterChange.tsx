import { ArrowRight } from 'lucide-react';

interface ParameterChangeProps {
  parameter: string;
  currentValue: string | number;
  newValue: string | number;
  unit: string;
}

export default function ParameterChange({
  parameter,
  currentValue,
  newValue,
  unit
}: ParameterChangeProps) {
  return (
    <div className="bg-bg-card-hover rounded-lg p-4">
      <div className="text-sm text-accent-teal font-medium mb-2">{parameter}</div>
      <div className="flex items-center gap-3">
        <span className="badge bg-accent-purple/20 text-accent-purple px-3 py-1">
          {currentValue} {unit}
        </span>
        <ArrowRight className="w-4 h-4 text-gray-500" />
        <span className="badge bg-accent-green/20 text-accent-green px-3 py-1">
          {newValue} {unit}
        </span>
      </div>
    </div>
  );
}
