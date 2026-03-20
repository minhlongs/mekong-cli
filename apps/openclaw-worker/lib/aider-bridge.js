// Stub aider-bridge for openclaw-worker
module.exports = {
  codeEdit: async (file, changes) => ({ success: true, diff: '' }),
  chat: async (prompt) => ({ response: 'noop' })
};
