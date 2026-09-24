const fs = require('node:fs/promises');
const path = require('node:path');
const yaml = require('js-yaml');
const { inventory } = require('./normalize');
const { SpecError } = require('./errors');

function parseDocument(input, source = 'input') {
  if (input && typeof input === 'object' && !Buffer.isBuffer(input)) return input;
  if (typeof input !== 'string' && !Buffer.isBuffer(input)) {
    throw new SpecError('A specification must be an object, string, or file path.', 'INVALID_INPUT');
  }
  const text = Buffer.from(input).toString('utf8');
  try {
    return JSON.parse(text);
  } catch (jsonError) {
    try {
      return yaml.load(text);
    } catch (yamlError) {
      throw new SpecError(`Unable to parse ${source} as JSON or YAML: ${yamlError.message}`, 'PARSE_ERROR', {
        json: jsonError.message
      });
    }
  }
}

async function loadSpec(filePath) {
  if (typeof filePath !== 'string' || !filePath) {
    throw new SpecError('A specification file path is required.', 'INVALID_INPUT');
  }
  let text;
  try {
    text = await fs.readFile(path.resolve(filePath), 'utf8');
  } catch (error) {
    throw new SpecError(`Unable to read specification "${filePath}": ${error.message}`, 'READ_ERROR');
  }
  return inventory(parseDocument(text, filePath));
}

function parseSpec(input) {
  return inventory(parseDocument(input));
}

module.exports = { parseSpec, loadSpec, inventory, SpecError };
