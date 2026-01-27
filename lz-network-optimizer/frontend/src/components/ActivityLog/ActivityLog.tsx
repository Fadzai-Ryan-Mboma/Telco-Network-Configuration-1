import { CheckCircle, XCircle, AlertCircle, Clock } from 'lucide-react';
import type { ActivityRecord } from '../../services/api';

interface ActivityLogProps {
  activities: ActivityRecord[];
  loading?: boolean;
}

export default function ActivityLog({ activities, loading }: ActivityLogProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-status-success" />;
      case 'rejected':
        return <XCircle className="w-5 h-5 text-status-error" />;
      case 'detected':
        return <AlertCircle className="w-5 h-5 text-status-warning" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-status-success/20';
      case 'rejected':
        return 'bg-status-error/20';
      case 'detected':
        return 'bg-status-warning/20';
      default:
        return 'bg-gray-500/20';
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="card animate-pulse">
            <div className="flex gap-4">
              <div className="w-10 h-10 bg-white/5 rounded-full" />
              <div className="flex-1">
                <div className="h-4 bg-white/5 rounded w-3/4 mb-2" />
                <div className="h-3 bg-white/5 rounded w-1/2" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (activities.length === 0) {
    return (
      <div className="card text-center py-8 text-gray-500">
        No recent activity. Start by running an optimization!
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {activities.map((activity, index) => (
        <div key={index} className="card">
          <div className="flex gap-4">
            {/* Status Icon */}
            <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${getStatusBg(activity.status)}`}>
              {getStatusIcon(activity.status)}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h4 className="font-medium text-white">{activity.description}</h4>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="badge badge-success text-xs">
                      {activity.site_name}
                    </span>
                  </div>
                </div>
                <span className="text-xs text-gray-500 flex-shrink-0">
                  {new Date(activity.timestamp).toLocaleTimeString()}
                </span>
              </div>

              {/* Changes */}
              {activity.changes && (
                <div className="mt-2 text-sm">
                  <span className="text-gray-500">Changes: </span>
                  <span className="text-gray-300 font-mono">{activity.changes}</span>
                </div>
              )}

              {/* Result */}
              {activity.result && (
                <div className="mt-1 text-sm">
                  <span className="text-gray-500">Result: </span>
                  <span className="text-gray-300">{activity.result}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
