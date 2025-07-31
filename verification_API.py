import os
import certifi
os.environ["SSL_CERT_FILE"] = certifi.where()

from flask import Flask, request, jsonify
from flask_cors import CORS
import random
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)

# Load SendGrid API key from environment
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
if not SENDGRID_API_KEY:
    raise RuntimeError("Please set the SENDGRID_API_KEY environment variable")

# In-memory store (demo only—swap for Redis/db in production)
verification_codes = {}

def generate_email_template(code):
    """Generate modern email template using university colors"""
    current_year = datetime.now().year
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>SCCS Verification Code</title>
      <style>
        body {{
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          background-color: #fafafa;
          margin: 0;
          padding: 0;
        }}
        .container {{
          max-width: 600px;
          margin: 0 auto;
          background: white;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }}
        .header {{
          background: #002366;
          padding: 30px 20px;
          text-align: center;
        }}
        .header h1 {{
          color: white;
          margin: 0;
          font-weight: 600;
        }}
        .content {{
          padding: 40px 30px;
          color: #333;
          line-height: 1.6;
        }}
        .code-box {{
          background: #FFD700;
          color: #002366;
          font-size: 32px;
          font-weight: 700;
          letter-spacing: 4px;
          padding: 20px;
          margin: 30px 0;
          text-align: center;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .footer {{
          background: #002366;
          color: white;
          text-align: center;
          padding: 20px;
          font-size: 12px;
        }}
        .note {{
          background: #FFF9E5;
          padding: 15px;
          border-radius: 6px;
          margin-top: 25px;
          font-size: 14px;
        }}
        .btn {{
          display: inline-block;
          background: #006400;
          color: white !important;
          padding: 12px 30px;
          text-decoration: none;
          border-radius: 4px;
          font-weight: 600;
          margin: 20px 0;
          transition: background 0.3s;
        }}
        .btn:hover {{
          background: #004D00;
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>University of Mpumalanga</h1>
        </div>
        
        <div class="content">
          <h2 style="color: #002366; margin-top: 0;">Secure Account Verification</h2>
          <p>Your SCCS verification code is:</p>
          <div class="code-box">{code}</div>
          <p>This code will expire in 10 minutes. Please do not share it with anyone.</p>
          
          <div class="note">
            <p>🛡️ <strong>Security notice:</strong> If you didn't request this code, 
            please contact our support team immediately.</p>
          </div>
        </div>
        
        <div class="footer">
          <p>© {current_year} University of Mpumalanga. All rights reserved.</p>
          <p>Contact: support@ump.ac.za | +27 (0)13 002 0001</p>
        </div>
      </div>
    </body>
    </html>
    """

@app.route("/send-code", methods=["POST"])
def send_verification_code():
    data = request.json or {}
    email = data.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400

    # Generate 6-digit code
    code = str(random.randint(100000, 999999))
    verification_codes[email] = code

    # Build the email with modern template
    html_content = generate_email_template(code)
    
    message = Mail(
        from_email="SCCS Verification <230252427@ump.ac.za>",
        to_emails=email,
        subject="Your SCCS Verification Code",
        html_content=html_content
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return jsonify({"message": "Verification code sent"}), 200
  
    except Exception as e:
        print("=== SendGrid Error ===")
        print(e)
        try:
            body = e.body.decode() if hasattr(e, "body") else str(e)
        except:
            body = str(e)
        return (
            jsonify({
              "error": "Failed to send email",
              "details": body
            }),
            500
        )

@app.route("/verify-code", methods=["POST"])
def verify_code():
    data = request.json or {}
    email = data.get("email")
    code = data.get("code")
    if verification_codes.get(email) == code:
        verification_codes.pop(email, None)
        return jsonify({"verified": True}), 200
    return jsonify({"verified": False, "error": "Invalid code"}), 401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)