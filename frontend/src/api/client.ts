const apiBase = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') || '';

export async function fetcher<T>(path: string): Promise<T> {
  const url = `${apiBase}${path}`;
  console.log('[API request]', url);
  const response = await fetch(url);

  if (!response.ok) {
    const payload = await response.text();
    throw new Error(`API request failed: ${response.status} ${response.statusText} - ${payload}`);
  }

  return response.json();
}
