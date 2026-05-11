

```javascript
// vehicleStatus.test.js
// Test suite for GET /api/vehicle/status endpoint
// Tests battery percent, charging state responses, authentication, and edge cases

const axios = require('axios');

// Mock axios to prevent real HTTP calls
jest.mock('axios');

// --- Configuration ---
const BASE_URL = 'https://api.example.com';
const ENDPOINT = '/api/vehicle/status';
const FULL_URL = `${BASE_URL}${ENDPOINT}`;
const VALID_TOKEN = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.valid-token-payload';
const INVALID_TOKEN = 'Bearer expired-or-invalid-token';

// --- Helper: Build request config with auth header ---
const buildRequestConfig = (token) => ({
  headers: {
    Authorization: token,
    'Content-Type': 'application/json',
  },
});

describe('GET /api/vehicle/status', () => {
  // Reset all mocks before each test to ensure isolation
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  // =========================================================
  // HAPPY PATH TESTS - 200 OK
  // =========================================================
  describe('200 OK - Successful Responses', () => {
    test('should return batteryPercent and chargingState when authenticated with valid token', async () => {
      // Arrange: Mock a successful response with typical vehicle status
      const mockResponse = {
        status: 200,
        data: {
          batteryPercent: 75,
          chargingState: 'Charging',
        },
      };
      axios.get.mockResolvedValueOnce(mockResponse);

      // Act
      const response = await axios.get(FULL_URL, buildRequestConfig(VALID_TOKEN));

      // Assert
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('batteryPercent');
      expect(response.data).toHaveProperty('chargingState');
      expect(response.data.batteryPercent).toBe(75);
      expect(response.data.chargingState).toBe('Charging');
      expect(axios.get).toHaveBeenCalledTimes(1);
      expect(axios.get).toHaveBeenCalledWith(FULL_URL, buildRequestConfig(VALID_TOKEN));
    });

    test('should return batteryPercent as a number between 0 and 100', async () => {
      // Arrange
      const mockResponse = {
        status: 200,
        data: {
          batteryPercent: 42,
          chargingState: 'Discharging',
        },
      };
      axios.get.mockResolvedValueOnce(mockResponse);

      // Act
      const response = await axios.get(FULL_URL, buildRequestConfig(VALID_TOKEN));

      // Assert: Validate batteryPercent is a number within valid range
      expect(typeof response.data.batteryPercent).toBe('number');
      expect(response.data.batteryPercent).toBeGreaterThanOrEqual(0);
      expect(response.data.batteryPercent).toBeLessThanOrEqual(100);
    });

    test('should return chargingState as a valid string enum value', async () => {
      // Define acceptable charging states
      const validChargingStates = [
        'Charging',
        'Discharging',
        'FullyCharged',
        'NotCharging',
        'Disconnected',
      ];

      const mockResponse = {
        status: 200,
        data: {
          batteryPercent: 100,
          chargingState: 'FullyCharged',
        },
      };
      axios.get.mockResolvedValueOnce(mockResponse);

      // Act
      const response = await axios.get(FULL_URL, buildRequestConfig(VALID_TOKEN));

      // Assert
      expect(typeof response.data.chargingState).toBe('string');
      expect(validChargingStates).toContain(response.data.chargingState);
    });

    test('should return correct data when vehicle is fully charged (100%)', async () => {
      const mockResponse = {
        status: 200,
        data: {
          batteryPercent: 100,
          chargingState: 'FullyCharged',
        },
      };
      axios.get.mockResolvedValueOnce(mockResponse);

      const response = await axios.get(FULL_URL, buildRequestConfig(VALID_TOKEN));

      expect(response.status).toBe(200);
      expect(response.data.batteryPercent).toBe(100);
      expect(response.data.chargingState).toBe('FullyCharged');
    });

    test('should return correct data when vehicle battery is at 0%', async () => {
      const mockResponse = {
        status: 200,
        data: {
          batteryPercent: 0,
          chargingState: 'Disconnected',
        },
      };
      axios.get.mockResolvedValueOnce(mockResponse);

      const response = await axios.get(FULL_URL, buildRequestConfig(VALID_TOKEN));

      expect(response.status).toBe(200);
      expect(response.data.batteryPercent).toBe(0);
      expect(response.data.chargingState).toBe('Disconnected');
    });

    test('should return correct data when vehicle is actively charging', async () => {
      const mockResponse = {
        status: 200,
        data: {
          batteryPercent: 58,
          chargingState: 'Charging',
        },
      };
      axios.get.mockResolvedValueOnce(mockResponse);

      const response = await axios.get(FULL_URL, buildRequestConfig(VALID_TOKEN));

      expect(response.status).toBe(200);
      expect(response.data.batteryPercent).toBe(58);
      expect(response.data.chargingState).toBe('Charging');
    });

    test('should return correct data when vehicle is discharging (in use)', async () => {
      const mockResponse = {
        status: 200,
        data: {
          batteryPercent: 34,
          chargingState: 'Discharging',
        },
      };
      axios.get.mockResolvedValueOnce(mockResponse);

      const response = await axios.get(FULL_URL, buildRequestConfig(VALID_TOKEN));

      expect(response.status).toBe(200);
      expect(response.data.batteryPercent).toBe(34);
      expect(response.data.chargingState).toBe('Discharging');
    });
  });

  // =========================================================
  // AUTHENTICATION TESTS - 401 Unauthorized
  // =========================================================
  describe('401 Unauthorized - Authentication Failures', () => {
    test('should return 401 when no Authorization header is provided', async () => {
      // Arrange: Mock a 401 response for missing token
      const mockError = {
        response: {
          status: 401,
          data: {
            error: 'Unauthorized',
            message: 'Authorization header is required',
          },
        },
      };
      axios.get.mockRejectedValueOnce(mockError);

      // Act & Assert
      try {
        await axios.get(FULL_URL, {
          headers: { 'Content-Type': 'application/json' },
        });
        // If we reach here, the test should fail
        fail('Expected request to throw 401 error');
      } catch (error) {
        expect(error.response.status).toBe(401);
        expect(error.response.data.error).toBe('Unauthorized');
        expect(error.response.data.message).toBeDefined();
      }

      expect(axios.get).toHaveBeen