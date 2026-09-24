class SpecError extends Error {
  constructor(message, code = 'INVALID_SPEC', details = {}) {
    super(message);
    this.name = 'SpecError';
    this.code = code;
    this.details = details;
  }
}

module.exports = { SpecError };
