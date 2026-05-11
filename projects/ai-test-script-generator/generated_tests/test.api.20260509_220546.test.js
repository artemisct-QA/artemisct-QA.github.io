

```javascript
/**
 * Jest Test Suite for GET /api/charging/stations
 * 
 * Tests the charging stations API endpoint that returns a paginated list
 * of EV charging stations based on geographic coordinates and optional filters.
 * 
 * Covers: 200 OK, 400 Bad Request, 401 Unauthorized, 404 Not Found
 * Filter options: AVAILABLE, IN_USE, ALL
 */

const axios = require('axios');

// Mock axios to prevent real HTTP calls
jest.mock('axios');

// ─── Configuration ───────────────────────────────────────────────────────────

const BASE_URL = 'https://api.example.com';
const ENDPOINT = '/api/charging/stations';
const VALID_AUTH_TOKEN = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.validtoken';
const EXPIRED_AUTH_TOKEN = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expiredtoken';

// ─── Test Data Fixtures ──────────────────────────────────────────────────────

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
        lastUpdated: '2024-01-15T10:30:00Z',
      },
      {
        id: 'station-002',
        name: 'Marina Green Charger',
        latitude: 37.8015,
        longitude: -122.4367,
        status: 'IN_USE',
        connectorTypes: ['CCS'],
        powerKw: 50,
        pricePerKwh: 0.28,
        address: '456 Marina Blvd, San Francisco, CA 94123',
        lastUpdated: '2024-01-15T11:00:00Z',
      },
      {
        id: 'station-003',
        name: 'SOMA Fast Charge',
        latitude: 37.7785,
        longitude: -122.3950,
        status: 'AVAILABLE',
        connectorTypes: ['CCS', 'Type2'],
        powerKw: 350,
        pricePerKwh: 0.42,
        address: '789 Howard St, San Francisco, CA 94103',
        lastUpdated: '2024-01-15T09:45:00Z',
      },
    ],
    pagination: {
      page: 1,
      pageSize: 20,
      totalItems: 3,
      totalPages: 1,
      hasNextPage: false,
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
    'x-ratelimit-remaining': '99',
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
        lastUpdated: '2024-01-15T10:30:00Z',
      },
      {
        id: 'station-003',
        name: 'SOMA Fast Charge',
        latitude: 37.7785,
        longitude: -122.3950,
        status: 'AVAILABLE',
        connectorTypes: ['CCS', 'Type2'],
        powerKw: 350,
        pricePerKwh: 0.42,
        address: '789 Howard St, San Francisco, CA 94103',
        lastUpdated: '2024-01-15T09:45:00Z',
      },
    ],
    pagination: {
      page: 1,
      pageSize: 20,
      totalItems: 2,
      totalPages: 1,
      hasNextPage: false,
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
        name: 'Marina Green Charger',
        latitude: 37.8015,
        longitude: -122.4367,
        status: 'IN_USE',
        connectorTypes: ['CCS'],
        powerKw: 50,
        pricePerKwh: 0.28,
        address: '456 Marina Blvd, San Francisco, CA 94123',
        lastUpdated: '2024-01-15T11:00:00Z',
      },
    ],
    pagination: {
      page: 1,
      pageSize: 20,
      totalItems: 1,
      totalPages: 1,
      hasNextPage: false,
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
      page: 1,
      pageSize: 20,
      totalItems: 0,
      totalPages: 0,
      hasNextPage: false,
      hasPreviousPage: false,
    },
    metadata: {
      searchRadius: '10km',
      centerLatitude: 71.0,
      centerLongitude: 25.0,
      filter: 'ALL',
      timestamp: '2024-01-15T12:00:00Z',
    },
  },
  status: 200,
  statusText: 'OK',
  headers: { 'content-type': 'application/json' },
};

const mockPaginatedPage1Response = {
  data: {
    stations: new Array(20).fill(null).map((_, i) => ({
      id: `station-${String(i + 1).padStart(3, '0')}`,
      name: `Station ${i + 1}`,
      latitude: 37.7749 + i * 0.001,
      longitude: -122.4194 + i * 0.001,
      status: i % 2 === 0 ? 'AVAILABLE' : 'IN_USE