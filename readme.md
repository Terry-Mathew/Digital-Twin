# Terry Mathew's Digital Twin

This project creates an AI-powered "Digital Twin" of Terry Mathew. It is an interactive chatbot designed to simulate a professional conversation with Terry, answering questions about his experience, skills, and background using his real-world data.

## Features

-   **Persona Simulation**: The bot acts as Terry Mathew, speaking in the first person and referencing his actual resume and summary.
-   **Knowledge Base**:
    -   **Resume**: Parses `me/linkedin.pdf` to answer career questions.
    -   **Summary**: Uses `me/summary.txt` for a professional overview.
    -   **Website**: Scrapes `terrymathew.com` for the latest portfolio content.
-   **Interactive Contact Flow**:
    -   Intelligently collects user contact details (Name, Email, Phone, Note).
    -   Verifies information before recording.
    -   Uses **Pushover** to send real-time notifications to Terry when a lead is captured.
-   **Tool Integration**:
    -   `record_user_details`: Saves contact info for follow-up.
    -   `record_unknown_question`: Logs queries the bot couldn't answer for future improvement.

## Tech Stack

-   **Engine**: [OpenRouter](https://openrouter.ai/) (using `mistralai/kodestral-2501`) for main chat and tool usage.
-   **Backup**: [Bytez SDK](https://bytez.com/) (using `Qwen/Qwen3-1.7B`) available for fallback text generation.
-   **Interface**: [Gradio](https://gradio.app/) for a clean, responsive web UI.
-   **Utilities**:
    -   `pypdf`: PDF parsing.
    -   `beautifulsoup4`: Web scraping.
    -   `python-dotenv`: Environment variable management.

## Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/Terry-Mathew/Digital-Twin.git
    cd Digital-Twin
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment**
    Create a `.env` file in the root directory:
    ```ini
    # OpenRouter (Primary Model)
    OPENROUTER_API_KEY=sk-or-v1-...

    # Bytez (Backup Model)
    BYTEZ_KEY=...

    # Notifications (Pushover)
    PUSHOVER_USER=...
    PUSHOVER_TOKEN=...
    ```

4.  **Run the Application**
    ```bash
    python app.py
    ```
    The Gradio interface will launch at `http://127.0.0.1:7860`.

## Project Structure

-   `app.py`: Main application logic (Bot class, Tool handling, UI).
-   `me/`: Directory containing personal data (`linkedin.pdf`, `summary.txt`).
-   `requirements.txt`: Python dependencies.