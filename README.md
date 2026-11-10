# 🕊️ Kabutar AI — Intelligent Communication Automation Agent

An LLM-powered communication automation application that transforms natural-language instructions into personalised messages and executes them through WhatsApp Web or Email.

**Built with:** Python · Flask · Groq LLM · Selenium · SMTP · JavaScript

## Overview

Kabutar AI is an AI-assisted communication agent designed to simplify everyday messaging.

Users can provide instructions in natural language, such as:

- "Tell Rahul I'll be 15 minutes late."
- "Email my professor requesting an appointment."
- "Send Priya a reminder about tomorrow's meeting."

The application uses a Large Language Model to interpret the instruction and compose a message. It then retrieves the selected recipient's contact information from a local JSON contact book and executes the selected communication workflow.

## Features

- **Natural-language message composition:** Converts casual instructions into natural, contextually appropriate messages.
- **WhatsApp automation:** Uses Selenium to interact with WhatsApp Web through a persistent Chrome session.
- **Email automation:** Uses Python's SMTP library to send emails.
- **Contact management:** Add, retrieve and delete contacts through the web interface.
- **Platform selection:** Choose between WhatsApp and Email.
- **Real-time progress notifications:** Streams execution-stage updates through Server-Sent Events (SSE).
- **Modular architecture:** Separates frontend, Flask routing and core agent logic.

## System Architecture

```text
             USER INSTRUCTION
                    |
                    v
             HTML / JS FRONTEND
                    |
                    v
               FLASK SERVER
                    |
                    v
              AGENT CORE
                    |
                    v
              GROQ LLM API
                    |
                    v
          MESSAGE COMPOSITION
                    |
                    v
            CONTACT RESOLUTION
              (Local JSON)
                    |
              +-----+-----+
              |           |
              v           v
           WHATSAPP     EMAIL
           SELENIUM     SMTP
              |           |
              v           v
         WHATSAPP WEB  SMTP SERVER
              |           |
              +-----+-----+
                    |
                    v
             EXECUTION RESULT
                    |
                    v
              SSE UPDATES
                    |
                    v
             FRONTEND STATUS
```

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Flask | Backend and HTTP APIs |
| Groq API | LLM inference |
| OpenAI Python SDK | Groq API integration |
| Selenium | Browser automation |
| Google Chrome | WhatsApp Web interaction |
| smtplib | Email communication |
| HTML, CSS, JavaScript | Web interface |
| Server-Sent Events | Live progress updates |
| JSON | Local contact management |
| python-dotenv | Environment configuration |

## Application Workflow

### 1. User Input

The user selects a communication platform and recipient, then enters a natural-language instruction.

### 2. Message Composition

The backend sends the instruction to the Groq LLM API using structured function calling.

The model generates the message content and an optional email subject.

### 3. Contact Resolution

The application retrieves the relevant phone number or email address from its local JSON contact store.

Contact details are not included in the LLM message-composition request.

### 4. Communication Execution

**WhatsApp**
- Opens or reuses a persistent Selenium-controlled Chrome session.
- Navigates to the selected recipient's WhatsApp chat.
- Enters the generated message and submits it.

**Email**
- Uses SMTP authentication.
- Constructs an email with a subject and message body.
- Submits the email through the configured SMTP server.

### 5. Real-Time Feedback

The Flask backend streams status events using SSE. The frontend displays progress notifications and the resulting success or failure message.

The current progress events indicate execution stages rather than continuous browser-level progress.

## Repository Structure

```text
kabutar-ai-communication-agent/
│
├── static/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── pigeon.png        # If included
│
├── agent_core.py
├── server.py
├── diagnose_chrome.py
├── requirements.txt
├── .gitignore
├── README.md
└── .env.example
```

Runtime data such as `.env`, `contacts.json` and the persistent Chrome profile should remain local and excluded from version control.

## Installation

### Prerequisites

- Python 3.10 or later
- Google Chrome
- Selenium-compatible browser driver support
- Groq API key
- SMTP-enabled email account for email functionality

### 1. Clone the repository

```bash
git clone https://github.com/Pranavi771/kabutar-ai-communication-agent.git

cd kabutar-ai-communication-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@example.com
SMTP_PASS=your_email_app_password

WA_CHROME_PROFILE=.whatsapp_chrome_profile
```

Configure SMTP credentials only if you intend to use email functionality.

Never commit actual API keys, passwords or personal contact information.

### 5. Run the application

```bash
python server.py
```

Open the local application:

```text
http://127.0.0.1:5000
```

On first use, scan the WhatsApp Web QR code if prompted.

The application uses a visible Chrome browser window during WhatsApp automation.

## Engineering Highlights

- Structured LLM function calling for natural-language message generation.
- Persistent Selenium browser-session management.
- Thread-safe WhatsApp automation using a threading lock.
- REST endpoints for contact management.
- Server-Sent Events for live frontend notifications.
- Separation of Flask routing and shared agent logic.
- Local contact resolution and environment-based configuration.

## Security and Limitations

- Designed as a local, single-user application.
- Flask binds to `127.0.0.1`; public deployment is not supported by the current configuration.
- Contact records and browser session data should remain private.
- Credentials must be stored outside version control.
- WhatsApp automation depends on WhatsApp Web and its page structure.
- SMTP delivery depends on valid credentials and network availability.
- The current application reports the result of its automation operation; this should not be interpreted as independent confirmation of recipient receipt or reading.

## Future Enhancements

- Add a message preview and explicit send confirmation.
- Improve request validation and error handling.
- Replace GET-based message submission with POST-based streaming.
- Add automated tests for contact management and message composition.
- Improve structured logging and browser-session recovery.
- Add authentication and access controls before supporting multiple users.
- Introduce stronger delivery-status verification.

## Author

**Pranavi Joshi**

B.Tech — Electronics & Communication Engineering (AIML)  
MIT World Peace University, Pune

[GitHub Profile](https://github.com/Pranavi771)

---

*An engineering project exploring the integration of Large Language Models, browser automation and communication workflows.*
