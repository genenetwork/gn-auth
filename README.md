# GeneNetwork Auth

This project is for the GeneNetwork Authentication/Authorisation server to be
used across the entire suite of the GeneNetwork services.



## Checks

### Linting

```bash
pylint *py tests gn_auth scripts
```

### Type-Checking

```bash
mypy --show-error-codes .
```

### Running Tests

```bash
export AUTHLIB_INSECURE_TRANSPORT=true
pytest -k unit_test
```
