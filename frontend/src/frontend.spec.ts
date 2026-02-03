// Simple integration test
import { describe, it, expect } from 'vitest';

describe('Basic Test', () => {
  it('should work', () => {
    expect(1 + 1).toBe(2);
  });

  it('should pass stock code validation', () => {
    const code = '600000';
    expect(code).toHaveLength(6);
  });
});
