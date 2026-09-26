# Scripts

## hello.py

A simple script that prints a welcome message.

**Usage:**
```bash
python hello.py
```

**Output:**
```
Welcome to MiMo Code Agent!
```

---

## sys_check.py

Displays system information including:
- Operating system name
- CPU core count
- RAM utilization percentage

**Requirements:**
```bash
pip install psutil
```

**Usage:**
```bash
python sys_check.py
```

**Example Output:**
```
OS: Windows
CPU Cores: 18
RAM Utilization: 74.7%
```

---

## calculator.py

A modern GUI calculator application built with Tkinter.

**Features:**
- **Standard & Scientific Modes**: Trigonometry (`sin`, `cos`, `tan`, `asin`, `acos`, `atan`), logarithms (`ln`, `log`, `log₂`), powers, roots, factorial (`n!`), and constants (`π`, `e`).
- **Interactive Calculation History**: Expandable history sidebar with clickable entries to recall expressions and answers.
- **Memory Operations**: `MC`, `MR`, `M+`, `M-`, `MS` with an active memory indicator badge.
- **Themes**: Switch between Modern Dark and Light themes with a single click.
- **Physical Keyboard Support**: Full keyboard input support with tactile button flash feedback animations.
- **Clipboard Integration**: Copy results directly via click or `Ctrl+C`.
- **High-DPI Aware**: Crisp typography on high-resolution Windows displays.
- **Zero External Dependencies**: Pure Python standard library (`tkinter`, `math`, `ast`).

**Usage:**
```bash
python scripts/calculator.py
```

---

## create_desktop_shortcut.py

Creates a Windows desktop shortcut for the Calculator app with the custom icon and silent background execution (`pythonw.exe`).

**Usage:**
```bash
python scripts/create_desktop_shortcut.py
```

