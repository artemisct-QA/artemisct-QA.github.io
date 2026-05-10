import React from 'react';
import { render } from '@testing-library/react';

// Mock the react-calendar module
jest.mock('react-calendar', () => {
  return function MockCalendar() {
    return <div data-testid="mock-calendar">Calendar Component</div>;
  };
});

import App from './App';

test('renders without crashing', () => {
  render(<App />);
});