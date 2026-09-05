export type ArtifactType = "markdown" | "html";

export interface Artifact {
  type: ArtifactType;
  title: string;
  content: string;
}

export function shouldGenerateArtifact(content: string): boolean {
  const normalized = content.trim().toLowerCase();

  if (!normalized) {
    return false;
  }

  const artifactPatterns = [
    /\bcreate\b.*\b(artifact|document|essay|html|markdown)\b/,
    /\bgenerate\b.*\b(artifact|document|essay|html|markdown)\b/,
    /\bmake\b.*\b(artifact|document|essay|html|markdown)\b/,
    /\bwrite\b.*\b(artifact|document|essay)\b/,
    /\bbuild\b.*\b(html|page|document)\b/,
    /\bturn\b.*\binto\b.*\b(document|essay|html|markdown)\b/,
    /\b30\s*for\s*30\b/,
    /\bdownloadable\b.*\b(document|file)\b/,
  ];

  return artifactPatterns.some((pattern) => pattern.test(normalized));
}
