
# import os
# from flask_cors import CORS
# import logging
# from logging.handlers import RotatingFileHandler
# from datetime import datetime
# import config # Importing the simplified config.py
# import random
# from flask import Flask, request, jsonify, Response
# import requests
# import base64
# import json
# from openai import OpenAI
# import time
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from email.utils import formataddr
# import smtplib
# import mysql.connector
# from pymongo import MongoClient
# from pymongo.errors import PyMongoError, ConnectionFailure
# import threading
# from typing import List, Dict, Any, Optional, Tuple


# # -------------------- Setup Logging --------------------
# # CRITICAL: Remove all existing handlers from the root logger.
# for handler in logging.root.handlers[:]:
#     logging.root.removeHandler(handler)

# if not os.path.exists("logs"):
#     os.makedirs("logs")

# log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(module)s] %(message)s')

# file_handler = RotatingFileHandler('logs/app.log', maxBytes=5*1024*1024, backupCount=5)
# file_handler.setFormatter(log_formatter)
# file_handler.setLevel(logging.DEBUG)

# app_logger = logging.getLogger('app_logger')
# app_logger.setLevel(logging.DEBUG)
# app_logger.addHandler(file_handler)
# app_logger.propagate = False

# # Suppress verbose logging from external libraries
# logging.getLogger("pymongo").setLevel(logging.CRITICAL)
# logging.getLogger("requests").setLevel(logging.CRITICAL)
# logging.getLogger("urllib3").setLevel(logging.CRITICAL)
# logging.getLogger("httpx").setLevel(logging.CRITICAL)
# logging.getLogger("httpcore").setLevel(logging.CRITICAL)
# logging.getLogger("openai").setLevel(logging.CRITICAL)
# logging.getLogger("werkzeug").setLevel(logging.CRITICAL)
# logging.getLogger("werkzeug.access").setLevel(logging.CRITICAL)


# # -------------------- Initialize Flask --------------------
# app = Flask(__name__)
# CORS(app)

# # -------------------- MongoDB Configuration --------------------
# client = None
# db = None
# gd_collection = None
# try:
#     if not config.MONGO_URI:
#         app_logger.critical("MongoDB URI is not configured. Please check your .env file.")
#         raise ValueError("MongoDB URI is missing.")
#     client = MongoClient(config.MONGO_URI)
#     db = client[config.MONGO_DB_NAME]
#     gd_collection = db[config.MONGO_COLLECTION_NAME]
#     # Test connection
#     client.admin.command('ping') # Ping to verify connection
#     app_logger.info("MongoDB connection established.")
# except Exception as e:
#     app_logger.critical(f"Failed to connect to MongoDB. Check MONGO_URI, MONGO_DB_NAME, MONGO_COLLECTION_NAME in config.py/.env: {e}", exc_info=True)


# # Session lock for thread safety
# session_lock = threading.Lock()

# # In-memory session storage.
# exam_memory: Dict[str, Dict[str, Any]] = {}

# # -------------------- Global Token Usage Tracking --------------------
# GLOBAL_TOKEN_USAGE = 0

# # -------------------- API Clients --------------------
# qwen_client = None
# openai_client = None
# try:
#     if not config.QWEN_API_KEY:
#         app_logger.critical("QWEN_API_KEY is not configured. Qwen client will not be available.")
#     else:
#         qwen_client = OpenAI(
#             api_key=config.QWEN_API_KEY,
#             base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
#         )
    
#     if not config.OPENAI_API_KEY:
#         app_logger.critical("OPENAI_API_KEY is not configured. OpenAI client will not be available.")
#     else:
#         openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
    
#     if qwen_client and openai_client:
#         app_logger.info("AI clients initialized.")
#     else:
#         app_logger.warning("One or more AI clients could not be fully initialized due to missing API keys. Related features may fail.")

# except Exception as e:
#     app_logger.critical(f"Failed to initialize OpenAI/Qwen clients: {e}", exc_info=True)


# # -------------------- Database Functions --------------------
# def get_db_connection(database: str):
#     """Establish MySQL database connection."""
#     try:
#         if not all([config.MYSQL_HOST, config.MYSQL_USER, config.MYSQL_PASSWORD, database]):
#             app_logger.error(f"MySQL connection details for '{database}' are incomplete.")
#             return None
#         connection = mysql.connector.connect(
#             host=config.MYSQL_HOST,
#             user=config.MYSQL_USER,
#             password=config.MYSQL_PASSWORD,
#             database=database,
#             port=config.MYSQL_PORT
#         )
#         return connection
#     except mysql.connector.Error as e:
#         app_logger.error(f"MySQL connection error to '{database}': {e}", exc_info=True)
#         return None

# def close_mysql_connection(connection):
#     """Close MySQL connection."""
#     if connection:
#         connection.close()
#         app_logger.info("MySQL connection is closed")

# def get_user_details(user_id: str) -> Optional[Dict[str, str]]:
#     """Fetch user details from MySQL database."""
#     # Check if MySQL config is available
#     if not all([config.MYSQL_HOST, config.MYSQL_USER, config.MYSQL_PASSWORD, config.MYSQL_USER_DB_NAME]):
#         app_logger.error("MySQL configuration is incomplete. Cannot fetch user details.")
#         return None

#     connection = get_db_connection(database=config.MYSQL_USER_DB_NAME)
#     if not connection:
#         return None
#     try:
#         with connection.cursor(dictionary=True) as cursor:
#             # Convert user_id to int for MySQL query
#             try:
#                 user_id_int = int(user_id)
#             except ValueError:
#                 app_logger.error(f"Invalid user_id format '{user_id}' received for MySQL query. Must be an integer.")
#                 return None
            
#             query = "SELECT username, email FROM users WHERE id = %s AND status = 'verified'"
#             cursor.execute(query, (user_id_int,))
#             result = cursor.fetchone()
#             if result:
#                 return {'username': result['username'], 'email': result['email']}
#             app_logger.warning(f"No verified user found with ID: {user_id}")
#             return None
#     except mysql.connector.Error as e:
#         app_logger.error(f"MySQL query error for user_id {user_id}: {e}", exc_info=True)
#         return None
#     finally:
#         close_mysql_connection(connection)

# def generate_gd_topic() -> str:
#     """Pick a static group discussion topic from a predefined list."""
#     try:
#         gd_topics = [
#             "Impact of Social Media on Youth", "Is Technology Making Us More Isolated?",
#             "The Role of AI in Future Job Markets", "Environmental Sustainability: A Global Responsibility",
#             "Should Cryptocurrency Replace Traditional Currency?", "Work from Home: The Future of Work Culture",
#             "Education System in India: Challenges and Opportunities", "Women Empowerment and Gender Equality",
#             "The Influence of Western Culture on Indian Traditions", "Is Online Learning as Effective as Classroom Learning?",
#             "Role of Government in Promoting Startups", "Ethical Concerns of Data Privacy in the Digital Age",
#             "Climate Change: Myth or Reality?", "The Impact of Globalization on Local Businesses",
#             "Should Mental Health Be a Priority in the Workplace?", "The Rise of E-commerce: Boon or Bane for Small Businesses?",
#             "Importance of Soft Skills in Professional Growth", "Can Renewable Energy Replace Fossil Fuels?",
#             "The Pros and Cons of Universal Basic Income", "Does Social Media Promote Free Speech or Hate Speech?",
#             "The Future of Electric Vehicles in India", "Impact of Automation on Employment Opportunities",
#             "Healthcare Accessibility for All: A Dream or Reality?", "Is Multitasking an Efficient Way to Work?",
#             "The Role of Media in Shaping Public Opinion", "Should India Adopt a Uniform Civil Code?",
#             "The Importance of Emotional Intelligence in Leadership", "Cybersecurity Threats in the Digital Era",
#             "Urbanization: A Step Forward or a Step Backward?", "The Need for Financial Literacy in Schools",
#             "Is Automation the Future of Manufacturing?", "The Role of Engineers in Climate Change Mitigation",
#             "Can India Become a Global Leader in Technology?", "Importance of Research and Development in Engineering",
#             "How Relevant is Coding for All Engineers?", "Are Electric Vehicles the Future of Transportation?",
#             "The Impact of 5G Technology on Communication Systems", "Should Renewable Energy Be Prioritized Over Fossil Fuels?",
#             "How Can Blockchain Revolutionize the Tech Industry?", "Role of Engineers in Smart City Development",
#             "Is work-from-home more productive than working from the office for entry-level employees?",
#             "Should coding skills be mandatory for all graduates, regardless of specialization?",
#             "Are internships more valuable than academic grades for freshers entering the job market?",
#             "How can freshers bridge the gap between theoretical knowledge and practical skills required by the industry?",
#             "Is job-hopping beneficial or detrimental for career growth in the first five years?",
#             "Should campus placements focus more on aptitude or specialized technical skills?",
#             "The impact of artificial intelligence on entry-level jobs: threat or opportunity?",
#             "Are traditional degrees losing relevance with the rise of specialized certifications and boot camps?",
#             "Should soft skills training be a mandatory part of the college curriculum?",
#             "Is entrepreneurship a viable alternative to corporate jobs for fresh graduates?",
#             "The role of social media in professional branding for freshers",
#             "Should freshers prioritize job satisfaction or salary when choosing their first job?",
#             "Is relocating to metro cities essential for better career opportunities in India?",
#             "How can freshers adapt to rapidly changing technological landscapes in their fields?",
#             "The importance of extracurricular activities in developing workplace-ready skills",
#             "Should companies lower experience requirements to give more opportunities to freshers?",
#             "Are fresher training programs effective or just a way to justify lower starting salaries?",
#             "The impact of automation on entry-level positions across different industries",
#             "Should freshers focus on specialization or versatility in their early careers?",
#             "The ethics of unpaid internships: valuable experience or exploitation?",
#             "How can educational institutions better prepare students for the current job market?",
#             "The role of networking versus merit in securing first jobs for freshers",
#             "Are startups or established companies better for freshers’ career growth?",
#             "Is the gig economy a viable career path for fresh graduates?",
#             "Environmental sustainability in the workplace: responsibility of corporates or individuals?",
#             "Is Globalization Leading to Cultural Erosion?",
#             "Skill Development vs. Degree Education: What Matters More?",
#             "The Role of Startups in India’s Economic Growth",
#             "How to Tackle Unemployment in Developing Countries?",
#             "Should Capital Punishment Be Abolished?",
#             "Impact of COVID-19 on the Global Economy",
#             "Data Privacy: Are We Sacrificing Privacy for Convenience?",
#             "Is India Ready for Digital Currency?",
#             "Sustainability vs. Profit: How Should Businesses Balance?",
#             "What Is More Important in a Job: Money or Job Satisfaction?"
#         ]
#         chosen_topic = random.choice(gd_topics)
#         app_logger.info(f"Selected GD Topic: {chosen_topic}")
#         return chosen_topic
#     except Exception as e:
#         app_logger.error(f"Error selecting GD topic: {e}", exc_info=True)
#         return "The impact of technology on education in India"

