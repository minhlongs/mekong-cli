export default {
  test: {
    globals: true,
    environment: 'node',
    include: ['packages/**/src/**/*.test.ts', 'src/**/*.test.ts'],
    exclude: ['**/node_modules/**', 'dist', '.next', 'apps/**/*', 'lib/**/*'],
  },
};
