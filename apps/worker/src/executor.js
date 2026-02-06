/**
 * Simulates task execution
 * In production, this would call Workers AI, OpenAI, or run local code
 */
export async function executeTask(jobData) {
  const { model, messages } = jobData;
  console.log(`🤖 Executing task with model: ${model}`);

  // Simulation delay
  await new Promise(resolve => setTimeout(resolve, 1000));

  const lastMessage = messages[messages.length - 1].content;

  return {
    role: 'assistant',
    content: `Processed by Worker: I received your message "${lastMessage.substring(0, 50)}..." and processed it using ${model}.`,
    usage: {
      prompt_tokens: lastMessage.length,
      completion_tokens: 20,
      total_tokens: lastMessage.length + 20
    }
  };
}
