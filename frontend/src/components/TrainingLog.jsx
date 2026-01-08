import React, { useState, useEffect } from 'react';

export function TrainingLog({ userId, functionCalls }) {
  const [runs, setRuns] = useState([]);
  const [weeklyStats, setWeeklyStats] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch runs on mount and when function calls update (new run logged)
  useEffect(() => {
    fetchRuns();
  }, [userId, functionCalls]);

  const fetchRuns = async () => {
    try {
      const response = await fetch(`/api/users/${userId}/runs`);
      if (response.ok) {
        const data = await response.json();
        setRuns(data);
        calculateWeeklyStats(data);
      }
    } catch (err) {
      console.error('Failed to fetch runs:', err);
    } finally {
      setLoading(false);
    }
  };

  const calculateWeeklyStats = (runData) => {
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    
    const weekRuns = runData.filter(r => new Date(r.run_date) >= weekAgo);
    const totalMiles = weekRuns.reduce((sum, r) => sum + r.distance_miles, 0);
    const totalMinutes = weekRuns.reduce((sum, r) => sum + r.duration_minutes, 0);
    
    setWeeklyStats({
      miles: totalMiles.toFixed(1),
      runs: weekRuns.length,
      time: formatDuration(totalMinutes)
    });
  };

  const formatDuration = (minutes) => {
    const hrs = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hrs > 0) {
      return `${hrs}h ${mins}m`;
    }
    return `${mins}m`;
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    }
    return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };

  if (loading) {
    return (
      <div className="p-4">
        <div className="animate-pulse space-y-4">
          <div className="h-20 bg-gray-200 rounded-lg" />
          <div className="h-16 bg-gray-200 rounded-lg" />
          <div className="h-16 bg-gray-200 rounded-lg" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-6">
      {/* Weekly Stats */}
      {weeklyStats && (
        <div className="bg-stride-50 rounded-xl p-4">
          <h3 className="text-sm font-medium text-stride-800 mb-3">This Week</h3>
          <div className="grid grid-cols-3 gap-2">
            <div className="text-center">
              <p className="text-2xl font-bold text-stride-600">{weeklyStats.miles}</p>
              <p className="text-xs text-stride-700">miles</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-stride-600">{weeklyStats.runs}</p>
              <p className="text-xs text-stride-700">runs</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-stride-600">{weeklyStats.time}</p>
              <p className="text-xs text-stride-700">time</p>
            </div>
          </div>
        </div>
      )}

      {/* Recent Runs */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-3">Recent Runs</h3>
        {runs.length === 0 ? (
          <p className="text-sm text-gray-500 italic">No runs logged yet. Tell me about your run!</p>
        ) : (
          <div className="space-y-2">
            {runs.slice(0, 10).map((run) => (
              <div key={run.id} className="bg-white border border-gray-200 rounded-lg p-3">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-gray-900">
                      {run.distance_miles} mi
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatDate(run.run_date)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-stride-600">
                      {run.pace_per_mile}/mi
                    </p>
                    <p className="text-xs text-gray-500">
                      {run.duration_minutes} min
                    </p>
                  </div>
                </div>
                {run.notes && (
                  <p className="text-xs text-gray-600 mt-2 border-t pt-2">
                    {run.notes}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Function Calls (for debugging/transparency) */}
      {functionCalls.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-3">Recent Actions</h3>
          <div className="space-y-2">
            {functionCalls.slice(-5).reverse().map((call, idx) => (
              <div key={idx} className="bg-gray-50 rounded-lg p-2 text-xs">
                <p className="font-medium text-gray-700">{formatFunctionName(call.name)}</p>
                {call.result?.message && (
                  <p className="text-gray-600 mt-1">{call.result.message}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function formatFunctionName(name) {
  const names = {
    'log_run': '🏃 Logged Run',
    'get_weekly_summary': '📊 Checked Weekly Stats',
    'get_weather': '🌤️ Checked Weather',
    'set_goal': '🎯 Set Goal',
    'suggest_workout': '💪 Suggested Workout',
    'get_past_context': '🔍 Searched History',
    'get_running_history': '📈 Reviewed Training',
    'get_goals': '🎯 Checked Goals'
  };
  return names[name] || name;
}