# 🤖 Doraemon – Your Personal Family AI Assistant

A personalized AI assistant designed to make everyday conversations smarter, simpler and more helpful.

## 🌟 About the Project

Doraemon is a personalized, family-oriented AI assistant built to provide intelligent conversations, contextual understanding and useful everyday assistance.

The idea is to create an AI that goes beyond a traditional chatbot by maintaining a consistent personality, remembering useful information about users and communicating naturally in multiple languages.

Doraemon primarily uses a locally hosted AI model for conversations while aiming to integrate online capabilities for accessing current information, such as today's news, weather, recent events and other real-time queries.

The goal is to combine the privacy and control of local AI with the knowledge and accessibility of online services.

## 🎯 Project Vision

To develop an intelligent family assistant that:

- Understands users and their conversational context.
- Remembers useful personal information.
- Communicates naturally in English, Hindi and Hinglish.
- Provides helpful and relevant everyday assistance.
- Accesses current information when required.
- Maintains a friendly, consistent and personalized personality.
- Combines local AI processing with online capabilities.

## ✨ Key Features

### 1. Personalized AI Personality

- Friendly, supportive and conversational behaviour.
- Natural humour and gentle teasing.
- Practical suggestions and problem-solving.
- Consistent assistant identity.

### 2. Multilingual Communication

- Supports English, Hindi and Hinglish.
- Adapts responses according to the user's language.
- Supports language transitions within conversations.
- Maintains appropriate Hindi and Hinglish scripts.

### 3. Conversation Memory

- Maintains previous conversation context.
- Supports contextual follow-up questions.
- Uses stored personal information to provide personalized responses.

### 4. Current Information Access

- Designed to retrieve up-to-date information through online services.
- Can be extended to answer questions about current events, weather, news and recent developments.
- Combines local model capabilities with external information sources.

### 5. Hybrid AI Architecture

- Uses a locally hosted language model for regular conversations.
- Can connect to online APIs and services when current information is required.
- Aims to reduce unnecessary dependence on external AI services.

## 🛠️ Technology Stack

| Component | Technology |
| --- | --- |
| Programming Language | Python |
| AI Model | Qwen3 4B |
| Model Runtime | Ollama |
| Backend | FastAPI |
| HTTP Communication | HTTPX |
| Database | SQLite |
| Frontend | HTML, CSS, JavaScript |
| Model Format | GGUF (Q4_K_M) |

## 🏗️ Project Architecture

The planned system follows this general workflow:

1. User Interface: Accepts user messages.
2. Backend (FastAPI): Processes requests and manages conversations.
3. Memory System: Retrieves relevant personal memories and conversation history.
4. AI Engine: Sends instructions and messages to the local language model.
5. Online Information Layer: Connects to suitable external APIs or information sources when real-time information is needed.
6. Response Generation: Combines relevant information and generates the final response.

## 📍 Development Status

| Component | Status |
| --- | --- |
| Local Qwen3 model setup | Completed |
| Custom Doraemon model | Created |
| FastAPI integration | Implemented |
| Personality configuration | Implemented |
| Conversation history | Implemented |
| Personal memory context | Implemented |
| Multilingual instructions | Implemented |
| Reliable language transitions | In progress |
| Real-time information integration | Planned |
| Model fine-tuning | Planned |
| Hybrid AI capabilities | In development |

## 🚀 Future Roadmap

- Improve language consistency and response accuracy.
- Develop a better long-term memory system.
- Integrate real-time information retrieval.
- Explore model fine-tuning for personalized behaviour.
- Add more family-oriented features.
- Improve response speed and overall performance.
- Expand integrations with useful online services.
- Improve privacy and security controls.

## 🔐 Privacy & Accessibility

Doraemon aims to prioritize user privacy by keeping regular AI processing and personal conversation data on the local system wherever possible.

Online services may be used when a task requires current information or external capabilities.

The long-term objective is to give users greater control over their personal information while maintaining access to useful online knowledge.

## 📜 License

This project is intended to use the Apache License 2.0.

See the "LICENSE" file for details.

## 💡 The Idea Behind Doraemon

Doraemon is not just about answering questions. It is about building an assistant that understands context, remembers what matters, communicates naturally and helps people in their everyday lives.

Local intelligence. Connected knowledge. Personalized assistance.
