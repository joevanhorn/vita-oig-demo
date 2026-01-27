/**
 * Demo Platform API client for updating component instance state
 */

const axios = require('axios');
const { logger } = require('./logger');
const { getConfig } = require('./config');

class PlatformService {
  constructor() {
    const config = getConfig();
    this.apiUrl = config.platform.apiUrl;
    this.apiToken = config.platform.apiToken;
  }

  /**
   * Update component instance state
   */
  async updateComponentState(instanceId, state) {
    if (!this.apiToken) {
      logger.warn('No platform API token configured, skipping state update');
      return;
    }

    logger.debug(`Updating component instance ${instanceId} state:`, state);

    try {
      const response = await axios.patch(
        `${this.apiUrl}/api/v1/component-instances/${instanceId}`,
        state,
        {
          headers: {
            'Authorization': `Bearer ${this.apiToken}`,
            'Content-Type': 'application/json'
          }
        }
      );

      logger.debug(`✅ Component state updated:`, response.data);
      return response.data;
    } catch (error) {
      logger.error('Failed to update component state:', {
        instanceId,
        error: error.message,
        response: error.response?.data
      });
      throw error;
    }
  }

  /**
   * Update provisioning progress
   */
  async updateProgress(instanceId, progress, message) {
    return this.updateComponentState(instanceId, {
      state: 'provisioning',
      progress,
      message
    });
  }

  /**
   * Mark as ready
   */
  async markReady(instanceId, metadata) {
    return this.updateComponentState(instanceId, {
      state: 'ready',
      progress: 100,
      message: 'Repository configured successfully',
      metadata
    });
  }

  /**
   * Mark as error
   */
  async markError(instanceId, errorMessage, errorDetails = null) {
    return this.updateComponentState(instanceId, {
      state: 'error',
      progress: 0,
      error_message: errorMessage,
      error_details: errorDetails
    });
  }
}

module.exports = PlatformService;
