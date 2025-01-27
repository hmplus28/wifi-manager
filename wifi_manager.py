import subprocess
import time
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import winsound
import threading
from tkinter import font as tkfont
import winshell
from win32com.client import Dispatch
import pystray
from PIL import Image, ImageDraw

# تنظیمات اولیه
BASE_DIR = os.path.dirname(__file__)  # مسیر دایرکتوری فایل فعلی
CONFIG_FILE = os.path.join(BASE_DIR, "wifi_config.json")  # مسیر فایل پیکربندی
LANG_FILE = os.path.join(BASE_DIR, "language.json")  # مسیر فایل زبان
ICON_PATH = os.path.join(BASE_DIR, "wifi_icon.ico")  # مسیر فایل آیکون

# تنظیمات زبان
LANGUAGES = {
    "en": {
        "title": "Wi-Fi Manager",
        "ssid_label": "SSID:",
        "password_label": "Password:",
        "connect_button": "Connect",
        "disconnect_button": "Disconnect",
        "auto_connect": "Auto Connect",
        "add_to_startup": "Add to Startup",
        "select_wifi": "Select Wi-Fi",
        "save_wifi": "Save Wi-Fi",
        "language_button": "فارسی",
        "help_title": "Help",
        "help_text": "You can connect to your Wi-Fi every time without disconnection. With the help of this tool, you can stay permanently connected to Wi-Fi and avoid disconnections.",
        "github_id": "GitHub ID: @hmplus28"
    },
    "fa": {
        "title": "مدیریت وای‌فای",
        "ssid_label": "نام شبکه:",
        "password_label": "رمز عبور:",
        "connect_button": "اتصال",
        "disconnect_button": "قطع اتصال",
        "auto_connect": "اتصال خودکار",
        "add_to_startup": "اضافه به استارتاپ",
        "select_wifi": "انتخاب وای‌فای",
        "save_wifi": "ذخیره وای‌فای",
        "language_button": "English",
        "help_title": "راهنمایی",
        "help_text": "با کمک این ابزار می‌توانید به طور دائم به وای‌فای وصل باشید و از آن قطع نشوید.",
        "github_id": "آیدی گیت هاب: @hmplus28"
    }
}

# ذخیره‌سازی تنظیمات
def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    else:
        config = {"wifi_list": [], "auto_connect": False, "language": "en"}

    # Ensure the "wifi_list" key exists
    if "wifi_list" not in config:
        config["wifi_list"] = []

    return config

# تغییر زبان
def change_language():
    config = load_config()
    new_lang = "fa" if config.get("language", "en") == "en" else "en"
    config["language"] = new_lang
    save_config(config)
    update_ui()

# به‌روزرسانی رابط کاربری با زبان انتخاب‌شده
def update_ui():
    config = load_config()
    lang = config.get("language", "en")
    texts = LANGUAGES[lang]
    root.title(texts["title"])
    ssid_label.config(text=texts["ssid_label"])
    password_label.config(text=texts["password_label"])
    connect_button.config(text=texts["connect_button"])
    disconnect_button.config(text=texts["disconnect_button"])
    auto_connect_check.config(text=texts["auto_connect"])
    add_to_startup_button.config(text=texts["add_to_startup"])
    select_wifi_button.config(text=texts["select_wifi"])
    save_wifi_button.config(text=texts["save_wifi"])
    language_button.config(text=texts["language_button"])
    help_button.config(text=texts["help_title"])
    help_text.set(texts["help_text"])
    github_id_label.config(text=texts["github_id"])

