import type { Command } from 'commander';
import type { MekongEngine } from '../../core/engine.js';
import { success, error as showError, info } from '../ui/output.js';
import { withSpinner } from '../ui/spinner.js';
import { AskDatabase, AskRetriever } from '@mekong/ask-core';
import { glob } from 'glob';
import * as fs from 'fs';
import * as path from 'path';

interface AskResult {
  answer: string;
  components_analyzed: string[];
  mermaid_diagram: string;
  recommendations: string[];
}

export function registerAskCommand(program: Command, engine: MekongEngine): void {
  program
    .command('ask <question...>')
    .description('Answer technical and architectural questions based on codebase rules and docs.')
    .action(async (questionParts: string[]) => {
      const question = questionParts.join(' ');
      try {
        const result = await withSpinner(`Answering: ${question}`, () => executeAsk(question, engine));
        
        success('\n── Answer Generated ──');
        console.log(result.answer);
        
        if (result.recommendations && result.recommendations.length > 0) {
          info('\n── Recommendations ──');
          result.recommendations.forEach(r => info(`  • ${r}`));
        }

        if (result.components_analyzed && result.components_analyzed.length > 0) {
          info('\n── Components & Files Analyzed ──');
          result.components_analyzed.forEach(c => info(`  • ${c}`));
        }

        if (result.mermaid_diagram && result.mermaid_diagram.trim().length > 0) {
          info('\n── Architecture Diagram (Mermaid) ──');
          console.log(result.mermaid_diagram);
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });
}

async function executeAsk(question: string, engine: MekongEngine): Promise<AskResult> {
  const db = new AskDatabase();
  const retriever = new AskRetriever(db);

  try {
    const workspaceRoot = process.cwd();
    
    // Auto-indexing check
    const totalVectors = db.getAllVectors().length;
    if (totalVectors === 0) {
      info('Database index empty. Triggering automated ingestion of codebase rules and docs...');
      const rulesFiles = await glob('.claude/rules/**/*.md', { cwd: workspaceRoot, absolute: true });
      const docsFiles = await glob('docs/**/*.md', { cwd: workspaceRoot, absolute: true });
      const files = [...rulesFiles, ...docsFiles];

      for (const file of files) {
        try {
          const relativePath = path.relative(workspaceRoot, file);
          const content = fs.readFileSync(file, 'utf-8');
          await retriever.indexFile(relativePath, content);
        } catch (fileErr) {
          // Skip unreadable files silently
        }
      }
    }

    // Retrieve context chunks
    const chunks = await retriever.retrieve(question, 5);

    const systemRules = chunks.filter(c => c.filePath.includes('.claude/rules/'));
    const documentationContext = chunks.filter(c => !c.filePath.includes('.claude/rules/'));

    let systemRulesXml = '';
    for (const c of systemRules) {
      systemRulesXml += `- Rule: ${c.title} (Source: ${c.filePath})\n${c.content}\n\n`;
    }

    let docsXml = '';
    for (const c of documentationContext) {
      docsXml += `- Document: ${c.title} (Source: ${c.filePath})\n${c.content}\n\n`;
    }

    const systemPrompt = `You are a powerful AI architectural and technical Q&A assistant for Mekong CLI.
You must respond ONLY with a valid JSON object matching the following structure:
{
  "answer": "A detailed explanation answering the question.",
  "components_analyzed": ["List of component names/files that were relevant"],
  "mermaid_diagram": "Mermaid syntax string for visual diagram, or empty string if not applicable",
  "recommendations": ["Key recommendation 1", "Key recommendation 2"]
}
Do NOT include markdown formatting like \`\`\`json or extra text outside the JSON object.

Context rules:
<system_rules>
${systemRulesXml || 'No matching system rules found.'}
</system_rules>

<documentation_context>
${docsXml || 'No matching documentation context found.'}
</documentation_context>
`;

    // Query LLM
    const response = await engine.llm.chat({
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: `Query: ${question}` }
      ],
      temperature: 0.2
    });

    let jsonText = response.content.trim();
    if (jsonText.startsWith('```')) {
      const match = jsonText.match(/^(?:```json\r?\n)?([\s\S]*?)(?:\r?\n```)?$/);
      if (match) {
        jsonText = match[1].trim();
      }
    }

    try {
      return JSON.parse(jsonText) as AskResult;
    } catch (e) {
      return {
        answer: response.content,
        components_analyzed: chunks.map(c => c.filePath),
        mermaid_diagram: '',
        recommendations: []
      };
    }
  } finally {
    db.close();
  }
}
