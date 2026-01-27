import { Code } from 'lucide-react';

interface MMLCommandsProps {
  commands: string[];
}

export default function MMLCommands({ commands }: MMLCommandsProps) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <Code className="w-4 h-4 text-accent-purple" />
        <h4 className="font-medium text-white">MML Commands</h4>
      </div>
      <div className="bg-bg-input rounded-lg p-4 font-mono text-sm overflow-x-auto">
        {commands.map((command, index) => (
          <div key={index} className="flex gap-4 py-1">
            <span className="text-gray-600 select-none w-6 text-right">
              {String(index + 1).padStart(2, '0')}
            </span>
            <span className="text-accent-teal">{command}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
