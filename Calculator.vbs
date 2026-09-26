' Launches Calculator GUI silently with pythonw (no command prompt window)
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "pythonw.exe """ & "scripts\calculator.py" & """", 0, False
