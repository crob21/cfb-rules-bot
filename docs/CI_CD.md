# CI/CD Setup

## GitHub Actions

This project uses GitHub Actions to automatically run tests on every push to `main` and on pull requests.

### Test Workflow

**File:** `.github/workflows/test.yml`

**What it does:**
1. ✅ Sets up Python 3.13
2. ✅ Installs all dependencies from `requirements.txt`
3. ✅ Installs Playwright browsers (for web scraping tests)
4. ✅ Runs unit tests with coverage reporting
5. ✅ Runs integration smoke tests

**When it runs:**
- Every push to `main` branch
- Every pull request targeting `main`

### Test Structure

**Smoke Tests** (`tests/unit/test_smoke.py`)
- Import tests - catch missing imports like `check_module_enabled`
- Syntax tests - catch basic Python errors
- **Runs first** - fail fast on obvious issues

**Unit Tests** (`tests/unit/`)
- Test individual components with mocks
- Fast execution
- No external dependencies

**Integration Tests** (`tests/integration/`)
- Test real interactions (bot startup, API calls)
- May require environment variables
- Allowed to fail in CI (continue-on-error)

## Viewing Test Results

1. Go to your GitHub repo
2. Click **Actions** tab
3. See all workflow runs
4. Click any run to see detailed logs

## Local Testing

Run tests locally before pushing:

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=src/cfb_bot --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_cfb_data_cog.py -v

# Run smoke tests only (fast!)
pytest tests/unit/test_smoke.py -v
```

## What Gets Caught

✅ **Import errors** - Missing imports like `check_module_enabled`  
✅ **Syntax errors** - Invalid Python code  
✅ **Type errors** - ONLY if we add integration tests with real data  
✅ **Logic errors** - Wrong behavior in functions  
❌ **Runtime errors with real data** - Tests use mocks, not real APIs

## Next Steps

To catch the string/int type errors, we'd need:
1. Integration tests that call real CFBD API
2. Test fixtures with actual API responses (captured and stored)
3. Run those tests in CI with rate limiting

For now, this catches **import and syntax errors** which is what bit us! 🎯

