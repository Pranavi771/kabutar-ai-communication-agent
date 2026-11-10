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

### Pr
