export type DisplayQualityClass = 'A' | 'B' | 'C' | 'E';

/** Normalize legacy/unverified labels without inferring evidence from a DOI alone. */
export function displayQualityClass(value: unknown, ...provenance: unknown[]): DisplayQualityClass {
  const hasDoi = provenance.some((item) => /10\.\d{4,9}\/\S+/i.test(String(item || '')));
  if (value === 'A' || value === 'B') return value;
  if (value === 'C' && hasDoi) return 'C';
  return 'E';
}
