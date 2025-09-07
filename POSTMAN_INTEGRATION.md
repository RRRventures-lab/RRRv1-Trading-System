# Postman GitHub Actions Integration Setup

This repository is configured with GitHub Actions to automatically run Postman API tests and sync collections.

## Prerequisites

1. **Postman Account**: You need a Postman account with API access
2. **Postman API Key**: Generate from Postman Dashboard → Settings → API Keys
3. **Collection/Environment IDs**: Get these from your Postman workspace

## Setup Instructions

### 1. Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and Variables → Actions

#### Required Secrets:
- `POSTMAN_API_KEY`: Your Postman API key

#### Required Variables:
- `POSTMAN_COLLECTION_ID`: ID of your Postman collection to test
- `POSTMAN_ENVIRONMENT_ID`: ID of your Postman environment (optional)
- `POSTMAN_API_ID`: ID of your API for governance checks (Enterprise only)
- `ENABLE_API_GOVERNANCE`: Set to 'true' to enable governance checks (Enterprise only)

### 2. Get Collection and Environment IDs

#### From Postman Web App:
1. Open your collection
2. Click the info icon (ⓘ) 
3. Copy the Collection ID from the URL or info panel

#### Using Postman CLI:
```bash
# List all collections
postman collection list

# List all environments  
postman environment list
```

### 3. Workflows Configured

#### `postman-tests.yml`
- **Triggers**: Push to main/develop, PRs, manual dispatch
- **Actions**: 
  - Runs API tests using Postman CLI
  - Uploads test results as artifacts
  - Runs API governance checks (Enterprise only)

#### `postman-collection-sync.yml`
- **Triggers**: Daily at 2 AM UTC, manual dispatch
- **Actions**:
  - Exports collections from Postman
  - Commits changes to repository
  - Keeps collections in sync with Postman workspace

### 4. Customization

#### Modify Test Workflow:
Edit `.github/workflows/postman-tests.yml` to:
- Add additional collections
- Change test environments
- Customize reporting
- Add notifications

#### Example Custom Commands:
```yaml
# Run specific collection with custom options
- name: Run Custom API Tests
  run: |
    postman collection run "${{ vars.POSTMAN_COLLECTION_ID }}" \
      --environment "${{ vars.POSTMAN_ENVIRONMENT_ID }}" \
      --timeout-request 30000 \
      --delay-request 100 \
      --bail \
      --reporters cli,htmlextra \
      --reporter-htmlextra-export test-report.html
```

### 5. Viewing Results

#### In GitHub:
- Go to Actions tab in your repository
- View workflow runs and results
- Download artifacts containing test results

#### In Postman:
- Open your API in Postman
- Navigate to Test and Automation
- View build status and collection run details

### 6. Best Practices

1. **Environment Management**: Use different environments for different branches
2. **Secret Security**: Store sensitive data in GitHub Secrets, not in code
3. **Test Organization**: Group related tests in collections
4. **Monitoring**: Set up notifications for test failures
5. **Documentation**: Keep API documentation updated with tests

### 7. Troubleshooting

#### Common Issues:
- **API Key Invalid**: Regenerate API key in Postman
- **Collection Not Found**: Verify collection ID is correct
- **Permission Denied**: Check Postman workspace permissions
- **CLI Installation Failed**: Use alternative installation method

#### Debug Commands:
```bash
# Verify CLI installation
postman --version

# Test API key
postman login --with-api-key YOUR_API_KEY

# List available collections
postman collection list
```

### 8. Advanced Features (Enterprise)

#### API Governance:
- Enforces API design standards
- Validates OpenAPI specifications
- Checks compliance rules

#### Security Scanning:
- Scans APIs for security vulnerabilities
- Validates authentication mechanisms
- Checks for sensitive data exposure

## Support

For issues with:
- **Postman CLI**: Check [Postman CLI documentation](https://learning.postman.com/docs/postman-cli/)
- **GitHub Actions**: Check [GitHub Actions documentation](https://docs.github.com/en/actions)
- **Integration**: Check [Postman GitHub integration docs](https://learning.postman.com/docs/integrations/available-integrations/github/)