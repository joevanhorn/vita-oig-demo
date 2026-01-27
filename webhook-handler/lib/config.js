/**
 * Configuration validation and management
 */

function validateConfig() {
  const required = [
    'GITHUB_TOKEN',
    'GITHUB_TEMPLATE_OWNER',
    'GITHUB_TEMPLATE_REPO',
    'COMPONENT_SECRET'
  ];

  const missing = required.filter(key => !process.env[key]);

  if (missing.length > 0) {
    throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
  }

  // Validate GitHub token format
  if (!process.env.GITHUB_TOKEN.startsWith('ghp_') &&
      !process.env.GITHUB_TOKEN.startsWith('github_pat_')) {
    console.warn('⚠️  Warning: GITHUB_TOKEN does not appear to be a valid GitHub Personal Access Token');
  }

  return true;
}

function getConfig() {
  return {
    port: process.env.PORT || 3000,
    nodeEnv: process.env.NODE_ENV || 'development',

    platform: {
      apiUrl: process.env.DEMO_PLATFORM_API_URL || 'https://api.demo.okta.com',
      apiToken: process.env.DEMO_PLATFORM_API_TOKEN,
      componentSecret: process.env.COMPONENT_SECRET
    },

    github: {
      token: process.env.GITHUB_TOKEN,
      templateOwner: process.env.GITHUB_TEMPLATE_OWNER || 'joevanhorn',
      templateRepo: process.env.GITHUB_TEMPLATE_REPO || 'okta-terraform-demo-template',
      botUsername: process.env.GITHUB_BOT_USERNAME || 'demo-engineering-bot'
    },

    features: {
      enableAutoImport: process.env.ENABLE_AUTO_IMPORT === 'true',
      enableCollaboratorInvite: process.env.ENABLE_COLLABORATOR_INVITE === 'true',
      defaultRepoVisibility: process.env.DEFAULT_REPO_VISIBILITY || 'private'
    }
  };
}

module.exports = {
  validateConfig,
  getConfig
};
