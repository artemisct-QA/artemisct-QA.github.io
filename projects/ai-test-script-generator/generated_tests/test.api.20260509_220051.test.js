

```javascript
/**
 * Jest Test Suite for GET /api/charging/stations
 * 
 * Tests the charging stations endpoint which returns a paginated list
 * of EV charging stations based on location and optional filter parameters.
 * 
 * Covers: 200 OK, 400 Bad Request, 401 Unauthorized, 404 Not Found
 */

const axios = require('axios');

// Mock axios to prevent real HTTP calls
jest.mock('axios');

// --- Configuration ---
const BASE_URL = 'https://api.example.com';
const ENDPOINT = '/api/charging/stations';
const VALID_TOKEN = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.validtoken';
const EXPIRED_TOKEN = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expiredtoken';

// --- Realistic Test Data ---
const mockStationsResponse = {
  data: {
    stations: [
      {
        id: 'station-001',
        name: 'Downtown Charging Hub',
        latitude: 37.7749,
        longitude: -122.4194,
        status: 'AVAILABLE',
        connectorTypes: ['CCS', 'CHAdeMO'],
        powerKw: 150,
        pricePerKwh: 0.35,
        address: '123 Market St, San Francisco, CA 94105',
        operatingHours: '24/7',
        lastUpdated: '2024-01-15T10:30:00Z',
      },
      {
        id: 'station-002',
        name: 'Marina Green Station',
        latitude: 37.8045,
        longitude: -122.4367,
        status: 'IN_USE',
        connectorTypes: ['CCS'],
        powerKw: 50,
        pricePerKwh: 0.28,
        address: '456 Marina Blvd, San Francisco, CA 94123',
        operatingHours: '06:00-23:00',
        lastUpdated: '2024-01-15T09:45:00Z',
      },
      {
        id: 'station-003',
        name: 'SoMa Fast Charge',
        latitude: 37.7785,
        longitude: -122.3950,
        status: 'AVAILABLE',
        connectorTypes: ['CCS', 'Type 2'],
        powerKw: 350,
        pricePerKwh: 0.42,
        address: '789 Howard St, San Francisco, CA 94103',
        operatingHours: '24/7',
        lastUpdated: '2024-01-15T11:00:00Z',
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
      searchRadius: '10km',
      centerLatitude: 37.7749,
      centerLongitude: -122.4194,
      filter: 'ALL',
      timestamp: '2024-01-15T12:00:00Z',
    },
  },
  status: 200,
  statusText: 'OK',
  headers: {
    'content-type': 'application/json',
    'x-ratelimit-remaining': '98',
    'x-request-id': 'req-abc123',
  },
};

const mockAvailableOnlyResponse = {
  data: {
    stations: [
      {
        id: 'station-001',
        name: 'Downtown Charging Hub',
        latitude: 37.7749,
        longitude: -122.4194,
        status: 'AVAILABLE',
        connectorTypes: ['CCS', 'CHAdeMO'],
        powerKw: 150,
        pricePerKwh: 0.35,
        address: '123 Market St, San Francisco, CA 94105',
        operatingHours: '24/7',
        lastUpdated: '2024-01-15T10:30:00Z',
      },
      {
        id: 'station-003',
        name: 'SoMa Fast Charge',
        latitude: 37.7785,
        longitude: -122.3950,
        status: 'AVAILABLE',
        connectorTypes: ['CCS', 'Type 2'],
        powerKw: 350,
        pricePerKwh: 0.42,
        address: '789 Howard St, San Francisco, CA 94103',
        operatingHours: '24/7',
        lastUpdated: '2024-01-15T11:00:00Z',
      },
    ],
    pagination: {
      currentPage: 1,
      totalPages: 3,
      totalItems: 28,
      itemsPerPage: 10,
      hasNextPage: true,
      hasPreviousPage: false,
    },
    metadata: {
      searchRadius: '10km',
      centerLatitude: 37.7749,
      centerLongitude: -122.4194,
      filter: 'AVAILABLE',
      timestamp: '2024-01-15T12:00:00Z',
    },
  },
  status: 200,
  statusText: 'OK',
  headers: { 'content-type': 'application/json' },
};

const mockInUseOnlyResponse = {
  data: {
    stations: [
      {
        id: 'station-002',
        name: 'Marina Green Station',
        latitude: 37.8045,
        longitude: -122.4367,
        status: 'IN_USE',
        connectorTypes: ['CCS'],
        powerKw: 50,
        pricePerKwh: 0.28,
        address: '456 Marina Blvd, San Francisco, CA 94123',
        operatingHours: '06:00-23:00',
        lastUpdated: '2024-01-15T09:45:00Z',
      },
    ],
    pagination: {
      currentPage: 1,
      totalPages: 2,
      totalItems: 19,
      itemsPerPage: 10,
      hasNextPage: true,
      hasPreviousPage: false,
    },
    metadata: {
      searchRadius: '10km',
      centerLatitude: 37.7749,
      centerLongitude: -122.4194,
      filter: 'IN_USE',
      timestamp: '2024-01-15T12:00:00Z',
    },
  },
  status: 200,
  statusText: 'OK',
  headers: { 'content-type': 'application/json' },
};

const mockEmptyResponse = {
  data: {
    stations: [],
    pagination: {
      currentPage: 1,
      totalPages: 0,
      totalItems: 0,
      itemsPerPage: 10,
      hasNextPage: false,
      hasPreviousPage: false,
    },
    metadata: {
      searchRadius: '10km',
      centerLatitude: 0.0,
      centerLongitude: 0.0,
      filter: 'ALL',
      timestamp: '2024-01-15T12:00:00Z',
    },
  },
  status: 200,
  statusText: 'OK',
  headers: { 'content-type': 'application/json' },
};

// --- Helper: API Client Wrapper ---
/**
 * Encapsulates the GET request to /api/charging/stations
 * so tests stay clean and DRY.
 */
const getChargingStations = async ({ latitude, longitude, filter, page, token } = {}) => {
  const params = {};