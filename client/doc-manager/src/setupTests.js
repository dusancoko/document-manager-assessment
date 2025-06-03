import '@testing-library/jest-dom';

// Mock FontAwesome
jest.mock('@fortawesome/react-fontawesome', () => ({
  FontAwesomeIcon: ({ icon, ...props }) => <i data-testid="fa-icon" {...props} />
}));

// Mock dayjs
jest.mock('dayjs', () => {
  const actualDayjs = jest.requireActual('dayjs');
  return jest.fn(() => ({
    format: jest.fn(() => '2024')
  }));
});