# X-CODERS Vue 3 + Vite Frontend

This directory contains the frontend application for the EX-Coders University Hackathon project.

## Architecture

- **Framework**: Vue 3 (Composition API)
- **Build Tool**: Vite (Extremely fast HMR)
- **Routing**: Vue Router
- **State Management**: Pinia
- **HTTP Client**: Axios (configured with JWT interceptors)
- **Styling**: Tailwind CSS + Custom Glassmorphism Theme

## Quick Start

The easiest way to start both the frontend and backend is to use the ignition scripts in the parent `solution-1` directory (`start.bat` for Windows or `./start.sh` for macOS/Linux).

If you wish to run the frontend independently:

```bash
# Install dependencies
npm install

# Start the dev server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

## Environment Variables

By default, Axios is configured to point to `http://127.0.0.1:8000/api`. If your backend is hosted elsewhere, create a `.env` file in this directory:

```env
VITE_API_BASE_URL=http://your-production-url/api
```
