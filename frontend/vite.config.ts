import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  build: {
    // Configure to output a library (single JS file)
    lib: {
      entry: path.resolve(__dirname, 'src/main.tsx'), // Your entry point
      name: 'ErrorPageBundle', // A global name for your bundle
      fileName: (format) => `error-page-bundle.${format}.js`, // Naming convention for the output file
      formats: ['umd'], // 'umd' is good for browser embedding
    },
    rollupOptions: {
      // Ensure React and ReactDOM are bundled INTO your single file
      // If you don't want them bundled (e.g., if you load them globally),
      // you would list them here as 'external'
      output: {
        globals: {
          react: 'React',
          'react-dom': 'ReactDOM',
        },
      },
    },
    outDir: '../static/js', // Output to your Flask static directory
    emptyOutDir: false, // Clean the output directory before building
  },
  // Base public path for assets. Important for production builds.
  base: '/static/js/',
});