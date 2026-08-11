/**
 * Factory class to instantiate and fetch the configured AI provider.
 * Keeps the application decoupled from concrete model provider adapters.
 */
class ProviderFactory {
  /**
   * Reads environment variables to instantiate the appropriate provider class.
   * Supports returning a mock provider in development/test if X-Mock-AI header is set.
   * @param {object} [req] - Optional Express request object to check for mock headers
   * @returns {object|null} Instance of BaseProvider implementation or null
   */
  static getProvider(req = null) {
    if (req && req.headers && req.headers['x-no-ai'] === 'true') {
      return null;
    }

    const provider = process.env.AI_PROVIDER;

    if (!provider) {
      return null;
    }

    switch (provider.toLowerCase()) {
      case 'gemini': {
        let apiKey = process.env.AI_API_KEY;
        
        // If testing via header and not in production, use mock key
        if (req && req.headers && req.headers['x-mock-ai'] === 'true' && process.env.NODE_ENV !== 'production') {
          apiKey = 'mock-testing-key';
        }

        if (!apiKey || apiKey.trim() === '') {
          console.warn('[ProviderFactory] Warning: AI_API_KEY is not configured. AI Assistant is disabled.');
          return null;
        }
        
        const GeminiProvider = require('./providers/GeminiProvider');
        return new GeminiProvider(apiKey);
      }
      
      case 'openai':
        return null;

      default:
        console.warn(`[ProviderFactory]: Unknown or unconfigured AI provider option: "${provider}"`);
        return null;
    }
  }
}

module.exports = ProviderFactory;
