/**
 * Webhook routes for Demo Platform component integration
 */

const express = require('express');
const router = express.Router();

const GitHubService = require('../lib/github');
const PlatformService = require('../lib/platform');
const { verifyWebhookSignature } = require('../lib/crypto');
const { logger } = require('../lib/logger');
const { getConfig } = require('../lib/config');

/**
 * Webhook: Component Instance Requested
 *
 * Fired when user adds "Okta Terraform GitOps" component to their demo
 */
router.post('/component-requested', async (req, res) => {
  const startTime = Date.now();
  logger.info('📥 Received component-requested webhook');

  // Verify signature
  const signature = req.headers['x-webhook-signature'];
  const config = getConfig();

  if (config.nodeEnv !== 'development') {
    if (!verifyWebhookSignature(req.body, signature, config.platform.componentSecret)) {
      logger.error('❌ Invalid webhook signature');
      return res.status(401).json({ error: 'Invalid signature' });
    }
  } else {
    logger.warn('⚠️  Development mode: Skipping signature verification');
  }

  // Extract payload
  const {
    demo_id,
    user_id,
    user_email,
    component_id,
    component_instance_id,
    configuration = {},
    okta_org
  } = req.body;

  // Validate required fields
  if (!component_instance_id || !okta_org) {
    logger.error('❌ Missing required fields in webhook payload');
    return res.status(400).json({
      error: 'Missing required fields',
      required: ['component_instance_id', 'okta_org']
    });
  }

  logger.info('Component instance requested:', {
    demo_id,
    component_instance_id,
    okta_org: okta_org.name
  });

  // Respond immediately (don't make platform wait)
  res.status(202).json({
    status: 'accepted',
    message: 'Provisioning started',
    component_instance_id,
    estimated_time: '60 seconds'
  });

  // Provision asynchronously
  provisionRepository({
    demo_id,
    user_id,
    user_email,
    component_instance_id,
    okta_org,
    configuration
  }).then(() => {
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    logger.info(`✅ Provisioning completed in ${duration}s`);
  }).catch(error => {
    logger.error('❌ Provisioning failed:', error);
  });
});

/**
 * Webhook: Component Instance Updated
 */
router.post('/component-updated', async (req, res) => {
  logger.info('📥 Received component-updated webhook');

  const { component_instance_id, configuration, metadata } = req.body;

  res.status(202).json({ status: 'accepted' });

  // Handle configuration updates
  // e.g., change repo visibility, enable/disable features
  logger.info('Component configuration updated:', {
    component_instance_id,
    configuration
  });

  // TODO: Implement update logic based on your requirements
});

/**
 * Webhook: Component Instance Deleted
 */
router.post('/component-deleted', async (req, res) => {
  logger.info('📥 Received component-deleted webhook');

  const { component_instance_id, metadata } = req.body;

  res.status(202).json({ status: 'accepted' });

  if (!metadata || !metadata.repo_name || !metadata.owner) {
    logger.warn('No repo metadata found, skipping cleanup');
    return;
  }

  // Archive the repository
  try {
    const github = new GitHubService();
    await github.archiveRepo(metadata.owner, metadata.repo_name);

    const platform = new PlatformService();
    await platform.updateComponentState(component_instance_id, {
      state: 'deleted',
      message: 'Repository archived'
    });

    logger.info(`✅ Repository archived: ${metadata.owner}/${metadata.repo_name}`);
  } catch (error) {
    logger.error('Failed to archive repository:', error);
  }
});

/**
 * Main provisioning logic
 */
async function provisionRepository(params) {
  const {
    demo_id,
    user_email,
    component_instance_id,
    okta_org,
    configuration
  } = params;

  const github = new GitHubService();
  const platform = new PlatformService();
  const config = getConfig();

  try {
    // Initialize
    logger.info(`🚀 Starting provisioning for ${okta_org.name}`);
    await platform.updateProgress(component_instance_id, 0, 'Initializing...');

    // Generate repo name
    const repoName = `okta-terraform-${github.sanitizeRepoName(okta_org.name)}`;
    const isPrivate = configuration.repo_visibility !== 'public';

    // STEP 1: Create repository from template
    await platform.updateProgress(component_instance_id, 20, 'Creating repository from template...');

    const repo = await github.createRepoFromTemplate(
      repoName,
      `Okta Terraform GitOps for ${okta_org.name} (Demo ${demo_id})`,
      isPrivate
    );

    // Wait for GitHub to complete template creation
    logger.info('⏳ Waiting for template creation to complete...');
    await github.sleep(5000);

    // STEP 2: Create GitHub Environments
    await platform.updateProgress(component_instance_id, 40, 'Creating GitHub Environments...');

    const environments = ['myorg', 'production', 'staging', 'development'];
    for (const env of environments) {
      await github.createEnvironment(config.github.botUsername, repoName, env);
    }

    // STEP 3: Add repository secrets
    await platform.updateProgress(component_instance_id, 50, 'Adding repository secrets...');

    await github.addRepositorySecret(
      config.github.botUsername,
      repoName,
      'AWS_ROLE_ARN',
      'arn:aws:iam::ACCOUNT_ID:role/REPLACE_ME'
    );

    // STEP 4: Add environment secrets
    await platform.updateProgress(component_instance_id, 60, 'Configuring Okta secrets...');

    await github.addEnvironmentSecret(repo.id, 'myorg', 'OKTA_API_TOKEN', okta_org.api_token);
    await github.addEnvironmentSecret(repo.id, 'myorg', 'OKTA_ORG_NAME', okta_org.name);
    await github.addEnvironmentSecret(repo.id, 'myorg', 'OKTA_BASE_URL', okta_org.base_url || 'okta.com');

    // STEP 5: Customize repository
    await platform.updateProgress(component_instance_id, 75, 'Customizing repository...');

    await github.customizeReadme(
      config.github.botUsername,
      repoName,
      okta_org.name,
      user_email
    );

    // STEP 6: Create setup issue
    await platform.updateProgress(component_instance_id, 85, 'Creating setup instructions...');

    await github.createSetupIssue(
      config.github.botUsername,
      repoName,
      {
        okta_org_name: okta_org.name,
        demo_id,
        user_email,
        repo_url: repo.html_url
      }
    );

    // STEP 7: Trigger import workflow (if enabled)
    if (config.features.enableAutoImport && configuration.auto_import !== false) {
      await platform.updateProgress(component_instance_id, 90, 'Triggering initial import...');

      await github.triggerWorkflow(
        config.github.botUsername,
        repoName,
        'import-all-resources.yml',
        {
          tenant_environment: 'myorg',
          update_terraform: 'true',
          commit_changes: 'true'
        }
      );
    }

    // STEP 8: Add user as collaborator (if enabled and email provided)
    if (config.features.enableCollaboratorInvite && user_email) {
      await platform.updateProgress(component_instance_id, 95, 'Adding collaborator...');

      // Attempt to derive GitHub username from email
      const username = user_email.split('@')[0];
      await github.addCollaborator(config.github.botUsername, repoName, username);
    }

    // COMPLETE
    await platform.markReady(component_instance_id, {
      repo_url: repo.html_url,
      repo_name: repoName,
      repo_id: repo.id,
      owner: config.github.botUsername,
      created_at: new Date().toISOString()
    });

    logger.info(`✅ Provisioning complete: ${repo.html_url}`);

    return {
      success: true,
      repo_url: repo.html_url,
      repo_name: repoName
    };

  } catch (error) {
    logger.error('❌ Provisioning error:', error);

    await platform.markError(
      component_instance_id,
      error.message,
      error.stack
    );

    throw error;
  }
}

module.exports = router;
