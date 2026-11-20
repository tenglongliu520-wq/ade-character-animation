const fs = require('node:fs');
const path = require('node:path');
const validator = require('gltf-validator');

validator.validateBytes(new Uint8Array(fs.readFileSync(path.join(__dirname,'ade.glb'))), {
  uri:'ade.glb', maxIssues:0
}).then(report => {
  fs.writeFileSync(path.join(__dirname,'gltf-validation.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report.issues,null,2));
  process.exitCode=report.issues.numErrors||report.issues.numWarnings?1:0;
}).catch(error => { console.error(error);process.exitCode=1; });
