from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import json
import os
import threading
import time
from webscrapper import scrape_rbi, save_to_local
from langchain_core.messages import HumanMessage, AIMessage
from vectorizer import process_and_store_pdf, query_collection, get_collection_name
from langchain_ollama.chat_models import ChatOllama
from notifications import send_update_notification
from dotenv import load_dotenv
from sqlconnector import db  # Import the database connector

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize database connection and tables
try:
    print("Initializing database connection...")
    if db.connect():
        print("Database connection established")
        # Explicitly create tables
        db.create_tables()
        print("Database tables created/verified")
except Exception as e:
    print(f"❌ Error initializing database: {str(e)}")

# Initialize Ollama LLM
llm = ChatOllama(
    model="llama3.2:3b",
    base_url="http://localhost:11434",
    temperature=0.7
)

# Global variable to track when we last scraped
last_scrape_time = 0
SCRAPE_INTERVAL = 300  # 5 minutes in seconds

def load_rbi_updates():
    """Load RBI updates from the JSON file"""
    try:
        if os.path.exists('rbi_press_releases.json'):
            with open('rbi_press_releases.json', 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading RBI updates: {str(e)}")
        return []

def background_scraper():
    """Background task to continuously scrape RBI website"""
    global last_scrape_time
    while True:
        try:
            print("🔍 Checking for new press releases...")
            new_entries = scrape_rbi()
            if new_entries:
                print(f"✅ Found {len(new_entries)} new press release(s). Saving...")
                save_to_local(new_entries)
                # Send notifications for new updates
                send_update_notification(new_entries)
            last_scrape_time = datetime.now().timestamp()
            time.sleep(SCRAPE_INTERVAL)
        except Exception as e:
            print(f"Error in background scraper: {str(e)}")
            time.sleep(60)  # Wait a minute before retrying if there's an error

def check_for_updates():
    """Check for new updates and return them"""
    global last_scrape_time
    current_time = datetime.now().timestamp()
    
    # If it's been more than 5 minutes since last scrape, scrape now
    if current_time - last_scrape_time > SCRAPE_INTERVAL:
        try:
            new_entries = scrape_rbi()
            if new_entries:
                save_to_local(new_entries)
                # Send notifications for new updates
                send_update_notification(new_entries)
            last_scrape_time = current_time
        except Exception as e:
            print(f"Error checking for updates: {str(e)}")

@app.route('/updates', methods=['GET'])
def get_updates():
    """
    Route to fetch RBI press release updates
    Returns a list of updates with their details
    """
    try:
        # Check for new updates before returning
        check_for_updates()
        
        # Get the latest data
        updates = load_rbi_updates()
        return jsonify({
            "status": "success",
            "updates": updates
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to fetch updates: {str(e)}"
        }), 500

@app.route('/vectorize', methods=['POST'])
def vectorize_document():
    """
    Process and store a document in ChromaDB when user clicks Pull & Chat
    """
    try:
        data = request.json
        doc_id = data.get('doc_id')
        pdf_link = data.get('pdf_link')
        
        if not doc_id or not pdf_link:
            return jsonify({
                'status': 'error',
                'message': 'Missing doc_id or pdf_link'
            }), 400
        
        # Process and store the document using doc_id as collection name
        collection_name = process_and_store_pdf(pdf_link=pdf_link, doc_id=doc_id)
        
        return jsonify({
            'status': 'success',
            'message': 'Document processed and stored successfully'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to process document: {str(e)}'
        }), 500

@app.route('/chat', methods=['POST'])
def chat():
    """
    Handle chat interactions with the LLM and store chat history
    """
    try:
        print("\n" + "="*50)
        print("� POST /chat endpoint called")
        print("⏰ Timestamp:", datetime.now().isoformat())
        
        data = request.json
        print(f"📝 Received request data:")
        print(json.dumps(data, indent=2))

        if not data or 'message' not in data:
            print("❌ Error: No message provided in request")
            return jsonify({
                'status': 'error',
                'message': 'No message provided'
            }), 400
            
        user_message = data['message']
        doc_id = data.get('doc_id')
        user_id = data.get('user_id', 'default_user')  # Use a default user if not provided
        
        print("\n📨 Message Details:")
        print(f"� User ID: {user_id}")
        print(f"💬 Message: {user_message}")
        print(f"� Document ID: {doc_id}")
        print("-"*30)
        
        if not doc_id:
            print("❌ Error: No doc_id provided")
            return jsonify({
                'status': 'error',
                'message': 'No doc_id provided'
            }), 400

        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            db.connect()
        print("\n💾 Database Operations:")
        # Store user message
        try:
            db.save_message(user_id, "user", user_message)
            print(f"✅ Stored user message for {user_id}")
            print(f"   Type: user")
            print(f"   Content: {user_message[:100]}...")
        except Exception as e:
            print(f"❌ Error storing user message: {str(e)}")
            raise
        
        # Get relevant context from ChromaDB using doc_id as collection name
        print("\n🔍 Retrieving context from ChromaDB:")
        collection_name = get_collection_name(doc_id)
        print(f"📚 Using collection: {collection_name}")
        try:
            results = query_collection(
                collection_name=collection_name,
                query=user_message,
                n_results=3
            )
            context = "\n\n".join(results["documents"][0])
            
        except Exception as e:
            print(f"❌ Error retrieving context: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'Error retrieving document context: {str(e)}'
            }), 500

        try:
            prompt = f"""Based on the following context, please answer the user's question.
            If the answer cannot be found in the context, say so.

            Context:
            {context}

            User Question: {user_message}"""
            
            response = llm.invoke(prompt)
            response_content = response.content            # Store AI response
            print("\n💾 Storing AI response:")
            try:
                db.save_message(user_id, "assistant", response_content)
                print(f"✅ Stored AI response for {user_id}")
                print(f"   Type: assistant")
                print(f"   Content: {response_content[:100]}...")
            except Exception as e:
                print(f"❌ Error storing AI response: {str(e)}")
                raise

            # Get chat history for the user
            print("\n📚 Fetching recent chat history:")
            chat_history = db.get_user_chat_history(user_id, limit=10)  # Get last 10 messages
            print(f"✅ Retrieved {len(chat_history)} recent messages")
            print("="*50)

            return jsonify({
                'status': 'success',
                'response': {
                    'content': response_content,
                    'context': context,
                    'chat_history': chat_history
                }
            })
        except Exception as e:
            print(f"❌ Error generating AI response: {str(e)}")
            import traceback
            print(f"Detailed error: {traceback.format_exc()}")
            return jsonify({
                'status': 'error',
                'message': f'Error generating response: {str(e)}'
            }), 500
            
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        print(f"Detailed error: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get response: {str(e)}'
        }), 500

