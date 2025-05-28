import tkinter as tk
from PIL import Image, ImageTk
import requests
import os
import sys
import main_app

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)

def launch_login():
    root = tk.Tk()
    root.title('Login Page')
    root.attributes('-fullscreen', True)
    root.overrideredirect(True)

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    bg_img = Image.open(resource_path('background.jpg')).resize((screen_width, screen_height))
    bg = ImageTk.PhotoImage(bg_img)
    canvas = tk.Canvas(root, width=screen_width, height=screen_height, highlightthickness=0)
    canvas.pack(fill='both', expand=True)
    canvas.create_image(0, 0, anchor='nw', image=bg)

    # Form position (further left)
    form_w, form_h = 450, 300
    form_x = screen_width // 8  # more to the left
    form_y = screen_height // 2 - form_h // 2

    # Semi-transparent black form background
    canvas.create_rectangle(form_x, form_y, form_x + form_w, form_y + form_h,
                            fill='black', stipple='gray50', outline='')

    # Title
    canvas.create_text(form_x + form_w // 2, form_y + 30, text='Login to Continue',
                       font=('Arial', 20, 'bold'), fill='white')

    # Username row
    username_label = tk.Label(root, text='Username:', font=('Arial', 14), bg='black', fg='white')
    username_entry = tk.Entry(root, font=('Arial', 14))
    canvas.create_window(form_x + 80, form_y + 80, window=username_label, anchor='w')
    canvas.create_window(form_x + 180, form_y + 80, window=username_entry, anchor='w', width=200)

    # Password row
    password_label = tk.Label(root, text='Password:', font=('Arial', 14), bg='black', fg='white')
    password_entry = tk.Entry(root, font=('Arial', 14), show='*')
    canvas.create_window(form_x + 80, form_y + 130, window=password_label, anchor='w')
    canvas.create_window(form_x + 180, form_y + 130, window=password_entry, anchor='w', width=200)

    # Error message
    msg_id = canvas.create_text(form_x + form_w // 2, form_y + 180, text='', font=('Arial', 12), fill='red')

    # Validate login
    def validate_login():
        user = username_entry.get().strip()
        pwd = password_entry.get().strip()
        if not user or not pwd:
            canvas.itemconfig(msg_id, text='Please enter both fields')
            return
        try:
            resp = requests.post(
                'https://spintofortune.in/api/app-sign-in.php',
                data={'login': user, 'password': pwd},
                timeout=10
            )
            result = resp.json()
        except Exception as e:
            canvas.itemconfig(msg_id, text=f'Error: {e}')
            return
        if result.get('status'):
            data = result.get('data', {})
            root.destroy()
            import main_app
            main_app.launch_main_app(data)
        else:
            canvas.itemconfig(msg_id, text=result.get('message', 'Login failed.'))

    # Submit button
    submit_btn = tk.Button(
        root,
        text='Submit',
        command=validate_login,
        font=('Arial', 14),
        bg='#27ae60',
        fg='white',
        bd=0,
        padx=10,
        pady=5
    )
    canvas.create_window(form_x + form_w // 2, form_y + 230, window=submit_btn)

    # Close button
    def exit_app():
        root.destroy()

    close_btn = tk.Button(
        root,
        text='✕',
        command=exit_app,
        font=('Arial', 12, 'bold'),
        bg='red',
        fg='white',
        bd=0
    )
    canvas.create_window(screen_width - 30, 20, window=close_btn)

    root.mainloop()

if __name__ == '__main__':
    launch_login()