# اتصال به وای‌فای
def connect_to_wifi(ssid, password=None, show_message=True):
    try:
        subprocess.run(["netsh", "wlan", "disconnect"], shell=True, check=True)

        if password:
            config = f"""<?xml version=\"1.0\"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>{ssid}</name>
    <SSIDConfig>
        <SSID>
            <name>{ssid}</name>
        </SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>WPA2PSK</authentication>
                <encryption>AES</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
            <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>{password}</keyMaterial>
            </sharedKey>
        </security>
    </MSM>
</WLANProfile>"""

            with open(f"{ssid}.xml", "w") as f:
                f.write(config)

            subprocess.run(["netsh", "wlan", "add", "profile", f"filename={ssid}.xml"], shell=True, check=True)

        subprocess.run(["netsh", "wlan", "connect", f"name={ssid}"], shell=True, check=True)

        if show_message:
            messagebox.showinfo(LANGUAGES[load_config().get("language", "en")]["title"], f"Connected to {ssid} successfully.")
        else:
            winsound.Beep(1000, 500)  # پخش صدای بیپ
    except subprocess.CalledProcessError as e:
        messagebox.showerror(LANGUAGES[load_config().get("language", "en")]["title"], f"Error connecting to Wi-Fi: {e}")

# قطع اتصال وای‌فای
def disconnect_wifi():
    try:
        subprocess.run(["netsh", "wlan", "disconnect"], shell=True, check=True)
        messagebox.showinfo(LANGUAGES[load_config().get("language", "en")]["title"], "Disconnected from Wi-Fi.")
    except subprocess.CalledProcessError as e:
        messagebox.showerror(LANGUAGES[load_config().get("language", "en")]["title"], f"Error disconnecting from Wi-Fi: {e}")

# بررسی اتصال
def check_connection(ssid):
    first_connection = True
    while True:
        result = subprocess.run(["netsh", "wlan", "show", "interfaces"], shell=True, capture_output=True, text=True)
        if ssid in result.stdout:
            time.sleep(5)
        else:
            if first_connection:
                connect_to_wifi(ssid, show_message=first_connection)
                first_connection = False
            time.sleep(10)

# شروع اتصال
def start_connection():
    ssid = ssid_entry.get()
    password = password_entry.get()
    config = load_config()
    config["wifi_list"].append({"ssid": ssid, "password": password})
    save_config(config)
    connect_to_wifi(ssid, password)
    threading.Thread(target=check_connection, args=(ssid,), daemon=True).start()

# انتخاب وای‌فای ذخیره‌شده
def select_wifi():
    config = load_config()
    if not config["wifi_list"]:
        messagebox.showinfo(LANGUAGES[load_config().get("language", "en")]["title"], "No saved Wi-Fi networks.")
        return

    def on_select(event):
        selected = wifi_var.get()
        for wifi in config["wifi_list"]:
            if wifi["ssid"] == selected:
                connect_to_wifi(wifi["ssid"], wifi["password"])
                ssid_entry.delete(0, tk.END)
                ssid_entry.insert(0, wifi["ssid"])
                password_entry.delete(0, tk.END)
                password_entry.insert(0, wifi["password"])
                select_window.destroy()
                break

    select_window = tk.Toplevel(root)
    select_window.title(LANGUAGES[load_config().get("language", "en")]["select_wifi"])

    wifi_var = tk.StringVar()
    wifi_dropdown = ttk.Combobox(select_window, textvariable=wifi_var)
    wifi_dropdown["values"] = [wifi["ssid"] for wifi in config["wifi_list"]]
    wifi_dropdown.bind("<<ComboboxSelected>>", on_select)
    wifi_dropdown.pack(padx=20, pady=20)

# ذخیره وای‌فای
def save_wifi():
    ssid = ssid_entry.get()
    password = password_entry.get()
    config = load_config()
    config["wifi_list"].append({"ssid": ssid, "password": password})
    save_config(config)
    messagebox.showinfo(LANGUAGES[load_config().get("language", "en")]["title"], "Wi-Fi saved successfully.")

