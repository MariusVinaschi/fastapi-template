# Cross-cutting Code Constraints

- Follow the repository's formatter, linter, type checker, complexity gate and
  domain-specific rules instead of inventing additional numeric style limits.
- Prefer simple, cohesive code. Introduce an abstraction only when the current
  change demonstrates a real need for it.
- Validate untrusted data at system boundaries with the project's existing
  schemas and authorization mechanisms.
- Handle an error at the boundary that can recover from it or translate it.
  Never silently discard failures or log the same failure at every layer.
- Make side effects explicit. Choose mutation or immutability according to the
  data model and framework; SQLAlchemy-managed state may be mutated deliberately.
