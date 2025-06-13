// frontend/src/components/ErrorPage.tsx
import React from 'react';

// Define the props interface for type safety
export interface ErrorPageProps { // Export this interface too
  statusCode: number;
  message: string;
  link?: string;
  link_text?: string;
  info?: string;
}

// Your React Component
const ErrorPage: React.FC<ErrorPageProps> = ({ link, link_text, info, statusCode, message }) => {
  let displayMessage = message || 'Something went wrong.';
  let displayTitle = 'An Error Occurred';

  if (statusCode === 404) {
    displayTitle = 'Page Not Found';
    displayMessage = message || 'The page you are looking for does not exist.';
  } else if (statusCode === 500) {
    displayTitle = 'Internal Server Error';
    displayMessage = message || 'There was an unexpected error on our server.';
  }

  return (
    <div className="error-container">
      <h1 className="error-title">{statusCode} - {displayTitle}</h1>
      <p className="error-message">{displayMessage}</p>
      <p>{info}</p>
      <a href={link}>{link_text}</a>
      <a href="/" className="error-home-link">Go to Homepage</a>
    </div>
  );
};

export default ErrorPage; // Export the component