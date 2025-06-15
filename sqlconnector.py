import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ChatDatabase:
    def __init__(self):
        self.config = {
            'host': 'localhost',
            'user': 'myuser',
            'password': 'March2016@',
            'database': 'vinay',
            'auth_plugin': 'mysql_native_password'
        }
        self.connection = None

    def connect(self):
        """Create a connection to MySQL database"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connection = mysql.connector.connect(**self.config)
                print("✅ Connected to MySQL database")
                self.create_tables()
            return True
        except Error as e:
            print(f"❌ Error connecting to MySQL: {e}")
            return False

    def disconnect(self):
        """Close the database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def create_tables(self):
        """Create chat history tables if they don't exist"""
        cursor = None
        try:
            cursor = self.connection.cursor()
            
            # Create a simple chat_history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(255),
                    message_type ENUM('user', 'assistant'),
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.connection.commit()
            print("✅ Chat history table ready")
            
        except Error as e:
            print(f"❌ Error creating table: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    def save_message(self, user_id, message_type, content):
        """Save a chat message to the database"""
        cursor = None
        try:
            cursor = self.connection.cursor()
            sql = """
                INSERT INTO chat_history (user_id, message_type, content)
                VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (user_id, message_type, content))
            self.connection.commit()
            return True
        except Error as e:
            print(f"❌ Error saving message: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    def get_user_chat_history(self, user_id, limit=50):
        """Get chat history for a user, defaults to last 50 messages"""
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            sql = """
                SELECT message_type, content, timestamp
                FROM chat_history
                WHERE user_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """
            cursor.execute(sql, (user_id, limit))
            return cursor.fetchall()
        except Error as e:
            print(f"❌ Error fetching chat history: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def delete_user_chat_history(self, user_id):
        """Delete all chat history for a user"""
        cursor = None
        try:
            cursor = self.connection.cursor()
            sql = "DELETE FROM chat_history WHERE user_id = %s"
            cursor.execute(sql, (user_id,))
            self.connection.commit()
            return True
        except Error as e:
            print(f"❌ Error deleting chat history: {e}")
            return False
        finally:
            if cursor:
                cursor.close()


# Create a singleton instance
db = ChatDatabase()


# Example usage
if __name__ == "__main__":
    try:
        if db.connect():
            # Test saving messages
            user_id = "user123"
            
            print("\nTesting chat operations:")
            
            print("1. Saving chat messages...")
            db.save_message(user_id, "user", "Hello! What can you help me with?")
            db.save_message(user_id, "assistant", "I can help you with financial compliance questions!")
            db.save_message(user_id, "user", "Great, thank you!")
            
            print("2. Retrieving chat history...")
            chat_history = db.get_user_chat_history(user_id)
            for msg in chat_history:
                print(f"[{msg['message_type']}]: {msg['content']}")
            
            print("\n✅ All operations completed successfully!")
            
    except Error as e:
        print(f"❌ Error during testing: {e}")
    finally:
        db.disconnect()