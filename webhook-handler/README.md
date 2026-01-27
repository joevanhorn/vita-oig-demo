# Okta Terraform GitOps - Webhook Handler POC

Proof of Concept webhook handler for integrating Okta Terraform GitOps component with the Demo Platform.

## 🎯 Purpose

This webhook handler:
1. Receives component lifecycle events from Demo Platform
2. Provisions GitHub repositories from template
3. Configures secrets and environments automatically
4. Updates platform with provisioning status

## 📋 Prerequisites

- Node.js 18+ installed
- GitHub Personal Access Token with `repo` and `workflow` scopes
- Demo Platform API credentials (optional for testing)
- Access to `joevanhorn/okta-terraform-demo-template` template

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd webhook-handler
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Required
GITHUB_TOKEN=ghp_YOUR_GITHUB_PAT_HERE
COMPONENT_SECRET=your-webhook-secret

# Optional for testing
DEMO_PLATFORM_API_URL=https://api.demo.okta.com
DEMO_PLATFORM_API_TOKEN=your-platform-token
```

### 3. Start Server

```bash
# Development mode (with auto-reload)
npm run dev

# Production mode
npm start
```

Server will start on `http://localhost:3000`

### 4. Test Locally

In another terminal:

```bash
npm test
```

This sends a mock webhook payload to the handler.

## 📡 Webhook Endpoints

### `POST /webhooks/component-requested`

Fired when user adds component to demo.

**Payload:**
```json
{
  "demo_id": "demo-123",
  "user_id": "user-456",
  "user_email": "user@example.com",
  "component_instance_id": "instance-789",
  "configuration": {
    "repo_visibility": "private",
    "auto_import": true
  },
  "okta_org": {
    "name": "acme-demo",
    "base_url": "oktapreview.com",
    "api_token": "00abc..."
  }
}
```

**Response:**
```json
{
  "status": "accepted",
  "message": "Provisioning started",
  "component_instance_id": "instance-789"
}
```

### `POST /webhooks/component-updated`

Fired when component configuration changes.

### `POST /webhooks/component-deleted`

Fired when component removed from demo. Archives the GitHub repository.

### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "okta-terraform-webhook-handler",
  "version": "1.0.0"
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `PORT` | No | Server port | `3000` |
| `NODE_ENV` | No | Environment | `development` |
| `GITHUB_TOKEN` | Yes | GitHub PAT | - |
| `GITHUB_TEMPLATE_OWNER` | No | Template owner | `joevanhorn` |
| `GITHUB_TEMPLATE_REPO` | No | Template repo | `okta-terraform-demo-template` |
| `GITHUB_BOT_USERNAME` | No | Bot account username | `demo-engineering-bot` |
| `COMPONENT_SECRET` | Yes | Webhook secret | - |
| `DEMO_PLATFORM_API_URL` | No | Platform API URL | `https://api.demo.okta.com` |
| `DEMO_PLATFORM_API_TOKEN` | No | Platform API token | - |
| `ENABLE_AUTO_IMPORT` | No | Auto-trigger import | `true` |
| `DEFAULT_REPO_VISIBILITY` | No | Repo visibility | `private` |
| `LOG_LEVEL` | No | Log level | `info` |

### Creating GitHub PAT

1. Go to: https://github.com/settings/tokens/new
2. Select scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
3. Generate token
4. Copy to `.env` file

## 📊 What Gets Created

When webhook fires, the handler:

1. ✅ **Creates repository** from template
2. ✅ **Creates 4 environments**: myorg, production, staging, development
3. ✅ **Adds repository secret**: `AWS_ROLE_ARN` (placeholder)
4. ✅ **Adds environment secrets** to myorg:
   - `OKTA_API_TOKEN`
   - `OKTA_ORG_NAME`
   - `OKTA_BASE_URL`
5. ✅ **Customizes README** with org name
6. ✅ **Creates setup issue** with instructions
7. ✅ **(Optional) Triggers import workflow**
8. ✅ **(Optional) Adds user as collaborator**