# def generate_ai_response_average_speaker(topic: str, conversation: str, participant_name: str) -> Tuple[str, int]:
#     """Generate a short and natural spoken response considering the entire conversation."""
#     global GLOBAL_TOKEN_USAGE
#     if not qwen_client:
#         app_logger.error("Qwen client not initialized. Cannot generate AI response for average speaker.")
#         return f"{participant_name} encountered an issue responding (AI service unavailable).", 0
#     try:
#         messages = [
#             {
#                 "role": "system",
#                 "content": [
#                     {"type": "text", "text": (
#                         f"You are in a debate about the topic: '{topic}'. "
#                         "Analyze the conversation and respond naturally in 2 to 3 sentences. "
#                         "Keep it simple, relevant, and engaging."
#                     )}
#                 ]
#             },
#             {"role": "user", "content": [{"type": "text", "text": conversation.strip() if conversation else "Please start the discussion."}]},
#             {
#                 "role": "assistant",
#                 "content": [{"type": "text", "text": f"As {participant_name}, respond briefly but meaningfully."}]
#             }
#         ]
#         response = exponential_backoff_retry(
#             lambda: qwen_client.chat.completions.create(
#                 model="qwen-vl-max",
#                 messages=messages,
#                 max_tokens=150,
#                 temperature=0.7,
#                 top_p=0.9,
#                 presence_penalty=0.3,
#                 frequency_penalty=0.2
#             )
#         )
#         token_usage = response.usage.total_tokens
#         GLOBAL_TOKEN_USAGE += token_usage
#         app_logger.info(f"Tokens used for AI response (average speaker): {token_usage}, Total tokens used so far: {GLOBAL_TOKEN_USAGE}")
#         return response.choices[0].message.content.strip(), token_usage
#     except Exception as e:
#         app_logger.error(f"Error generating AI response for {participant_name}: {e}", exc_info=True)
#         return f"{participant_name} encountered an issue responding.", 0

# def generate_ai_response_advanced_speaker(topic: str, conversation_context: str, participant_name: str) -> Tuple[str, int]:
#     """Generate a concise AI response for an advanced speaker using OpenAI GPT-4 Mini."""
#     global GLOBAL_TOKEN_USAGE
#     if not openai_client:
#         app_logger.error("OpenAI client not initialized. Cannot generate AI response for advanced speaker.")
#         return f"{participant_name} encountered an issue responding (AI service unavailable).", 0
#     try:
#         system_message = (
#             f"You are participating in a formal debate on: '{topic}'. "
#             "Provide a single, insightful argument in 3-5 lines. Ensure it is clear, impactful, and avoids verbosity."
#         )
#         response = exponential_backoff_retry(
#             lambda: openai_client.chat.completions.create(
#                 model="gpt-4o-mini-2024-07-18",
#                 messages=[
#                     {"role": "system", "content": system_message},
#                     {"role": "user", "content": conversation_context},
#                     {"role": "assistant", "content": "Provide clear and thoughtful points."}
#                 ],
#                 max_tokens=150,
#                 temperature=0.6
#             )
#         )
#         token_usage = response.usage.total_tokens
#         GLOBAL_TOKEN_USAGE += token_usage
#         app_logger.info(f"Tokens used for AI response (advanced speaker): {token_usage}, Total tokens used so far: {GLOBAL_TOKEN_USAGE}")
#         return response.choices[0].message.content.strip(), token_usage
#     except Exception as e:
#         app_logger.error(f"Error generating AI response for {participant_name} (advanced speaker): {e}", exc_info=True)
#         return f"As {participant_name}, I believe digital detox is essential for mental well-being.", 0

# def generate_response_evaluation(responses: List[str], gd_topic: str) -> Dict[str, Any]:
#     """Evaluate the user's responses with 1-10 scale feedback using GPT-4 Mini.
#        Generates an evaluation for EACH user response provided."""
#     global GLOBAL_TOKEN_USAGE
#     if not openai_client:
#         app_logger.error("OpenAI client not initialized. Cannot generate evaluation.")
#         return {"error": "AI evaluation service unavailable."}
#     try:
#         # Simplified example for the prompt to guide the LLM on output format
#         single_example_evaluation_json = """
#         {
#             "response_id": 1,
#             "coherence": {"score": 7, "feedback": "The response was clear and flowed logically, demonstrating a good grasp of the argument."},
#             "engagement": {"score": 6, "feedback": "It showed good engagement with the topic, but could have built more directly on previous points."},
#             "overall_quality": {"score": 7, "feedback": "A solid contribution that added value to the discussion without being overly verbose."},
#             "relevance": {"score": 8, "feedback": "Directly addressed the topic and remained focused on the core arguments."}
#         }
#         """

#         prompt = f"""As an expert evaluator for group discussions, you must provide a concise evaluation for *EACH* of the following user responses using a 1-10 scoring scale.
#         Topic: '{gd_topic}'
        
#         Evaluation Criteria:
#         1-3: Poor - Off-topic, incoherent, or unoriginal.
#         4-6: Average - Partially relevant but lacks depth/clarity.
#         7-8: Good - Clear, relevant, and contributes meaningfully.
#         9-10: Excellent - Exceptionally insightful, original, and drives discussion.

#         You MUST generate a JSON array of evaluation objects. For EACH user response provided below, create a separate object in the 'evaluations' array. Each object MUST have a 'response_id' corresponding to its 1-based index in the 'User Responses' list.

#         Example of the EXACT JSON format for a SINGLE evaluation entry:
#         {single_example_evaluation_json}

#         Your final JSON output MUST contain an 'evaluations' array with one object for EVERY user response provided.

#         User Responses:
#         """
#         # Append all user responses to the prompt
#         prompt += '\n'.join(f'Response {i+1}: {response}' for i, response in enumerate(responses))
        
#         response = exponential_backoff_retry(
#             lambda: openai_client.chat.completions.create(
#                 model="gpt-4o-mini-2024-07-18",
#                 messages=[
#                     {"role": "system", "content": "You are an expert evaluator providing concise 1-10 scale feedback for each user response in a group discussion, in JSON format. Generate an evaluation object for *every* user response provided."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 max_tokens=config.LLM_EVALUATION_MAX_TOKENS + (len(responses) * config.LLM_TOKENS_PER_RESPONSE_EVALUATION),
#                 temperature=0.5,
#                 response_format={"type": "json_object"}
#             )
#         )
        
#         token_usage = response.usage.total_tokens
#         GLOBAL_TOKEN_USAGE += token_usage
#         app_logger.info(f"Tokens used for evaluation: {token_usage}, Total: {GLOBAL_TOKEN_USAGE}")
#         evaluation_data = json.loads(response.choices[0].message.content)

