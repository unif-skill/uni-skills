'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { inside, managedBlock, features, digest, projectFiles, requiredFiles } = require('../templates/scripts/check-delivery.cjs');
const [directory, list, repository] = process.argv.slice(2);
if (!directory || !list || !/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repository || ''))
  throw new Error('Usage: node write-delivery.cjs target-path managed-list owner/repo');
const root = fs.realpathSync(directory);
const target = inside(root, '.github/delivery.json');
const previous = fs.existsSync(target) ? JSON.parse(fs.readFileSync(target, 'utf8')) : {};
const adopted = { organization: fs.existsSync(inside(root, '.github/organization.json')),
  prAgent: fs.existsSync(inside(root, '.github/workflows/pr-agent.yml')) };
const files = Object.fromEntries([...new Set(fs.readFileSync(list, 'utf8').trim().split('\n').filter(Boolean))]
  .sort().map(relative => [relative, digest(fs.readFileSync(inside(root, relative)))]));
const sourceRoot = path.resolve(__dirname, '..');
const sources = ['scripts', 'templates'].flatMap(folder => fs.readdirSync(path.join(sourceRoot, folder), { recursive: true })
  .map(file => `${folder}/${file}`).filter(file => !file.includes('__pycache__') && !file.endsWith('.pyc') && fs.statSync(path.join(sourceRoot, file)).isFile())).sort();
const sourceDigest = digest(sources.map(file => `${file}\0${digest(fs.readFileSync(path.join(sourceRoot, file)))}`).join('\n'));
const checks = previous.requiredChecks || ['actionlint', 'lint', 'test', 'build-library', 'build-android', 'build-ios', 'verified',
  ...(features(root).native ? ['lint-cpp', 'lint-kotlin'] : [])];
adopted.requiredChecks = checks;
for (const relative of requiredFiles(root, adopted)) if (!files[relative]) throw new Error(`Missing managed source: ${relative}`);
const receipt = { schemaVersion: 1, standard: 'uni-github-delivery/rn', sourceDigest, repository, ...adopted,
  packageName: JSON.parse(fs.readFileSync(inside(root, 'package.json'), 'utf8')).name,
  features: features(root), projectFiles: projectFiles(previous.projectFiles), requiredChecks: checks, files,
  blocks: { 'AGENTS.md': digest(managedBlock(fs.readFileSync(inside(root, 'AGENTS.md'), 'utf8'))) } };
fs.writeFileSync(target, JSON.stringify(receipt, null, 2) + '\n');
