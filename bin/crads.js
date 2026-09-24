#!/usr/bin/env node
const { loadSpec, SpecError } = require('../src');

async function main() {
  const file = process.argv[2];
  if (!file || process.argv.includes('--help')) {
    console.error('Usage: crads <openapi-or-swagger-file>');
    process.exitCode = file ? 0 : 2;
    return;
  }
  try {
    const result = await loadSpec(file);
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  } catch (error) {
    if (error instanceof SpecError) {
      console.error(`CRADS ${error.code}: ${error.message}`);
      process.exitCode = 1;
      return;
    }
    throw error;
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