#         if len(evaluation_data.get('evaluations', [])) != len(responses):
#             app_logger.warning(f"LLM did not return evaluations for all {len(responses)} responses. Received {len(evaluation_data.get('evaluations', []))} evaluations for session '{gd_topic}'.")
            
#         return evaluation_data
#     except json.JSONDecodeError as e:
#         app_logger.error(f"JSON parsing error in evaluation: {str(e)}. Raw response: {response.choices[0].message.content if response else 'No response'}", exc_info=True)
#         return {"error": f"Failed to parse evaluation JSON: {str(e)}", "raw_llm_response": response.choices[0].message.content if response else 'No response'}
#     except Exception as e:
#         app_logger.error(f"Evaluation error: {str(e)}", exc_info=True)
#         return {"error": "Failed to generate evaluation"}

# def format_evaluation_html(evaluation: Dict[str, Any]) -> str:
#     """Format evaluations into a table structure, including summary scores."""
#     try:
#         if not evaluation or 'evaluations' not in evaluation:
#             return "<p>No evaluation data</p>"
        
#         html = """
#         <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
#             <thead>
#                 <tr>
#                     <th>Response ID</th>
#                     <th>Coherence (Score - Feedback)</th>
#                     <th>Engagement (Score - Feedback)</th>
#                     <th>Overall Quality (Score - Feedback)</th>
#                     <th>Relevance (Score - Feedback)</th>
#                 </tr>
#             </thead>
#             <tbody>
#         """
#         for eval_item in evaluation.get('evaluations', []):
#             response_id = eval_item.get('response_id', 'N/A')
#             coherence = eval_item.get('coherence', {'score': 'N/A', 'feedback': 'Missing'})
#             engagement = eval_item.get('engagement', {'score': 'N/A', 'feedback': 'Missing'})
#             overall_quality = eval_item.get('overall_quality', {'score': 'N/A', 'feedback': 'Missing'})
#             relevance = eval_item.get('relevance', {'score': 'N/A', 'feedback': 'Missing'})
#             html += f"""
#                 <tr>
#                     <td>{response_id}</td>
#                     <td>{coherence['score']} - {coherence['feedback']}</td>
#                     <td>{engagement['score']} - {engagement['feedback']}</td>
#                     <td>{overall_quality['score']} - {overall_quality['feedback']}</td>
#                     <td>{relevance['score']} - {relevance['feedback']}</td>
#                 </tr>
#             """
#         html += """
#             </tbody>
#         </table>
#         """
        
#         if 'summary_scores' in evaluation:
#             summary = evaluation['summary_scores']
#             html += f"""
#             <h3>Summary Scores:</h3>
#             <p><strong>Total Overall Quality Score:</strong> {summary.get('total_overall_quality_score', 'N/A')}</p>
#             <p><strong>Average Overall Quality Score:</strong> {summary.get('average_overall_quality_score', 'N/A')}</p>
#             """
        
#         return html
#     except Exception as e:
#         app_logger.error(f"Error formatting evaluation HTML: {str(e)}", exc_info=True)
#         return "<p>Error formatting evaluation data</p>"

# def send_feedback_email(session_data: Dict[str, Any]) -> bool:
#     """Sends the feedback email with structured HTML content in table format."""
#     try:
#         if not all([config.MAIL_USERNAME, config.MAIL_PASSWORD, config.SMTP_SERVER]):
#             app_logger.error("Email configuration is incomplete (username, password, or server missing). Cannot send feedback email.")
#             return False

#         if not session_data:
#             app_logger.error("Session data is empty for email.")
#             return False
#         user_name = session_data.get('user_name', 'User')
#         user_email = session_data.get('user_email')
#         gd_topic = session_data.get('gd_topic', 'No Topic')
#         user_responses = session_data.get('user_responses', [])
#         evaluation = session_data.get('evaluation', {})
#         session_id = session_data.get('sessionId', 'N/A') # Get session_id for logging

#         app_logger.debug(f"Preparing email for {user_email} (session {session_id}) with topic: {gd_topic}")

#         if not user_email:
#             app_logger.error(f"No email found in session data for session {session_id}.")
#             return False

#         msg = MIMEMultipart('alternative')
#         msg['From'] = formataddr(("AI Interviewer", config.MAIL_USERNAME))
#         msg['To'] = user_email
#         msg['Subject'] = "AI Interviewer Feedback"

#         html_content = f"""
#         <html>
#         <head>
#             <style>
#                 table {{ border-collapse: collapse; width: 100%; }}
#                 th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
#                 th {{ background-color: #f2f2f2; }}
#             </style>
#         </head>
#         <body>
#             <h2>AI Interviewer Feedback</h2>
#             <p>Dear {user_name},</p>
#             <h3>Topic:</h3>
#             <p>{gd_topic}</p>
#             <h3>Your Responses:</h3>
#             <ol>
#                 {''.join(f'<li>{resp}</li>' for resp in user_responses)}
#             </ol>
#             <h3>Evaluation:</h3>
#             {format_evaluation_html(evaluation)}
#             <p>Best regards,<br>AI Interviewer Team</p>
#         </body>
#         </html>
#         """

#         text_content = f"""
#         AI Interviewer Feedback

#         Dear {user_name},

#         Thank you for participating in the group discussion.

#         Topic: {gd_topic}

#         Your responses have been evaluated and detailed feedback is attached above.

#         Best regards,
#         AI Interviewer Team
#         """

#         msg.attach(MIMEText(text_content, 'plain'))
#         msg.attach(MIMEText(html_content, 'html'))

#          # --- MODIFICATION START ---
#         # Use smtplib.SMTP for STARTTLS on port 587
#         try:
#             with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT, timeout=10) as server:
#                 server.starttls() # Upgrade the connection to TLS
#                 server.login(config.MAIL_USERNAME, config.MAIL_PASSWORD)
#                 server.send_message(msg)
#             app_logger.info(f"Email sent successfully to: {user_email} for session {session_id} via STARTTLS.")
#             return True
#         except smtplib.SMTPException as e:
#             # Re-raise to be caught by the outer try-except for consistent logging
#             raise e 
#         # --- MODIFICATION END ---
#     except smtplib.SMTPAuthenticationError as e:
#         app_logger.error(f"SMTP Authentication Error for {user_email} (session {session_id}): {e}. Check MAIL_USERNAME and MAIL_PASSWORD.", exc_info=True)
#         return False
#     except smtplib.SMTPException as e:
#         app_logger.error(f"SMTP Error for {user_email} (session {session_id}): {str(e)}. Check SMTP_SERVER and SMTP_PORT.", exc_info=True)
#         return False
#     except Exception as e:
#         app_logger.error(f"Unexpected error in send_feedback_email for {user_email} (session {session_id}): {str(e)}", exc_info=True)
#         return False
    
# def exponential_backoff_retry(api_call, max_retries=3, initial_delay=1):
#     """Retry API calls with exponential backoff."""
#     for attempt in range(max_retries):
#         try:
#             return api_call()
#         except Exception as e:
#             if attempt < max_retries - 1:
#                 delay = initial_delay * (2 ** attempt)
#                 app_logger.warning(f"Error occurred (attempt {attempt+1}/{max_retries}). Retrying in {delay} seconds... Error: {e}")
#                 time.sleep(delay)
#             else:
#                 raise # Re-raise after max retries
#     raise Exception("Max retries exceeded.")


# # -------------------- API Endpoints --------------------
# @app.route('/group_discussion', methods=['POST'])
# def group_discussion():
#     """Handle the group discussion flow with AI participants."""
#     # Initialize variables for error logging context
#     session_id: str = "N/A"
#     user_id: str = "N/A"

#     try:
#         # Check if essential services are available at the start of the endpoint
#         if gd_collection is None:
#             return jsonify({"error": "Database service unavailable. Please check server logs."}), 503
#         if qwen_client is None or openai_client is None:
#             return jsonify({"error": "AI generation service unavailable. Please check server logs."}), 503

#         data = request.json
#         # user_input is the *current* input from the user for this request
#         current_user_input = data.get("response")
#         user_id_raw = data.get("userId")
#         session_id_raw = data.get("sessionId")

#         # --- SESSION_ID COERCION & VALIDATION ---
#         if session_id_raw is None:
#             app_logger.error("sessionId is required but was not provided in the request.")
#             return jsonify({"error": "sessionId is required."}), 400
#         session_id = str(session_id_raw) # Always coerce to string

#         # --- USER_ID COERCION & VALIDATION ---
#         if user_id_raw is None:
#             app_logger.error(f"userId is required but was not provided in the request for session {session_id}.")
#             return jsonify({"error": "userId is required."}), 400
#         user_id = str(user_id_raw) # Always coerce to string

