const apiBase = import.meta.env.VITE_API_URL?.replace(/\/$/, '') || '';

export async function fetcher<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBase}${path}`);

  if (!response.ok) {
    const payload = await response.text();
    throw new Error(`API request failed: ${response.status} ${response.statusText} - ${payload}`);
  }

  return response.json();
}
