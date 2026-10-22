# /test-setup — Phase 4: Create CI/CD Workflow

> Part of `/test-setup`. `SKILL.md` names when to read this file; the settings it
> resolved and the rules under its later headings still apply here.

## Phase 4: Create CI/CD Workflow

**In this file:**

- Unity

### Unity

Create `.github/workflows/tests.yml`:

```yaml
name: Automated Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    name: Run Unity Tests
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v7
        with:
          lfs: true

      - name: Run Edit Mode Tests
        uses: game-ci/unity-test-runner@v4
        env:
          UNITY_LICENSE: ${{ secrets.UNITY_LICENSE }}
        with:
          testMode: editmode
          artifactsPath: test-results/editmode

      - name: Run Play Mode Tests
        uses: game-ci/unity-test-runner@v4
        env:
          UNITY_LICENSE: ${{ secrets.UNITY_LICENSE }}
        with:
          testMode: playmode
          artifactsPath: test-results/playmode

      - name: Upload Test Results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: test-results
          path: test-results/
```

Note: Unity CI requires a `UNITY_LICENSE` secret. Add to GitHub repository
secrets before the first CI run.

---
