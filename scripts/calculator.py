#!/usr/bin/env python3
"""
Modern Calculator App with GUI
Features:
- Sleek modern dark / light theme with polished styling and hover effects
- Standard and Scientific calculation modes
- Calculation history panel with clickable past results
- Memory functions (MC, MR, M+, M-, MS) with active status indicator
- Safe AST-based mathematical evaluation (no insecure eval)
- Full physical keyboard navigation with visual button flash feedback
- Copy result to clipboard (Ctrl+C or click display) with toast notification
- Angle mode toggle: Degrees (DEG) and Radians (RAD)
- High-DPI scaling awareness for crisp rendering on Windows
"""

import ast
import math
import operator
import os
import re
import sys
import tkinter as tk
from tkinter import messagebox

# Enable High-DPI awareness and AppUserModelID on Windows if available
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("antariix.moderncalculator.gui.v1")
    except Exception:
        pass


# ----------------------------------------------------------------------
# Math Evaluation Engine
# ----------------------------------------------------------------------
class MathEvaluator:
    """Safely parses and evaluates mathematical expressions using AST."""

    @staticmethod
    def evaluate(expression: str, is_deg: bool = True) -> float:
        clean = expression.strip()
        if not clean:
            return 0.0

        # Normalize symbols
        clean = clean.replace('×', '*').replace('÷', '/').replace('−', '-').replace('^', '**')
        clean = clean.replace('π', 'pi')

        # Handle factorials like 5! or (3+2)! -> fact(5)
        clean = re.sub(r'(\d+(?:\.\d+)?|\bpi\b|\be\b|\([^()]+\))!', r'fact(\1)', clean)

        # Handle implicit multiplication: e.g. 2(3) -> 2*(3), 5pi -> 5*pi, (2)(3) -> (2)*(3)
        clean = re.sub(r'(\d)(pi|e|\()', r'\1*\2', clean)
        clean = re.sub(r'(\))(pi|e|\d|\()', r'\1*\2', clean)

        def _sin(x):
            rad = math.radians(x) if is_deg else x
            # normalize values close to 0 (e.g. sin(180 deg))
            val = math.sin(rad)
            return 0.0 if abs(val) < 1e-15 else val

        def _cos(x):
            rad = math.radians(x) if is_deg else x
            val = math.cos(rad)
            return 0.0 if abs(val) < 1e-15 else val

        def _tan(x):
            rad = math.radians(x) if is_deg else x
            cos_val = math.cos(rad)
            if abs(cos_val) < 1e-12:
                raise ValueError("Tangent undefined (division by zero)")
            val = math.tan(rad)
            return 0.0 if abs(val) < 1e-15 else val

        def _asin(x):
            if not -1.0 <= x <= 1.0:
                raise ValueError("Domain error for asin: [-1, 1]")
            val = math.asin(x)
            return math.degrees(val) if is_deg else val

        def _acos(x):
            if not -1.0 <= x <= 1.0:
                raise ValueError("Domain error for acos: [-1, 1]")
            val = math.acos(x)
            return math.degrees(val) if is_deg else val

        def _atan(x):
            val = math.atan(x)
            return math.degrees(val) if is_deg else val

        def _fact(x):
            if x < 0 or abs(x - round(x)) > 1e-9:
                raise ValueError("Factorial requires non-negative integer")
            if x > 170:
                raise OverflowError("Factorial overflow")
            return float(math.factorial(int(round(x))))

        def _sqrt(x):
            if x < 0:
                raise ValueError("Cannot calculate square root of negative number")
            return math.sqrt(x)

        def _log(x):
            if x <= 0:
                raise ValueError("Logarithm domain error: must be > 0")
            return math.log10(x)

        def _ln(x):
            if x <= 0:
                raise ValueError("Natural log domain error: must be > 0")
            return math.log(x)

        def _log2(x):
            if x <= 0:
                raise ValueError("Log2 domain error: must be > 0")
            return math.log2(x)

        def _cbrt(x):
            return math.copysign(abs(x) ** (1.0 / 3.0), x)

        funcs = {
            'sin': _sin, 'cos': _cos, 'tan': _tan,
            'asin': _asin, 'acos': _acos, 'atan': _atan,
            'sqrt': _sqrt, 'cbrt': _cbrt,
            'log': _log, 'ln': _ln, 'log2': _log2,
            'abs': abs, 'fact': _fact,
        }

        consts = {
            'pi': math.pi,
            'e': math.e,
        }

        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
        }

        def _eval_node(node):
            if isinstance(node, ast.Expression):
                return _eval_node(node.body)
            elif isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    return float(node.value)
                raise ValueError("Unsupported constant type")
            elif isinstance(node, ast.Name):
                if node.id in consts:
                    return float(consts[node.id])
                raise ValueError(f"Unknown symbol: {node.id}")
            elif isinstance(node, ast.BinOp):
                left = _eval_node(node.left)
                right = _eval_node(node.right)
                op_type = type(node.op)
                if op_type in ops:
                    if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
                        raise ZeroDivisionError("Cannot divide by zero")
                    if op_type == ast.Pow and left < 0 and abs(right - round(right)) > 1e-9:
                        raise ValueError("Complex result not supported")
                    res = ops[op_type](left, right)
                    if math.isnan(res) or math.isinf(res):
                        raise OverflowError("Calculation overflow")
                    return float(res)
                raise ValueError(f"Unsupported binary operator: {op_type.__name__}")
            elif isinstance(node, ast.UnaryOp):
                val = _eval_node(node.operand)
                if isinstance(node.op, ast.USub):
                    return -val
                elif isinstance(node.op, ast.UAdd):
                    return +val
                raise ValueError("Unsupported unary operator")
            elif isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name) or node.func.id not in funcs:
                    raise ValueError(f"Unsupported function call")
                args = [_eval_node(arg) for arg in node.args]
                return float(funcs[node.func.id](*args))
            raise ValueError(f"Invalid syntax")

        try:
            tree = ast.parse(clean, mode='eval')
            return _eval_node(tree)
        except (SyntaxError, IndentationError):
            raise ValueError("Malformed expression syntax")

    @staticmethod
    def format_number(val: float) -> str:
        """Cleanly formats numbers, stripping floating point jitter."""
        if math.isnan(val):
            return "NaN"
        if math.isinf(val):
            return "Infinity" if val > 0 else "-Infinity"
        # Round close integers
        if abs(val - round(val)) < 1e-11:
            val = round(val)
            if abs(val) < 1e15:
                return f"{int(val):,}"

        # Large numbers or microscopic numbers: scientific notation
        abs_v = abs(val)
        if (abs_v >= 1e14 or (abs_v < 1e-6 and abs_v > 0)):
            sci = f"{val:.8g}".replace("+0", "+").replace("-0", "-")
            return sci

        # Standard decimal formatting
        formatted = f"{val:.10f}".rstrip("0").rstrip(".")
        parts = formatted.split(".")
        int_part = f"{int(parts[0]):,}"
        if len(parts) > 1:
            return f"{int_part}.{parts[1]}"
        return int_part


