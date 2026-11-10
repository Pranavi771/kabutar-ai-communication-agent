# 🕊️ Kabutar AI — Intelligent Communication Automation Agent

An LLM-powered communication automation system that transforms natural-language instructions into personalised messages and delivers them through WhatsApp or Email.

Built using Python, Flask, Groq LLMs, Selenium and SMTP.

## Overview

Kabutar AI is a communication automation agent designed to simplify everyday messaging.

Instead of manually composing messages, users can provide casual natural-language instructions such as:

- "Tell Rahul I'll be 15 minutes late."
- "Email my professor requesting an appointment."
- "Send Priya a reminder about tomorrow's meeting."

The system interprets the instruction using a Large Language Model (LLM), resolves the selected recipient from a locally stored contact book, and executes the message delivery through the selected communication platform.

## Key Features

- **Natural Language Processing:** Converts informal instructions into contextually appropriate messages using an LLM.
- **WhatsApp Automation:** Sends messages through WhatsApp Web using Selenium.
- **Email Automation:** Sends emails using Python's SMTP functionality.
- **Contact Management:** Supports adding, retrieving and deleting locally stored contacts.
- **Persistent Browser Session:** Reuses a Chrome profile and Selenium browser session for WhatsApp automation.
- **Real-Time Progress Updates:** Uses Server-Sent Events (SSE) to stream execution status to the web interface.
- **Centralised Agent Architecture:** Keeps LLM, contact resolution and communication logic inside a shared core module.

## System Architecture

```text
             USER INSTRUCTION
                    |
                    v
             FLASK WEB SERVER
                    |
                    v
             AGENT CORE MODULE
                    |
                    v
              GROQ LLM API
                    |
                    v
          NATURAL LANGUAGE MESSAGE
                    |
                    v
            CONTACT RESOLUTION
             (Local JSON Store)
                    |
             +------+------+
             |             |
             v             v
         WHATSAPP        EMAIL
         SELENIUM        SMTP
             |             |
             v             v
       WHATSAPP WEB    EMAIL SERVER
             |             |
             +------+------+
                    |
                    v
             DELIVERY STATUS
                    |
                    v
               SSE UPDATES
```

## Technology Stack

| Technology | Application |
|---|---|
| Python | Core programming and agent logic |
| Flask | Backend web application and REST APIs |
| Groq API | LLM inference |
| OpenAI Python SDK | OpenAI-compatible API integration |
| Selenium | WhatsApp Web browser automation |
| ChromeDriver | Browser control |
| smtplib | Email delivery |
| JSON | Local contact storage |
| Server-Sent Events | Real-time status communication |
| HTML, CSS, JavaScript | Web interface |

## Project Structure

```text
kabutar-ai-communication-agent/
│
├── static/
│   └── index.html
│
├── agent_core.py
├── server.py
├── diagnose_chrome.py
├── requirements.txt
├── .gitignore
├── README.md
└── .env.example
```

Runtime files such as `.env`, `contacts.json` and the persistent WhatsApp Chrome profile should remain local and must not be committed.

## How It Works

### 1. Instruction Processing

The user enters a natural-language instruction and selects a recipient and communication platform.

### 2. LLM-Based Message Generation

The Groq API processes the instruction and generates an appropriate message using structured tool calling.

### 3. Contact Resolution

The agent retrieves the recipient's phone number or email address from the locally stored contact database.

Contact details are resolved locally and are not included in the LLM prompt.

### 4. Message Delivery

- WhatsApp messages are delivered through a persistent Selenium-controlled Chrome session.
- Emails are delivered through SMTP using configured email credentials.

### 5. Real-Time Feedback

The Flask backend streams status events to the frontend using Server-Sent Events, allowing users to see the progress and final result.

Note: WhatsApp automation is a blocking operation. The current progress events indicate stages before and after the send operation rather than second-by-second browser activity.

## Installation and Setup

### Prerequisites

- Python 3.10 or later
- Google Chrome
- ChromeDriver support through Selenium
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

Create a `.env` file in the project root.

Example configuration:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@example.com
SMTP_PASS=your_app_password

WA_CHROME_PROFILE=.whatsapp_chrome_profile
```

Only configure the SMTP variables if you intend to use email functionality.

Never upload your actual `.env` file or credentials to GitHub.

### 5. Launch the application

```bash
python server.py
```

The application initialises the WhatsApp browser session and waits for authentication when necessary.

The Flask server runs locally at:

```text
http://127.0.0.1:5000
```

WhatsApp automation uses a visible Chrome window. Leave the mouse and keyboard alone while an automated send is running.

## Engineering Highlights

- Persistent Selenium browser-session management.
- Thread-safe WhatsApp automation using a threading lock.
- Structured LLM tool calling for message composition.
- Separation of application routing and agent business logic.
- Local contact resolution for privacy-conscious recipient handling.
- Asynchronous progress communication using Server-Sent Events.
- Environment-based configuration for API and email credentials.

## Security and Limitations

- Designed as a local, single-user application.
- The Flask server binds to `127.0.0.1` and is not intended for public exposure.
- Contact information and browser-session data should remain private.
- API credentials must be stored in environment variables.
- Browser automation depends on WhatsApp Web and its interface remaining compatible with the Selenium selectors.
- Message delivery depends on successful authentication and network availability.
- The current interface reports progress at defined stages, not continuously throughout browser execution.

## Future Improvements

- Add a message preview and explicit confirmation before sending.
- Improve input validation and API error handling.
- Introduce automated unit and integration tests.
- Add structured application logging.
- Improve browser-session recovery.
- Add stronger authentication and access controls before considering multi-user deployment.
- Improve delivery verification and retry handling.

## Author

**Pranavi Joshi**

B.Tech — Electronics & Communication Engineering (AIML)  
MIT World Peace University, Pune

GitHub: https://github.com/Pranavi771

---

*An engineering project exploring the integration of LLMs, browser automation and communication workflows.*
