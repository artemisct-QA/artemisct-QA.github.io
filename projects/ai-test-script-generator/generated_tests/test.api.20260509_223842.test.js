

```javascript
/**
 * Jest Test Suite: Charging Network Subscription API
 * Endpoint: GET /api/subscriptions/{subscriptionId}
 * 
 * Tests cover:
 * - 200: Successful retrieval (with and without details flag)
 * - 400: Bad/invalid subscription ID
 * - 401: Unauthorized access
 * - 404: Subscription not found
 * - Edge cases: missing params, special characters, empty responses
 */

const axios = require('axios');

// Mock axios to prevent real HTTP calls
jest.mock('axios');

// ============================================================
// Service Layer - Wraps the API call for testability
// ============================================================
const subscriptionService = {
  BASE_URL: 'https://api.chargingnetwork.com',

  /**
   * Fetch a subscription by ID with optional details flag
   * @param {string} subscriptionId - The subscription identifier
   * @param {boolean} details - Whether to include expanded details
   * @param {string} authToken - Bearer token for authentication
   * @returns {Promise<object>} - Subscription data
   */
  async getSubscription(subscriptionId, details = false, authToken) {
    if (!subscriptionId) {
      throw new Error('subscriptionId is required');
    }

    if (!authToken) {
      throw new Error('Authentication token is required');
    }

    const params = {};
    if (details) {
      params.details = true;
    }

    const response = await axios.get(
      `${this.BASE_URL}/api/subscriptions/${subscriptionId}`,
      {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        params,
      }
    );

    return response.data;
  },
};

// ============================================================
// Test Data Fixtures
// ============================================================
const TEST_DATA = {
  validToken: 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.valid-token-payload',
  expiredToken: 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.expired-token-payload',
  invalidToken: 'not-a-real-token',

  validSubscriptionId: 'sub_8a3f2b1c-94e7-4d6a-b8c1-3e5f7a9d0c2e',
  nonExistentSubscriptionId: 'sub_00000000-0000-0000-0000-000000000000',
  malformedSubscriptionId: '!!!invalid-id@@@',
  emptySubscriptionId: '',
  numericSubscriptionId: '12345',
  sqlInjectionId: "1; DROP TABLE subscriptions;--",
  veryLongSubscriptionId: 'sub_' + 'a'.repeat(500),

  // Successful response without details
  subscriptionBasicResponse: {
    id: 'sub_8a3f2b1c-94e7-4d6a-b8c1-3e5f7a9d0c2e',
    userId: 'usr_f47ac10b-58cc-4372-a567-0e02b2c3d479',
    plan: 'premium',
    status: 'active',
    networkName: 'ChargePoint Plus',
    startDate: '2024-01-15T00:00:00Z',
    endDate: '2025-01-15T00:00:00Z',
    monthlyRate: 29.99,
    currency: 'USD',
    createdAt: '2024-01-10T14:30:00Z',
    updatedAt: '2024-06-20T09:15:00Z',
  },

  // Successful response with details flag
  subscriptionDetailedResponse: {
    id: 'sub_8a3f2b1c-94e7-4d6a-b8c1-3e5f7a9d0c2e',
    userId: 'usr_f47ac10b-58cc-4372-a567-0e02b2c3d479',
    plan: 'premium',
    status: 'active',
    networkName: 'ChargePoint Plus',
    startDate: '2024-01-15T00:00:00Z',
    endDate: '2025-01-15T00:00:00Z',
    monthlyRate: 29.99,
    currency: 'USD',
    createdAt: '2024-01-10T14:30:00Z',
    updatedAt: '2024-06-20T09:15:00Z',
    details: {
      chargingStationsIncluded: 15000,
      freeKwhPerMonth: 200,
      overage_rate_per_kwh: 0.12,
      prioritySupport: true,
      roamingEnabled: true,
      roamingPartners: ['EVgo', 'Electrify America', 'Blink'],
      billingHistory: [
        {
          invoiceId: 'inv_001',
          date: '2024-06-01T00:00:00Z',
          amount: 29.99,
          status: 'paid',
        },
        {
          invoiceId: 'inv_002',
          date: '2024-05-01T00:00:00Z',
          amount: 29.99,
          status: 'paid',
        },
      ],
      usageStats: {
        currentMonthKwh: 145.7,
        averageMonthlyKwh: 132.4,
        totalSessions: 87,
        favoriteStation: 'station_abc123',
      },
    },
  },

  // Error responses
  badRequestResponse: {
    error: {
      code: 'INVALID_SUBSCRIPTION_ID',
      message: 'The provided subscription ID format is invalid.',
      statusCode: 400,
      timestamp: '2024-07-01T12:00:00Z',
    },
  },

  unauthorizedResponse: {
    error: {
      code: 'UNAUTHORIZED',
      message: 'Authentication credentials are missing or invalid.',
      statusCode: 401,
      timestamp: '2024-07-01T12:00:00Z',
    },
  },

  notFoundResponse: {
    error: {
      code: 'SUBSCRIPTION_NOT_FOUND',
      message: 'No subscription found with the given ID.',
      statusCode: 404,
      timestamp: '2024-07-01T12:00:00Z',
    },
  },
};

// ============================================================
// Helper: Create Axios Error (simulates real axios error shape)
// ============================================================
function createAxiosError(status, data, message = 'Request failed') {
  const error = new Error(message);
  error.response = {
    status,
    data,
    headers: { 'content-type': 'application/json' },
  };
  error.isAxiosError = true;
  error.config = {};
  return error;
}

// ============================================================
// Test Suite
// ============================================================
describe('Charging Network Subscription API - GET /api/subscriptions/{subscriptionId}', () => {
  beforeEach(() => {
    // Clear all mocks before each test to ensure isolation
    jest.clearAllMocks();
  });

  afterEach(() => {
    // Reset all mocks after each test
    jest.restoreAllMocks();
  });

  // ----------------------------------------------------------
  // 200 OK - Successful Retrieval
  // ----------------------------------------------------------
  describe('200 OK - Successful Subscription Retrieval', () => {
    test('should return basic subscription data without details flag', async () => {
      // Arrange
      axios.get.mockResolvedValueOnce({
        status: 200,
        data: TEST