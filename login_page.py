import webview
import requests
import os
import sys
import base64
import pygame
import main_app

# Globals to hold the current window and any successful login data
_cur_window = None
_login_data = None

def resource_path(relative_path):
    """Locate bundled resources when using PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Login Page</title>
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
      font-family: Arial, sans-serif;
    }}
    html, body {{
      width: 100%;
      height: 100%;
      overflow: hidden;
    }}
    /* Full‐screen background */
    body {{
      background: url('data:image/jpeg;base64,{bg_data}') no-repeat center center fixed;
      background-size: cover;
    }}
    /* Semi‐transparent container */
    .login-container {{
      position: absolute;
      top: 50%;
      left: 10%; /* left‐center */
      transform: translateY(-50%);
      width: 450px;
      height: 55vh;
      background: rgba(0, 0, 0, 0.1); /* very light translucent */
      border: 1px solid red;
      border-radius: 8px;
      padding: 20px 15px;
      backdrop-filter: blur(8px);
    }}
    /* Logo */
    .logo-img {{
      display: block;
      margin: 0 auto 20px auto;
      max-width: 100%;
      height: auto;
    }}
    /* Input wrapper */
    .input-wrapper {{
      position: relative;
      margin: 20px 0;
    }}
    .input-wrapper input {{
      width: calc(100%);
      padding: 12px 15px 12px 45px;
      font-size: 16px;
      border: 1px solid red;
      border-radius: 4px;
      background: rgba(255, 255, 255, 0.1);
      outline: none;
      color: white;
    }}
    .input-wrapper input::placeholder {{
      color: #888;
    }}
    .input-wrapper .icon {{
      position: absolute;
      left: 15px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 20px;
      color: #f1c40f; /* yellow */
    }}
    /* Login button */
    .btn-login {{
      display: block;
      margin: 30px auto 0 auto;
      width: 100%;
      padding: 12px 0;
      text-align: center;
      font-size: 18px;
      font-weight: bold;
      color: #fff;
      background: #f1c40f;
      border: none;
      border-radius: 25px;
      cursor: pointer;
      transition: background 0.2s ease;
    }}
    .btn-login:hover {{
      background: #d4ac0d;
    }}
    /* Error message */
    .error-msg {{
      text-align: center;
      margin-top: 10px;
      color: #e74c3c;
      font-size: 14px;
      height: 18px; /* reserve space even when empty */
    }}
    /* Close‐button "X" */
    .close-btn {{
      position: absolute;
      top: 10px;
      right: 10px;
      font-size: 18px;
      color: #fff;
      background: #e74c3c;
      width: 28px;
      height: 28px;
      border-radius: 14px;
      text-align: center;
      line-height: 28px;
      cursor: pointer;
    }}
  </style>
</head>
<body>
  <div class="close-btn" onclick="closeWindow()">✕</div>
  <div class="login-container">
    <!-- Logo -->
    <img src="data:image/png;base64,{logo_data}" alt="Logo" class="logo-img" />
    <!-- Username Field -->
    <div class="input-wrapper">
      <div class="icon">👤</div>
      <input
        id="username"
        type="text"
        placeholder="Enter username"
        autocomplete="off"
      />
    </div>
    <!-- Password Field -->
    <div class="input-wrapper">
      <div class="icon">🔒</div>
      <input
        id="password"
        type="password"
        placeholder="Enter password"
      />
    </div>
    <!-- Error message placeholder -->
    <div class="error-msg" id="errorMsg"></div>
    <!-- Login Button -->
    <button class="btn-login" onclick="attemptLogin()">Login</button>
  </div>

  <script>
    function attemptLogin() {{
      const user = document.getElementById('username').value.trim();
      const pwd = document.getElementById('password').value.trim();
      if (!user || !pwd) {{
        document.getElementById('errorMsg').innerText = 'Please enter both fields';
        return;
      }}
      const btn = document.querySelector('.btn-login');
      btn.disabled = true;
      btn.style.opacity = '0.6';

      window.pywebview.api.login(user, pwd)
        .then(response => {{
          btn.disabled = false;
          btn.style.opacity = '1';
          if (response.status) {{
            window.pywebview.api.onLoginSuccess(response.data);
          }} else {{
            document.getElementById('errorMsg').innerText = response.message || 'Login failed.';
          }}
        }})
        .catch(err => {{
          btn.disabled = false;
          btn.style.opacity = '1';
          document.getElementById('errorMsg').innerText = 'Error: ' + err;
        }});
    }}

    function closeWindow() {{
      window.pywebview.api.closeWindow();
    }}
  </script>
</body>
</html>
"""

class API:
    def login(self, username, password):
        """Called from JS: performs POST, returns JSON dict."""
        try:
            resp = requests.post(
                "https://spintofortune.in/api/app-sign-in.php",
                data={"login": username, "password": password},
                timeout=10
            )
            return resp.json()
        except Exception as e:
            return {"status": False, "message": f"Error: {e}"}

    def onLoginSuccess(self, data):
        """Store successful login data and close window."""
        global _login_data, _cur_window
        _login_data = data
        if _cur_window:
            _cur_window.destroy()

    def closeWindow(self):
        """Close window without logging in."""
        global _cur_window
        if _cur_window:
            _cur_window.destroy()

def load_base64_image(path):
    """Load a file and return base64‐encoded string."""
    with open(resource_path(path), "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def launch_login():
    global _cur_window, _login_data

    # Read images and embed as base64
    bg_data = load_base64_image("background.jpg")
    logo_data = load_base64_image("logo.png")
    html = HTML_TEMPLATE.format(bg_data=bg_data, logo_data=logo_data)

    api = API()
    _cur_window = webview.create_window(
        title="Login",
        html=html,
        frameless=True,
        fullscreen=True,
        js_api=api
    )

    # Start event loop; returns once window is closed
    webview.start(http_server=True)

    # After the window is closed, check if login was successful
    if _login_data:
        # Initialize pygame before calling main_app
        pygame.init()
        main_app.launch_main_app(_login_data)

if __name__ == "__main__":
    launch_login()