# اضافه به استارتاپ
def add_to_startup():
    try:
        # مسیر فایل اجرایی برنامه
        program_path = os.path.abspath(__file__)

        # مسیر پوشه استارتاپ
        startup_folder = os.path.join(
            os.environ["APPDATA"],
            "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
        )

        # ایجاد میانبر در پوشه استارتاپ
        shortcut_path = os.path.join(startup_folder, "WiFi Manager.lnk")
        if not os.path.exists(shortcut_path):
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = program_path
            shortcut.WorkingDirectory = os.path.dirname(program_path)
            shortcut.save()

            messagebox.showinfo(
                LANGUAGES[load_config().get("language", "en")]["title"],
                "Program added to startup successfully."
            )
        else:
            messagebox.showinfo(
                LANGUAGES[load_config().get("language", "en")]["title"],
                "Program is already in startup."
            )
    except Exception as e:
        messagebox.showerror(
            LANGUAGES[load_config().get("language", "en")]["title"],
            f"Error adding to startup: {e}"
        )

# ایجاد رابط کاربری
root = tk.Tk()
root.title("Wi-Fi Manager")
if os.path.exists(ICON_PATH):
    root.iconbitmap(ICON_PATH)

# فونت بهتر
custom_font = tkfont.Font(family="Tahoma", size=10)

# اجزای رابط کاربری
ssid_label = tk.Label(root, text="SSID:", font=custom_font)
ssid_label.grid(row=0, column=0, padx=10, pady=10)
ssid_entry = tk.Entry(root, font=custom_font)
ssid_entry.grid(row=0, column=1, padx=10, pady=10)

password_label = tk.Label(root, text="Password:", font=custom_font)
password_label.grid(row=1, column=0, padx=10, pady=10)
password_entry = tk.Entry(root, show="*", font=custom_font)
password_entry.grid(row=1, column=1, padx=10, pady=10)

auto_connect_var = tk.BooleanVar()
auto_connect_check = tk.Checkbutton(
    root,
    text="Auto Connect",
    variable=auto_connect_var,
    font=custom_font,
    command=lambda: save_config({**load_config(), "auto_connect": auto_connect_var.get()})
)
auto_connect_check.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

connect_button = tk.Button(root, text="Connect", command=start_connection, font=custom_font)
connect_button.grid(row=3, column=0, padx=10, pady=10)

disconnect_button = tk.Button(root, text="Disconnect", command=disconnect_wifi, font=custom_font)
disconnect_button.grid(row=3, column=1, padx=10, pady=10)

select_wifi_button = tk.Button(root, text="Select Wi-Fi", command=select_wifi, font=custom_font)
select_wifi_button.grid(row=4, column=0, padx=10, pady=10)

save_wifi_button = tk.Button(root, text="Save Wi-Fi", command=save_wifi, font=custom_font)
save_wifi_button.grid(row=4, column=1, padx=10, pady=10)

add_to_startup_button = tk.Button(root, text="Add to Startup", command=add_to_startup, font=custom_font)
add_to_startup_button.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

language_button = tk.Button(root, text="فارسی", command=change_language, font=custom_font)
language_button.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

help_text = tk.StringVar()
help_button = tk.Button(root, text="Help", command=lambda: messagebox.showinfo(LANGUAGES[load_config().get("language", "en")]["help_title"], help_text.get()), font=custom_font)
help_button.grid(row=7, column=0, columnspan=2, padx=10, pady=10)

github_id_label = tk.Label(root, text="GitHub ID: your_github_id", font=custom_font)
github_id_label.grid(row=8, column=0, columnspan=2, padx=10, pady=10)

# بارگذاری تنظیمات و به‌روزرسانی رابط کاربری
config = load_config()
auto_connect_var.set(config.get("auto_connect", False))
update_ui()

# بررسی اتصال خودکار
if config.get("auto_connect", False) and config["wifi_list"]:
    ssid = config["wifi_list"][0]["ssid"]
    password = config["wifi_list"][0]["password"]
    connect_to_wifi(ssid, password, show_message=False)

# تابع برای مینیمایز کردن به سیستم تری
def minimize_to_tray():
    root.withdraw()
    image = Image.open(ICON_PATH)
    menu = (pystray.MenuItem('Quit', quit_app),)
    icon = pystray.Icon("name", image, "Wi-Fi Manager", menu)
    icon.run()

def quit_app(icon, item):
    icon.stop()
    os._exit(0)

root.protocol('WM_DELETE_WINDOW', minimize_to_tray)

root.mainloop()