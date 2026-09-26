# Modern GUI Calculator — Application Guide & Session Context

This document captures the complete technical context, architecture, operational guide, and artifact reference for the **Modern GUI Calculator Application** built for Windows.

---

## 1. Executive Summary & Deliverables

A modern, high-DPI aware, desktop-ready calculator built using Python and Tkinter. The application has **zero external runtime dependencies** (built purely with the Python standard library) and is packaged as a standalone Windows desktop app with silent launch capabilities and a dedicated custom application icon.

### What Was Created:

1. **Clickable Desktop Shortcut (`Calculator.lnk`)**:
   - **Path:** `C:\Users\antar\Desktop\Calculator.lnk`
   - **Behavior:** Executes via `pythonw.exe`, running silently in the background with **no command prompt or black console window**.
   - **Icon:** Custom multi-resolution icon linked directly to the shortcut.

2. **Custom High-Resolution Application Icon**:
   - **Files:** `assets/calculator.ico` (multi-resolution: 16×16 to 256×256) and `assets/calculator.png` (512×512).
   - **Taskbar Integration:** Registered via Windows `AppUserModelID` (`antariix.moderncalculator.gui.v1`), allowing Windows to pin and group the app independently on the taskbar with its own icon instead of the generic Python feather.

3. **Standalone Launchers in Project Root**:
   - `Calculator.vbs`: VBScript silent launcher for instant double-click launch from Windows File Explorer without a terminal window.
   - `Calculator.bat`: Batch script launcher.
   - `scripts/create_desktop_shortcut.py`: Automated setup script to regenerate or repair the desktop shortcut anytime.

4. **Core Application Script**:
   - `scripts/calculator.py`: Main application code implementing dual modes (Standard & Scientific), calculation history drawer, memory controls, AST mathematical evaluation, and dual themes (Dark/Light).

---

## 2. How to Open and Run the App

| Launch Method | Instructions |
| :--- | :--- |
| **From Desktop** | Double-click the **Calculator** icon on your Windows Desktop (`C:\Users\antar\Desktop\Calculator.lnk`). |
| **From File Explorer** | Double-click `Calculator.vbs` (silent, recommended) or `Calculator.bat` in the repository root. |
| **From Terminal (PowerShell / Command Prompt)** | Run: <br> `python scripts/calculator.py` |
| **Recreate Desktop Shortcut** | If moved or deleted, run: <br> `python scripts/create_desktop_shortcut.py` |

---

## 3. Architecture & How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    CalculatorApp (Tkinter)                  │
├───────────────────────────────┬─────────────────────────────┤
│ Header Toolbar                │ Mode (Std/Sci), DEG/RAD,   │
│                               │ History Toggle, Dark/Light  │
├───────────────────────────────┼─────────────────────────────┤
│ Display Card                  │ Memory Badge, Toast alerts, │
│                               │ Live formula, Large digits  │
├───────────────────────────────┼─────────────────────────────┤
│ Memory Bar                    │ MC, MR, M+, M-, MS          │
├───────────────────────────────┼─────────────────────────────┤
│ Keypad Container              │                             │
│  ├─ Scientific Keypad (left)  │ sin, cos, tan, log, ln, ... │
│  └─ Standard Keypad (right)   │ digits, +, -, ×, ÷, =, etc. │
├───────────────────────────────┼─────────────────────────────┤
│ History Drawer (collapsible)  │ Interactive past cards with │
│                               │ click-to-recall & clear     │
└───────────────────────────────┴─────────────────────────────┘
                               ▲
                               │
               ┌───────────────┴───────────────┐
               │         MathEvaluator         │
               │   (AST Tree + Safe Math)      │
               └───────────────────────────────┘