#         user_details = get_user_details(user_id)
#         if not user_details:
#             app_logger.error(f"User details not found in the database for userId: {user_id} (session {session_id}).")
#             return jsonify({"error": "User not found or not verified."}), 400

#         user_email = user_details.get('email')
#         user_name = user_details.get('username', 'User')

#         app_logger.debug(f"Received request: user_id={user_id}, raw_sessionId={session_id_raw}, coerced_sessionId={session_id}, user_email={user_email}, current_user_input={current_user_input}")

#         # Acquire session lock for thread safety
#         with session_lock:
#             # --- New Session Start ---
#             if session_id not in exam_memory:
#                 gd_topic = generate_gd_topic()
#                 ai_participant_1_text, _ = generate_ai_response_average_speaker(gd_topic, "", "Participant 1")
#                 ai_participant_2_text, _ = generate_ai_response_advanced_speaker(gd_topic, "", "Participant 2")

#                 gd_topic = gd_topic.replace("**", "")
#                 ai_participant_1_text = ai_participant_1_text.replace("**", "")
#                 ai_participant_2_text = ai_participant_2_text.replace("**", "")

#                 initial_ai_responses_for_db = [
#                     {"participant_1": ai_participant_1_text},
#                     {"participant_2": ai_participant_2_text}
#                 ]

#                 new_gd_document = {
#                     "sessionId": session_id,
#                     "user_id": user_id,
#                     "user_email": user_email,
#                     "gd_topic": gd_topic,
#                     "start_time": datetime.now(),
#                     "conversation_history": [],
#                     "status": "in_progress"
#                 }
                
#                 try:
#                     insert_result = gd_collection.insert_one(new_gd_document)
#                 except PyMongoError as e:
#                     app_logger.error(f"MongoDB insert error for new session {session_id} (user {user_id}): {e}", exc_info=True)
#                     return jsonify({"error": "Failed to start new session due to database error."}), 500
                
#                 exam_memory[session_id] = { 
#                     "gd_topic": gd_topic,
#                     "start_time": datetime.now(),
#                     "turns": 0,
#                     "user_email": user_email,
#                     "user_id": user_id,
#                     "_mongo_id": insert_result.inserted_id,
#                     "pending_ai_responses_for_next_user_input": initial_ai_responses_for_db,
#                     "conversation_history_for_memory": []
#                 }

#                 app_logger.info(f"New session started: sessionId={session_id}, topic={gd_topic}, MongoDB _id={insert_result.inserted_id}. Initial AI responses pending user input.")

#                 return jsonify({
#                     "gd_topic": gd_topic,
#                     "ai_responses": {
#                         "participant_1": {"text": ai_participant_1_text},
#                         "participant_2": {"text": ai_participant_2_text}
#                     },
#                     "message": "AI participants have initiated the discussion. Please share your views."
#                 })

#             # --- Existing Session Logic ---
#             session_data = exam_memory[session_id] 
#             mongo_doc_id = session_data.get("_mongo_id")
#             if not mongo_doc_id:
#                  app_logger.error(f"MongoDB _id not found in memory for sessionId: {session_id}. Session state corrupted for user {user_id}.")
#                  return jsonify({"error": "Server error: Session state corrupted."}), 500

#             gd_topic = session_data["gd_topic"]
#             start_time = session_data["start_time"]
#             elapsed_time = (datetime.now() - start_time).total_seconds()

#             # --- Process current user input first, if any, before checking time limit for evaluation ---
#             # This ensures the last user input is always recorded and included in evaluation
#             if current_user_input and current_user_input.strip():
#                 pending_ai_responses = session_data.pop("pending_ai_responses_for_next_user_input", None)
#                 if not pending_ai_responses:
#                     app_logger.error(f"No pending AI responses found for sessionId={session_id} (user {user_id}) when user input arrived. Session state inconsistency.")
#                     return jsonify({"error": "Server error: No pending AI responses for current user input."}), 500

#                 current_turn_entry = {
#                     "ai_responses": pending_ai_responses,
#                     "user_input": current_user_input,
#                     "timestamp": datetime.now().isoformat()
#                 }
#                 session_data["conversation_history_for_memory"].append(current_turn_entry)

#                 try:
#                     gd_collection.update_one(
#                         {"_id": mongo_doc_id, "sessionId": session_id},
#                         {"$push": {"conversation_history": current_turn_entry}}
#                     )
#                     app_logger.debug(f"User input '{current_user_input[:50]}...' for session {session_id} stored.")
#                 except PyMongoError as e:
#                     app_logger.error(f"MongoDB update error for session {session_id} (user {user_id}) on user input: {e}", exc_info=True)
#                     return jsonify({"error": "Failed to save conversation history to database."}), 500
#             elif current_user_input is not None: # If user sent empty/whitespace, log it but don't add to history
#                 app_logger.warning(f"Received empty/whitespace user input for session {session_id} (user {user_id}). Not adding to history.")


#             # --- NOW Check Time Limit for Evaluation ---
#             if elapsed_time > config.GD_TIME_LIMIT_SECONDS:
#                 app_logger.info(f"Session {session_id} for user {user_id} time exceeded ({elapsed_time:.2f}s). Preparing feedback...")

#                 user_responses = [item["user_input"] for item in session_data["conversation_history_for_memory"] 
#                                   if "user_input" in item and item["user_input"] and item["user_input"].strip()]
                
#                 if not user_responses:
#                     app_logger.warning(f"No valid user responses found for evaluation for sessionId {session_id} (user {user_id}). Discussion ended before or without user input.")
#                     try:
#                         gd_collection.update_one(
#                             {"_id": mongo_doc_id, "sessionId": session_id},
#                             {
#                                 "$set": {
#                                     "end_time": datetime.now(),
#                                     "status": "completed",
#                                     "evaluation": {"evaluations": [], "summary_scores": {"total_overall_quality_score": 0, "average_overall_quality_score": 0}}
#                                 }
#                             }
#                         )
#                     except PyMongoError as e:
#                         app_logger.error(f"MongoDB update error for time-exceeded session {session_id} with no responses (user {user_id}): {e}", exc_info=True)
                    
#                     del exam_memory[session_id]
#                     return jsonify({
#                         "message": "Group discussion time is over. No user responses to evaluate.",
#                         "feedback": {"user_evaluation": {"evaluations": [], "summary_scores": {"total_overall_quality_score": 0, "average_overall_quality_score": 0}}},
#                         "email_status": "not_sent"
#                     }), 200

#                 user_evaluation = generate_response_evaluation(user_responses, gd_topic)
#                 app_logger.debug(f"Generated evaluation for session {session_id} (user {user_id}): {user_evaluation}")

#                 # Calculate and add summary scores
#                 total_overall_score = 0
#                 count_evaluations = 0
#                 if user_evaluation and 'evaluations' in user_evaluation:
#                     for eval_item in user_evaluation['evaluations']:
#                         if 'overall_quality' in eval_item and 'score' in eval_item['overall_quality']:
#                             try:
#                                 score = int(eval_item['overall_quality']['score'])
#                                 total_overall_score += score
#                                 count_evaluations += 1
#                             except ValueError:
#                                 app_logger.warning(f"Invalid 'overall_quality' score found for session {session_id} (user {user_id}): {eval_item['overall_quality']['score']}")
                    
#                 average_overall_score = round(total_overall_score / count_evaluations, 2) if count_evaluations > 0 else 0

#                 if user_evaluation and isinstance(user_evaluation, dict):
#                     user_evaluation['summary_scores'] = {
#                         'total_overall_quality_score': total_overall_score,
#                         'average_overall_quality_score': average_overall_score
#                     }
#                 else:
#                     user_evaluation = {"error": "Evaluation generation failed or returned invalid format."}

#                 email_data = {
#                     "user_name": user_name,
#                     "user_email": user_email,
#                     "gd_topic": gd_topic,
#                     "user_responses": user_responses,
#                     "evaluation": user_evaluation,
#                     "sessionId": session_id
#                 }

#                 email_sent = False
#                 max_retries = 3
#                 for attempt in range(max_retries):
#                     try:
#                         email_sent = send_feedback_email(email_data)
#                         if email_sent:
#                             app_logger.info(f"Email sent successfully to {user_email} for session {session_id} on attempt {attempt + 1}")
#                             break
#                         else:
#                             app_logger.warning(f"Email sending failed for session {session_id} on attempt {attempt + 1}")
#                             time.sleep(2 ** attempt)
#                     except Exception as e:
#                         app_logger.error(f"Email sending error for session {session_id} on attempt {attempt + 1}: {str(e)}", exc_info=True)
#                         if attempt == max_retries - 1:
#                             try:
#                                 gd_collection.update_one(
#                                     {"_id": mongo_doc_id, "sessionId": session_id},
#                                     {
#                                         "$set": {
#                                             "evaluation": user_evaluation,
#                                             "end_time": datetime.now(),
#                                             "status": "completed"
#                                         }
#                                     }
#                                 )
#                             except PyMongoError as mongo_err:
#                                 app_logger.error(f"MongoDB update error after email failure for session {session_id}: {mongo_err}", exc_info=True)
#                             del exam_memory[session_id]
#                             return jsonify({
#                                 "message": "Group discussion time is over.",
#                                 "feedback": {"user_evaluation": user_evaluation},
#                                 "error": "Failed to send email feedback"
#                             }), 500
#                         time.sleep(2 ** attempt)