# ----------------------------------------------------------------------
# Themes & Styling
# ----------------------------------------------------------------------
THEMES = {
    "dark": {
        "bg_main": "#121316",
        "bg_card": "#1c1d22",
        "card_border": "#2c2d35",
        "text_primary": "#f8fafc",
        "text_secondary": "#94a3b8",
        "text_accent": "#818cf8",
        # Button styles: (bg, hover, active, text)
        "btn_num": ("#24262d", "#2e313a", "#393d48", "#f8fafc"),
        "btn_func": ("#2d323f", "#373d4d", "#454d61", "#cbd5e1"),
        "btn_op": ("#4f46e5", "#6366f1", "#4338ca", "#ffffff"),
        "btn_eq": ("#10b981", "#059669", "#047857", "#ffffff"),
        "btn_mem": ("#191b22", "#232630", "#2c303c", "#94a3b8"),
        "btn_sci": ("#1f2430", "#282f3f", "#333c4f", "#a5b4fc"),
        "history_bg": "#16171b",
        "history_item_bg": "#1f2128",
        "history_item_hover": "#2a2d37",
        "history_item_border": "#2c2e37",
        "badge_bg": "#312e81",
        "badge_fg": "#c7d2fe",
    },
    "light": {
        "bg_main": "#f1f5f9",
        "bg_card": "#ffffff",
        "card_border": "#e2e8f0",
        "text_primary": "#0f172a",
        "text_secondary": "#64748b",
        "text_accent": "#4f46e5",
        # Button styles: (bg, hover, active, text)
        "btn_num": ("#ffffff", "#f8fafc", "#f1f5f9", "#0f172a"),
        "btn_func": ("#e2e8f0", "#cbd5e1", "#94a3b8", "#1e293b"),
        "btn_op": ("#4f46e5", "#4338ca", "#3730a3", "#ffffff"),
        "btn_eq": ("#10b981", "#059669", "#047857", "#ffffff"),
        "btn_mem": ("#f8fafc", "#e2e8f0", "#cbd5e1", "#64748b"),
        "btn_sci": ("#eef2ff", "#e0e7ff", "#c7d2fe", "#4338ca"),
        "history_bg": "#f8fafc",
        "history_item_bg": "#ffffff",
        "history_item_hover": "#f1f5f9",
        "history_item_border": "#e2e8f0",
        "badge_bg": "#e0e7ff",
        "badge_fg": "#3730a3",
    }
}


