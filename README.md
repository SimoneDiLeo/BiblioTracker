# BiblioTracker

BiblioTracker is a research information system.

## Project Structure

The project is organized into two main parts:

-   **`frontend/`**: Contains the user interface components.
    -   `templates/`: HTML files.
    -   `static/`: CSS, JavaScript, and other static assets.
-   **`api/`, `services/`, `database/`, etc.** (Python modules): These directories form the backend of the application, providing APIs and business logic.
-   **`main.py`**: The main FastAPI application file that serves both the frontend and the backend APIs.

## Running the Application

To run the application, you typically need to have Python and pip installed.

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Run the FastAPI server:**
    ```bash
    uvicorn main:app --reload
    ```
    The application will usually be available at `http://127.0.0.1:8000`.
