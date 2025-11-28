const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

export async function submitQuery(text: string) {
  const res = await fetch(`${API_URL}/api/queries`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: 'include',
    body: JSON.stringify({ query: text }),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: 'Failed to submit query' }));
    throw new Error(error.message || "Failed to submit query");
  }

  return res.json();
}

export async function getReports() {
  const res = await fetch(`${API_URL}/api/reports`, {
    credentials: 'include',
  });
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: 'Failed to fetch reports' }));
    throw new Error(error.message || 'Failed to fetch reports');
  }
  
  return res.json();
}

export async function getReport(id: string) {
  const res = await fetch(`${API_URL}/api/reports/${id}`, {
    credentials: 'include',
  });
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: 'Failed to fetch report' }));
    throw new Error(error.message || 'Failed to fetch report');
  }
  
  return res.json();
}

export async function getDashboards() {
  const res = await fetch(`${API_URL}/api/dashboards`, {
    credentials: 'include',
  });
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: 'Failed to fetch dashboards' }));
    throw new Error(error.message || 'Failed to fetch dashboards');
  }
  
  return res.json();
}

export async function getAlerts() {
  const res = await fetch(`${API_URL}/api/alerts`, {
    credentials: 'include',
  });
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: 'Failed to fetch alerts' }));
    throw new Error(error.message || 'Failed to fetch alerts');
  }
  
  return res.json();
}

export async function createAlert(alert: any) {
  const res = await fetch(`${API_URL}/api/alerts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(alert),
  });
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: 'Failed to create alert' }));
    throw new Error(error.message || 'Failed to create alert');
  }
  
  return res.json();
}

export async function getMetrics(params?: { timeRange?: string; metrics?: string[] }) {
  const queryParams = new URLSearchParams();
  if (params?.timeRange) queryParams.append('timeRange', params.timeRange);
  if (params?.metrics) params.metrics.forEach(m => queryParams.append('metrics', m));
  
  const res = await fetch(`${API_URL}/api/metrics?${queryParams}`, {
    credentials: 'include',
  });
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: 'Failed to fetch metrics' }));
    throw new Error(error.message || 'Failed to fetch metrics');
  }
  
  return res.json();
}