# ----------------------------------------------------------------------
# Modern Styled Button Component
# ----------------------------------------------------------------------
class CalcButton(tk.Frame):
    """Modern flat button with smooth hover, click states, and keyboard flash."""

    def __init__(self, parent, text, command, style_colors, font=("Segoe UI", 12, "bold"),
                 height=48, width=None, corner_radius=8, **kwargs):
        super().__init__(parent, bg=style_colors[0], cursor="hand2", **kwargs)
        self.command = command
        self.text = text
        self.style_colors = style_colors  # (bg, hover, active, fg)
        self.font = font
        self.is_flashing = False

        self.label = tk.Label(
            self,
            text=text,
            font=font,
            fg=style_colors[3],
            bg=style_colors[0],
            cursor="hand2"
        )
        self.label.pack(expand=True, fill="both", padx=2, pady=2)

        # Bind events
        for widget in (self, self.label):
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
            widget.bind("<Button-1>", self._on_press)
            widget.bind("<ButtonRelease-1>", self._on_release)

    def update_colors(self, style_colors):
        self.style_colors = style_colors
        self.config(bg=style_colors[0])
        self.label.config(bg=style_colors[0], fg=style_colors[3])

    def _on_enter(self, event=None):
        if not self.is_flashing:
            self.config(bg=self.style_colors[1])
            self.label.config(bg=self.style_colors[1])

    def _on_leave(self, event=None):
        if not self.is_flashing:
            self.config(bg=self.style_colors[0])
            self.label.config(bg=self.style_colors[0])

    def _on_press(self, event=None):
        self.config(bg=self.style_colors[2])
        self.label.config(bg=self.style_colors[2])

    def _on_release(self, event=None):
        self.config(bg=self.style_colors[1])
        self.label.config(bg=self.style_colors[1])
        if self.command:
            self.command()

    def flash(self):
        """Visual pulse when triggered via keyboard shortcut."""
        self.is_flashing = True
        self.config(bg=self.style_colors[2])
        self.label.config(bg=self.style_colors[2])

        def restore():
            self.is_flashing = False
            self.config(bg=self.style_colors[0])
            self.label.config(bg=self.style_colors[0])

        self.after(120, restore)


