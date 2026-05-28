export default {
  test: {
    globals: true,
    environment: 'node',
    include: ['tests/**/*.test.ts', 'src/**/*.test.ts'],
    exclude: ['**/node_modules/**', 'dist']
  }
};
