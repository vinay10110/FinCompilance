# FinCompilance - RBI Document Analysis Assistant

An AI-powered tool that helps users analyze and interact with RBI (Reserve Bank of India) documents and press releases. The application provides real-time updates, document analysis, and an interactive chat interface to query document contents.

## Features

- **Real-time RBI Updates**: Automatically scrapes and monitors RBI press releases
- **Document Processing**: Processes and vectorizes PDF documents for intelligent querying
- **Interactive Chat Interface**: AI-powered chat interface to ask questions about RBI documents
- **User Authentication**: Secure user authentication using Clerk
- **Persistent Chat History**: Maintains chat history per user across sessions
- **Document Context**: Provides relevant document excerpts in responses
- **Modern UI**: Clean and responsive interface built with React and Chakra UI

## Tech Stack

### Backend
- Python (Flask)
- LangChain with Ollama LLM
- MySQL for chat history storage
- ChromaDB for document vector storage

### Frontend
- React.js
- Chakra UI
- Clerk Authentication
- Vite

## Setup

### Prerequisites
- Python 3.11 or higher
- Node.js and npm
- MySQL Server
- Ollama with llama3.2:3b model

### Backend Setup
1. Clone the repository
2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
3. Install Python dependencies:
```bash
pip install -r requirements.txt
```
4. Set up your environment variables in `.env`
5. Start the Flask server:
```bash
python app.py
```

### Frontend Setup
1. Navigate to the client directory:
```bash
cd client
```
2. Install dependencies:
```bash
npm install
```
3. Start the development server:
```bash
npm run dev
```

## Project Structure

```
FinCompilance/
├── app.py                 # Main Flask application
├── Agentic_rag.py        # RAG implementation
├── vectorizer.py         # Document vectorization
├── sqlconnector.py       # Database operations
├── webscrapper.py        # RBI website scraping
├── notifications.py      # Update notifications
├── requirements.txt      # Python dependencies
├── client/              # Frontend React application
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.jsx
│   │   │   ├── Navigation.jsx
│   │   │   └── Sidebar.jsx
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
└── chroma_db/           # Vector database storage
```

## Features in Detail

### Document Analysis
- Automatically scrapes RBI press releases
- Processes PDF documents into searchable vectors
- Maintains document context for accurate responses

### Chat Interface
- Real-time AI responses with document context
- Persistent chat history per user
- Document switching with preserved chat context
- System notifications for document changes

### User Experience
- Clean and intuitive interface
- Real-time updates
- Document context visualization
- Error handling and loading states

## Contributing

Feel free to submit issues and enhancement requests.

## License

[MIT License](LICENSE)
