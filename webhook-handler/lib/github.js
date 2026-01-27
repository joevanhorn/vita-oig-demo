/**
 * GitHub API operations for repository provisioning
 */

const { Octokit } = require('@octokit/rest');
const { encryptSecret } = require('./crypto');
const { logger } = require('./logger');
const { getConfig } = require('./config');

class GitHubService {
  constructor() {
    const config = getConfig();
    this.octokit = new Octokit({ auth: config.github.token });
    this.config = config.github;
  }

  /**
   * Create repository from template
   */
  async createRepoFromTemplate(repoName, description, isPrivate = true) {
    logger.info(`Creating repo from template: ${repoName}`);

    const { data: repo } = await this.octokit.repos.createUsingTemplate({
      template_owner: this.config.templateOwner,
      template_repo: this.config.templateRepo,
      owner: this.config.botUsername,
      name: repoName,
      description,
      private: isPrivate,
      include_all_branches: false
    });

    logger.info(`✅ Repository created: ${repo.html_url}`);
    return repo;
  }

  /**
   * Create GitHub Environment
   */
  async createEnvironment(owner, repo, environmentName) {
    logger.debug(`Creating environment: ${environmentName}`);

    await this.octokit.repos.createOrUpdateEnvironment({
      owner,
      repo,
      environment_name: environmentName,
      wait_timer: 0,
      reviewers: []
    });

    logger.debug(`✅ Environment created: ${environmentName}`);
  }

  /**
   * Add repository secret
   */
  async addRepositorySecret(owner, repo, secretName, secretValue) {
    logger.debug(`Adding repository secret: ${secretName}`);

    // Get public key
    const { data: publicKeyData } = await this.octokit.actions.getRepoPublicKey({
      owner,
      repo
    });

    // Encrypt secret
    const encryptedValue = await encryptSecret(secretValue, publicKeyData.key);

    // Create secret
    await this.octokit.actions.createOrUpdateRepoSecret({
      owner,
      repo,
      secret_name: secretName,
      encrypted_value: encryptedValue,
      key_id: publicKeyData.key_id
    });

    logger.debug(`✅ Repository secret added: ${secretName}`);
  }

  /**
   * Add environment secret
   */
  async addEnvironmentSecret(repositoryId, environmentName, secretName, secretValue) {
    logger.debug(`Adding environment secret: ${environmentName}/${secretName}`);

    // Get environment public key
    const { data: publicKeyData } = await this.octokit.request(
      'GET /repositories/{repository_id}/environments/{environment_name}/secrets/public-key',
      {
        repository_id: repositoryId,
        environment_name: environmentName
      }
    );

    // Encrypt secret
    const encryptedValue = await encryptSecret(secretValue, publicKeyData.key);

    // Create secret
    await this.octokit.request(
      'PUT /repositories/{repository_id}/environments/{environment_name}/secrets/{secret_name}',
      {
        repository_id: repositoryId,
        environment_name: environmentName,
        secret_name: secretName,
        encrypted_value: encryptedValue,
        key_id: publicKeyData.key_id
      }
    );

    logger.debug(`✅ Environment secret added: ${environmentName}/${secretName}`);
  }

  /**
   * Customize README file
   */
  async customizeReadme(owner, repo, orgName, userEmail) {
    logger.debug('Customizing README...');

    try {
      // Get current README
      const { data: readmeFile } = await this.octokit.repos.getContent({
        owner,
        repo,
        path: 'README.md'
      });

      // Decode content
      const content = Buffer.from(readmeFile.content, 'base64').toString('utf-8');

      // Customize
      const customized = content
        .replace(/demo-myorg/g, this.sanitizeRepoName(orgName))
        .replace(/MyOrg/g, orgName)
        .replace(/okta-terraform-demo-template/g, repo);

      // Update file
      await this.octokit.repos.createOrUpdateFileContents({
        owner,
        repo,
        path: 'README.md',
        message: `chore: Customize README for ${orgName}`,
        content: Buffer.from(customized).toString('base64'),
        sha: readmeFile.sha
      });

      logger.debug('✅ README customized');
    } catch (error) {
      logger.warn('Could not customize README:', error.message);
    }
  }

