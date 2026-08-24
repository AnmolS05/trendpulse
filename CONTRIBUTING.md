# Contributing to Trendpulse

First off, thank you for considering contributing to Trendpulse! It's people like you that make Trendpulse such a great tool.

## Where do I go from here?

If you've noticed a bug or have a feature request, make sure to check our [Issues](../../issues) to see if someone else has already created a ticket. If not, go ahead and make one!

## Setting up for development

### Prerequisites
- Python (v3.10+)
- Node.js (v18+)
- Docker (optional, but recommended)

### Local Setup (Using Docker)
The easiest way to get started is using Docker Compose:
```bash
docker-compose up --build
```
This will start both the frontend and backend services.

### Local Setup (Manual)
1. Fork the repo and create your branch from `main`.
2. Clone your fork locally.
3. In the `backend/` directory, set up your virtual environment, install dependencies (`pip install -r requirements.txt`), and run the server.
4. In the `frontend/` directory, run `npm install`, set up your `.env`, and `npm run dev`.

## Making a Pull Request

1. Ensure any install or build dependencies are removed before the end of the layer when doing a build.
2. Update the README.md with details of changes to the interface, this includes new environment variables, exposed ports, useful file locations and container parameters.
3. You may merge the Pull Request in once you have the sign-off of two other developers, or if you do not have permission to do that, you may request the second reviewer to merge it for you.

## Code Style
We use Prettier and ESLint for the frontend, and Black/Flake8 for the backend. Please ensure your code passes linting before submitting a PR.

Thank you!
