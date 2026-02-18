const cp = require('child_process');

console.log('DEBUG: Helper loaded child_process');
console.log('DEBUG: Helper cp keys:', Object.keys(cp));
console.log('DEBUG: Helper cp.spawn isMock:', cp.spawn && cp.spawn._isMockFunction);

module.exports = {
  runSpawn: () => {
    console.log('DEBUG: runSpawn calling cp.spawn');
    return cp.spawn('echo', ['hello']);
  }
};
