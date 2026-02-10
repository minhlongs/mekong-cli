import { Agent, AgentContext, AgentResult, Logger } from '../types/index.js';

export abstract class BaseAgent implements Agent {
  abstract readonly name: string;
  
  protected context!: AgentContext;
  protected logger!: Logger;
  
  async execute(context: AgentContext): Promise<AgentResult> {
    this.context = context;
    this.logger = context.logger;
    
    this.logger.debug(`Starting agent: ${this.name}`, { app: context.app.name });
    
    try {
      const result = await this.run();
      this.logger.debug(`Agent completed: ${this.name}`);
      return { success: true, ...result };
    } catch (error) {
      this.logger.error(`Agent failed: ${this.name}`, { error });
      return {
        success: false,
        error: error instanceof Error ? error : new Error(String(error)),
      };
    }
  }
  
  protected abstract run(): Promise<Partial<AgentResult>>;
  
  protected isDryRun(): boolean {
    return process.env.DRY_RUN === 'true';
  }
}
