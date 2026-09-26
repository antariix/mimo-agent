#!/usr/bin/env python3
"""
Creates a desktop shortcut for the Modern Calculator App.
The shortcut launches via pythonw.exe (no terminal window popup)
and uses the custom calculator icon.
"""

import os
import sys

def get_desktop_path() -> str:
    """Gets the path to the current user's Desktop."""
    # Try win32com or shell
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        return shell.SpecialFolders("Desktop")
    except Exception:
        # Fallback to standard user desktop
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if os.path.exists(desktop):
            return desktop
        # Try OneDrive desktop if enabled
        onedrive_desktop = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
        if os.path.exists(onedrive_desktop):
            return onedrive_desktop
        return desktop

def find_pythonw() -> str:
    """Finds the pythonw.exe executable."""
    py_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(py_dir, "pythonw.exe")
    if os.path.exists(pythonw):
        return pythonw
    return sys.executable

def create_shortcut():
    repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    script_path = os.path.join(repo_dir, "scripts", "calculator.py")
    icon_path = os.path.join(repo_dir, "assets", "calculator.ico")
    desktop_dir = get_desktop_path()
    shortcut_path = os.path.join(desktop_dir, "Calculator.lnk")

    pythonw_path = find_pythonw()

    print(f"Creating shortcut on: {shortcut_path}")
    print(f"Target: {pythonw_path}")
    print(f"Script: {script_path}")
    print(f"Icon: {icon_path}")

    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = pythonw_path
        shortcut.Arguments = f'"{script_path}"'
        shortcut.WorkingDirectory = repo_dir
        if os.path.exists(icon_path):
            shortcut.IconLocation = f"{icon_path},0"
        shortcut.Description = "Modern Scientific & Standard Calculator"
        shortcut.Save()
        print("[OK] Desktop shortcut created successfully via WScript.Shell!")
        return True
    except Exception as e:
        print(f"COM dispatch fallback ({e}), attempting PowerShell fallback...")
        import subprocess
        ps_cmd = f"""
        $WshShell = New-Object -ComObject WScript.Shell;
        $Shortcut = $WshShell.CreateShortcut('{shortcut_path}');
        $Shortcut.TargetPath = '{pythonw_path}';
        $Shortcut.Arguments = '"{script_path}"';
        $Shortcut.WorkingDirectory = '{repo_dir}';
        $Shortcut.IconLocation = '{icon_path},0';
        $Shortcut.Description = 'Modern Scientific & Standard Calculator';
        $Shortcut.Save();
        """
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
        if res.returncode == 0:
            print("[OK] Desktop shortcut created successfully via PowerShell!")
            return True
        else:
            print(f"PowerShell error: {res.stderr}")
            return False

if __name__ == "__main__":
    create_shortcut()
