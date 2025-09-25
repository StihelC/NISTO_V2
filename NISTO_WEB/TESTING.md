# NISTO Web Application - Testing Guide

This document describes how to run tests for the NISTO web application, which includes both React frontend and FastAPI backend components.

## 🚀 Quick Start

### Windows (PowerShell - Recommended)
```powershell
# Run all tests
.\run-tests.ps1

# Run specific component tests
.\run-tests.ps1 -Target frontend
.\run-tests.ps1 -Target backend

# Run with coverage
.\run-tests.ps1 -Coverage

# Run frontend in watch mode
.\run-tests.ps1 -Target frontend -Watch
```

### Windows (Batch - Simple)
```cmd
# Run all tests
run-tests.bat

# Run specific component tests
run-tests.bat frontend
run-tests.bat backend
```

### Cross-Platform (Bash)
```bash
# Make executable (Linux/Mac)
chmod +x run-tests.sh

# Run all tests
./run-tests.sh

# Run specific component tests
./run-tests.sh -t frontend
./run-tests.sh -t backend

# Run with coverage
./run-tests.sh -c

# Run frontend in watch mode
./run-tests.sh -t frontend -w
```

### Using NPM Scripts (Workspace)
```bash
# Run all tests
npm test

# Run specific component tests  
npm run test:frontend
npm run test:backend

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

## 📋 Test Coverage

### Frontend Tests (React + TypeScript)
The frontend test suite includes comprehensive regression tests for:

- **Component Tests**:
  - `DeviceList.test.tsx` - Device CRUD operations, selection, validation
  - `TopologyCanvas.test.tsx` - Device selection, drag/drop, click handling  
  - `PropertyEditor.test.tsx` - Property editing, tab switching, form validation

- **Redux State Tests**:
  - `devicesSlice.test.ts` - Device state management, async operations
  - `uiSlice.test.ts` - UI state, selection persistence
  - `connectionsSlice.test.ts` - Connection management, device relationships

- **Key Regression Coverage**:
  - ✅ **Duplicate device creation prevention**
  - ✅ **Device selection persistence after click**
  - ✅ **Single dispatch for async operations**
  - ✅ **Drag vs click differentiation**
  - ✅ **Property updates without duplication**

### Backend Tests (FastAPI + Python)
The backend test suite covers:

- **API Endpoint Tests**:
  - Device CRUD operations (`/api/devices/`)
  - Connection CRUD operations (`/api/connections/`)
  - Health check endpoint (`/healthz`)

- **Database Tests**:
  - SQLAlchemy model validation
  - Relationship integrity
  - Transaction handling

- **Authentication & Security**:
  - CORS configuration
  - Content Security Policy headers
  - Input validation

## 🔧 Test Configuration

### Frontend Test Setup
- **Framework**: Vitest + React Testing Library
- **Configuration**: `frontend/vite.config.ts`
- **Test Utils**: `frontend/src/test/test-utils.tsx`
- **Setup File**: `frontend/src/test/setup.ts`

### Backend Test Setup  
- **Framework**: pytest + FastAPI TestClient
- **Configuration**: `backend/pytest.ini` (auto-generated)
- **Test Files**: `backend/tests/`

## 📊 Test Reports

### Coverage Reports
When running with coverage (`-Coverage` flag), you'll get:

- **Frontend**: HTML coverage report in `frontend/coverage/`
- **Backend**: Terminal coverage report with missing lines

### Test Output
- **Success**: Green checkmarks ✅
- **Failure**: Red X marks ❌  
- **Warnings**: Yellow warning symbols ⚠️
- **Info**: Blue info symbols ℹ️

## 🐛 Troubleshooting

### Common Issues

1. **"npm test" not found**
   ```bash
   cd frontend
   npm install
   ```

2. **Python module not found**
   ```bash
   cd backend
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **PowerShell execution policy error**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

4. **Port conflicts during testing**
   - Frontend tests use mock APIs (no real server needed)
   - Backend tests use test database (isolated from dev data)

### Test Dependencies

**Frontend:**
- Node.js 18+
- npm/yarn
- React Testing Library
- Vitest

**Backend:**
- Python 3.11+
- pytest
- FastAPI TestClient
- SQLAlchemy with SQLite

## 📈 Adding New Tests

### Frontend Component Tests
1. Create test file: `src/components/__tests__/YourComponent.test.tsx`
2. Use test utilities: `import { render } from '../../test/test-utils'`
3. Include regression tests for known issues
4. Test user interactions with `userEvent`

### Backend API Tests
1. Create test file: `tests/test_your_feature.py`
2. Use test client: `from tests.conftest import client`
3. Test all HTTP methods and status codes
4. Validate response schemas

### Redux State Tests
1. Create test file: `src/store/__tests__/yourSlice.test.ts`
2. Test all actions and reducers
3. Include edge cases and error scenarios
4. Verify state immutability

## 🎯 Best Practices

### Test Organization
- **Unit Tests**: Test individual functions/components
- **Integration Tests**: Test component interactions
- **Regression Tests**: Prevent known bugs from reoccurring
- **E2E Tests**: Test complete user workflows (future addition)

### Test Naming
- Use descriptive test names: `"REGRESSION: only dispatches createDeviceAsync once when creating device"`
- Group related tests with `describe` blocks
- Use `it.skip()` for temporarily disabled tests

### Mocking Strategy
- Mock external dependencies (APIs, timers)
- Use real Redux store for integration tests
- Mock browser APIs not available in test environment

## 🚀 Continuous Integration

The test scripts are designed to work in CI environments:

- Exit codes: 0 (success), non-zero (failure)
- Machine-readable output available
- Coverage reports can be uploaded to services
- Parallel execution supported

### Example CI Configuration
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Run Tests
        run: ./run-tests.sh -c
```

## 📝 Contributing

When adding new features:

1. **Write tests first** (TDD approach recommended)
2. **Include regression tests** for bug fixes
3. **Maintain test coverage** above 80%
4. **Update this documentation** for new test patterns

---

## 📞 Support

If you encounter issues with the test suite:

1. Check this documentation first
2. Review error messages carefully  
3. Ensure all dependencies are installed
4. Try running tests individually to isolate issues
5. Check the issue tracker for known problems

Happy testing! 🧪✨

