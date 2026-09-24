# CRADS

CRADS Phase 1 ingests OpenAPI 3.x and Swagger 2.x documents and produces a stable,
JSON-serializable endpoint inventory. Both JSON and YAML input are supported.

## CLI

```sh
npm install
npx crads ./openapi.yaml > inventory.json
```

The CLI writes the inventory to stdout and reports parse, read, version, and
validation errors on stderr with a `CRADS <CODE>` prefix.

## JavaScript API

```js
const { parseSpec, loadSpec } = require('crads');

const inventory = parseSpec(openapiObjectOrJsonOrYamlString);
const fromFile = await loadSpec('./openapi.yaml');
```

An inventory contains normalized `info`, `servers`, `securitySchemes`, `tags`,
and `endpoints`. Each endpoint includes its `id`, normalized `path` and HTTP
`method`, operation metadata, merged parameters, request body content,
responses, and security requirements. Content is keyed by media type and
preserves schemas/examples for downstream tooling.

Run focused tests with `npm test`.