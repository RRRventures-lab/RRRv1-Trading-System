# Postman Collections

This directory contains exported Postman collections that are synced with your Postman workspace.

## Structure

- `collections/` - Postman collection JSON files
- `environments/` - Postman environment JSON files

## Auto-Sync

Collections are automatically synced daily via GitHub Actions. Manual sync can be triggered from the Actions tab.

## Usage

Import these collections into Postman:
1. Open Postman
2. Click Import
3. Select the JSON file from this directory
4. Configure the appropriate environment

## Collection Guidelines

- Keep collections organized by API/service
- Include comprehensive test scripts
- Document request parameters and responses
- Use environment variables for dynamic values