@app.route('/getchats', methods=['GET'])
def get_chat_history():
    """
    Get chat history for a user
    Returns all previous chats between the user and AI
    """
    try:
        print("\n" + "="*50)
        print("📱 GET /getchats endpoint called")
        
        # Get user_id from query parameters
        user_id = request.args.get('user_id', 'default_user')
        print(f"� User ID from request: {user_id}")
        
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            print("🔄 Reconnecting to database...")
            db.connect()
            print("✅ Database connection established")
        
        # Get chat history for the user (all messages)
        print(f"🔍 Fetching chat history for user: {user_id}")
        chat_history = db.get_user_chat_history(user_id, limit=100)  # Get last 100 messages
        print(f"📊 Found {len(chat_history)} messages in history")
        
        # Format the chat history for the response
        formatted_history = []
        for msg in chat_history:
            formatted_message = {
                'role': msg['message_type'],
                'content': msg['content'],
                'timestamp': msg['timestamp'].isoformat() if msg['timestamp'] else None
            }
            formatted_history.append(formatted_message)
            print(f"💬 Message: {msg['message_type']} at {msg['timestamp']}: {msg['content'][:50]}...")
        
        print(f"✅ Successfully formatted {len(formatted_history)} messages")
        print("="*50)
          # Format messages to match frontend expectations
        messages = []
        for msg in formatted_history:
            messages.append({
                'content': msg['content'],
                'message_type': msg['role'],  # Convert role back to message_type
                'isUser': msg['role'] == 'user'  # Add isUser flag
            })
        
        print(f"🔄 Sending {len(messages)} formatted messages to frontend")
        
        return jsonify({
            'status': 'success',
            'messages': messages  # Changed to 'messages' to match frontend expectation
        })
        
    except Exception as e:
        print(f"❌ Error retrieving chat history: {str(e)}")
        import traceback
        print(f"Detailed error: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve chat history: {str(e)}'
        }), 500
        

if __name__ == '__main__':
    import time
    # Start the background scraper in a separate thread
    scraper_thread = threading.Thread(target=background_scraper, daemon=True)
    scraper_thread.start()
    
    # Run the Flask app
    app.run(debug=True, port=5000)