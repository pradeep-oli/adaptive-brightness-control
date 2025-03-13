import customtkinter as ctk
import cv2
import screen_brightness_control as sbc
import threading
import time
import pystray
from PIL import Image
import os

class BrightnessControl(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Brightness Control")
        self.geometry("300x400")
        self.attributes('-alpha', 1.0)
        ctk.set_appearance_mode("dark")
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
            icon_image = Image.open(icon_path)
            self.tray_icon_image = icon_image
            ctk_icon = ctk.CTkImage(light_image=icon_image, dark_image=icon_image, size=(32, 32))
            self.iconbitmap(icon_path)

        # Initialize variables
        self.auto_brightness = True
        self.auto_brightness_thread = None
        self.current_brightness = sbc.get_brightness()[0]
        self.is_minimized = False
        self.tray_thread = None
        self.tray_icon = None

        # Create main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Title label
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Brightness Control",
            font=("Helvetica", 24)
        )
        self.title_label.pack(pady=20)

        # Manual brightness control
        self.brightness_label = ctk.CTkLabel(
            self.main_frame,
            text=f"Brightness: {self.current_brightness}%",
            font=("Helvetica", 16)
        )
        self.brightness_label.pack(pady=10)

        self.brightness_slider = ctk.CTkSlider(
            self.main_frame,
            from_=0,
            to=100,
            command=lambda value: self.update_brightness(value),
            number_of_steps=100
        )
        self.brightness_slider.set(self.current_brightness)
        self.brightness_slider.pack(pady=10, padx=20, fill="x")
        self.brightness_slider.configure(state="normal")
        self.brightness_slider.bind("<Button-1>", lambda e: self.enable_manual_control())

        # Status label
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="Auto brightness disabled",
            font=("Helvetica", 12)
        )
        self.status_label.pack(pady=10)

        # Auto brightness toggle
        self.auto_switch = ctk.CTkSwitch(
            self.main_frame,
            text="Auto Brightness",
            command=self.toggle_auto_brightness,
            font=("Helvetica", 16)
        )
        self.auto_switch.pack(pady=10)
        self.auto_switch.select()

        # Minimize to tray button
        self.minimize_button = ctk.CTkButton(
            self.main_frame,
            text="Minimize to Tray",
            command=self.minimize_to_tray,
            font=("Helvetica", 16)
        )
        self.minimize_button.pack(pady=10)

        # Stop button
        self.stop_button = ctk.CTkButton(
            self.main_frame,
            text="Stop Application",
            command=self.stop_application,
            font=("Helvetica", 16),
            fg_color="#D35B58",  # Red color for warning
            hover_color="#C83532"  # Darker red for hover
        )
        self.stop_button.pack(pady=10)

        # Watermark label
        self.watermark_label = ctk.CTkLabel(
            self.main_frame,
            text="Developed by Pradeep Oli",
            font=("Helvetica", 10),
            text_color="gray"
        )
        self.watermark_label.pack(pady=(0, 10))

        # Setup system tray
        self.setup_system_tray()

        # Enable auto-brightness immediately
        self.toggle_auto_brightness()

        # Bind window close event
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_system_tray(self):
        # Use the application icon for the system tray
        icon_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "icon.ico")
        icon = Image.open(icon_path) if os.path.exists(icon_path) else Image.new('RGB', (64, 64), color='black')
        
        # Create menu items
        menu = pystray.Menu(
            pystray.MenuItem(
                "Show",
                self.show_window,
                default=True
            ),
            pystray.MenuItem(
                "Exit",
                self.quit_window
            )
        )
        
        # Create the tray icon
        self.tray_icon = pystray.Icon(
            "brightness_control",
            icon,
            "Brightness Control",
            menu
        )
        
        # Apply dark theme using Win32 API
        if os.name == 'nt':  # Windows only
            try:
                import ctypes
                from ctypes import wintypes
                import winreg
                
                # Constants
                DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                DWMWA_SYSTEMBACKDROP_TYPE = 38
                DWMWA_MICA_EFFECT = 1029
                HKEY_CURRENT_USER = winreg.HKEY_CURRENT_USER
                KEY_ALL_ACCESS = winreg.KEY_ALL_ACCESS
                REG_DWORD = winreg.REG_DWORD
                
                # Set Windows 11 dark context menu
                try:
                    key = winreg.CreateKeyEx(HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", 0, KEY_ALL_ACCESS)
                    winreg.SetValueEx(key, "UseCustomContextMenu", 0, REG_DWORD, 0)
                    winreg.SetValueEx(key, "TaskbarAcrylicOpacity", 0, REG_DWORD, 1)
                    winreg.SetValueEx(key, "TaskbarTheme", 0, REG_DWORD, 1)  # Force dark theme
                    winreg.CloseKey(key)
                    
                    # Set personalization settings
                    personalization_key = winreg.CreateKeyEx(HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize", 0, KEY_ALL_ACCESS)
                    winreg.SetValueEx(personalization_key, "AppsUseLightTheme", 0, REG_DWORD, 0)
                    winreg.SetValueEx(personalization_key, "SystemUsesLightTheme", 0, REG_DWORD, 0)
                    winreg.SetValueEx(personalization_key, "EnableTransparency", 0, REG_DWORD, 1)
                    winreg.CloseKey(personalization_key)
                except Exception as e:
                    print(f"Failed to set registry keys: {e}")
                
                # Function prototypes
                SetWindowTheme = ctypes.windll.uxtheme.SetWindowTheme
                set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
                get_parent = ctypes.windll.user32.GetParent
                get_window_thread_process_id = ctypes.windll.user32.GetWindowThreadProcessId
                get_current_thread_id = ctypes.windll.kernel32.GetCurrentThreadId
                attach_thread_input = ctypes.windll.user32.AttachThreadInput
                
                def set_dark_mode(hwnd):
                    # Apply dark mode
                    value = ctypes.c_int(2)  # 2 = dark mode
                    set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                                       ctypes.byref(value),
                                       ctypes.sizeof(value))
                    
                    # Apply system backdrop
                    backdrop_value = ctypes.c_int(4)  # 4 = DWMSBT_MAINWINDOW
                    set_window_attribute(hwnd, DWMWA_SYSTEMBACKDROP_TYPE,
                                       ctypes.byref(backdrop_value),
                                       ctypes.sizeof(backdrop_value))
                    
                    # Set dark theme
                    SetWindowTheme(hwnd, "DarkMode_Explorer", None)
                    
                    # Attach to window thread to ensure theme is applied
                    window_thread = get_window_thread_process_id(hwnd, None)
                    current_thread = get_current_thread_id()
                    if window_thread != current_thread:
                        attach_thread_input(window_thread, current_thread, True)
                        SetWindowTheme(hwnd, "DarkMode_Explorer", None)
                        attach_thread_input(window_thread, current_thread, False)
                
                def win_enum_callback(hwnd, _):
                    # Check if this window belongs to our tray icon
                    parent = get_parent(hwnd)
                    if parent == 0:  # Top-level window
                        try:
                            set_dark_mode(hwnd)
                        except:
                            pass
                    return True
                
                # Enumerate windows to apply dark mode
                enum_windows = ctypes.windll.user32.EnumWindows
                enum_windows.argtypes = [ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int), ctypes.c_int]
                enum_windows.restype = ctypes.c_bool
                
                # Set callback
                WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
                callback = WNDENUMPROC(win_enum_callback)
                
                # Apply dark mode to all windows
                enum_windows(callback, 0)
            except Exception as e:
                print(f"Failed to apply dark theme: {e}")

    def run_tray_icon(self):
        try:
            self.tray_icon.run()
        except Exception as e:
            print(f"Error running tray icon: {e}")
            self.deiconify()

    def minimize_to_tray(self):
        if hasattr(self, 'tray_icon') and self.tray_icon is not None:
            self.tray_icon.stop()
        self.withdraw()
        self.setup_system_tray()  # Create a new tray icon instance
        self.tray_thread = threading.Thread(target=self.run_tray_icon)
        self.tray_thread.daemon = True
        self.tray_thread.start()

    def show_window(self, icon=None):
        if hasattr(self, 'tray_icon'):
            self.tray_icon.stop()
            self.tray_icon = None
        self.deiconify()
        self.lift()
        self.focus_force()

    def stop_application(self):
        # Stop auto-brightness if running
        if self.auto_brightness:
            self.auto_brightness = False
            if self.auto_brightness_thread:
                self.auto_brightness_thread.join(timeout=1)

        # Stop system tray if running
        if hasattr(self, 'tray_icon') and self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None

        # Destroy the window and quit the application
        self.quit()
        self.destroy()

    def quit_window(self, icon=None):
        self.stop_application()

    def on_closing(self):
        self.minimize_to_tray()

    def update_brightness(self, value):
        try:
            brightness = min(max(int(float(value)), 0), 100)  # Ensure value is between 0 and 100
            sbc.set_brightness(brightness)
            self.current_brightness = brightness
            self.brightness_label.configure(text=f"Brightness: {brightness}%")
            self.brightness_slider.set(brightness)  # Ensure slider position matches actual brightness
        except Exception as e:
            print(f"Error setting brightness: {e}")
            # Restore slider to previous valid brightness
            self.brightness_slider.set(self.current_brightness)

    def enable_manual_control(self):
        if self.auto_brightness:
            self.auto_switch.deselect()
            self.toggle_auto_brightness()

    def toggle_auto_brightness(self):
        self.auto_brightness = self.auto_switch.get()
        if self.auto_brightness:
            self.status_label.configure(text="Auto brightness enabled")
            self.start_auto_brightness()
        else:
            self.status_label.configure(text="Auto brightness disabled")
            self.stop_auto_brightness()

    def start_auto_brightness(self):
        if not self.auto_brightness_thread or not self.auto_brightness_thread.is_alive():
            self.auto_brightness_thread = threading.Thread(target=self.auto_brightness_loop)
            self.auto_brightness_thread.daemon = True
            self.auto_brightness_thread.start()

    def stop_auto_brightness(self):
        self.auto_brightness = False
        if self.auto_brightness_thread:
            self.auto_brightness_thread.join(timeout=1)

    def auto_brightness_loop(self):
        cap = cv2.VideoCapture(0)
        while self.auto_brightness:
            ret, frame = cap.read()
            if ret and self.auto_brightness:  # Double-check auto_brightness state
                # Calculate average brightness
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                avg_brightness = int(gray.mean())
                
                # Map camera brightness (0-255) to screen brightness (0-100)
                screen_brightness = int((avg_brightness / 255) * 100)
                
                # Only update if auto-brightness is still enabled
                if self.auto_brightness:
                    sbc.set_brightness(screen_brightness)
                    self.current_brightness = screen_brightness
                    self.brightness_label.configure(text=f"Brightness: {screen_brightness}%")
                    self.brightness_slider.set(screen_brightness)
                
                time.sleep(1)  # Adjust delay as needed
            
        cap.release()

if __name__ == "__main__":
    app = BrightnessControl()
    app.mainloop()