import { describe, it, expect } from 'vitest';

// Simple email validation regex
function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// Password validation: min 8 chars
function isValidPassword(password: string): boolean {
  return password.length >= 8;
}

describe('Auth Validators', () => {
  describe('isValidEmail', () => {
    it('accepts valid email', () => {
      expect(isValidEmail('test@example.com')).toBe(true);
      expect(isValidEmail('user.name+tag@domain.co.uk')).toBe(true);
    });

    it('rejects invalid email', () => {
      expect(isValidEmail('invalid')).toBe(false);
      expect(isValidEmail('missing@domain')).toBe(false);
      expect(isValidEmail('@nodomain.com')).toBe(false);
      expect(isValidEmail('spaces in@email.com')).toBe(false);
    });
  });

  describe('isValidPassword', () => {
    it('accepts password with 8+ chars', () => {
      expect(isValidPassword('12345678')).toBe(true);
      expect(isValidPassword('longerpassword')).toBe(true);
    });

    it('rejects password with < 8 chars', () => {
      expect(isValidPassword('short')).toBe(false);
      expect(isValidPassword('1234567')).toBe(false);
    });
  });
});
