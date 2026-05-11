

```javascript
/**
 * Jest Test Suite for GET /api/charging/stations
 * 
 * Tests the charging stations endpoint that returns a paginated list
 * of stations based on latitude, longitude, and optional filter parameters.
 * 
 * Covers: 200 OK, 400 Bad Request, 401 Unauthorized, 404 Not Found
 */

const axios = require('axios');

// Mock axios to prevent real API calls
jest.mock('axios');

// --- Configuration ---
const BASE_URL = 'https://api.example.com';
const ENDPOINT = '/api/charging/stations';
const VALID_TOKEN = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.validtoken';
const EXPIRED_TOKEN = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expiredtoken';

// --- API Client Wrapper ---
/**
 * Fetches charging stations from the API.
 * This simulates what the actual service/client layer would look like.
 */
async function getChargingStations({ latitude, longitude, filter, page, limit, token } = {}) {
  const params = {};

  if (latitude !== undefined) params.latitude = latitude;
  if (longitude !== undefined) params.longitude = longitude;
  if (filter !== undefined) params.filter = filter;
  if (page !== undefined) params.page = page;
  if (limit !== undefined) params.limit = limit;

  const headers = {};
  if (token) {
    headers['Authorization'] = token;
  }

  const response = await axios.get(`${BASE_URL}${ENDPOINT}`, {
    params,
    headers,
  });

  return response;
}

// --- Realistic Test Data Fixtures ---
const mockStationsPage1 = {
  data: {
    stations: [
      {
        id: 'station-001',
        name: 'Downtown Supercharger',
        latitude: 37.7749,
        longitude: -122.4194,
        status: 'AVAILABLE',
        connectorTypes: ['CCS', 'CHAdeMO'],
        maxPowerKw: 150,
        pricePerKwh: 0.35,
        address: '123 Market St, San Francisco, CA 94105',
        operatingHours: '24/7',
        lastUpdated: '2024-01-15T10:30:00Z',
      },
      {
        id: 'station-002',
        name: 'Mission Bay Charging Hub',
        latitude: 37.7705,
        longitude: -122.3872,
        status: 'IN_USE',
        connectorTypes: ['CCS', 'Type2'],
        maxPowerKw: 350,
        pricePerKwh: 0.42,
        address: '456 Terry Francois Blvd, San Francisco, CA 94158',
        operatingHours: '06:00-23:00',
        lastUpdated: '2024-01-15T11:00:00Z',
      },
      {
        id: 'station-003',
        name: 'SoMa Quick Charge',
        latitude: 37.7785,
        longitude: -122.3950,
        status: 'AVAILABLE',
        connectorTypes: ['CCS'],
        maxPowerKw: 50,
        pricePerKwh: 0.28,
        address: '789 Folsom St, San Francisco, CA 94107',
        operatingHours: '24/7',
        lastUpdated: '2024-01-15T09:45:00Z',
      },
    ],
    pagination: {
      currentPage: 1,
      totalPages: 5,
      totalItems: 47,
      itemsPerPage: 10,
      hasNextPage: true,
      hasPreviousPage: false,
    },
    metadata: {
      searchCenter: { latitude: 37.7749, longitude: -122.4194 },
      radiusKm: 10,
      filterApplied: 'ALL',
    },
  },
  status: 200,
  statusText: 'OK',
  headers: {
    'content-type': 'application/json',
    'x-ratelimit-remaining': '98',
    'x-request-id': 'req-abc-123',
  },
};

const mockStationsAvailableOnly = {
  data: {
    stations: [
      {
        id: 'station-001',
        name: 'Downtown Supercharger',
        latitude: 37.7749,
        longitude: -122.4194,
        status: 'AVAILABLE',
        connectorTypes: ['CCS', 'CHAdeMO'],
        maxPowerKw: 150,
        pricePerKwh: 0.35,
        address: '123 Market St, San Francisco, CA 94105',
        operatingHours: '24/7',
        lastUpdated: '2024-01-15T10:30:00Z',
      },
      {
        id: 'station-003',
        name: 'SoMa Quick Charge',
        latitude: 37.7785,
        longitude: -122.3950,
        status: 'AVAILABLE',
        connectorTypes: ['CCS'],
        maxPowerKw: 50,
        pricePerKwh: 0.28,
        address: '789 Folsom St, San Francisco, CA 94107',
        operatingHours: '24/7',
        lastUpdated: '2024-01-15T09:45:00Z',
      },
    ],
    pagination: {
      currentPage: 1,
      totalPages: 3,
      totalItems: 25,
      itemsPerPage: 10,
      hasNextPage: true,
      hasPreviousPage: false,
    },
    metadata: {
      searchCenter: { latitude: 37.7749, longitude: -122.4194 },
      radiusKm: 10,
      filterApplied: 'AVAILABLE',
    },
  },
  status: 200,
  statusText: 'OK',
  headers: { 'content-type': 'application/json' },
};

const mockStationsInUseOnly = {
  data: {
    stations: [
      {
        id: 'station-002',
        name: 'Mission Bay Charging Hub',
        latitude: 37.7705,
        longitude: -122.3872,
        status: 'IN_USE',
        connectorTypes: ['CCS', 'Type2'],
        maxPowerKw: 350,
        pricePerKwh: 0.42,
        address: '456 Terry Francois Blvd, San Francisco, CA 94158',
        operatingHours: '06:00-23:00',
        lastUpdated: '2024-01-15T11:00:00Z',
      },
    ],
    pagination: {
      currentPage: 1,
      totalPages: 2,
      totalItems: 12,
      itemsPerPage: 10,
      hasNextPage: true,
      hasPreviousPage: false,
    },
    metadata: {
      searchCenter: { latitude: 37.7749, longitude: -122.4194 },
      radiusKm: 10,
      filterApplied: 'IN_USE',
    },
  },
  status: 200,
  statusText: 'OK',
  headers: { 'content-type': 'application/json' },
};

const mockEmptyStations = {
  data: {
    stations: [],
    pagination: {
      currentPage: 1,
      totalPages: 0,
      totalItems: 0,
      itemsPerPage: 10,
      hasNextPage: false,
      hasPreviousPage