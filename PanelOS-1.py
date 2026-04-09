import os
import platform
import psutil
import subprocess
import sys
import tkinter as tk
import tkinter.font as tkfont

class PushTerminal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Push Terminal")
        self.geometry("800x600")
        self.resizable(True, True)
        self.font = tkfont.Font(family="JetBrains Mono Regular", size=12)
        self.scrollbar = tk.Scrollbar(self)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text = tk.Text(self, height=20, width=80, font=self.font, bg="black", fg="white", insertbackground="white", yscrollcommand=self.scrollbar.set)
        self.text.pack(fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.text.yview)
        self.entry = tk.Entry(self, font=self.font, bg="black", fg="white", insertbackground="white")
        self.entry.pack(fill=tk.X)
        self.entry.bind("<Return>", self.process_command)
        self.text.tag_configure("red", foreground="red")
        self.text.tag_configure("cyan", foreground="cyan")
        self.text.tag_configure("yellow", foreground="yellow")
        self.text.tag_configure("green", foreground="green")
        self.waiting_for_input = False
        self.input_callback = None
        self.text.config(state="disabled")
        self.print("Push Terminal", "green")
        self.print("type help for help")
        self.entry.focus()

    def print(self, text, color=None):
        self.text.config(state="normal")
        self.text.insert(tk.END, text + "\n", color)
        self.text.config(state="disabled")
        self.text.see(tk.END)

    def prompt_input(self, prompt, callback):
        self.print(prompt)
        self.waiting_for_input = True
        self.input_callback = callback

    def process_command(self, event):
        command = self.entry.get().strip()
        self.entry.delete(0, tk.END)
        if self.waiting_for_input:
            self.waiting_for_input = False
            if self.input_callback:
                self.input_callback(command)
            return
        if command == "fetch":
            self.print("HOST OS: " + platform.system() + " " + platform.release(), "green")
            self.print("CPU: " + platform.processor(), "green")
            self.print("RAM: " + str(round(psutil.virtual_memory().total / (1024**3), 1)) + " GB", "green")
            self.print("Python: " + platform.python_version(), "green")
        elif command == "help":
            self.print("command list: fetch, quit, systemterminal, apps, python, colorguide, pwsh <command> (Windows), linux <command> (Linux), about")
        elif command == "systemterminal":
            self.print("opening system terminal", "cyan")
            if platform.system() == "Windows":
                subprocess.Popen("start cmd", shell=True)
            elif platform.system() == "Linux":
                subprocess.Popen("x-terminal-emulator", shell=True)
                self.print("system terminal opened", "green")
            else:
                self.print("Unsupported OS", "red")
        elif command == "apps":
            self.print("Scanning for installed apps. This may take a moment...", "cyan")
            apps = self.scan_apps()
            if not apps:
                self.print("No apps found.", "red")
            else:
                app_names = sorted(apps.keys())
                self.print(f"Found {len(app_names)} apps.", "green")
                for name in app_names[:100]:
                    self.print(name)
                if len(app_names) > 100:
                    self.print(f"...and {len(app_names) - 100} more", "cyan")
                self.prompt_input("Type the app name to open, or press Enter to cancel: ", lambda choice: self.launch_app(choice, apps) if choice else None)
        elif command == "python":
            self.print("Scanning for Python scripts. This may take a moment...", "cyan")
            scripts = self.scan_python_files()
            if not scripts:
                self.print("No Python scripts found.", "red")
            else:
                script_names = sorted(scripts.keys())
                self.print(f"Found {len(script_names)} Python scripts.", "green")
                for name in script_names[:100]:
                    self.print(name)
                if len(script_names) > 100:
                    self.print(f"...and {len(script_names) - 100} more", "cyan")
                self.prompt_input("Type the script name or path to run, or press Enter to cancel: ", lambda choice: self.launch_python_script(choice, scripts) if choice else None)
        elif command == "quit":
            self.quit()
        elif command == "about":
            self.print("Push Terminal v1.0", "green")
            self.print("A simple command-line interface for system operations.")
            self.print("Supports Windows and Linux platforms.")
        elif command == "colorguide":
            self.print("color guide:")
            self.print("green: success", "green")
            self.print("cyan: working", "cyan")
            self.print("yellow: warning", "yellow")
            self.print("red: error", "red")
        elif command.startswith("pwsh "):
            subcommand = command[5:].strip()
            if platform.system() == "Windows":
                try:
                    result = subprocess.run(["powershell", "-Command", subcommand], capture_output=True, text=True)
                    if result.stdout:
                        self.print(result.stdout.strip())
                    if result.stderr:
                        self.print(result.stderr.strip(), "red")
                    if result.returncode == 0:
                        self.print("Executed: " + subcommand, "green")
                    else:
                        self.print("Command failed with return code: " + str(result.returncode), "red")
                except Exception as e:
                    self.print("Error executing command: " + str(e), "red")
            else:
                self.print("pwsh command only available on Windows", "red")
        elif command.startswith("linux "):
            subcommand = command[6:].strip()
            if platform.system() == "Linux":
                try:
                    result = subprocess.run("sudo " + subcommand, shell=True, capture_output=True, text=True)
                    if result.stdout:
                        self.print(result.stdout.strip())
                    if result.stderr:
                        self.print(result.stderr.strip(), "red")
                    if result.returncode == 0:
                        self.print("Executed: " + subcommand, "green")
                    else:
                        self.print("Command failed with return code: " + str(result.returncode), "red")
                except Exception as e:
                    self.print("Error executing command: " + str(e), "red")
            else:
                self.print("linux command only available on Linux", "red")
        else:
            self.print(f"Unknown command: {command}", "red")

    def is_executable_file(self, path):
        if platform.system() == "Windows":
            return path.lower().endswith((".exe", ".bat", ".cmd", ".com"))
        return os.path.isfile(path) and os.access(path, os.X_OK)

    def scan_apps(self):
        system = platform.system()
        search_dirs = set()
        search_dirs.update(d for d in os.environ.get("PATH", "").split(os.pathsep) if d)
        if system == "Windows":
            for env_var in ("ProgramFiles", "ProgramFiles(x86)", "SystemRoot"):
                dir_path = os.environ.get(env_var)
                if dir_path:
                    search_dirs.add(dir_path)
        elif system == "Linux":
            search_dirs.update(["/usr/bin", "/usr/local/bin", "/opt"])
        apps = {}
        def walk_folder(folder, depth=0):
            if depth > 3:
                return
            try:
                with os.scandir(folder) as it:
                    for entry in it:
                        if entry.is_dir(follow_symlinks=False):
                            walk_folder(entry.path, depth + 1)
                        elif entry.is_file(follow_symlinks=False) and self.is_executable_file(entry.path):
                            name = entry.name.lower()
                            if name not in apps:
                                apps[name] = entry.path
            except (PermissionError, FileNotFoundError, OSError):
                return
        for directory in search_dirs:
            if os.path.isdir(directory):
                walk_folder(directory, 0)
        return apps

    def launch_app(self, app_name, apps):
        target = app_name.strip().lower()
        if not target:
            self.print("No app entered.", "red")
            return False
        exact_matches = [path for name, path in apps.items() if name == target]
        partial_matches = [path for name, path in apps.items() if target in name]
        candidates = exact_matches or partial_matches
        if not candidates:
            self.print("App not found: " + app_name, "red")
            return False
        if len(candidates) > 1:
            self.print("Multiple matches found:")
            for idx, path in enumerate(candidates, 1):
                self.print(f"{idx}. {os.path.basename(path)} - {path}")
            self.prompt_input("Choose number to open: ", lambda choice: self.launch_selected_app(choice, candidates))
        else:
            target_path = candidates[0]
            try:
                if platform.system() == "Windows":
                    os.startfile(target_path)
                else:
                    subprocess.Popen([target_path])
                self.print("Opened " + target_path, "green")
                return True
            except Exception as err:
                self.print("Failed to open app: " + str(err), "red")
                return False

    def launch_selected_app(self, choice, candidates):
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(candidates):
            self.print("Invalid selection.", "red")
            return False
        target_path = candidates[int(choice) - 1]
        try:
            if platform.system() == "Windows":
                os.startfile(target_path)
            else:
                subprocess.Popen([target_path])
            self.print("Opened " + target_path, "green")
            return True
        except Exception as err:
            self.print("Failed to open app: " + str(err), "red")
            return False

    def scan_python_files(self):
        search_dirs = {os.getcwd()}
        search_dirs.update(d for d in os.environ.get("PATH", "").split(os.pathsep) if d)
        if platform.system() == "Windows":
            for env_var in ("USERPROFILE", "PROGRAMDATA"):
                dir_path = os.environ.get(env_var)
                if dir_path:
                    search_dirs.add(dir_path)
        else:
            home_dir = os.environ.get("HOME")
            if home_dir:
                search_dirs.add(home_dir)
            search_dirs.update(["/usr/bin", "/usr/local/bin", "/opt"])
        scripts = {}
        def walk_folder(folder, depth=0):
            if depth > 3:
                return
            try:
                with os.scandir(folder) as it:
                    for entry in it:
                        if entry.is_dir(follow_symlinks=False):
                            walk_folder(entry.path, depth + 1)
                        elif entry.is_file(follow_symlinks=False) and entry.name.lower().endswith(".py"):
                            name = entry.name.lower()
                            if name not in scripts:
                                scripts[name] = entry.path
            except (PermissionError, FileNotFoundError, OSError):
                return
        for directory in search_dirs:
            if os.path.isdir(directory):
                walk_folder(directory, 0)
        return scripts

    def launch_python_script(self, script_name, scripts):
        target = script_name.strip()
        if not target:
            self.print("No script entered.", "red")
            return False
        if os.path.isabs(target) or os.path.exists(target):
            if target.lower().endswith(".py"):
                target_path = target
            else:
                self.print("Path is not a Python script.", "red")
                return False
        else:
            lower_target = target.lower()
            exact_matches = [path for name, path in scripts.items() if name == lower_target]
            partial_matches = [path for name, path in scripts.items() if lower_target in name]
            candidates = exact_matches or partial_matches
            if not candidates:
                self.print("Script not found: " + script_name, "red")
                return False
            if len(candidates) > 1:
                self.print("Multiple matches found:")
                for idx, path in enumerate(candidates, 1):
                    self.print(f"{idx}. {os.path.basename(path)} - {path}")
                self.prompt_input("Choose number to run: ", lambda choice: self.launch_selected_script(choice, candidates))
            else:
                target_path = candidates[0]
        try:
            subprocess.run([sys.executable, target_path])
            self.print("Ran " + target_path, "green")
            return True
        except Exception as err:
            self.print("Failed to run script: " + str(err), "red")
            return False

    def launch_selected_script(self, choice, candidates):
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(candidates):
            self.print("Invalid selection.", "red")
            return False
        target_path = candidates[int(choice) - 1]
        try:
            subprocess.run([sys.executable, target_path])
            self.print("Ran " + target_path, "green")
            return True
        except Exception as err:
            self.print("Failed to run script: " + str(err), "red")
            return False

if __name__ == "__main__":
    if platform.system() == "Windows":
        try:
            import ctypes
            kernel32 = ctypes.WinDLL('kernel32')
            user32 = ctypes.WinDLL('user32')
            hwnd = kernel32.GetConsoleWindow()
            if hwnd:
                user32.ShowWindow(hwnd, 0)
        except Exception:
            pass
    app = PushTerminal()
    app.mainloop()