#                 try:
#                     gd_collection.update_one(
#                         {"_id": mongo_doc_id, "sessionId": session_id},
#                         {
#                             "$set": {
#                                 "evaluation": user_evaluation,
#                                 "end_time": datetime.now(),
#                                 "status": "completed"
#                             }
#                         }
#                     )
#                 except PyMongoError as e:
#                     app_logger.error(f"MongoDB update error for completed session {session_id} (user {user_id}): {e}", exc_info=True)
#                     return jsonify({"error": "Failed to save final test results to database."}), 500

#                 del exam_memory[session_id]
#                 return jsonify({
#                     "message": "Group discussion time is over.",
#                     "feedback": {"user_evaluation": user_evaluation},
#                     "email_status": "sent" if email_sent else "failed"
#                 })

#             # --- Continue Discussion (if time limit not exceeded) ---
#             # Generate the *next* AI responses
#             # The current_user_input (if any) has already been processed and added to history.
#             conversation_context_lines = []
#             for item in session_data["conversation_history_for_memory"]:
#                 if item["ai_responses"]:
#                     for ai_resp_obj in item["ai_responses"]:
#                         for participant, text in ai_resp_obj.items():
#                             conversation_context_lines.append(f"{participant.replace('_', ' ').title()}: {text}")
#                 if item["user_input"]:
#                     conversation_context_lines.append(f"User: {item['user_input']}")
            
#             conversation_context = "\n".join(conversation_context_lines)

#             next_ai_participant_1_text, _ = generate_ai_response_average_speaker(
#                 gd_topic, conversation_context, "Participant 1"
#             )
#             next_ai_participant_2_text, _ = generate_ai_response_advanced_speaker(
#                 gd_topic, conversation_context, "Participant 2"
#             )

#             next_ai_responses_for_client = {
#                 "participant_1": {"text": next_ai_participant_1_text},
#                 "participant_2": {"text": next_ai_participant_2_text}
#             }

#             session_data["pending_ai_responses_for_next_user_input"] = [
#                 {"participant_1": next_ai_participant_1_text},
#                 {"participant_2": next_ai_participant_2_text}
#             ]
            
#             session_data["turns"] += 1
#             elapsed_time = (datetime.now() - start_time).total_seconds()

#             return jsonify({
#                 "gd_topic": gd_topic,
#                 "ai_responses": next_ai_responses_for_client,
#                 "message": "Responses recorded. AI participants have responded. Please continue the discussion.",
#                 "elapsed_time": elapsed_time
#             })

#     except Exception as e:
#         app_logger.critical(f"Critical error in group_discussion for sessionId {session_id} (user {user_id}): {str(e)}", exc_info=True)
#         return jsonify({"error": "An internal server error occurred.", "details": str(e)}), 500


# @app.route('/synthesize_speech_gcs', methods=['POST'])
# def synthesize_speech():
#     """Synthesize text to speech using Google Cloud Text-to-Speech API."""
#     if not config.GOOGLE_CLOUD_API_KEY or config.GOOGLE_CLOUD_API_KEY.strip() == "":
#         app_logger.error("GOOGLE_CLOUD_API_KEY is not set or is empty. Cannot synthesize speech.")
#         return jsonify({"error": "Speech synthesis service not configured (missing API key)."}), 500

#     app_logger.info("Processing text-to-speech request.")
#     try:
#         text = request.json.get('text')
#         if not text:
#             app_logger.error("Text parameter is missing in request for speech synthesis.")
#             return jsonify({"error": "Text parameter is required."}), 400
        
#         url = f'https://texttospeech.googleapis.com/v1beta1/text:synthesize?key={config.GOOGLE_CLOUD_API_KEY}'
#         headers = {"Content-Type": "application/json"}
#         voice_name = config.GCS_TTS_DEFAULT_VOICE
#         body = {
#             "input": {"text": text},
#             "voice": {"languageCode": config.GCS_TTS_LANGUAGE_CODE, "name": voice_name},
#             "audioConfig": {"audioEncoding": config.GCS_TTS_AUDIO_ENCODING, "speakingRate": config.GCS_TTS_SPEAKING_RATE}
#         }
#         # removed "pitch": config.GCS_TTS_PITCH from line 2648 
#         response = exponential_backoff_retry(
#             lambda: requests.post(url, headers=headers, json=body)
#         )
        
#         if response.status_code != 200:
#             error_message = response.json().get("error", {}).get("message", "Unknown error from TTS API")
#             app_logger.error(f"Error from TTS API: {error_message}")
#             if "Voice" in error_message and "does not exist" in error_message:
#                 voice_name = config.GCS_TTS_FALLBACK_VOICE
#                 body["voice"]["name"] = voice_name
#                 app_logger.warning(f"Default TTS voice failed, trying fallback voice: {voice_name} for text '{text[:50]}...'.")
#                 response = exponential_backoff_retry(
#                     lambda: requests.post(url, headers=headers, json=body)
#                 )
#                 if response.status_code != 200:
#                     app_logger.error(f"Fallback voice also failed for text '{text[:50]}...': {response.text}")
#                     return jsonify({"error": "Failed to synthesize speech using default and fallback voices."}), response.status_code
#             else:
#                 return jsonify({"error": "Failed to synthesize speech"}), response.status_code
        
#         audio_content = response.json().get('audioContent')
#         if not audio_content:
#             app_logger.error(f"No audio content received from TTS API for text '{text[:50]}...'.")
#             return jsonify({"error": "No audio content received"}), 500
        
#         audio_data = base64.b64decode(audio_content)
#         return Response(audio_data, mimetype=config.GCS_TTS_MIMETYPE)
    
#     except Exception as e:
#         app_logger.error(f"Error during text-to-speech processing: {e}", exc_info=True)
#         return jsonify({"error": "An error occurred during speech synthesis."}), 500

# if __name__ == '__main__':
#     app_logger.info("Starting Flask app. Terminal output will be minimal; all detailed logs go to logs/app.log.")
    
#     # Check if essential API keys and database URIs are loaded (more robust check)
#     if not all([config.MONGO_URI, config.QWEN_API_KEY, config.OPENAI_API_KEY]):
#         app_logger.critical("CRITICAL: Essential API keys (Qwen, OpenAI) or MongoDB URI are missing. Please check your .env file.")
#         # import sys
#         # sys.exit(1) # Uncomment this line if you want the app to crash if critical config is missing
    
#     app.run(debug=True, port=5008, host="0.0.0.0")

# import os
# import json
# import random
# import logging
# from logging.handlers import RotatingFileHandler
# from datetime import datetime
# import time
# import sys
# import threading
# import uuid
# from typing import Dict, Any, Optional

# from flask import Flask, request, jsonify, Response
# from flask_cors import CORS
# import requests
# import base64
# from openai import OpenAI
# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from email.utils import formataddr

# # Database imports
# from pymongo import MongoClient
# import mysql.connector

# # Local Modules
# import config
# import email_services
# import evaluation

# # -------------------- Setup Logging --------------------
# for handler in logging.root.handlers[:]:
#     logging.root.removeHandler(handler)

# if not os.path.exists("logs"):
#     os.makedirs("logs")

# log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(module)s] %(message)s')
# file_handler = RotatingFileHandler('logs/app.log', maxBytes=5*1024*1024, backupCount=5)
# file_handler.setFormatter(log_formatter)
# file_handler.setLevel(logging.DEBUG)

# app_logger = logging.getLogger('app_logger')
# app_logger.setLevel(logging.DEBUG)
# app_logger.addHandler(file_handler)

# # -------------------- Initialize Flask --------------------
# app = Flask(__name__)
# CORS(app)

# if not os.path.exists("temp_audio"):
#     os.makedirs("temp_audio")

# # -------------------- Load Topics --------------------
# SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# TOPICS_FILE = os.path.join(SCRIPT_DIR, 'topics.json')
# USED_TOPICS_SESSION_MAP = {} 

# def get_unique_topic(session_id: str) -> str:
#     try:
#         with open(TOPICS_FILE, 'r') as f:
#             data = json.load(f)
#         all_topics = []
#         for category, topics in data.items():
#             all_topics.extend(topics)
#         if not all_topics: return "Default Topic: Artificial Intelligence"

#         if session_id not in USED_TOPICS_SESSION_MAP:
#             USED_TOPICS_SESSION_MAP[session_id] = set()

