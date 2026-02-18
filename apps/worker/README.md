# AgencyOS RaaS Background Worker

This repository contains the background worker service for the AgencyOS RaaS (Robotics as a Service) platform. It is responsible for processing asynchronous tasks, managing job queues, and interacting with the database to support the core functionalities of AgencyOS.

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Database Setup](#database-setup)
  - [Running the Worker](#running-the-worker)
- [Scripts](#scripts)
- [Project Structure](#project-structure)
- [Docker](#docker)
- [Special Notes](#special-notes)
- [Contributing](#contributing)
- [License](#license)

## Features

*   **Asynchronous Job Processing:** Leverages `BullMQ` for robust and scalable job queuing.
*   **Database ORM:** Utilizes `Prisma` for type-safe database interactions with PostgreSQL.
*   **Redis Integration:** Seamlessly connects to Redis for job queue management and caching via `ioredis`.
*   **Environment Variable Management:** Uses `dotenv` for secure and flexible configuration.
*   **Dockerized Deployment:** Ready for containerization with a provided `Dockerfile`.
*   **ES Modules:** Modern JavaScript module system (`"type": "module"`).

## Getting Started

Follow these instructions to set up and run the worker service locally.

### Prerequisites

Before you begin, ensure you have the following installed:

*   [Node.js](https://nodejs.org/en/) (v18 or higher recommended)
*   [npm](https://www.npmjs.com/) (comes with Node.js) or [Yarn](https://yarnpkg.com/)
*   [Docker](https://www.docker.com/get-started) (optional, for containerized deployment)
*   [PostgreSQL](https://www.postgresql.org/download/) database instance
*   [Redis](https://redis.io/download/) instance

### Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd worker
    ```
2.  Install the dependencies:
    ```bash
    npm install
    ```

### Environment Variables

Create a `.env` file in the root of the project based on the `.env.example` (if available, otherwise create it manually). This file will contain your environment-specific configurations.

```env
# Database Configuration
DATABASE_URL="postgresql://user:password@host:port/database?schema=public"

# Redis Configuration for BullMQ
REDIS_HOST="localhost"
REDIS_PORT="6379"
REDIS_PASSWORD="" # Optional, if your Redis requires a password
```

### Database Setup

This project uses Prisma for database management.

1.  Generate the Prisma client:
    ```bash
    npm run db:generate
    ```
2.  Push the Prisma schema to your database (this will create or update tables based on your `prisma/schema.prisma`):
    ```bash
    npm run db:push
    ```

### Running the Worker

You can run the worker in development mode with hot-reloading or in production mode.

*   **Development Mode:**
    ```bash
    npm run dev
    ```
    This will start the worker using `node --watch`, automatically restarting on file changes.

*   **Production Mode:**
    ```bash
    npm start
    ```
    This will start the worker in a production-ready environment.

## Scripts

The `package.json` includes several utility scripts:

*   `npm start`: Starts the worker in production mode.
*   `npm run dev`: Starts the worker in development mode with file watching for automatic restarts.
*   `npm run db:generate`: Generates the Prisma client based on the `prisma/schema.prisma` file. This should be run whenever your schema changes.
*   `npm run db:push`: Pushes the current Prisma schema to the connected database, creating or updating tables. Useful for rapid development.

## Project Structure

*   `src/`: Contains the main application logic, including job processors, service definitions, and the entry point (`index.js`).
*   `prisma/`: Houses the Prisma schema (`schema.prisma`) and any generated migrations.
*   `Dockerfile`: Defines the Docker image for containerizing the worker service.
*   `.env`: Environment variables for local development (should not be committed to version control).
*   `CLAUDE.md`: Specific documentation or notes related to Claude AI integration or usage within the worker.

## Docker

The worker can be easily containerized using Docker.

1.  **Build the Docker image:**
    ```bash
    docker build -t agency-worker .
    ```
2.  **Run the Docker container:**
    ```bash
    docker run --env-file .env agency-worker
    ```
    Ensure your `.env` file is correctly configured with `DATABASE_URL` and `REDIS_HOST`/`REDIS_PORT` accessible from within the Docker container (e.g., if Redis/PostgreSQL are also in Docker, use their service names).

## Special Notes

Please refer to `CLAUDE.md` for any specific instructions, configurations, or considerations related to the integration or usage of Claude AI within this worker service.

## Contributing

Contributions are welcome! Please refer to the main AgencyOS repository for contribution guidelines.

## License

This project is licensed under the MIT License. See the main AgencyOS repository for full details.