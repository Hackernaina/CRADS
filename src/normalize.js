const { SpecError } = require('./errors');

const HTTP_METHODS = ['get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace'];
const STATUS_PATTERN = /^(default|[1-5]\d{2}|[1-5]XX)$/i;

function asArray(value) {
  if (value === undefined || value === null) return [];
  return Array.isArray(value) ? value : [value];
}

function contentMap(content = {}) {
  if (!content || typeof content !== 'object' || Array.isArray(content)) return {};
  return Object.fromEntries(Object.entries(content).map(([mediaType, value]) => [
    mediaType,
    {
      mediaType,
      schema: value && value.schema,
      example: value && value.example,
      examples: value && value.examples
    }
  ]));
}

function parameter(parameter) {
  if (!parameter || typeof parameter !== 'object') return null;
  return {
    name: parameter.name,
    in: parameter.in,
    required: Boolean(parameter.required),
    description: parameter.description,
    deprecated: Boolean(parameter.deprecated),
    style: parameter.style,
    explode: parameter.explode,
    schema: parameter.schema || (parameter.type ? {
      type: parameter.type,
      format: parameter.format,
      items: parameter.items,
      enum: parameter.enum,
      default: parameter.default
    } : undefined),
    example: parameter.example,
    examples: parameter.examples
  };
}

function normalizeParameters(pathParameters, operationParameters) {
  const merged = new Map();
  [...asArray(pathParameters), ...asArray(operationParameters)].forEach((value) => {
    const normalized = parameter(value);
    if (!normalized || !normalized.name || !normalized.in) return;
    merged.set(`${normalized.in}:${normalized.name}`, normalized);
  });
  return [...merged.values()];
}

function normalizeRequestBody(operation, root) {
  if (operation.requestBody && typeof operation.requestBody === 'object') {
    return {
      required: Boolean(operation.requestBody.required),
      description: operation.requestBody.description,
      content: contentMap(operation.requestBody.content)
    };
  }
  const bodyParameters = asArray(operation.parameters).filter((item) => item && item.in === 'body');
  const formParameters = asArray(operation.parameters).filter((item) => item && item.in === 'formData');
  if (!bodyParameters.length && !formParameters.length) return undefined;
  const consumes = asArray(operation.consumes || root.consumes || ['application/json']);
  const body = bodyParameters[0];
  const schema = body && body.schema;
  const properties = formParameters.reduce((result, item) => {
    result[item.name] = {
      type: item.type,
      format: item.format,
      items: item.items,
      description: item.description
    };
    return result;
  }, {});
  const required = formParameters.filter((item) => item.required).map((item) => item.name);
  return {
    required: Boolean((body && body.required) || required.length),
    description: body && body.description,
    content: Object.fromEntries(consumes.map((mediaType) => [mediaType, {
      mediaType,
      schema: schema || (formParameters.length ? { type: 'object', properties, required } : undefined)
    }]))
  };
}

function normalizeResponses(operation, root) {
  const responses = operation.responses;
  if (!responses || typeof responses !== 'object' || Array.isArray(responses)) {
    throw new SpecError('Each operation must define a responses object.', 'MISSING_RESPONSES');
  }
  const produces = asArray(operation.produces || root.produces);
  return Object.entries(responses).map(([statusCode, response]) => {
    if (!STATUS_PATTERN.test(statusCode)) {
      throw new SpecError(`Invalid response status "${statusCode}".`, 'INVALID_RESPONSE_STATUS');
    }
    const value = response && typeof response === 'object' ? response : {};
    let content = contentMap(value.content);
    if (!Object.keys(content).length && value.schema) {
      content = Object.fromEntries(produces.map((mediaType) => [mediaType, { mediaType, schema: value.schema }]));
    }
    return {
      statusCode,
      description: value.description || '',
      headers: value.headers || {},
      content
    };
  });
}

function normalizeSecurity(operation, root) {
  const security = operation.security !== undefined ? operation.security : root.security;
  return security === undefined ? [] : asArray(security);
}

function normalizeSecuritySchemes(root) {
  const schemes = root.components && root.components.securitySchemes
    ? root.components.securitySchemes
    : root.securityDefinitions || {};
  return Object.fromEntries(Object.entries(schemes).map(([name, scheme]) => [name, {
    name,
    type: scheme.type,
    scheme: scheme.scheme,
    bearerFormat: scheme.bearerFormat,
    in: scheme.in,
    parameterName: scheme.name,
    flows: scheme.flows,
    scopes: scheme.scopes || {}
  }]));
}

function normalizePath(path) {
  if (path === '/' || path === '') return '/';
  return `/${path.replace(/^\/+|\/+$/g, '')}`;
}

function inventory(spec) {
  if (!spec || typeof spec !== 'object' || Array.isArray(spec)) {
    throw new SpecError('The parsed specification must be an object.', 'INVALID_SPEC');
  }
  const version = spec.openapi || spec.swagger;
  if (typeof version !== 'string' || !(version.startsWith('3.') || version.startsWith('2.'))) {
    throw new SpecError('Only OpenAPI 3.x and Swagger 2.x specifications are supported.', 'UNSUPPORTED_VERSION');
  }
  if (!spec.info || typeof spec.info !== 'object') {
    throw new SpecError('Specification is missing required "info" metadata.', 'MISSING_INFO');
  }
  if (!spec.paths || typeof spec.paths !== 'object' || Array.isArray(spec.paths)) {
    throw new SpecError('Specification is missing a valid "paths" object.', 'MISSING_PATHS');
  }
  const endpoints = [];
  for (const [rawPath, pathItem] of Object.entries(spec.paths)) {
    if (!pathItem || typeof pathItem !== 'object') continue;
    for (const method of HTTP_METHODS) {
      const operation = pathItem[method];
      if (!operation) continue;
      if (typeof operation !== 'object' || Array.isArray(operation)) {
        throw new SpecError(`Operation ${method.toUpperCase()} ${rawPath} must be an object.`, 'INVALID_OPERATION');
      }
      const path = normalizePath(rawPath);
      const params = normalizeParameters(pathItem.parameters, operation.parameters);
      endpoints.push({
        id: operation.operationId || `${method}:${path}`,
        path,
        method: method.toUpperCase(),
        operationId: operation.operationId,
        summary: operation.summary,
        description: operation.description,
        deprecated: Boolean(operation.deprecated),
        tags: asArray(operation.tags),
        parameters: params,
        requestBody: normalizeRequestBody(operation, spec),
        responses: normalizeResponses(operation, spec),
        security: normalizeSecurity(operation, spec),
        servers: operation.servers || spec.servers
      });
    }
  }
  return {
    version,
    format: spec.openapi ? 'openapi' : 'swagger',
    info: { title: spec.info.title, version: spec.info.version, description: spec.info.description },
    servers: spec.servers || (spec.host ? [{ url: `${(spec.schemes || ['http'])[0]}://${spec.host}${spec.basePath || ''}` }] : []),
    securitySchemes: normalizeSecuritySchemes(spec),
    tags: asArray(spec.tags),
    endpoints
  };
}

module.exports = { inventory, normalizePath };
