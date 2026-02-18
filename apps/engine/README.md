# AgencyOS RaaS Engine API

## Overview

The `agency-engine` is the core API for the AgencyOS RaaS (Robotics as a Service) platform. It is responsible for managing and orchestrating various agency operations, providing a robust and scalable backend for the entire system. Built with Fastify, it offers a high-performance and efficient API layer, integrated with a PostgreSQL database via Prisma ORM and a powerful job queue system using BullMQ and Redis.

## Features

*   **High-Performance API**: Leverages Fastify for a fast and low-overhead web framework.
*   **Database Management**: Utilizes Prisma ORM for type-safe database access and migrations with PostgreSQL.
*   **Asynchronous Job Processing**: Implements BullMQ with Redis for reliable background job queuing and processing.
*   **Modular Design**: Organized `src` directory for maintainable and scalable code.
*   **Environment Configuration**: Easy configuration management using `.env` files.

## Technologies Used

*   **Node.js**: JavaScript runtime environment.
*   **Fastify**: Fast and low-overhead web framework.
*   **Prisma**: Next-generation ORM for Node.js and TypeScript.
*   **PostgreSQL**: Powerful, open-source relational database system.
*   **BullMQ**: Robust, fast, and reliable queue system for Node.js.
*   **ioredis**: High-performance Redis client for Node.js.
*   **Zod**: TypeScript-first schema declaration and validation library.
*   **dotenv**: Loads environment variables from a `.env` file.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

Before you begin, ensure you have the following installed:

*   Node.js (v18 or higher recommended)
*   npm (comes with Node.js)
*   PostgreSQL database instance
*   Redis instance
*   Docker (optional, for containerized deployment)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd agency-engine
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```

### Environment Variables

Create a `.env` file in the root of the project based on the `.env.example` (if provided, otherwise create one manually) and populate it with your environment-specific values.

Example `.env` file:

```env
DATABASE_URL="postgresql://user:password@localhost:5432/agency_engine_db"
REDIS_HOST="localhost"
REDIS_PORT="6379"
# Add any other necessary environment variables here
```

### Database Setup

1.  **Generate Prisma Client:**
    This command generates the Prisma client based on your `prisma/schema.prisma` file.
    ```bash
    npm run db:generate
    ```

2.  **Push Schema to Database:**
    This command pushes the Prisma schema to your PostgreSQL database, creating or updating tables.
    ```bash
    npm run db:push
    ```

    If you need to inspect your database, you can use Prisma Studio:
    ```bash
    npm run db:studio
    ```

### Running the Application

#### Development Mode

To run the application in development mode with file watching:

```bash
npm run dev
```

This will start the server, and it will automatically restart when changes are detected in the `src` directory.

#### Production Mode

To run the application in production mode:

```bash
npm start
```

The API will typically be available at `http://localhost:3000` (or the port configured in your environment variables).

## Available Scripts

In the project directory, you can run:

*   `npm start`: Starts the application in production mode.
*   `npm run dev`: Starts the application in development mode with `node --watch`.
*   `npm run db:generate`: Generates the Prisma client based on `prisma/schema.prisma`.
*   `npm run db:push`: Pushes the Prisma schema to the connected database.
*   `npm run db:studio`: Opens Prisma Studio to browse your database.

## Project Structure

*   `src/`: Contains the main application source code, including API routes, services, and business logic.
*   `prisma/`: Holds the Prisma schema definition (`schema.prisma`) and database migration files.
*   `plans/`: Directory for storing planning documents or architectural diagrams.
*   `CLAUDE.md`: Documentation specific to Claude AI interactions or configurations.
*   `Dockerfile`: Defines the Docker image for containerizing the application.
*   `.env`: Environment variables for local development (not committed to VCS).
*   `package.json`: Project metadata and script definitions.

## Contributing

Contributions are welcome! Please follow standard GitHub flow: fork the repository, create a feature branch, commit your changes, and open a pull request.

## License

This project is licensed under the MIT License - see the `LICENSE` file (if present) for details.