## 🧪 Testing

### Local Testing

```bash
# Start server
npm run dev

# In another terminal, send test webhook
npm test
```

### Test with curl

```bash
curl -X POST http://localhost:3000/webhooks/component-requested \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: test" \
  -d @test/mock-webhook-payload.json
```

### Modify Test Payload

Edit `test/mock-webhook-payload.json`:

```json
{
  "okta_org": {
    "name": "your-test-org",
    "api_token": "your-test-token"
  }
}
```

## 🚢 Deployment

### Option 1: Deploy to AWS Lambda

```bash
# Install serverless
npm install -g serverless

# Deploy
serverless deploy
```

### Option 2: Deploy to Heroku

```bash
# Create app
heroku create okta-terraform-webhook

# Set env vars
heroku config:set GITHUB_TOKEN=ghp_...
heroku config:set COMPONENT_SECRET=...

# Deploy
git push heroku main
```

### Option 3: Deploy to Docker

```bash
# Build image
docker build -t okta-terraform-webhook .

# Run container
docker run -p 3000:3000 --env-file .env okta-terraform-webhook
```

## 📁 Project Structure

```
webhook-handler/
├── server.js              # Express server
├── routes/
│   └── webhooks.js        # Webhook endpoints
├── lib/
│   ├── github.js          # GitHub API operations
│   ├── platform.js        # Platform API client
│   ├── crypto.js          # Signature verification
│   ├── logger.js          # Logging utility
│   └── config.js          # Configuration management
├── test/
│   ├── test-webhook.js    # Test script
│   └── mock-webhook-payload.json
├── config/                # Optional GitHub App config
├── package.json
├── .env.example
└── README.md
```

## 🔍 Troubleshooting

### Server won't start

**Check:**
- Node.js version: `node --version` (need 18+)
- Dependencies installed: `npm install`
- `.env` file exists and has required vars

### Webhook test fails

**Check:**
- Server is running: `curl http://localhost:3000/health`
- GitHub token is valid: `curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user`
- Mock payload has valid structure

### Repository creation fails

**Check:**
- GitHub token has `repo` scope
- Bot user has access to template repo
- Template repo name is correct in `.env`
- GitHub API rate limits: https://api.github.com/rate_limit

### Secrets can't be added

**Check:**
- libsodium installed: `npm list libsodium-wrappers`
- Repository exists and is accessible
- GitHub token has necessary permissions

### Platform state updates fail

**Check:**
- Platform API URL is correct
- Platform API token is valid
- Network connectivity to platform

## 📝 Logs

Logs show each step:

```
ℹ️  [2025-11-19T14:30:00.000Z] INFO: 📥 Received component-requested webhook
ℹ️  [2025-11-19T14:30:01.000Z] INFO: 🚀 Starting provisioning for acme-demo
ℹ️  [2025-11-19T14:30:05.000Z] INFO: Creating repo from template: okta-terraform-acme-demo
ℹ️  [2025-11-19T14:30:08.000Z] INFO: ✅ Repository created: https://github.com/...
ℹ️  [2025-11-19T14:30:12.000Z] INFO: ✅ Provisioning completed in 11.23s
```

Set `LOG_LEVEL=debug` for more verbose output.

## 🔒 Security

- Webhook signatures verified (disabled in dev mode)
- Secrets encrypted before sending to GitHub
- No secrets logged
- Rate limiting recommended for production
- HTTPS required for production webhooks

## 📖 Next Steps

1. ✅ **Test locally** with mock payloads
2. **Deploy to staging** environment
3. **Register component** with Demo Platform
4. **Test end-to-end** with real demo
5. **Monitor and iterate** based on results

## 🆘 Support

- **Issues:** Create GitHub issue in this repo
- **Documentation:** See `/docs/DEMO_PLATFORM_INTEGRATION_ADDENDUM.md`
- **Questions:** Contact Demo Engineering team

## 📄 License

MIT