# ----------------------------------------------------------------------
# Main Application Window
# ----------------------------------------------------------------------
class CalculatorApp(tk.Tk):
    """Feature-rich, modern GUI Calculator."""

    def __init__(self):
        super().__init__()

        self.title("Calculator")
        self.minsize(380, 580)
        self.geometry("400x630")

        # Application Icon
        script_dir = os.path.dirname(os.path.abspath(__file__))
        repo_dir = os.path.dirname(script_dir)
        ico_path = os.path.join(repo_dir, "assets", "calculator.ico")
        png_path = os.path.join(repo_dir, "assets", "calculator.png")

        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass
        if os.path.exists(png_path):
            try:
                self._icon_img = tk.PhotoImage(file=png_path)
                self.iconphoto(True, self._icon_img)
            except Exception:
                pass

        # Calculator State
        self.expression = ""          # Full mathematical formula in progress
        self.expression_display = ""  # Upper history/preview formula
        self.display_text = "0"       # Active display string
        self.eval_ready = False       # True if last action evaluated expression
        self.is_scientific = False    # Scientific mode toggled
        self.show_history = False     # History panel toggled
        self.is_deg = True            # Trig mode: True = DEG, False = RAD
        self.memory = 0.0             # Stored memory value
        self.memory_active = False    # Has value stored in memory
        self.history = []             # List of (expr, result)
        self.theme_name = "dark"      # Current theme: "dark" or "light"

        self.button_registry = {}     # Maps key string -> CalcButton for keyboard flashes

        self._init_ui()
        self._apply_theme()
        self._bind_keyboard()

    def _init_ui(self):
        """Constructs layout hierarchy."""
        # Top Container
        self.main_container = tk.Frame(self)
        self.main_container.pack(fill="both", expand=True)

        # Left/Center: Calculator body
        self.calc_body = tk.Frame(self.main_container)
        self.calc_body.pack(side="left", fill="both", expand=True, padx=12, pady=12)

        # Right: Collapsible History Sidebar
        self.history_frame = tk.Frame(self.main_container, width=250)

        # 1. Header Toolbar
        self._build_header(self.calc_body)

        # 2. Display Card
        self._build_display(self.calc_body)

        # 3. Memory Bar
        self._build_memory_bar(self.calc_body)

        # 4. Keypad Section (Scientific drawer + Standard grid)
        self.keypad_container = tk.Frame(self.calc_body)
        self.keypad_container.pack(fill="both", expand=True, pady=(8, 0))

        # Scientific drawer (hidden by default)
        self.sci_frame = tk.Frame(self.keypad_container)

        # Standard keypad
        self.std_frame = tk.Frame(self.keypad_container)
        self.std_frame.pack(side="right", fill="both", expand=True)

        self._build_scientific_keypad(self.sci_frame)
        self._build_standard_keypad(self.std_frame)

        # Build History Panel content
        self._build_history_panel(self.history_frame)

    # ------------------------------------------------------------------
    # Header Toolbar
    # ------------------------------------------------------------------
    def _build_header(self, parent):
        self.header_frame = tk.Frame(parent)
        self.header_frame.pack(fill="x", pady=(0, 10))

        # Left side buttons: Mode and Angle
        left_box = tk.Frame(self.header_frame)
        left_box.pack(side="left", fill="y")
        self.header_left_box = left_box

        self.btn_mode = tk.Button(
            left_box,
            text="📐 Scientific",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.toggle_scientific
        )
        self.btn_mode.pack(side="left", padx=(0, 4))

        # Deg/Rad Indicator Button (shown only in Scientific mode)
        self.btn_angle = tk.Button(
            left_box,
            text="DEG",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            padx=8,
            pady=5,
            cursor="hand2",
            command=self.toggle_angle_mode
        )
        # Not packed initially (only in scientific mode)

        # Right side buttons: Theme and History
        right_box = tk.Frame(self.header_frame)
        right_box.pack(side="right", fill="y")
        self.header_right_box = right_box

        self.btn_theme = tk.Button(
            right_box,
            text="☀️",
            font=("Segoe UI", 10),
            relief="flat",
            bd=0,
            padx=8,
            pady=3,
            cursor="hand2",
            command=self.toggle_theme
        )
        self.btn_theme.pack(side="right", padx=(6, 0))

        self.btn_history_toggle = tk.Button(
            right_box,
            text="📜 History",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.toggle_history
        )
        self.btn_history_toggle.pack(side="right")

    # ------------------------------------------------------------------
    # Display Card
    # ------------------------------------------------------------------
    def _build_display(self, parent):
        self.display_card = tk.Frame(parent, bd=1, relief="solid")
        self.display_card.pack(fill="x", pady=(0, 8), ipady=6)

        # Upper row: Memory Badge + Secondary expression label
        top_row = tk.Frame(self.display_card)
        top_row.pack(fill="x", padx=12, pady=(6, 0))

        self.memory_badge = tk.Label(
            top_row,
            text="",
            font=("Segoe UI", 8, "bold"),
            padx=6,
            pady=1
        )
        self.memory_badge.pack(side="left")

        # Toast notification for "Copied!"
        self.toast_label = tk.Label(
            top_row,
            text="",
            font=("Segoe UI", 8, "bold")
        )
        self.toast_label.pack(side="left", padx=8)

        self.lbl_expr = tk.Label(
            top_row,
            text="",
            font=("Segoe UI", 10),
            anchor="e"
        )
        self.lbl_expr.pack(side="right", fill="x", expand=True)

        # Main numeric display
        self.lbl_display = tk.Label(
            self.display_card,
            text="0",
            font=("Segoe UI", 28, "bold"),
            anchor="e",
            cursor="hand2"
        )
        self.lbl_display.pack(fill="x", padx=12, pady=(2, 6))

        # Click on display to copy to clipboard
        self.lbl_display.bind("<Button-1>", lambda e: self.copy_to_clipboard())
        self.display_card.bind("<Button-1>", lambda e: self.copy_to_clipboard())

    # ------------------------------------------------------------------
    # Memory Bar
    # ------------------------------------------------------------------
    def _build_memory_bar(self, parent):
        self.memory_bar = tk.Frame(parent)
        self.memory_bar.pack(fill="x", pady=(0, 6))

        self.memory_buttons = {}
        mem_ops = [
            ("MC", self.mem_clear),
            ("MR", self.mem_recall),
            ("M+", self.mem_add),
            ("M-", self.mem_sub),
            ("MS", self.mem_store)
        ]

        for i, (text, cmd) in enumerate(mem_ops):
            self.memory_bar.columnconfigure(i, weight=1)
            btn = tk.Button(
                self.memory_bar,
                text=text,
                font=("Segoe UI", 8, "bold"),
                relief="flat",
                bd=0,
                pady=4,
                cursor="hand2",
                command=cmd
            )
            btn.grid(row=0, column=i, sticky="nsew", padx=2)
            self.memory_buttons[text] = btn

    # ------------------------------------------------------------------
    # Standard Keypad (4 columns x 6 rows)
    # ------------------------------------------------------------------
    def _build_standard_keypad(self, parent):
        grid = [
            [("C", "btn_func", self.clear_all), ("←", "btn_func", self.backspace),
             ("%", "btn_func", lambda: self.apply_operator("%")), ("÷", "btn_op", lambda: self.apply_operator("÷"))],

            [("(", "btn_func", lambda: self.append_token("(")), (")", "btn_func", lambda: self.append_token(")")),
             ("√x", "btn_func", self.op_sqrt), ("×", "btn_op", lambda: self.apply_operator("×"))],

            [("7", "btn_num", lambda: self.append_digit("7")), ("8", "btn_num", lambda: self.append_digit("8")),
             ("9", "btn_num", lambda: self.append_digit("9")), ("−", "btn_op", lambda: self.apply_operator("−"))],

            [("4", "btn_num", lambda: self.append_digit("4")), ("5", "btn_num", lambda: self.append_digit("5")),
             ("6", "btn_num", lambda: self.append_digit("6")), ("+", "btn_op", lambda: self.apply_operator("+"))],

            [("1", "btn_num", lambda: self.append_digit("1")), ("2", "btn_num", lambda: self.append_digit("2")),
             ("3", "btn_num", lambda: self.append_digit("3")), ("=", "btn_eq", self.calculate_result)],

            [("±", "btn_num", self.toggle_sign), ("0", "btn_num", lambda: self.append_digit("0")),
             (".", "btn_num", self.append_decimal), ("^", "btn_op", lambda: self.apply_operator("^"))]
        ]

        for r, row in enumerate(grid):
            parent.rowconfigure(r, weight=1)
            for c, (text, style_key, cmd) in enumerate(row):
                parent.columnconfigure(c, weight=1)
                colors = THEMES[self.theme_name][style_key]
                btn = CalcButton(
                    parent,
                    text=text,
                    command=cmd,
                    style_colors=colors,
                    font=("Segoe UI", 13, "bold" if style_key in ("btn_op", "btn_eq") else "normal")
                )
                btn.grid(row=r, column=c, sticky="nsew", padx=3, pady=3)
                self.button_registry[text] = btn

    # ------------------------------------------------------------------
    # Scientific Keypad (Expandable 3 columns x 6 rows)
    # ------------------------------------------------------------------
    def _build_scientific_keypad(self, parent):
        grid = [
            [("sin", lambda: self.append_function("sin(")), ("cos", lambda: self.append_function("cos(")), ("tan", lambda: self.append_function("tan("))],
            [("asin", lambda: self.append_function("asin(")), ("acos", lambda: self.append_function("acos(")), ("atan", lambda: self.append_function("atan("))],
            [("ln", lambda: self.append_function("ln(")), ("log", lambda: self.append_function("log(")), ("log₂", lambda: self.append_function("log2("))],
            [("x²", self.op_square), ("x³", self.op_cube), ("1/x", self.op_reciprocal)],
            [("π", lambda: self.append_digit("π")), ("e", lambda: self.append_digit("e")), ("n!", self.op_factorial)],
            [("|x|", lambda: self.append_function("abs(")), ("∛x", self.op_cbrt), ("10ˣ", self.op_ten_pow)]
        ]

        for r, row in enumerate(grid):
            parent.rowconfigure(r, weight=1)
            for c, (text, cmd) in enumerate(row):
                parent.columnconfigure(c, weight=1)
                colors = THEMES[self.theme_name]["btn_sci"]
                btn = CalcButton(
                    parent,
                    text=text,
                    command=cmd,
                    style_colors=colors,
                    font=("Segoe UI", 10, "bold")
                )
                btn.grid(row=r, column=c, sticky="nsew", padx=3, pady=3)
                self.button_registry[text] = btn

    # ------------------------------------------------------------------
    # History Sidebar
    # ------------------------------------------------------------------
    def _build_history_panel(self, parent):
        top_bar = tk.Frame(parent)
        top_bar.pack(fill="x", padx=8, pady=(8, 4))
        self.history_top_bar = top_bar

        lbl_title = tk.Label(top_bar, text="History", font=("Segoe UI", 11, "bold"))
        lbl_title.pack(side="left")

        btn_clear_hist = tk.Button(
            top_bar,
            text="🗑️ Clear",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            bd=0,
            padx=6,
            pady=3,
            cursor="hand2",
            command=self.clear_history
        )
        btn_clear_hist.pack(side="right")
        self.btn_clear_hist = btn_clear_hist

        # Scrollable container for history items
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.history_items_frame = tk.Frame(canvas)

        self.history_items_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.history_items_frame, anchor="nw", width=226)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=4)
        scrollbar.pack(side="right", fill="y", pady=4)

        self.history_canvas = canvas
        self.history_scrollbar = scrollbar
        self.lbl_hist_title = lbl_title

        self._refresh_history_ui()

    def _refresh_history_ui(self):
        """Redraws the history list with interactive cards."""
        for widget in self.history_items_frame.winfo_children():
            widget.destroy()

        t = THEMES[self.theme_name]

        if not self.history:
            empty_lbl = tk.Label(
                self.history_items_frame,
                text="No calculations yet",
                font=("Segoe UI", 9, "italic"),
                fg=t["text_secondary"],
                bg=t["history_bg"],
                pady=20
            )
            empty_lbl.pack(fill="x")
            return

        for expr, result in reversed(self.history):
            card = tk.Frame(
                self.history_items_frame,
                bg=t["history_item_bg"],
                highlightbackground=t["history_item_border"],
                highlightthickness=1,
                bd=0,
                cursor="hand2",
                padx=10,
                pady=6
            )
            card.pack(fill="x", pady=4, padx=2)

            expr_lbl = tk.Label(
                card,
                text=expr + " =",
                font=("Segoe UI", 9),
                fg=t["text_secondary"],
                bg=t["history_item_bg"],
                anchor="e",
                cursor="hand2"
            )
            expr_lbl.pack(fill="x")

            res_lbl = tk.Label(
                card,
                text=result,
                font=("Segoe UI", 12, "bold"),
                fg=t["text_primary"],
                bg=t["history_item_bg"],
                anchor="e",
                cursor="hand2"
            )
            res_lbl.pack(fill="x")

            # Click to recall result
            def make_recall(res_val):
                return lambda e: self.recall_history(res_val)

            for w in (card, expr_lbl, res_lbl):
                w.bind("<Button-1>", make_recall(result))
                w.bind("<Enter>", lambda e, c=card, el=expr_lbl, rl=res_lbl: (
                    c.config(bg=t["history_item_hover"]),
                    el.config(bg=t["history_item_hover"]),
                    rl.config(bg=t["history_item_hover"])
                ))
                w.bind("<Leave>", lambda e, c=card, el=expr_lbl, rl=res_lbl: (
                    c.config(bg=t["history_item_bg"]),
                    el.config(bg=t["history_item_bg"]),
                    rl.config(bg=t["history_item_bg"])
                ))

    def recall_history(self, val_str):
        clean = val_str.replace(",", "")
        self.display_text = clean
        self.expression = clean
        self.eval_ready = False
        self._update_display()
        self.show_toast(f"Recalled: {val_str}")

    def clear_history(self):
        self.history.clear()
        self._refresh_history_ui()

    # ------------------------------------------------------------------
    # Theming & Visuals
    # ------------------------------------------------------------------
    def toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self._apply_theme()

    def _apply_theme(self):
        t = THEMES[self.theme_name]

        # Windows and containers
        self.config(bg=t["bg_main"])
        self.main_container.config(bg=t["bg_main"])
        self.calc_body.config(bg=t["bg_main"])
        self.header_frame.config(bg=t["bg_main"])
        self.header_left_box.config(bg=t["bg_main"])
        self.header_right_box.config(bg=t["bg_main"])
        self.keypad_container.config(bg=t["bg_main"])
        self.std_frame.config(bg=t["bg_main"])
        self.sci_frame.config(bg=t["bg_main"])
        self.memory_bar.config(bg=t["bg_main"])

        # Display Card
        self.display_card.config(bg=t["bg_card"], highlightbackground=t["card_border"], highlightcolor=t["card_border"])
        for child in self.display_card.winfo_children():
            child.config(bg=t["bg_card"])
            if isinstance(child, tk.Frame):
                for subchild in child.winfo_children():
                    if subchild != self.memory_badge:
                        subchild.config(bg=t["bg_card"])

        self.lbl_expr.config(fg=t["text_secondary"])
        self.lbl_display.config(fg=t["text_primary"])
        self.toast_label.config(fg=t["text_accent"], bg=t["bg_card"])

        # Header Buttons
        for b in (self.btn_mode, self.btn_angle, self.btn_history_toggle, self.btn_theme):
            b.config(bg=t["btn_func"][0], fg=t["btn_func"][3], activebackground=t["btn_func"][1], activeforeground=t["btn_func"][3])

        self.btn_theme.config(text="🌙" if self.theme_name == "dark" else "☀️")

        # Memory Badge
        if self.memory_active:
            self.memory_badge.config(
                text=f"M = {MathEvaluator.format_number(self.memory)}",
                bg=t["badge_bg"],
                fg=t["badge_fg"]
            )
        else:
            self.memory_badge.config(text="", bg=t["bg_card"])

        # Memory Bar buttons
        for btn in self.memory_buttons.values():
            btn.config(
                bg=t["btn_mem"][0],
                fg=t["btn_mem"][3],
                activebackground=t["btn_mem"][1],
                activeforeground=t["btn_mem"][3]
            )

        # Standard & Sci Keypad buttons
        for text, btn in self.button_registry.items():
            if text in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ".", "±"):
                btn.update_colors(t["btn_num"])
            elif text in ("+", "−", "×", "÷", "^"):
                btn.update_colors(t["btn_op"])
            elif text == "=":
                btn.update_colors(t["btn_eq"])
            elif text in ("sin", "cos", "tan", "asin", "acos", "atan", "ln", "log", "log₂", "x²", "x³", "1/x", "π", "e", "n!", "|x|", "∛x", "10ˣ"):
                btn.update_colors(t["btn_sci"])
            else:
                btn.update_colors(t["btn_func"])

        # History frame
        self.history_frame.config(bg=t["history_bg"])
        self.history_top_bar.config(bg=t["history_bg"])
        self.history_canvas.config(bg=t["history_bg"])
        self.history_items_frame.config(bg=t["history_bg"])
        self.lbl_hist_title.config(bg=t["history_bg"], fg=t["text_primary"])
        self.btn_clear_hist.config(bg=t["btn_func"][0], fg=t["btn_func"][3], activebackground=t["btn_func"][1], activeforeground=t["btn_func"][3])
        self._refresh_history_ui()

    # ------------------------------------------------------------------
    # Toast & Display Updates
    # ------------------------------------------------------------------
    def show_toast(self, message: str):
        self.toast_label.config(text=message)
        self.after(1600, lambda: self.toast_label.config(text=""))

    def copy_to_clipboard(self):
        val = self.display_text.replace(",", "")
        self.clipboard_clear()
        self.clipboard_append(val)
        self.show_toast("✓ Copied!")

    def _update_display(self):
        """Refreshes text and scales down font if string is very long."""
        txt = self.display_text
        if len(txt) > 16:
            font_size = 18
        elif len(txt) > 12:
            font_size = 22
        else:
            font_size = 28

        self.lbl_display.config(text=txt, font=("Segoe UI", font_size, "bold"))
        self.lbl_expr.config(text=self.expression_display)

    # ------------------------------------------------------------------
    # Keyboard Bindings & Flash
    # ------------------------------------------------------------------
    def _bind_keyboard(self):
        """Binds full keyboard for natural typing."""
        self.bind("<Key>", self._on_key_press)

    def _on_key_press(self, event):
        char = event.char
        keysym = event.keysym

        # Copy shortcut
        if event.state & 4 and keysym.lower() == 'c':  # Ctrl+C
            self.copy_to_clipboard()
            return

        # Numeric and basic keys
        key_map = {
            '0': '0', '1': '1', '2': '2', '3': '3', '4': '4',
            '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
            '.': '.', '+': '+', '-': '−', '*': '×', '/': '÷',
            '^': '^', '%': '%', '(': '(', ')': ')', '=': '='
        }

        if char in key_map:
            target = key_map[char]
            if target in self.button_registry:
                self.button_registry[target].flash()
            if target in '0123456789':
                self.append_digit(target)
            elif target == '.':
                self.append_decimal()
            elif target in ('+', '−', '×', '÷', '^', '%'):
                self.apply_operator(target)
            elif target in ('(', ')'):
                self.append_token(target)
            elif target == '=':
                self.calculate_result()
            return

        if keysym in ("Return", "KP_Enter"):
            if "=" in self.button_registry:
                self.button_registry["="].flash()
            self.calculate_result()
        elif keysym == "BackSpace":
            for k in ("←", "⌫"):
                if k in self.button_registry:
                    self.button_registry[k].flash()
            self.backspace()
        elif keysym in ("Escape", "Delete"):
            if "C" in self.button_registry:
                self.button_registry["C"].flash()
            self.clear_all()

    # ------------------------------------------------------------------
    # Calculator Business Logic
    # ------------------------------------------------------------------
    def append_digit(self, digit: str):
        if self.eval_ready:
            self.expression = ""
            self.display_text = "0"
            self.eval_ready = False

        if self.display_text == "0" and digit != ".":
            self.display_text = digit
        else:
            self.display_text += digit

        self.expression += digit
        self.expression_display = self.expression
        self._update_display()

    def append_decimal(self):
        if self.eval_ready:
            self.expression = "0"
            self.display_text = "0"
            self.eval_ready = False

        # Check if current number segment already has a decimal
        parts = re.split(r'[+\-×÷^%() ]', self.display_text)
        current_num = parts[-1] if parts else ""
        if "." in current_num:
            return

        if not self.display_text or self.display_text[-1] in "+-×÷^%(":
            self.display_text += "0."
            self.expression += "0."
        else:
            self.display_text += "."
            self.expression += "."

        self.expression_display = self.expression
        self._update_display()

    def append_token(self, token: str):
        if self.eval_ready:
            if token == "(":
                self.expression = ""
                self.display_text = ""
            self.eval_ready = False

        if self.display_text == "0" and token == "(":
            self.display_text = "("
            self.expression = "("
        else:
            self.display_text += token
            self.expression += token

        self.expression_display = self.expression
        self._update_display()

    def append_function(self, func_prefix: str):
        if self.eval_ready:
            self.expression = ""
            self.display_text = ""
            self.eval_ready = False

        if self.display_text == "0":
            self.display_text = func_prefix
            self.expression = func_prefix
        else:
            self.display_text += func_prefix
            self.expression += func_prefix

        self.expression_display = self.expression
        self._update_display()

    def apply_operator(self, op: str):
        if self.eval_ready:
            self.eval_ready = False

        if not self.expression:
            self.expression = "0"

        # If previous character was an operator, replace it
        if self.expression and self.expression[-1] in "+−×÷^%":
            self.expression = self.expression[:-1] + op
            self.display_text = self.display_text[:-1] + op
        else:
            self.expression += f" {op} "
            self.display_text += f" {op} "

        self.expression_display = self.expression
        self._update_display()

    def backspace(self):
        if self.eval_ready:
            self.expression = ""
            self.expression_display = ""
            self.display_text = "0"
            self.eval_ready = False
            self._update_display()
            return

        # Strip whitespace if deleting an operator with spaces
        if self.display_text.endswith(" "):
            self.display_text = self.display_text.rstrip()
            self.expression = self.expression.rstrip()

        self.display_text = self.display_text[:-1]
        self.expression = self.expression[:-1]

        if not self.display_text:
            self.display_text = "0"

        self.expression_display = self.expression
        self._update_display()

    def clear_all(self):
        self.expression = ""
        self.expression_display = ""
        self.display_text = "0"
        self.eval_ready = False
        self._update_display()

    def toggle_sign(self):
        if self.eval_ready:
            self.eval_ready = False

        try:
            # If current display is a simple number
            val = float(self.display_text.replace(",", ""))
            val = -val
            formatted = MathEvaluator.format_number(val)
            self.display_text = formatted
            self.expression = formatted
        except ValueError:
            # Wrap entire current expression with -1 * (...)
            if self.expression:
                self.expression = f"-({self.expression})"
                self.display_text = self.expression

        self.expression_display = self.expression
        self._update_display()

    # Scientific quick operations
    def op_sqrt(self):
        self._apply_unary_func("sqrt")

    def op_square(self):
        self.apply_operator("^")
        self.append_digit("2")

    def op_cube(self):
        self.apply_operator("^")
        self.append_digit("3")

    def op_cbrt(self):
        self._apply_unary_func("cbrt")

    def op_reciprocal(self):
        if not self.display_text or self.display_text == "0":
            self.show_toast("Cannot divide by 0")
            return
        self.expression = f"1/({self.expression})"
        self.calculate_result()

    def op_factorial(self):
        self.append_token("!")
        self.calculate_result()

    def op_ten_pow(self):
        self.append_function("10^(")

    def _apply_unary_func(self, func_name: str):
        if not self.expression:
            self.expression = "0"
        self.expression = f"{func_name}({self.expression})"
        self.calculate_result()

    # ------------------------------------------------------------------
    # Result Evaluation
    # ------------------------------------------------------------------
    def calculate_result(self):
        expr = self.expression.strip()
        if not expr:
            return

        # Auto-close open parentheses
        open_parens = expr.count("(") - expr.count(")")
        if open_parens > 0:
            expr += ")" * open_parens
            self.expression = expr

        try:
            val = MathEvaluator.evaluate(expr, is_deg=self.is_deg)
            formatted = MathEvaluator.format_number(val)

            # Record history
            self.history.append((expr, formatted))
            self._refresh_history_ui()

            # Update display
            self.expression_display = f"{expr} ="
            self.display_text = formatted
            self.expression = formatted
            self.eval_ready = True
            self._update_display()

        except ZeroDivisionError:
            self.display_text = "Cannot divide by 0"
            self.eval_ready = True
            self._update_display()
        except OverflowError:
            self.display_text = "Overflow"
            self.eval_ready = True
            self._update_display()
        except ValueError as e:
            self.display_text = "Error"
            self.show_toast(str(e))
            self.eval_ready = True
            self._update_display()
        except Exception:
            self.display_text = "Syntax Error"
            self.eval_ready = True
            self._update_display()

    # ------------------------------------------------------------------
    # Memory Functions
    # ------------------------------------------------------------------
    def _get_current_numeric_value(self) -> float:
        try:
            return float(self.display_text.replace(",", ""))
        except ValueError:
            return MathEvaluator.evaluate(self.expression, is_deg=self.is_deg)

    def mem_clear(self):
        self.memory = 0.0
        self.memory_active = False
        self._apply_theme()
        self.show_toast("Memory Cleared")

    def mem_recall(self):
        if not self.memory_active:
            self.show_toast("Memory is empty")
            return
        formatted = MathEvaluator.format_number(self.memory)
        self.display_text = formatted
        self.expression = formatted
        self.expression_display = f"Ans: {formatted}"
        self.eval_ready = False
        self._update_display()
        self.show_toast(f"Recalled M: {formatted}")

    def mem_store(self):
        try:
            val = self._get_current_numeric_value()
            self.memory = val
            self.memory_active = True
            self._apply_theme()
            self.show_toast(f"Stored M = {MathEvaluator.format_number(val)}")
        except Exception:
            self.show_toast("Cannot store invalid value")

    def mem_add(self):
        try:
            val = self._get_current_numeric_value()
            self.memory += val
            self.memory_active = True
            self._apply_theme()
            self.show_toast(f"M+ = {MathEvaluator.format_number(self.memory)}")
        except Exception:
            self.show_toast("Invalid value")

    def mem_sub(self):
        try:
            val = self._get_current_numeric_value()
            self.memory -= val
            self.memory_active = True
            self._apply_theme()
            self.show_toast(f"M- = {MathEvaluator.format_number(self.memory)}")
        except Exception:
            self.show_toast("Invalid value")

    # ------------------------------------------------------------------
    # Drawer / Toggles
    # ------------------------------------------------------------------
    def toggle_scientific(self):
        self.is_scientific = not self.is_scientific
        current_h = self.winfo_height()
        if self.is_scientific:
            self.btn_mode.config(text="🔢 Standard")
            self.btn_angle.pack(side="left", padx=4)
            self.sci_frame.pack(side="left", fill="both", expand=True, padx=(0, 6))
            target_w = 650 + (250 if self.show_history else 0)
            self.geometry(f"{target_w}x{current_h}")
        else:
            self.btn_mode.config(text="📐 Scientific")
            self.btn_angle.pack_forget()
            self.sci_frame.pack_forget()
            target_w = 400 + (250 if self.show_history else 0)
            self.geometry(f"{target_w}x{current_h}")

    def toggle_angle_mode(self):
        self.is_deg = not self.is_deg
        self.btn_angle.config(text="DEG" if self.is_deg else "RAD")
        self.show_toast(f"Angle Mode: {'Degrees' if self.is_deg else 'Radians'}")

    def toggle_history(self):
        self.show_history = not self.show_history
        current_h = self.winfo_height()
        base_w = 650 if self.is_scientific else 400
        if self.show_history:
            self.history_frame.pack(side="right", fill="both", padx=(10, 0))
            self.geometry(f"{base_w + 250}x{current_h}")
        else:
            self.history_frame.pack_forget()
            self.geometry(f"{base_w}x{current_h}")


def main():
    app = CalculatorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
