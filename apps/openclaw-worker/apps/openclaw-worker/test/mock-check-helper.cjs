const { spawn } = require('child_process');

module.exports = {
  runSpawn: () => {
    return spawn('ls');
  }
};