#         available_topics = [t for t in all_topics if t not in USED_TOPICS_SESSION_MAP[session_id]]
#         if not available_topics:
#             USED_TOPICS_SESSION_MAP[session_id] = set()
#             available_topics = all_topics

#         chosen_topic = random.choice(available_topics)
#         USED_TOPICS_SESSION_MAP[session_id].add(chosen_topic)
#         app_logger.info(f"Selected Topic for {session_id}: {chosen_topic}")
#         return chosen_topic
#     except Exception as e:
#         app_logger.error(f"Error loading topics: {e}", exc_info=True)
#         return "Default Topic: Work from Home"

# # -------------------- DB & API Setup --------------------
# client = None
# gd_collection = None
# try:
#     if config.MONGO_URI:
#         client = MongoClient(config.MONGO_URI)
#         db = client[config.MONGO_DB_NAME]
#         gd_collection = db[config.MONGO_COLLECTION_NAME]
#     else:
#         app_logger.critical("MONGO_URI not found.")
# except Exception as e:
#     app_logger.critical(f"MongoDB Error: {e}")

# qwen_client = OpenAI(api_key=config.QWEN_API_KEY, base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1") if config.QWEN_API_KEY else None
# openai_client = OpenAI(api_key=config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None

# session_lock = threading.Lock()
# exam_memory: Dict[str, Dict[str, Any]] = {}

# # -------------------- Helper Functions --------------------

# def get_user_details(user_id: str):
#     try:
#         connection = mysql.connector.connect(
#             host=config.MYSQL_HOST, user=config.MYSQL_USER, 
#             password=config.MYSQL_PASSWORD, database=config.MYSQL_USER_DB_NAME, port=config.MYSQL_PORT
#         )
#         cursor = connection.cursor(dictionary=True)
#         cursor.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
#         res = cursor.fetchone()
#         connection.close()
#         return res
#     except Exception as e:
#         app_logger.error(f"MySQL Error: {e}")
#         return None

# def transcribe_audio_file(file_path):
#     """Transcribes audio using OpenAI Whisper."""
#     if not openai_client: return "Transcription Unavailable"
#     try:
#         with open(file_path, "rb") as audio_file:
#             transcript = openai_client.audio.transcriptions.create(
#                 model="whisper-1", 
#                 file=audio_file
#             )
#         return transcript.text
#     except Exception as e:
#         app_logger.error(f"Transcription failed: {e}")
#         return ""

# # --- Speaker Generation Functions ---

# def generate_host_intro(topic: str) -> str:
#     return f"Hello everyone, and welcome to today's group discussion. I am your instructor. The topic for your group discussion is {topic}. Who would like to start?"

# def generate_aryan_response(topic: str, context: str, is_opening: bool = False) -> str:
#     if not qwen_client: return "I agree with the points raised."
#     duration_instr = "Your response must be approximately 60 to 80 words (30 seconds). CRITICAL: Finish your sentences."
#     if is_opening:
#         role_instr = f"You are 'Speaker 1 (Aryan)'. Topic: '{topic}'. You are starting the discussion. Give a clear opening argument."
#     else:
#         role_instr = f"You are 'Speaker 1 (Aryan)'. Topic: '{topic}'. The User just spoke. Acknowledge their point politely, then add your own view."
#     try:
#         msgs = [{"role": "system", "content": f"{role_instr} {duration_instr}"}, {"role": "user", "content": context}, {"role": "assistant", "content": "Aryan:"}]
#         resp = qwen_client.chat.completions.create(model="qwen-vl-max", messages=msgs, max_tokens=150)
#         return resp.choices[0].message.content.strip()
#     except: return "I think this is a valid point."

# def generate_rohi_response(topic: str, context: str) -> str:
#     if not openai_client: return "To add a different perspective..."
#     duration_instr = "Your response must be approximately 90 to 110 words (40 seconds). CRITICAL: Finish your sentences."
#     role_instr = f"You are 'Speaker 2 (Rohi)'. Topic: '{topic}'. The previous speaker was Aryan. Analyze his point and the User's previous point. Use advanced vocabulary and logic. Build upon the discussion."
#     try:
#         msgs = [{"role": "system", "content": f"{role_instr} {duration_instr}"}, {"role": "user", "content": context}, {"role": "assistant", "content": "Rohi:"}]
#         resp = openai_client.chat.completions.create(model="gpt-4o-mini", messages=msgs, max_tokens=250)
#         return resp.choices[0].message.content.strip()
#     except: return "Allow me to elaborate."

# # -------------------- API Routes --------------------

# @app.route('/group_discussion', methods=['POST'])
# def group_discussion():
#     # --- FIX: silent=True prevents 415 error on File Uploads ---
#     req_json = request.get_json(silent=True) or {}
    
#     # Priority: Form Data (for audio) -> JSON (for text)
#     session_id = request.form.get("sessionId") or req_json.get("sessionId")
#     user_id = request.form.get("userId") or req_json.get("userId")
#     uploaded_file = request.files.get('audio')
#     user_text_input = request.form.get("response") or req_json.get("response")

#     if not user_id:
#         return jsonify({"error": "userId is required"}), 400

#     user_id = str(user_id)

#     with session_lock:
#         # ---------------------------------------------------------
#         # CASE 1: START NEW SESSION
#         # ---------------------------------------------------------
#         if not session_id or (session_id not in exam_memory):
#             user_details = get_user_details(user_id)
#             if not user_details: return jsonify({"error": "User not found"}), 404
            
#             session_id = str(uuid.uuid4())
#             topic = get_unique_topic(session_id)
#             host_text = generate_host_intro(topic)
            
#             new_doc = {
#                 "sessionId": session_id, "user_id": user_id, "gd_topic": topic,
#                 "start_time": datetime.now(), "conversation_history": [], "status": "in_progress"
#             }
#             res = gd_collection.insert_one(new_doc)
            
#             exam_memory[session_id] = {
#                 "gd_topic": topic, "start_time": datetime.now(), "mongo_id": res.inserted_id,
#                 "user_email": user_details['email'], "user_name": user_details['username'],
#                 "history": [f"Host: {host_text}"],
#                 "next_speaker": "Aryan", 
#                 "last_audio_path": None 
#             }
            
#             return jsonify({
#                 "gd_topic": topic,
#                 "host": host_text,
#                 "message": "Session started.",
#                 "sessionId": session_id
#             })

#         # ---------------------------------------------------------
#         # CASE 2: EXISTING SESSION
#         # ---------------------------------------------------------
#         session_data = exam_memory[session_id]
#         mongo_id = session_data["mongo_id"]
#         topic = session_data["gd_topic"]
#         next_speaker = session_data["next_speaker"]
#         elapsed = (datetime.now() - session_data["start_time"]).total_seconds()

#         if elapsed > config.GD_TIME_LIMIT_SECONDS:
#             app_logger.info(f"Time limit reached for {session_id}")
#             user_full_text = "\n".join([line.replace("User: ", "") for line in session_data["history"] if line.startswith("User:")])
            
#             # Use last audio path for evaluation
#             report_text = evaluation.generate_full_report(user_full_text, audio_path=session_data.get("last_audio_path"))
            
#             html_body, text_body = email_services.get_feedback_email_content(session_data["user_name"], topic, [], report_text)
            
#             msg = MIMEMultipart('alternative')
#             msg['From'] = formataddr(("AI Interviewer", config.MAIL_USERNAME))
#             msg['To'] = session_data["user_email"]
#             msg['Subject'] = "Your GD Evaluation Report"
#             msg.attach(MIMEText(text_body, 'plain'))
#             msg.attach(MIMEText(html_body, 'html'))
#             try:
#                 with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
#                     server.starttls()
#                     server.login(config.MAIL_USERNAME, config.MAIL_PASSWORD)
#                     server.send_message(msg)
#             except Exception as e:
#                 app_logger.error(f"Email failed: {e}")

#             gd_collection.update_one({"_id": mongo_id}, {"$set": {"status": "completed", "evaluation_report": report_text}})
#             if session_data.get("last_audio_path") and os.path.exists(session_data["last_audio_path"]):
#                 try: os.remove(session_data["last_audio_path"])
#                 except: pass
#             del exam_memory[session_id]
#             return jsonify({"message": "Time is up.", "report": report_text, "email_status": "sent"})

#         # --- ARYAN ---
#         if next_speaker == "Aryan":
#             is_opening = (len(session_data["history"]) == 1)
#             context = "\n".join(session_data["history"][-3:])
#             aryan_text = generate_aryan_response(topic, context, is_opening=is_opening)
            
#             session_data["history"].append(f"Speaker 1 (Aryan): {aryan_text}")
#             gd_collection.update_one({"_id": mongo_id}, {"$push": {"conversation_history": {"speaker": "Speaker 1 (Aryan)", "text": aryan_text, "time": datetime.now()}}})
            
