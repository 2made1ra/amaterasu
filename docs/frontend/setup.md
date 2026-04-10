# Frontend Setup Guide

This guide describes how to run and build the Svelte frontend application.

## Prerequisites

* **Node.js:** Ensure you have Node.js installed (v18 or higher is recommended).
* **NPM or Yarn:** A package manager to install dependencies.

## Installation

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install the project dependencies:
   ```bash
   npm install
   ```

## Development

To start the development server with Hot Module Replacement (HMR):

```bash
npm run dev
```

The application will typically be available at `http://localhost:5173/` (or the port specified in your console).

**Note:** Ensure the backend server is running and accessible (default is usually `http://localhost:8000`) so the frontend can make API calls. You may need to configure the backend API URL in the frontend environment or configuration if it differs from the default.

## Building for Production

To create an optimized production build:

```bash
npm run build
```

This command compiles the Svelte components and assets into the `dist/` directory. These static files can then be served by any static web server (like Nginx, Apache, or a Node.js static server).

## Previewing Production Build

To preview the built application locally before deployment:

```bash
npm run preview
```
