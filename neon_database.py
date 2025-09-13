# db.py
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv
load_dotenv()
class Database:
    def __init__(self):
        self.connection = None

    def connect(self):
        if self.connection and not self.connection.closed:
            return self.connection

        self.connection = psycopg2.connect(
            host=os.getenv("PGHOST"),
            dbname=os.getenv("PGDATABASE"),
            user=os.getenv("PGUSER"),
            password=os.getenv("PGPASSWORD"),
            sslmode=os.getenv("PGSSLMODE", "require")
        )
        self.connection.autocommit = False
        return self.connection

    def save_message(self, user_id, role, content):
        conn = self.connect()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO chat_messages (user_id, role, content, created_at)
                    VALUES (%s, %s, %s, NOW())
                """, (user_id, role, content))
                conn.commit()
        except Exception as e:
            print(f"❌ Error saving message: {e}")
            conn.rollback()
            raise

    def get_user_chat_history(self, user_id, limit=10):
        conn = self.connect()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT role, content, created_at
                FROM chat_messages
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (user_id, limit))
            return [dict(row) for row in cur.fetchall()]

    def save_press_release(self, entry: dict):
        conn = self.connect()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO press_releases
                (title, press_release_link, pdf_link, date_published, is_new, doc_id, date_scraped)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    entry["title"],
                    entry["press_release_link"],
                    entry["pdf_link"],
                    entry["date_published"],
                    entry["is_new"],
                    entry["doc_id"],
                    entry["date_scraped"],
                ),
            )
        conn.commit()
    def get_existing_links(self):
        conn = self.connect()
        with conn.cursor() as cur:
            cur.execute("SELECT press_release_link FROM press_releases")
            # normalize: strip + lowercase
            links = {row[0].strip().lower() for row in cur.fetchall() if row[0]}
            return links
    def get_latest_press_releases(self, limit=20):
        conn = self.connect()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT doc_id, title, press_release_link, pdf_link, date_published, date_scraped, is_new
                FROM press_releases
                ORDER BY date_published DESC
                LIMIT %s
            """, (limit,))
            return [dict(row) for row in cur.fetchall()]

    def save_circular(self, entry):
        """Save a master circular into the database"""
        conn = self.connect()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                INSERT INTO rbi_circulars
                    (doc_id, category, title, pdf_link, date_published, date_scraped, is_new)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (doc_id) DO NOTHING
            """, (
                entry["doc_id"],
                entry["category"],
                entry["title"],
                entry["pdf_link"],
                entry["date_published"],
                entry["date_scraped"],
                entry["is_new"]
            ))
            conn.commit()
            print(f"✅ Saved circular: {entry['title'][:50]}...")
        except Exception as e:
            print(f"❌ Error saving circular to database: {e}")
            print(f"Entry data: {entry}")
            conn.rollback()
            raise


    def get_existing_circular_links(self):
        """Fetch existing circular PDF links (normalized)"""
        conn = self.connect()
        with conn.cursor() as cur:
            cur.execute("SELECT pdf_link FROM rbi_circulars")
            return {row[0].strip().lower() for row in cur.fetchall() if row[0]}

    def get_latest_circulars(self, limit=20):
        """Fetch the latest master circulars"""
        conn = self.connect()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT doc_id, category, title, pdf_link, date_published, date_scraped, is_new
                FROM rbi_circulars
                ORDER BY date_published DESC
                LIMIT %s
            """, (limit,))
            return [dict(row) for row in cur.fetchall()]

    # Workflow methods
    def create_workflow(self, user_id, name=None, description=None):
        """Create a new workflow"""
        conn = self.connect()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    INSERT INTO workflows (user_id, name, description, created_at)
                    VALUES (%s, %s, %s, NOW())
                    RETURNING *
                """, (user_id, name, description))
                conn.commit()
                return dict(cur.fetchone())
        except Exception as e:
            print(f"❌ Error creating workflow: {e}")
            conn.rollback()
            raise

    def add_document_to_workflow(self, workflow_id, doc_type, doc_id):
        """Add document to workflow with validation"""
        conn = self.connect()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Validate doc exists
                if doc_type == 'press_release':
                    cur.execute("SELECT 1 FROM press_releases WHERE id=%s", (doc_id,))
                else:
                    cur.execute("SELECT 1 FROM rbi_circulars WHERE id=%s", (doc_id,))
                if cur.fetchone() is None:
                    raise ValueError(f"{doc_type} with id={doc_id} does not exist")

                # Insert
                cur.execute("""
                    INSERT INTO workflow_documents (workflow_id, doc_type, doc_id, added_at)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (workflow_id, doc_type, doc_id) DO NOTHING
                    RETURNING *
                """, (workflow_id, doc_type, doc_id))
                conn.commit()
                result = cur.fetchone()
                return dict(result) if result else None
        except Exception as e:
            print(f"❌ Error adding document to workflow: {e}")
            print(f"Details - workflow_id: {workflow_id}, doc_type: {doc_type}, doc_id: {doc_id}")
            conn.rollback()
            raise


    def get_workflow_with_documents(self, workflow_id):
        """Get workflow with its linked documents"""
        conn = self.connect()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get workflow details
            cur.execute("""
                SELECT * FROM workflows WHERE id = %s
            """, (workflow_id,))
            workflow = cur.fetchone()
            
            if not workflow:
                return None
            
            # Get associated documents
            cur.execute("""
                SELECT * FROM workflow_documents WHERE workflow_id = %s
            """, (workflow_id,))
            documents = cur.fetchall()
            
            workflow_dict = dict(workflow)
            workflow_dict['documents'] = [dict(doc) for doc in documents]
            
            return workflow_dict

    def get_user_workflows(self, user_id, limit=50):
        """Get all workflows for a user"""
        conn = self.connect()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT * FROM workflows 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (user_id, limit))
            return [dict(row) for row in cur.fetchall()]

    def get_press_release_id_by_doc_id(self, doc_id):
        conn = self.connect()
        with conn.cursor() as cur:
            cur.execute("""SELECT id FROM press_releases WHERE doc_id = %s""", (doc_id,))
            result = cur.fetchone()
            return result[0] if result else None


    def get_circular_id_by_doc_id(self, doc_id):
        conn = self.connect()
        with conn.cursor() as cur:
            cur.execute("""SELECT id FROM rbi_circulars WHERE doc_id = %s""", (doc_id,))
            result = cur.fetchone()
            return result[0] if result else None

    def get_document_by_type_and_id(self, doc_type, doc_id):
        """Get document details by doc_type and database ID"""
        conn = self.connect()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            if doc_type == 'press_release':
                cur.execute("""
                    SELECT id, doc_id, title, press_release_link, pdf_link, date_published, date_scraped, is_new
                    FROM press_releases 
                    WHERE id = %s
                """, (doc_id,))
            elif doc_type == 'circular':
                cur.execute("""
                    SELECT id, doc_id, category, title, pdf_link, date_published, date_scraped, is_new
                    FROM rbi_circulars 
                    WHERE id = %s
                """, (doc_id,))
            else:
                return None
            
            result = cur.fetchone()
            return dict(result) if result else None

    # Workflow Chat Messages methods
    def save_workflow_chat_message(self, workflow_id, user_id, role, content, document_data=None):
        """Save a chat message for a specific workflow"""
        conn = self.connect()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    INSERT INTO workflow_chat_messages 
                    (workflow_id, user_id, role, content, document_data, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    RETURNING *
                """, (workflow_id, user_id, role, content, document_data))
                conn.commit()
                return dict(cur.fetchone())
        except Exception as e:
            print(f"❌ Error saving workflow chat message: {e}")
            conn.rollback()
            raise

    def get_workflow_chat_history(self, workflow_id, user_id, limit=50):
        """Get chat history for a specific workflow and user"""
        conn = self.connect()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT id, role, content, document_data, created_at
                FROM workflow_chat_messages
                WHERE workflow_id = %s AND user_id = %s
                ORDER BY created_at ASC
                LIMIT %s
            """, (workflow_id, user_id, limit))
            return [dict(row) for row in cur.fetchall()]

    def clear_workflow_chat_history(self, workflow_id, user_id):
        """Clear chat history for a specific workflow and user"""
        conn = self.connect()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM workflow_chat_messages
                    WHERE workflow_id = %s AND user_id = %s
                """, (workflow_id, user_id))
                conn.commit()
                return cur.rowcount
        except Exception as e:
            print(f"❌ Error clearing workflow chat history: {e}")
            conn.rollback()
            raise

    def remove_document_from_workflow(self, workflow_id, doc_type, doc_id):
        """Remove document from workflow"""
        conn = self.connect()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM workflow_documents 
                    WHERE workflow_id = %s AND doc_type = %s AND doc_id = %s
                """, (workflow_id, doc_type, doc_id))
                conn.commit()
                return cur.rowcount > 0
        except Exception as e:
            print(f"❌ Error removing document from workflow: {e}")
            conn.rollback()
            raise

    def delete_workflow(self, workflow_id, user_id):
        """Delete a workflow and all associated data"""
        conn = self.connect()
        try:
            with conn.cursor() as cur:
                # First verify the workflow belongs to the user
                cur.execute("""
                    SELECT id FROM workflows 
                    WHERE id = %s AND user_id = %s
                """, (workflow_id, user_id))
                
                if not cur.fetchone():
                    return False
                
                # Delete workflow (CASCADE will handle related records)
                cur.execute("""
                    DELETE FROM workflows 
                    WHERE id = %s AND user_id = %s
                """, (workflow_id, user_id))
                
                conn.commit()
                return cur.rowcount > 0
        except Exception as e:
            print(f"❌ Error deleting workflow: {e}")
            conn.rollback()
            raise


db = Database()