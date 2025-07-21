import { render, screen } from '@testing-library/react';
import App from './App';

test('renders Agentic AI Document Generator heading', () => {
  render(<App />);
  const heading = screen.getByText(/Agentic AI Document Generator/i);
  expect(heading).toBeInTheDocument();
});
