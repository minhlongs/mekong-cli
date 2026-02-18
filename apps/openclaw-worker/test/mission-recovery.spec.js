const { diagnoseFailure, truncatePrompt, TRUNCATED_PROMPT_LENGTH, getFallbackModel } = require('../lib/mission-recovery');
const config = require('../config');

describe('Mission Recovery Logic', () => {

  describe('diagnoseFailure', () => {
    it('should detect HTTP 400 as model error', () => {
      const output = 'Error: Request failed with status code 400';
      const result = diagnoseFailure(output);
      expect(result.action).toBe('model_failover');
      expect(result.model).toBeTruthy();
    });

    it('should detect "model_not_found" as model error', () => {
      const output = 'Exception: model_not_found: The model `claude-3-opus` does not exist';
      const result = diagnoseFailure(output);
      expect(result.action).toBe('model_failover');
    });

    it('should detect "overloaded" as model error', () => {
      const output = 'The model is currently overloaded. Please try again later.';
      const result = diagnoseFailure(output);
      expect(result.action).toBe('model_failover');
    });

    it('should detect context overflow', () => {
      const output = 'Error: prompt is too long. context overflow.';
      const result = diagnoseFailure(output);
      expect(result.action).toBe('context_truncate');
    });

    it('should detect "token limit" as context overflow', () => {
      const output = 'Exceeded token limit of 128000';
      const result = diagnoseFailure(output);
      expect(result.action).toBe('context_truncate');
    });

    it('should return null action for unrelated errors', () => {
      const output = 'ReferenceError: x is not defined';
      const result = diagnoseFailure(output);
      expect(result.action).toBe(null);
    });
  });

  describe('getFallbackModel', () => {
    it('should return a valid fallback string', () => {
      const model = getFallbackModel();
      expect(typeof model).toBe('string');
      expect(model.length).toBeGreaterThan(0);
      console.log(`Current fallback model: ${model}`);
    });
  });

  describe('truncatePrompt', () => {
    it('should not truncate short prompts', () => {
      const shortPrompt = 'Short prompt';
      expect(truncatePrompt(shortPrompt)).toBe(shortPrompt);
    });

    it('should truncate long prompts', () => {
      // Create a string longer than TRUNCATED_PROMPT_LENGTH
      const longPrompt = 'a'.repeat(TRUNCATED_PROMPT_LENGTH + 100);
      const truncated = truncatePrompt(longPrompt);

      expect(truncated.length).toBeLessThan(longPrompt.length);
      expect(truncated).toContain('[TRUNCATED');
      // Should preserve the start
      expect(truncated.startsWith('aaaa')).toBe(true);
    });
  });
});
