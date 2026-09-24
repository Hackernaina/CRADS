const test = require('node:test');
const assert = require('node:assert/strict');
const { parseSpec, SpecError } = require('../src');

test('normalizes an OpenAPI 3 JSON document into an endpoint inventory', () => {
  const inventory = parseSpec({
    openapi: '3.0.3',
    info: { title: 'Pet API', version: '1.0.0' },
    servers: [{ url: 'https://api.example.test' }],
    components: { securitySchemes: { bearer: { type: 'http', scheme: 'bearer' } } },
    paths: {
      '/pets/': {
        parameters: [{ name: 'tenant', in: 'header', required: true, schema: { type: 'string' } }],
        get: {
          operationId: 'listPets',
          tags: ['pets'],
          parameters: [{ name: 'limit', in: 'query', schema: { type: 'integer' } }],
          responses: { '200': { description: 'OK', content: { 'application/json': { schema: { type: 'array' } } } } }
        }
      }
    }
  });
  assert.equal(inventory.format, 'openapi');
  assert.deepEqual(inventory.securitySchemes.bearer, {
    name: 'bearer', type: 'http', scheme: 'bearer', bearerFormat: undefined,
    in: undefined, parameterName: undefined, flows: undefined, scopes: {}
  });
  assert.equal(inventory.endpoints[0].path, '/pets');
  assert.equal(inventory.endpoints[0].id, 'listPets');
  assert.equal(inventory.endpoints[0].parameters.length, 2);
  assert.equal(inventory.endpoints[0].responses[0].content['application/json'].mediaType, 'application/json');
});

test('supports Swagger 2 body and form parameters and response produces', () => {
  const inventory = parseSpec(`
swagger: '2.0'
info:
  title: Legacy API
  version: '1'
host: api.example.test
basePath: /v1
schemes: [https]
consumes: [application/json]
produces: [application/json]
securityDefinitions:
  apiKey:
    type: apiKey
    name: X-API-Key
    in: header
paths:
  /pets:
    post:
      operationId: createPet
      parameters:
        - name: body
          in: body
          required: true
          schema:
            $ref: '#/definitions/Pet'
      responses:
        '201':
          description: Created
          schema:
            $ref: '#/definitions/Pet'
`);
  assert.equal(inventory.format, 'swagger');
  assert.equal(inventory.servers[0].url, 'https://api.example.test/v1');
  assert.equal(inventory.securitySchemes.apiKey.parameterName, 'X-API-Key');
  assert.equal(inventory.endpoints[0].requestBody.content['application/json'].schema.$ref, '#/definitions/Pet');
  assert.equal(inventory.endpoints[0].responses[0].content['application/json'].schema.$ref, '#/definitions/Pet');
});

test('rejects unsupported versions and missing responses explicitly', () => {
  assert.throws(() => parseSpec({ openapi: '1.0', info: {}, paths: {} }), (error) => {
    assert.ok(error instanceof SpecError);
    assert.equal(error.code, 'UNSUPPORTED_VERSION');
    return true;
  });
  assert.throws(() => parseSpec({
    openapi: '3.0.0', info: { title: 'x' }, paths: { '/x': { get: {} } }
  }), (error) => error.code === 'MISSING_RESPONSES');
});