  /**
   * Create setup issue
   */
  async createSetupIssue(owner, repo, details) {
    logger.debug('Creating setup issue...');

    const { okta_org_name, demo_id, repo_url } = details;

    const issueBody = `
# 🎉 Your Okta Terraform Environment is Ready!

This repository has been automatically configured for **${okta_org_name}** (Demo: ${demo_id}).

## ✅ What's Already Configured

- [x] GitHub repository created from template
- [x] GitHub Environments set up (myorg, production, staging, development)
- [x] Okta secrets configured in **myorg** environment
- [x] Workflows enabled and ready to use

## 🚀 Next Steps

### 1. Import Your Okta Configuration

Your Okta org is already connected. Import existing resources:

\`\`\`bash
# Via GitHub CLI
gh workflow run import-all-resources.yml -f tenant_environment=myorg

# Or via GitHub UI
Actions → Import All Resources → Run workflow
\`\`\`

### 2. Make Changes via Pull Requests

\`\`\`bash
git checkout -b add-new-users
# Edit files in environments/myorg/terraform/
git commit -m "feat: Add marketing team"
git push
# Create PR → Terraform plan runs automatically
\`\`\`

## 📚 Documentation

- [CLAUDE.md](${repo_url}/blob/main/CLAUDE.md) - Complete repository guide
- [README.md](${repo_url}/blob/main/README.md) - Overview
- [docs/](${repo_url}/tree/main/docs) - Full documentation

## 🆘 Need Help?

- [Documentation Index](${repo_url}/blob/main/docs/00-INDEX.md)
- Create an issue in this repository

---

**Automatically configured by Demo Platform**
**Demo ID:** ${demo_id}
**Repository:** ${repo_url}
`;

    const { data: issue } = await this.octokit.issues.create({
      owner,
      repo,
      title: '🚀 Your Okta Terraform Environment is Ready!',
      body: issueBody,
      labels: ['setup', 'documentation', 'auto-configured']
    });

    logger.info(`✅ Setup issue created: ${issue.html_url}`);
    return issue;
  }

  /**
   * Trigger workflow
   */
  async triggerWorkflow(owner, repo, workflowId, inputs = {}) {
    logger.debug(`Triggering workflow: ${workflowId}`);

    try {
      await this.octokit.actions.createWorkflowDispatch({
        owner,
        repo,
        workflow_id: workflowId,
        ref: 'main',
        inputs
      });

      logger.info(`✅ Workflow triggered: ${workflowId}`);
      return true;
    } catch (error) {
      logger.warn(`Could not trigger workflow ${workflowId}:`, error.message);
      return false;
    }
  }

  /**
   * Add collaborator
   */
  async addCollaborator(owner, repo, username, permission = 'admin') {
    logger.debug(`Adding collaborator: ${username}`);

    try {
      await this.octokit.repos.addCollaborator({
        owner,
        repo,
        username,
        permission
      });

      logger.info(`✅ Collaborator added: ${username}`);
      return true;
    } catch (error) {
      logger.warn(`Could not add collaborator ${username}:`, error.message);
      return false;
    }
  }

  /**
   * Archive repository
   */
  async archiveRepo(owner, repo) {
    logger.info(`Archiving repository: ${owner}/${repo}`);

    await this.octokit.repos.update({
      owner,
      repo,
      archived: true
    });

    logger.info(`✅ Repository archived: ${owner}/${repo}`);
  }

  /**
   * Utility: Sanitize repo name
   */
  sanitizeRepoName(name) {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9-]/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');
  }

  /**
   * Utility: Wait
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

module.exports = GitHubService;
