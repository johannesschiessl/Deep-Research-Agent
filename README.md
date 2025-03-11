# Deep-Research-Agent
An open source local deep research agent.

## Setup Instructions

### Prerequisites

- **Git**: Ensure you have Git installed on your system. You can download it from [git-scm.com](https://git-scm.com/).
- **Python**: Make sure Python 3.12 is installed. You can download it from [python.org](https://www.python.org/downloads/).
- **uv**: This project uses `uv` for managing the Python environment. Install it using pip:
  ```bash
  pip install uv
  ```

### Cloning the Repository

1. Open your terminal or command prompt.
2. Clone the repository using Git:
   ```bash
   git clone https://github.com/johannesschiessl/Deep-Research-Agent.git
   ```
3. Navigate into the project directory:
   ```bash
   cd Deep-Research-Agent
   ```

### Setting Up the Python Environment

Use `uv` to create a new virtual environment and install all dependencies:
   ```bash
   uv sync
   ```

### Running the Application

1. Ensure your `.env` file is set up with the necessary environment variables, including `OPENAI_API_KEY`.
2. Run the application:
   ```bash
   uv run deep_research_agent/main.py
   ```
3. Follow the on-screen instructions to conduct research.

## Contributing
We welcome contributions! Please feel free to submit a issue or a pull request.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.