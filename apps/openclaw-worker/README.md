# OpenClaw Worker

The `openclaw-worker` project serves as a distributed worker service for the broader OpenClaw ecosystem. Leveraging Cloudflare Workers, it provides a robust and scalable platform for executing various automated tasks through an agentic architecture. This project is designed to orchestrate complex workflows, from initial planning and design to execution, monitoring, and deployment, utilizing a collection of specialized daemons.

## Table of Contents

-   [Features](#features)
-   [Key Components (Daemons)](#key-components-daemons)
-   [Technologies Used](#technologies-used)
-   [Getting Started](#getting-started)
    -   [Prerequisites](#prerequisites)
    -   [Installation](#installation)
    -   [Configuration](#configuration)
-   [Available Scripts](#available-scripts)
-   [Further Documentation](#further-documentation)
-   [Contributing](#contributing)
-   [License](#license)

## Features

*   **Agentic Architecture**: Composed of specialized daemons, each responsible for a distinct part of the workflow.
*   **Cloudflare Workers**: Utilizes a serverless platform for highly scalable and performant execution.
*   **Automated Task Execution**: Designed to handle a wide range of automated tasks within the OpenClaw project.
*   **Modular Design**: Easy to extend and maintain with clearly defined roles for each daemon.
*   **Comprehensive Testing**: Includes a testing suite to ensure reliability and correctness.

## Key Components (Daemons)

The project is structured around several daemon files, each representing a distinct agent or service:

*   `architect-daemon.js`: Responsible for high-level planning, design, and strategic decision-making within the system.
*   `artist-daemon.js`: Likely handles creative tasks, content generation, or visual asset creation.
*   `builder-daemon.js`: Manages the construction, assembly, or compilation of project components.
*   `diplomat-daemon.js`: Facilitates communication, negotiation, and coordination between different agents or external systems.
*   `dispatcher-daemon.js`: Routes incoming tasks to the appropriate daemons based on their capabilities and current load.
*   `hunter-daemon.js`: Potentially responsible for data gathering, exploration, or identifying resources.
*   `config.js`: Centralized configuration file for the worker and its daemons.
*   `ecosystem.config.js`: Configuration for process management (e.g., PM2) in a production environment, ensuring daemon resilience.
*   `openclaw-tunnel`: **Serveo.net tunnel manager** (replaces deprecated Cloudflare Tunnel).

## Technologies Used

*   **Cloudflare Workers**: Serverless execution environment for deploying the worker.
*   **JavaScript/TypeScript**: Primary development languages.
*   **Wrangler**: Cloudflare's CLI tool for developing, testing, and deploying Workers.
*   **Vitest**: A fast and modern testing framework for unit and integration tests.
*   **Playwright**: A powerful library for browser automation, suggesting capabilities for web interaction, scraping, or UI testing.

## Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

*   Node.js (LTS version recommended)
*   npm (comes with Node.js)
*   A Cloudflare account (for deployment)
*   Wrangler CLI installed and configured (`npm i -g wrangler`)

### Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd openclaw-worker
    ```
2.  Install NPM dependencies:
    ```bash
    npm install
    ```

### Configuration

1.  Ensure your Cloudflare Wrangler CLI is authenticated:
    ```bash
    wrangler login
    ```
2.  Review and configure `wrangler.toml` (implied by the `.wrangler` directory) for your Cloudflare Worker settings.
3.  Adjust settings in `config.js` as needed for local development or specific daemon behaviors.

## Available Scripts

In the project directory, you can run:

*   `npm run deploy`: Deploys the worker to your Cloudflare account. This command uses `wrangler deploy`.
*   `npm run dev` / `npm start`: Starts a local development server for the worker, allowing you to test it locally without deploying.
*   `npm run test`: Executes the test suite using Vitest to ensure all components are functioning correctly.
*   `npm run cf-typegen`: Generates Cloudflare Workers types, enhancing development experience with better autocompletion and type checking.

## Further Documentation

For more in-depth information on specific aspects of the project, refer to the following documents:

*   `CLAUDE.md`: Documentation related to integration or usage of the Claude AI model.
*   `IMPLEMENTATION_STATUS.md`: Provides an overview of the current implementation status of various features and components.
*   `RULES_DNA_FIRST_v30.md`: Outlines the core principles and rules guiding the development and operation of the OpenClaw system (version 3.0).
*   `TASK-WATCHER-IMPLEMENTATION.md`: Detailed documentation on how the task watcher component is implemented.
*   `TASK_WATCHER_PLAN.md`: The planning document outlining the design and strategy for the task watcher feature.

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information. (Note: A `LICENSE` file is not provided in the file list, but this is a common placeholder.)