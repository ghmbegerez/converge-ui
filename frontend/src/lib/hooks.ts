import { useEffect, useState } from "react";

export function usePersistedState(key: string, initialValue: string) {
  const [value, setValue] = useState<string>(() => {
    if (typeof window === "undefined") {
      return initialValue;
    }
    return window.localStorage.getItem(key) ?? initialValue;
  });

  useEffect(() => {
    window.localStorage.setItem(key, value);
  }, [key, value]);

  return [value, setValue] as const;
}

export async function api<T = Record<string, unknown>>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

export function useSnapshot<T = Record<string, unknown>>(path: string, intervalMs = 5000) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const payload = await api<T>(path);
        if (active) {
          setData(payload);
          setError(null);
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "Unknown error");
        }
      }
    };
    load();
    const timer = window.setInterval(load, intervalMs);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [path, intervalMs]);

  return { data, error };
}
