import { describe, it, expect } from 'vitest';
import {
  BuildOptimizerError,
  ConfigError,
  BuildError,
  AgentError,
  OptimizationFailedError,
  ValidationError,
} from './errors.js';

describe('errors', () => {
  describe('BuildOptimizerError', () => {
    it('should create base error with code', () => {
      const error = new BuildOptimizerError('message', 'CODE', { foo: 'bar' });
      
      expect(error.message).toBe('message');
      expect(error.code).toBe('CODE');
      expect(error.context).toEqual({ foo: 'bar' });
      expect(error.name).toBe('BuildOptimizerError');
    });
  });
  
  describe('ConfigError', () => {
    it('should create config error', () => {
      const error = new ConfigError('invalid config', { path: '/config' });
      
      expect(error.message).toBe('invalid config');
      expect(error.code).toBe('CONFIG_ERROR');
      expect(error.name).toBe('ConfigError');
    });
  });
  
  describe('BuildError', () => {
    it('should create build error', () => {
      const error = new BuildError('build failed', { exitCode: 1 });
      
      expect(error.message).toBe('build failed');
      expect(error.code).toBe('BUILD_ERROR');
      expect(error.name).toBe('BuildError');
    });
  });
  
  describe('AgentError', () => {
    it('should create agent error with agent name', () => {
      const error = new AgentError('agent failed', 'monitor', { reason: 'timeout' });
      
      expect(error.message).toBe('agent failed');
      expect(error.code).toBe('AGENT_ERROR');
      expect(error.agentName).toBe('monitor');
      expect(error.name).toBe('AgentError');
    });
  });
  
  describe('OptimizationFailedError', () => {
    it('should create optimization error', () => {
      const error = new OptimizationFailedError('optimization failed');
      
      expect(error.message).toBe('optimization failed');
      expect(error.code).toBe('OPTIMIZATION_FAILED');
      expect(error.name).toBe('OptimizationFailedError');
    });
  });
  
  describe('ValidationError', () => {
    it('should create validation error', () => {
      const error = new ValidationError('validation failed', { field: 'name' });
      
      expect(error.message).toBe('validation failed');
      expect(error.code).toBe('VALIDATION_ERROR');
      expect(error.name).toBe('ValidationError');
    });
  });
});
