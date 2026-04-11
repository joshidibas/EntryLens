const EMBEDDING_DELTA_THRESHOLD = 0.35;

export function getEmbeddingKey(embedding: number[] | undefined, precision = 3): string {
  if (!embedding || embedding.length === 0) {
    return "";
  }

  return embedding.map((value) => value.toFixed(precision)).join(",");
}

export function getEmbeddingDistance(a: number[] | undefined, b: number[] | undefined): number {
  if (!a || !b || a.length !== b.length || a.length === 0) {
    return Number.POSITIVE_INFINITY;
  }

  let sum = 0;
  for (let index = 0; index < a.length; index += 1) {
    const delta = a[index] - b[index];
    sum += delta * delta;
  }

  return Math.sqrt(sum / a.length);
}

export function hasMeaningfulEmbeddingChange(
  a: number[] | undefined,
  b: number[] | undefined,
  threshold = EMBEDDING_DELTA_THRESHOLD,
): boolean {
  return getEmbeddingDistance(a, b) > threshold;
}
