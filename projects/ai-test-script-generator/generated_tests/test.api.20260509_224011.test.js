

```javascript
/**
 * Jest Test Suite: Vehicle Remote Start API
 * Endpoint: POST /api/vehicle/remote/start
 * 
 * Tests cover:
 * - 200: Successful remote start with control token
 * - 400: Invalid duration parameter
 * - 401: Unauthorized (missing/invalid auth)
 * - 403: Remote start not enabled for vehicle
 * - 409: Vehicle engine already running
 */

const axios = require('axios');

// Mock axios to prevent real API calls
jest.mock('axios');

// --- Configuration ---
const BASE_URL = 'https://api.vehicle-control.example.com';
const ENDPOINT = '/api/vehicle/remote/start';
const FULL_URL = `${BASE_URL}${ENDPOINT}`;

// --- Test Data Fixtures ---
const VALID_AUTH_TOKEN = 'Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.validtoken.signature';
const EXPIRED_AUTH_TOKEN = 'Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.expiredtoken.signature';
const INVALID_AUTH_TOKEN = 'Bearer malformed-token';

const VALID_VEHICLE_ID = 'VH-2024-AB1234';
const DISABLED_VEHICLE_ID = 'VH-2024-DISABLED';
const RUNNING_VEHICLE_ID = 'VH-2024-RUNNING';

const createRequestPayload = (overrides = {}) => ({
  vehicleId: VALID_VEHICLE_ID,
  duration: 15, // minutes
  ...overrides,
});

const createHeaders = (token = VALID_AUTH_TOKEN) => ({
  headers: {
    Authorization: token,
    'Content-Type': 'application/json',
    'X-Request-ID': expect.any(String),
  },
});

// --- Helper: API Client Wrapper ---
const vehicleRemoteStartAPI = {
  /**
   * Sends a POST request to start a vehicle remotely.
   * @param {Object} payload - Request body with vehicleId and duration
   * @param {string} authToken - Bearer token for authentication
   * @returns {Promise} Axios response promise
   */
  startVehicle: async (payload, authToken) => {
    const requestId = `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    return axios.post(FULL_URL, payload, {
      headers: {
        Authorization: authToken,
        'Content-Type': 'application/json',
        'X-Request-ID': requestId,
      },
    });
  },
};

// ============================================================
// TEST SUITE
// ============================================================

describe('POST /api/vehicle/remote/start', () => {
  beforeEach(() => {
    // Reset all mocks before each test to ensure isolation
    jest.clearAllMocks();
    jest.restoreAllMocks();
  });

  afterEach(() => {
    // Verify no unexpected calls were made
    // (additional safety net for test isolation)
  });

  // ----------------------------------------------------------
  // 200 - Successful Remote Start
  // ----------------------------------------------------------
  describe('200 - Successful Remote Start', () => {
    const mockSuccessResponse = {
      status: 200,
      data: {
        success: true,
        controlToken: 'ctrl-tkn-a1b2c3d4e5f6',
        vehicleId: VALID_VEHICLE_ID,
        duration: 15,
        expiresAt: '2024-12-15T10:30:00Z',
        startedAt: '2024-12-15T10:15:00Z',
        message: 'Vehicle remote start initiated successfully.',
      },
      headers: {
        'x-ratelimit-remaining': '49',
        'x-ratelimit-limit': '50',
      },
    };

    test('should return a control token when valid duration and auth are provided', async () => {
      axios.post.mockResolvedValueOnce(mockSuccessResponse);

      const payload = createRequestPayload({ duration: 15 });
      const response = await vehicleRemoteStartAPI.startVehicle(payload, VALID_AUTH_TOKEN);

      // Verify the request was made correctly
      expect(axios.post).toHaveBeenCalledTimes(1);
      expect(axios.post).toHaveBeenCalledWith(
        FULL_URL,
        expect.objectContaining({
          vehicleId: VALID_VEHICLE_ID,
          duration: 15,
        }),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: VALID_AUTH_TOKEN,
            'Content-Type': 'application/json',
          }),
        })
      );

      // Verify response structure
      expect(response.status).toBe(200);
      expect(response.data.success).toBe(true);
      expect(response.data.controlToken).toBeDefined();
      expect(response.data.controlToken).toMatch(/^ctrl-tkn-/);
      expect(response.data.vehicleId).toBe(VALID_VEHICLE_ID);
      expect(response.data.duration).toBe(15);
      expect(response.data.expiresAt).toBeDefined();
      expect(response.data.startedAt).toBeDefined();
    });

    test('should accept minimum valid duration of 1 minute', async () => {
      const minDurationResponse = {
        ...mockSuccessResponse,
        data: {
          ...mockSuccessResponse.data,
          duration: 1,
          controlToken: 'ctrl-tkn-min-duration',
        },
      };
      axios.post.mockResolvedValueOnce(minDurationResponse);

      const payload = createRequestPayload({ duration: 1 });
      const response = await vehicleRemoteStartAPI.startVehicle(payload, VALID_AUTH_TOKEN);

      expect(response.status).toBe(200);
      expect(response.data.duration).toBe(1);
      expect(response.data.controlToken).toBe('ctrl-tkn-min-duration');
    });

    test('should accept maximum valid duration of 30 minutes', async () => {
      const maxDurationResponse = {
        ...mockSuccessResponse,
        data: {
          ...mockSuccessResponse.data,
          duration: 30,
          controlToken: 'ctrl-tkn-max-duration',
        },
      };
      axios.post.mockResolvedValueOnce(maxDurationResponse);

      const payload = createRequestPayload({ duration: 30 });
      const response = await vehicleRemoteStartAPI.startVehicle(payload, VALID_AUTH_TOKEN);

      expect(response.status).toBe(200);
      expect(response.data.duration).toBe(30);
      expect(response.data.controlToken).toBe('ctrl-tkn-max-duration');
    });

    test('should include X-Request-ID header in the request', async () => {
      axios.post.mockResolvedValueOnce(mockSuccessResponse);

      const payload = createRequestPayload();
      await vehicleRemoteStartAPI.startVehicle(payload, VALID_AUTH_TOKEN);

      const callArgs = axios.post.mock.calls[0];
      const headers = callArgs[2].headers;
      expect(headers).toHaveProperty('X-Request-ID');
      expect(typeof headers['X-Request-ID']).toBe('string');
      expect(headers['X-Request-ID'].length).toBeGreaterThan(0);
    });

    test('should return expiresAt timestamp that is after startedAt', async () => {
      axios.post.mockResolvedValueOnce(mockSuccessResponse);

      const payload = createRequestPayload({ duration: 15 });
      const response = await vehicleRemoteStartAPI.startVehicle(payload, VALID_AUTH_TOKEN);

      const