```

### 3.1. Safe Mathematical Evaluation Engine (`MathEvaluator`)
Unlike naive calculator implementations that use Python's dangerous `eval()`, this app uses an **AST (Abstract Syntax Tree) Parser**:
- **AST Node Traversal:** Expressions are parsed into an AST (`ast.parse(clean, mode='eval')`) and recursively visited. Only explicitly allowed mathematical nodes (`ast.BinOp`, `ast.UnaryOp`, `ast.Constant`, `ast.Call`) are evaluated.
- **Implicit Multiplication:** Normalizes expressions like `2(3)` to `2*(3)`, `5pi` to `5*pi`, and `(4)(5)` to `(4)*(5)`.
- **Factorial Preprocessing:** Converts postfix factorials like `5!` into `fact(5)` automatically.
- **Trigonometric Evaluation & Angle Modes:**
  - `DEG` Mode: Converts inputs via `math.radians()` before evaluation. Normalizes rounding artifacts (e.g., `sin(180°)` evaluates cleanly to `0` instead of `1.22e-16`).
  - `RAD` Mode: Direct radian computation.
  - Supports `sin`, `cos`, `tan`, `asin`, `acos`, `atan`.
- **Safe Division & Error Trapping:** Intercepts `ZeroDivisionError`, domain errors (e.g., square root of negative numbers, logarithms of zero or negative numbers), and overflows without crashing the application.
- **Number Formatting:** Strips floating-point representation jitter (e.g., `0.1 + 0.2` outputs `0.3`), formats large numbers with comma grouping (`1,234,567`), and switches to scientific notation for numbers $\ge 10^{14}$ or $< 10^{-6}$.

### 3.2. Windows Integration & High-DPI Scaling
- **High-DPI Awareness:** Automatically calls `ctypes.windll.shcore.SetProcessDpiAwareness(1)` (or `SetProcessDPIAware()`) on startup, preventing blurry fonts and controls on modern 1080p, 1440p, and 4K displays.
- **Taskbar AppUserModelID:** Invokes `ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("antariix.moderncalculator.gui.v1")` so Windows identifies the calculator as an independent native application rather than a generic Python script.
- **Window & Icon Setup:** Sets both `self.iconbitmap(ico_path)` and `self.iconphoto(True, png_img)` to ensure the title bar, Alt-Tab switcher, and taskbar display the custom icon.

### 3.3. GUI Design & Interaction
- **Fluent Flat Keypad (`CalcButton`):** Custom borderless interactive buttons with instant hover state transitions, click depression, and keypress flash animations.
- **Responsive Dynamic Display:** Automatically scales font size down from `28pt` to `22pt` or `18pt` when entering long expressions to prevent text clipping.
- **Interactive Calculation History Drawer:** Clicking "📜 History" expands a side panel with previous calculation cards. Clicking any card immediately loads the expression or result back into the active display.
- **Clipboard Support:** Clicking the display card or pressing `Ctrl+C` copies the unformatted numeric result to the Windows clipboard and triggers a floating `"✓ Copied!"` toast notification.
- **Theme Engine:** Instant switching between Charcoal Dark (`#121316`) and Fluent Light (`#f1f5f9`) themes with coordinated button, card, and background palettes.

---

## 4. Keyboard Shortcuts Reference

| Physical Key | Function / Action |
| :--- | :--- |
| `0` – `9` | Append digit (with visual button flash) |
| `.` | Decimal point (prevents duplicate decimals) |
| `+`, `-`, `*`, `/` | Operators (`+`, `−`, `×`, `÷`) |
| `^` | Power / Exponentiation |
| `%` | Modulo / Percentage |
| `(` and `)` | Parentheses (auto-balances unclosed parentheses on `=`) |
| `Enter` or `=` | Calculate result |
| `Backspace` | Delete last character / token |
| `Escape` or `Delete` | Clear all (`C`) |
| `Ctrl + C` | Copy current display value to clipboard |

---

## 5. File Inventory & Repository Structure

```
mimo-agent/
│
├── assets/
│   ├── calculator.ico              # Windows multi-res icon (16x16 to 256x256)
│   └── calculator.png              # High-res icon asset (512x512)
│
├── scripts/
│   ├── calculator.py               # Main application GUI & math engine
│   ├── create_desktop_shortcut.py   # Desktop shortcut generator
│   ├── hello.py                    # Starter script
│   ├── sys_check.py                # System diagnostic script
│   └── README.md                   # Scripts reference
│
├── Calculator.bat                  # Batch launcher
├── Calculator.vbs                  # Silent background launcher
├── CALCULATOR_APP.md               # Complete application guide (this file)
└── AGENTS.md                       # Project agent configuration
```

---

## 6. How the Desktop Shortcut Was Created

The shortcut was created using the Windows `WScript.Shell` COM interface:
```python
import win32com.client

shell = win32com.client.Dispatch("WScript.Shell")
shortcut = shell.CreateShortCut(r"C:\Users\antar\Desktop\Calculator.lnk")
shortcut.TargetPath = r"C:\Python314\pythonw.exe"
shortcut.Arguments = r'"C:\Users\antar\mimo-agent\scripts\calculator.py"'
shortcut.WorkingDirectory = r"C:\Users\antar\mimo-agent"
shortcut.IconLocation = r"C:\Users\antar\mimo-agent\assets\calculator.ico,0"
shortcut.Description = "Modern Scientific & Standard Calculator"
shortcut.Save()
```
*Note: Using `pythonw.exe` instead of `python.exe` is what allows the app to start without showing a Windows Command Prompt terminal window.*
