import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sympy as sp
from sympy.parsing.sympy_parser import (
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
    function_exponentiation,
    parse_expr
)

# Parser transformations: allow implicit multiplication and ^ as exponent
transformations = (
    standard_transformations +
    (implicit_multiplication_application, convert_xor, function_exponentiation)
)

class IntegratorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Чисельне інтегрування")
        self._build_ui()
        self._set_defaults()

    def _build_ui(self):
        frm = tk.Frame(self)
        frm.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Context menu for copy/select/paste
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Копіювати", command=self._copy)
        self.menu.add_command(label="Вставити", command=self._paste)
        self.menu.add_command(label="Вибрати все", command=self._select_all)

        # Input fields
        tk.Label(frm, text="Вираз f(x):", font=(None, 12)).grid(row=0, column=0, sticky=tk.W)
        self.func_entry = tk.Entry(frm, width=40, font=(None, 12))
        self.func_entry.grid(row=0, column=1, columnspan=3, pady=2, sticky=tk.W)
        self._bind_context(self.func_entry)

        tk.Label(frm, text="a:", font=(None, 12)).grid(row=1, column=0, sticky=tk.W)
        self.a_entry = tk.Entry(frm, width=12, font=(None, 12))
        self.a_entry.grid(row=1, column=1, pady=2, sticky=tk.W)
        self._bind_context(self.a_entry)

        tk.Label(frm, text="b:", font=(None, 12)).grid(row=1, column=2, sticky=tk.W)
        self.b_entry = tk.Entry(frm, width=12, font=(None, 12))
        self.b_entry.grid(row=1, column=3, pady=2, sticky=tk.W)
        self._bind_context(self.b_entry)

        tk.Label(frm, text="n (розбиття):", font=(None, 12)).grid(row=2, column=0, sticky=tk.W)
        self.n_entry = tk.Entry(frm, width=12, font=(None, 12))
        self.n_entry.grid(row=2, column=1, pady=2, sticky=tk.W)
        self._bind_context(self.n_entry)

        # Buttons
        btn_frame = tk.Frame(frm)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=10)
        tk.Button(btn_frame, text="Обчислити", command=self.compute, font=(None, 12)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Завантажити з файлу", command=self.load_file, font=(None, 12)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Очистити", command=self.clear_fields, font=(None, 12)).pack(side=tk.LEFT, padx=5)

        # Results area
        self.result_text = tk.Text(self, height=4, font=(None, 12))
        self.result_text.pack(fill=tk.X, padx=10, pady=5)
        self._bind_context(self.result_text)

        # Plot area
        fig = Figure(figsize=(6,4))
        self.ax = fig.add_subplot(111)
        self.ax.set_xlabel('x', fontsize=12)
        self.ax.set_ylabel('f(x)', fontsize=12)
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _bind_context(self, widget):
        widget.bind('<Button-3>', self._show_menu)

    def _show_menu(self, event):
        self.event_widget = event.widget
        self.event_widget.focus()
        self.menu.tk_popup(event.x_root, event.y_root)

    def _copy(self):
        try:
            if isinstance(self.event_widget, tk.Entry):
                text = self.event_widget.selection_get()
            else:
                text = self.event_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(text)
        except tk.TclError:
            pass

    def _paste(self):
        try:
            paste_text = self.clipboard_get()
            w = self.event_widget
            w.insert(tk.INSERT, paste_text)
        except tk.TclError:
            pass

    def _select_all(self):
        w = self.event_widget
        if isinstance(w, tk.Entry):
            w.selection_range(0, tk.END)
        else:
            w.tag_add(tk.SEL, '1.0', tk.END)
            w.mark_set(tk.INSERT, '1.0')

    def _set_defaults(self):
        self.func_entry.insert(0, "(x + 1)*(sin(x))")
        self.a_entry.insert(0, "1.6")
        self.b_entry.insert(0, "2.4")
        self.n_entry.insert(0, "10")
        self.compute()

    def clear_fields(self):
        for widget in [self.func_entry, self.a_entry, self.b_entry, self.n_entry]:
            widget.delete(0, tk.END)
        self.result_text.delete(1.0, tk.END)
        self.ax.clear()
        self.ax.set_xlabel('x')
        self.ax.set_ylabel('f(x)')
        self.canvas.draw()

    def load_file(self):
        messagebox.showinfo(
            "Формат файлу .txt",
            "Формат файлу (4 рядки):\n"
            "1) функція f(x)\n"
            "2) нижня межа a (число, . або ,)\n"
            "3) верхня межа b (число)\n"
            "4) n (ціле число, парне для Симпсона)"
        )
        fname = filedialog.askopenfilename(
            title="Відкрити файл з даними",
            filetypes=[("Text files","*.txt"), ("All files","*")]
        )
        if not fname:
            return
        try:
            with open(fname, 'r', encoding='utf-8') as f:
                parts = [line.strip() for line in f if line.strip()]
            if len(parts) < 4:
                raise ValueError("Файл має містити 4 рядки: функція, a, b, n")
            # Validate
            expr_str = parts[0]
            a_val = float(parts[1].replace(',', '.'))
            b_val = float(parts[2].replace(',', '.'))
            n_val = int(parts[3])
            if a_val >= b_val:
                raise ValueError("У файлі має бути a < b")
            if n_val <= 0:
                raise ValueError("n має бути більше за 0")
            parse_expr(expr_str, transformations=transformations)
        except Exception as e:
            messagebox.showerror("Помилка завантаження", f"Невірний формат даних у файлі:\n{e}")
            return
        self.func_entry.delete(0, tk.END)
        self.func_entry.insert(0, expr_str)
        self.a_entry.delete(0, tk.END)
        self.a_entry.insert(0, parts[1].replace(',', '.'))
        self.b_entry.delete(0, tk.END)
        self.b_entry.insert(0, parts[2].replace(',', '.'))
        self.n_entry.delete(0, tk.END)
        self.n_entry.insert(0, parts[3])
        self.compute()

    def compute(self):
        self.result_text.delete(1.0, tk.END)
        self.ax.clear()
        try:
            expr_str = self.func_entry.get().strip()
            a = float(self.a_entry.get().replace(',', '.'))
            b = float(self.b_entry.get().replace(',', '.'))
            n = int(self.n_entry.get())
            if a >= b:
                raise ValueError("Потрібно: a < b")
            if n <= 0:
                raise ValueError("n має бути більше за 0")
        except ValueError as e:
            messagebox.showerror("Некоректні вхідні дані", str(e))
            return

        try:
            x = sp.symbols('x')
            expr = parse_expr(expr_str, transformations=transformations)
            f_np = sp.lambdify(x, expr, modules=['numpy'])
            latex_expr = sp.latex(expr)
        except Exception as e:
            msg = ("Не вдалося розібрати функцію. Перевірте:\n"
                   "- Змінну: x\n"
                   "- Операції: +, -, *, /, ^\n"
                   "- Функції: sin(), cos(), exp(), log() тощо\n"
                   f"Деталі: {e}")
            messagebox.showerror("Помилка розбору функції", msg)
            return

        xs_plot = np.linspace(a, b, 400)
        try:
            ys_plot = f_np(xs_plot)
        except Exception as e:
            messagebox.showerror("Помилка при обчисленні функції", str(e))
            return

        self.ax.plot(xs_plot, ys_plot, label='f(x)')
        self.ax.fill_between(xs_plot, ys_plot, where=(xs_plot>=a)&(xs_plot<=b), alpha=0.3)
        self.ax.set_title(rf"$\int_{{{a}}}^{{{b}}} {latex_expr} \,dx$", fontsize=14)
        self.ax.legend(fontsize=12)
        self.ax.grid(True)

        # Numerical methods
        h = (b - a) / n
        try:
            # Midpoint rectangle
            mid_x = a + (np.arange(n) + 0.5) * h
            I_rect = np.sum(f_np(mid_x)) * h
            # Trapezoidal
            trap_x = a + np.arange(n+1) * h
            trap_y = f_np(trap_x)
            I_trap = (h/2) * (trap_y[0] + 2*np.sum(trap_y[1:-1]) + trap_y[-1])
            # Simpson
            if n % 2 != 0:
                raise ValueError("Для Симпсона n має бути парним")
            simp_y = trap_y
            I_simp = (h/3) * (simp_y[0] + 4*np.sum(simp_y[1:-1:2]) + 2*np.sum(simp_y[2:-1:2]) + simp_y[-1])
        except Exception as e:
            messagebox.showerror("Помилка обчислення", str(e))
            return

        # Виведення результатів
        self.result_text.insert(tk.END, f"Інтеграл прямокутників (середні точки): {I_rect:.6f}\n")
        self.result_text.insert(tk.END, f"Інтеграл трапецій: {I_trap:.6f}\n")
        self.result_text.insert(tk.END, f"Інтеграл Сімпсона: {I_simp:.6f}\n")
        self.canvas.draw()

if __name__ == '__main__':
    IntegratorGUI().mainloop()