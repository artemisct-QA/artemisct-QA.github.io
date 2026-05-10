import React from 'react';
import { render } from '@testing-library/react';

jest.mock('react-calendar', () => {
  return function MockCalendar() {
    return <div data-testid="mock-calendar">Calendar Component</div>;
  };
});

import App from './App';

test('renders without crashing', () => {
  render(<App />);
});

test('renders the Reservation Date heading', () => {
  const { getByText } = render(<App />);
  const heading = getByText('Reservation Date');
  expect(heading).toBeInTheDocument();
});

test('renders the calendar component', () => {
  const { getByTestId } = render(<App />);
  const calendar = getByTestId('mock-calendar');
  expect(calendar).toBeInTheDocument();
});

test('renders the Continue button', () => {
  const { getByText } = render(<App />);
  const button = getByText('Continue');
  expect(button).toBeInTheDocument();
});

test('displays selected date text', () => {
  const { getByText } = render(<App />);
  const selectedText = getByText(/Selected:/i);
  expect(selectedText).toBeInTheDocument();
});
