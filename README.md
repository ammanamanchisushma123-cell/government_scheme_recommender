# GovScheme AI v3

Features requested:
- First-time registration with mobile OTP (DEMO OTP in local app)
- Profile creation after OTP
- Password set during registration
- Returning login with mobile + password, no OTP every time
- Forgot password using OTP + new password
- myScheme-inspired information architecture (not a copy): Home -> Find Schemes -> Results -> Details
- Profile-based TF-IDF recommendation using existing PKL files
- Save schemes
- User profile in SQLite
- Indian language selection
- AI assistant with optional Gemini API

Run with Python 3.12.x:

```powershell
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
python -m streamlit run app.py
```

### Important OTP note
The local version uses a **demo OTP** displayed in the app. It is not real SMS authentication. For production, connect the OTP function to an SMS provider such as Firebase/MSG91/Twilio and never display the OTP.

### Enable real SMS with Twilio
Create a Twilio Verify Service, then set these variables in the same PowerShell window before starting Streamlit:

```powershell
$env:TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
$env:TWILIO_AUTH_TOKEN="your_auth_token"
$env:TWILIO_VERIFY_SERVICE_SID="VAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
python -m streamlit run app.py
```

Use an Indian mobile number in `+919876543210` format. Twilio Verify sends the OTP to that number. Keep these values private and do not add them to `app.py` or GitHub.

### Gemini
PowerShell:
```powershell
$env:GEMINI_API_KEY="YOUR_API_KEY"
python -m streamlit run app.py
```
Do not put the key in app.py or GitHub.

### Model files
Keep these beside app.py:
- scheme_recommendation_model.pkl
- scheme_tfidf_matrix.pkl
- government_schemes_data.pkl

The `.pkl` files are binary and should not be opened in the VS Code text editor.