#             session_data["next_speaker"] = "Rohi"
#             return jsonify({"sessionId": session_id, "speaker": "Aryan", "content": aryan_text, "next_turn": "Rohi"})

#         # --- ROHI ---
#         elif next_speaker == "Rohi":
#             context = "\n".join(session_data["history"][-3:])
#             rohi_text = generate_rohi_response(topic, context)
            
#             session_data["history"].append(f"Speaker 2 (Rohi): {rohi_text}")
#             gd_collection.update_one({"_id": mongo_id}, {"$push": {"conversation_history": {"speaker": "Speaker 2 (Rohi)", "text": rohi_text, "time": datetime.now()}}})
            
#             session_data["next_speaker"] = "User"
#             return jsonify({"sessionId": session_id, "speaker": "Rohi", "content": rohi_text, "next_turn": "User"})

#         # --- USER (Audio) ---
#         elif next_speaker == "User":
#             if not uploaded_file:
#                 return jsonify({"error": "It is your turn. Please upload an 'audio' file."}), 400
            
#             file_ext = os.path.splitext(uploaded_file.filename)[1] or ".wav"
#             filename = f"{session_id}_{int(time.time())}{file_ext}"
#             file_path = os.path.join("temp_audio", filename)
#             uploaded_file.save(file_path)
            
#             transcribed_text = transcribe_audio_file(file_path)
#             if not transcribed_text: transcribed_text = "[Unintelligible Audio]"

#             session_data["history"].append(f"User: {transcribed_text}")
#             session_data["last_audio_path"] = file_path # Keep for evaluation
            
#             gd_collection.update_one({"_id": mongo_id}, {"$push": {"conversation_history": {"speaker": "User", "text": transcribed_text, "time": datetime.now()}}})
#             session_data["next_speaker"] = "Aryan"
            
#             return jsonify({
#                 "sessionId": session_id,
#                 "message": "Audio received and transcribed.",
#                 "transcription": transcribed_text,
#                 "next_turn": "Aryan"
#             })

#     return jsonify({"error": "Unknown state"}), 500

# @app.route('/synthesize_speech_gcs', methods=['POST'])
# def synthesize_speech_gcs():
#     # Fix: also use silent=True here just in case
#     req_json = request.get_json(silent=True) or {}
#     text = req_json.get('text')
#     if not text: return jsonify({"error": "No text"}), 400
    
#     url = f'https://texttospeech.googleapis.com/v1beta1/text:synthesize?key={config.GOOGLE_CLOUD_API_KEY}'
#     body = {
#         "input": {"text": text},
#         "voice": {"languageCode": config.GCS_TTS_LANGUAGE_CODE, "name": config.GCS_TTS_DEFAULT_VOICE},
#         "audioConfig": {"audioEncoding": config.GCS_TTS_AUDIO_ENCODING}
#     }
    
#     try:
#         resp = requests.post(url, json=body)
#         if resp.status_code == 200:
#             audio_content = resp.json().get('audioContent')
#             return Response(base64.b64decode(audio_content), mimetype=config.GCS_TTS_MIMETYPE)
#         return jsonify({"error": "TTS Failed"}), resp.status_code
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# if __name__ == '__main__':
#     app.run(debug=True, port=5008, host="0.0.0.0")


import os
import json
import random
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import time
import sys
import threading
import uuid
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
import base64
from openai import OpenAI
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

# Database imports
from pymongo import MongoClient
import mysql.connector

# Local Modules
import config
import email_services
import evaluation

# -------------------- Setup Logging --------------------
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

if not os.path.exists("logs"):
    os.makedirs("logs")

log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(module)s] %(message)s')
file_handler = RotatingFileHandler('logs/app.log', maxBytes=5*1024*1024, backupCount=5)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)

app_logger = logging.getLogger('app_logger')
app_logger.setLevel(logging.DEBUG)
app_logger.addHandler(file_handler)

# -------------------- Initialize Flask --------------------
app = Flask(__name__)
CORS(app)

if not os.path.exists("temp_audio"):
    os.makedirs("temp_audio")

# -------------------- Load Topics --------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOPICS_FILE = os.path.join(SCRIPT_DIR, 'topics.json')
USED_TOPICS_SESSION_MAP = {} 

def get_unique_topic(session_id: str) -> str:
    try:
        with open(TOPICS_FILE, 'r') as f:
            data = json.load(f)
        all_topics = []
        for category, topics in data.items():
            all_topics.extend(topics)
        if not all_topics: return "Default Topic: Artificial Intelligence"

        if session_id not in USED_TOPICS_SESSION_MAP:
            USED_TOPICS_SESSION_MAP[session_id] = set()

        available_topics = [t for t in all_topics if t not in USED_TOPICS_SESSION_MAP[session_id]]
        if not available_topics:
            USED_TOPICS_SESSION_MAP[session_id] = set()
            available_topics = all_topics

        chosen_topic = random.choice(available_topics)
        USED_TOPICS_SESSION_MAP[session_id].add(chosen_topic)
        app_logger.info(f"Selected Topic for {session_id}: {chosen_topic}")
        return chosen_topic
    except Exception as e:
        app_logger.error(f"Error loading topics: {e}", exc_info=True)
        return "Default Topic: Work from Home"

# -------------------- DB & API Setup --------------------
client = None
gd_collection = None
try:
    if config.MONGO_URI:
        client = MongoClient(config.MONGO_URI)
        db = client[config.MONGO_DB_NAME]
        gd_collection = db[config.MONGO_COLLECTION_NAME]
    else:
        app_logger.critical("MONGO_URI not found.")
except Exception as e:
    app_logger.critical(f"MongoDB Error: {e}")

