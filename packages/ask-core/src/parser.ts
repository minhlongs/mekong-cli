import * as crypto from 'crypto';
import { basename } from 'path';
import { Chunk } from './db';

/**
 * Generates a deterministic unique ID for a chunk.
 */
export function generateChunkId(
  filePath: string,
  title: string,
  content: string,
  parentHeaders: string[]
): string {
  const hashInput = `${filePath}:${parentHeaders.join('>')}:${title}:${content}`;
  return crypto.createHash('sha256').update(hashInput).digest('hex');
}

/**
 * Parses markdown file content and splits it into logical chunks grouped by headers.
 * 
 * Rules:
 * - Chunks are defined by header boundaries (#, ##, ###, ####).
 * - Code blocks are respected, and lines starting with '#' inside them are NOT treated as headers.
 * - Content at the top of the file before any headers is grouped into an "Overview" chunk.
 * - Parent headers are inherited and automatically passed down to child chunks.
 * 
 * @param filePath The path of the file being parsed (used for metadata).
 * @param markdownContent The raw string content of the markdown file.
 */
export function parseMarkdown(filePath: string, markdownContent: string): Chunk[] {
  const fileName = basename(filePath);
  
  // Strip YAML frontmatter if present
  let contentToParse = markdownContent;
  const linesRaw = markdownContent.split(/\r?\n/);
  let firstLineIdx = -1;
  for (let i = 0; i < linesRaw.length; i++) {
    const trimmedLine = linesRaw[i].trim();
    if (trimmedLine === '') continue;
    if (trimmedLine === '---') {
      firstLineIdx = i;
    }
    break;
  }
  if (firstLineIdx !== -1) {
    let secondLineIdx = -1;
    for (let i = firstLineIdx + 1; i < linesRaw.length; i++) {
      if (linesRaw[i].trim() === '---') {
        secondLineIdx = i;
        break;
      }
    }
    if (secondLineIdx !== -1) {
      contentToParse = linesRaw.slice(secondLineIdx + 1).join('\n');
    }
  }

  const lines = contentToParse.split(/\r?\n/);
  
  const chunks: Chunk[] = [];
  const headerStack: (string | null)[] = [null, null, null, null, null, null]; // H1 to H6
  
  let currentChunkLines: string[] = [];
  let currentTitle = fileName; // Default to filename for content before any headers
  let currentLevel = 0; // 0 represents overview/no header level
  let inCodeBlock = false;

  // Helper to save the current accumulated chunk
  const saveCurrentChunk = () => {
    const content = currentChunkLines.join('\n').trim();
    if (content.length === 0) {
      return; // Skip empty chunks
    }

    // Build the parent headers path (all non-null headers up to current level)
    const parentHeaders: string[] = [];
    if (currentLevel > 1) {
      for (let l = 0; l < currentLevel - 1; l++) {
        const h = headerStack[l];
        if (h) {
          parentHeaders.push(h);
        }
      }
    }

    const h1 = headerStack[0] || null;
    const h2 = headerStack[1] || null;
    const h3 = headerStack[2] || null;
    const h4 = headerStack[3] || null;

    const id = generateChunkId(filePath, currentTitle, content, parentHeaders);

    chunks.push({
      id,
      filePath,
      title: currentTitle,
      content,
      h1,
      h2,
      h3,
      h4,
      parentHeaders
    });
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Detect code blocks to avoid parsing comments/headers inside them
    if (line.trim().startsWith('```')) {
      inCodeBlock = !inCodeBlock;
      currentChunkLines.push(line);
      continue;
    }

    if (inCodeBlock) {
      currentChunkLines.push(line);
      continue;
    }

    // Detect markdown headers: starts with 1-6 '#' followed by a space
    const headerMatch = line.match(/^(#{1,6})\s+(.+)$/);
    if (headerMatch) {
      const level = headerMatch[1].length; // 1 to 6
      const titleText = headerMatch[2].trim().replace(/\s+#+$/, ''); // clean trailing '#' if present

      // Save the previous chunk before updating the header hierarchy
      saveCurrentChunk();

      // Reset nested header levels in the stack
      for (let l = level - 1; l < 6; l++) {
        headerStack[l] = null;
      }
      
      // Update the current level
      headerStack[level - 1] = titleText;
      
      // Set the title for the new chunk
      currentTitle = titleText;
      currentLevel = level;
      currentChunkLines = [line]; // Start new chunk content with the header line
    } else {
      // Normal content line
      currentChunkLines.push(line);
    }
  }

  // Save the final chunk
  saveCurrentChunk();

  return chunks;
}
