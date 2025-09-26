from flask import Flask, render_template, request, send_from_directory
from cryptography.fernet import Fernet
import os

app = Flask(__name__)

# Folders for file handling
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# AES Setup
key = Fernet.generate_key()
cipher = Fernet(key)

# Caesar Cipher functions
def caesar_encrypt(text, shift=3):
    result = ""
    for char in text:
        if char.isalpha():
            shift_base = 65 if char.isupper() else 97
            result += chr((ord(char) - shift_base + shift) % 26 + shift_base)
        else:
            result += char
    return result

def caesar_decrypt(text, shift=3):
    return caesar_encrypt(text, -shift)

@app.route("/", methods=["GET", "POST"])
def home():
    result = ""
    file_url = None

    if request.method == "POST":
        action = request.form.get("action")
        method = request.form.get("method")
        text = request.form.get("text","").strip()
        file = request.files.get("file")

        # --- Process Text Input ---
        if text:
            try:
                if method == "AES":
                    result = cipher.encrypt(text.encode()).decode() if action=="encrypt" else cipher.decrypt(text.encode()).decode()
                elif method == "Caesar":
                    result = caesar_encrypt(text) if action=="encrypt" else caesar_decrypt(text)
            except Exception:
                result = f"Failed to {action} text with {method}!"

        # --- Process File Input ---
        elif file:
            input_path = os.path.join(UPLOAD_FOLDER, file.filename)
            output_filename = f"{action}_{method}_{file.filename}"
            output_path = os.path.join(PROCESSED_FOLDER, output_filename)

            file.save(input_path)

            try:
                with open(input_path, "rb") as f:
                    data = f.read()

                if method == "AES":
                    processed = cipher.encrypt(data) if action=="encrypt" else cipher.decrypt(data)
                elif method == "Caesar":
                    # Caesar works only for text files
                    text_data = data.decode()
                    processed = (caesar_encrypt(text_data) if action=="encrypt" else caesar_decrypt(text_data)).encode()

                with open(output_path, "wb") as f:
                    f.write(processed)

                file_url = f"/download/{output_filename}"

            except Exception:
                result = f"Failed to {action} file with {method}!"

        else:
            result = "Please provide text or upload a file."

    return render_template("index.html", result=result, file_url=file_url)

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(PROCESSED_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