qwen_client = OpenAI(api_key=config.QWEN_API_KEY, base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1") if config.QWEN_API_KEY else None
openai_client = OpenAI(api_key=config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None

session_lock = threading.Lock()
exam_memory: Dict[str, Dict[str, Any]] = {}

# -------------------- Helper Functions --------------------

def get_user_details(user_id: str):
    try:
        connection = mysql.connector.connect(
            host=config.MYSQL_HOST, user=config.MYSQL_USER, 
            password=config.MYSQL_PASSWORD, database=config.MYSQL_USER_DB_NAME, port=config.MYSQL_PORT
        )
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
        res = cursor.fetchone()
        connection.close()
        return res
    except Exception as e:
        app_logger.error(f"MySQL Error: {e}")
        return None

def transcribe_audio_file(file_path):
    """Transcribes audio using OpenAI Whisper."""
    if not openai_client: return "Transcription Unavailable"
    try:
        with open(file_path, "rb") as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                prompt="The speaker may use filler words like um, uh, like, basically. Please transcribe them verbatim."
            )
        return transcript.text
    except Exception as e:
        app_logger.error(f"Transcription failed: {e}")
        return ""

# --- Speaker Generation Functions (MODIFIED PROMPTS) ---

def generate_host_intro(topic: str) -> str:
    return f"Hello everyone, and welcome to today's group discussion. I am your instructor. The topic for your group discussion is {topic}. Who would like to start?"

def generate_aryan_response(topic: str, context: str, is_opening: bool = False) -> str:
    if not qwen_client: return "I agree with the points raised."
    
    # Updated constraints
    duration_instr = "Your response must be approximately 60 to 80 words (30 seconds). CRITICAL: Finish your sentences."
    
    if is_opening:
        # PERSONA: College Student, Natural, No "Thank you host"
        role_instr = (
            f"You are Aryan, a college student participating in a Group Discussion on '{topic}'. "
            "Speak naturally and confidently, like you are talking to peers. "
            "Do NOT start with 'Thank you, host' or 'Thank you for the opportunity'. "
            "Start with phrases like: 'Hello everyone, I think...', 'Hi guys, let me share my views on...', 'To start off, I feel that...', or 'In my opinion...'. "
            "Don't sound robotic."
        )
    else:
        # PERSONA: College Student, Conversational
        role_instr = (
            f"You are Aryan, a college student. Topic: '{topic}'. The User just spoke. "
            "Respond to them naturally, like a friend or classmate. "
            "Do NOT start with 'Thank you'. "
            "Use openers like: 'That's a good point, but...', 'I see what you mean, however...', 'Adding to that...', or 'I actually disagree because...'. "
        )

    try:
        msgs = [{"role": "system", "content": f"{role_instr} {duration_instr}"}, {"role": "user", "content": context}, {"role": "assistant", "content": "Aryan:"}]
        resp = qwen_client.chat.completions.create(model="qwen-vl-max", messages=msgs, max_tokens=150)
        return resp.choices[0].message.content.strip()
    except: return "I think this is a valid point."

def generate_rohi_response(topic: str, context: str) -> str:
    if not openai_client: return "To add a different perspective..."
    
    duration_instr = "Your response must be approximately 90 to 110 words (40 seconds). CRITICAL: Finish your sentences."
    
    # PERSONA: Advanced Speaker, but still natural
    role_instr = (
        f"You are Rohi, a smart and articulate participant in a GD on '{topic}'. "
        "The previous speaker was Aryan. Analyze his point and the User's previous point. "
        "Use strong vocabulary and logic, but keep it conversational. "
        "Do NOT start with 'Thank you'. "
        "Start directly with your analysis or transition like: 'Taking a step back...', 'Critically speaking...', or 'While I understand that perspective...'."
    )
    
    try:
        msgs = [{"role": "system", "content": f"{role_instr} {duration_instr}"}, {"role": "user", "content": context}, {"role": "assistant", "content": "Rohi:"}]
        resp = openai_client.chat.completions.create(model="gpt-4o-mini", messages=msgs, max_tokens=250)
        return resp.choices[0].message.content.strip()
    except: return "Allow me to elaborate."

# -------------------- API Routes --------------------

@app.route('/group_discussion', methods=['POST'])
def group_discussion():
    req_json = request.get_json(silent=True) or {}
    
    session_id = request.form.get("sessionId") or req_json.get("sessionId")
    user_id = request.form.get("userId") or req_json.get("userId")
    uploaded_file = request.files.get('audio')
    
    if not user_id: return jsonify({"error": "userId is required"}), 400
    user_id = str(user_id)

    with session_lock:
        # ---------------------------------------------------------
        # CASE 1: START NEW SESSION
        # ---------------------------------------------------------
        if not session_id or (session_id not in exam_memory):
            user_details = get_user_details(user_id)
            if not user_details: return jsonify({"error": "User not found"}), 404
            
            session_id = str(uuid.uuid4())
            topic = get_unique_topic(session_id)
            host_text = generate_host_intro(topic)
            
            new_doc = {
                "sessionId": session_id, "user_id": user_id, "gd_topic": topic,
                "start_time": datetime.now(), "conversation_history": [], "status": "in_progress"
            }
            res = gd_collection.insert_one(new_doc)
            
            exam_memory[session_id] = {
                "gd_topic": topic, "start_time": datetime.now(), "mongo_id": res.inserted_id,
                "user_email": user_details['email'], "user_name": user_details['username'],
                "history": [f"Host: {host_text}"],
                "next_speaker": "Aryan", 
                "user_audio_files": [] 
            }
            
            return jsonify({
                "gd_topic": topic,
                "host": host_text,
                "message": "Session started.",
                "sessionId": session_id
            })

        # ---------------------------------------------------------
        # CASE 2: EXISTING SESSION
        # ---------------------------------------------------------
        session_data = exam_memory[session_id]
        mongo_id = session_data["mongo_id"]
        topic = session_data["gd_topic"]
        next_speaker = session_data["next_speaker"]
        
        # --- PRIORITY: HANDLE USER INPUT FIRST ---
        user_input_processed = False
        transcribed_text = ""

        if next_speaker == "User" and uploaded_file:
            file_ext = os.path.splitext(uploaded_file.filename)[1] or ".wav"
            filename = f"{session_id}_{len(session_data['user_audio_files'])}_{int(time.time())}{file_ext}"
            file_path = os.path.join("temp_audio", filename)
            uploaded_file.save(file_path)
            
            transcribed_text = transcribe_audio_file(file_path)
            if not transcribed_text: transcribed_text = "[Unintelligible Audio]"

            session_data["history"].append(f"User: {transcribed_text}")
            
            # Store audio path for Cumulative Evaluation
            session_data["user_audio_files"].append(file_path)
            
            gd_collection.update_one({"_id": mongo_id}, {"$push": {"conversation_history": {"speaker": "User", "text": transcribed_text, "time": datetime.now()}}})
            
            session_data["next_speaker"] = "Aryan"
            user_input_processed = True

        # --- NOW CHECK TIME LIMIT ---
        elapsed = (datetime.now() - session_data["start_time"]).total_seconds()
        
        if elapsed > config.GD_TIME_LIMIT_SECONDS:
            app_logger.info(f"Time limit reached for {session_id}")
            
            user_full_text = "\n".join([line.replace("User: ", "") for line in session_data["history"] if line.startswith("User:")])
            
            # EVALUATE ALL AUDIO FILES COLLECTED
            eval_result = evaluation.generate_full_evaluation(user_full_text, audio_paths=session_data.get("user_audio_files", []))
            
            overall_score = eval_result.get("overall_score", 0)
            acoustic_data = eval_result.get("acoustics", {})
            linguistic_data = eval_result.get("linguistics", {})

            html_body, text_body = email_services.get_feedback_email_content(
                session_data["user_name"], 
                topic, 
                [], 
                eval_result
            )
            
            msg = MIMEMultipart('alternative')
            msg['From'] = formataddr(("AI Interviewer", config.MAIL_USERNAME))
            msg['To'] = session_data["user_email"]
            msg['Subject'] = f"Performance Report: {topic} (Score: {overall_score}/10)"
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            try:
                with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
                    server.starttls()
                    server.login(config.MAIL_USERNAME, config.MAIL_PASSWORD)
                    server.send_message(msg)
            except Exception as e:
                app_logger.error(f"Email failed: {e}")

            gd_collection.update_one(
                {"_id": mongo_id}, 
                {
                    "$set": {
                        "status": "completed", 
                        "overall_score": overall_score,
                        "acoustic_metrics": acoustic_data,
                        "linguistic_metrics": linguistic_data,
                        "full_transcript": user_full_text
                    }
                }
            )

            # Cleanup ALL audio files
            for path in session_data.get("user_audio_files", []):
                if os.path.exists(path):
                    try: os.remove(path)
                    except: pass
            
            del exam_memory[session_id]
            
            return jsonify({
                "message": "Time is up.", 
                "overall_score": overall_score,
                "acoustics": acoustic_data,
                "linguistics": linguistic_data,
                "email_status": "sent"
            })

        # --- IF TIME NOT UP AND USER JUST SPOKE ---
        if user_input_processed:
            return jsonify({
                "sessionId": session_id,
                "message": "Audio received and transcribed.",
                "transcription": transcribed_text,
                "next_turn": "Aryan",
                "elapsed_time": elapsed
            })

        # --- ARYAN'S TURN ---
        if next_speaker == "Aryan":
            is_opening = (len(session_data["history"]) == 1)
            context = "\n".join(session_data["history"][-3:])
            aryan_text = generate_aryan_response(topic, context, is_opening=is_opening)
            
            session_data["history"].append(f"Speaker 1 (Aryan): {aryan_text}")
            gd_collection.update_one({"_id": mongo_id}, {"$push": {"conversation_history": {"speaker": "Speaker 1 (Aryan)", "text": aryan_text, "time": datetime.now()}}})
            
            session_data["next_speaker"] = "Rohi"
            return jsonify({"sessionId": session_id, "speaker": "Aryan", "content": aryan_text, "next_turn": "Rohi", "elapsed_time": elapsed})

        # --- ROHI'S TURN ---
        elif next_speaker == "Rohi":
            context = "\n".join(session_data["history"][-3:])
            rohi_text = generate_rohi_response(topic, context)
            
            session_data["history"].append(f"Speaker 2 (Rohi): {rohi_text}")
            gd_collection.update_one({"_id": mongo_id}, {"$push": {"conversation_history": {"speaker": "Speaker 2 (Rohi)", "text": rohi_text, "time": datetime.now()}}})
            
            session_data["next_speaker"] = "User"
            return jsonify({"sessionId": session_id, "speaker": "Rohi", "content": rohi_text, "next_turn": "User", "elapsed_time": elapsed})

        # --- USER'S TURN (Waiting for input) ---
        elif next_speaker == "User":
            return jsonify({
                "error": "It is your turn. Please upload an 'audio' file.",
                "elapsed_time": elapsed
            }), 400

    return jsonify({"error": "Unknown state"}), 500

@app.route('/synthesize_speech_gcs', methods=['POST'])
def synthesize_speech_gcs():
    req_json = request.get_json(silent=True) or {}
    text = req_json.get('text')
    if not text: return jsonify({"error": "No text"}), 400
    
    url = f'https://texttospeech.googleapis.com/v1beta1/text:synthesize?key={config.GOOGLE_CLOUD_API_KEY}'
    body = {
        "input": {"text": text},
        "voice": {"languageCode": config.GCS_TTS_LANGUAGE_CODE, "name": config.GCS_TTS_DEFAULT_VOICE},
        "audioConfig": {"audioEncoding": config.GCS_TTS_AUDIO_ENCODING}
    }
    
    try:
        resp = requests.post(url, json=body)
        if resp.status_code == 200:
            audio_content = resp.json().get('audioContent')
            return Response(base64.b64decode(audio_content), mimetype=config.GCS_TTS_MIMETYPE)
        return jsonify({"error": "TTS Failed"}), resp.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5008, host="0.0.0.0")