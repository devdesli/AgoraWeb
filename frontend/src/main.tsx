// frontend/src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import ErrorPage from './ErrorPage'; // Import the component (value)
import type { ErrorPageProps } from './ErrorPage'; // Explicitly import the type

declare global {
  interface Window {
    ErrorPageBundle: {
      render: (elementId: string, props: ErrorPageProps) => void; // Using the imported type
    };
  }
}

window.ErrorPageBundle = {
  render: (elementId: string, props: ErrorPageProps) => { // Using the imported type
    const rootElement = document.getElementById(elementId);
    if (rootElement) {
      const root = ReactDOM.createRoot(rootElement);
      root.render(
        <React.StrictMode>
          <ErrorPage {...props} />
        </React.StrictMode>
      );
    } else {
      console.error(`Root element with ID '${elementId}' not found.`);
    }
  },
};