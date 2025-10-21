import tkinter as tk
from tkinter import ttk

HIT_R = 8
PT_R  = 5
PADDING = 20

def bezier_cubic(P0, P1, P2, P3, t):
    u = 1 - t
    return (
        (u**3)*P0[0] + 3*(u**2)*t*P1[0] + 3*u*(t**2)*P2[0] + (t**3)*P3[0],
        (u**3)*P0[1] + 3*(u**2)*t*P1[1] + 3*u*(t**2)*P2[1] + (t**3)*P3[1],
    )

class BezierGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Составная кубическая кривая Безье — редактирование опорных точек")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.points = []
        self.selected = None
        self.dragging = False
        self._build_ui()
        self.bind("<Configure>", lambda e: self._schedule_redraw())

    def _build_ui(self):
        left = tk.Frame(self, padx=8, pady=8)
        left.pack(side=tk.LEFT, fill=tk.Y)
        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        row = 0
        ttk.Label(left, text="Кубические сплайны Безье").grid(row=row, column=0, sticky="w"); row += 1
        ttk.Separator(left).grid(row=row, column=0, sticky="we", pady=6); row += 1
        self.mode = tk.StringVar(value="move")
        fm = tk.Frame(left); fm.grid(row=row, column=0, sticky="we"); row += 1
        ttk.Radiobutton(fm, text="Перемещение", variable=self.mode, value="move").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(fm, text="Добавление",  variable=self.mode, value="add").grid(row=0, column=1, sticky="w", padx=(8,0))
        ttk.Radiobutton(fm, text="Удаление",    variable=self.mode, value="delete").grid(row=0, column=2, sticky="w", padx=(8,0))
        g = tk.Frame(left); g.grid(row=row, column=0, sticky="we"); row += 1
        self.show_poly = tk.BooleanVar(value=True)
        self.show_pts  = tk.BooleanVar(value=True)
        ttk.Checkbutton(g, text="Контрольный многоугольник", variable=self.show_poly, command=self._schedule_redraw).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(g, text="Опорные точки", variable=self.show_pts, command=self._schedule_redraw).grid(row=1, column=0, sticky="w")
        h = tk.Frame(left); h.grid(row=row, column=0, sticky="we"); row += 1
        ttk.Label(h, text="Точек на сегмент").grid(row=0, column=0, sticky="w")
        self.samples = tk.IntVar(value=60)
        ttk.Spinbox(h, from_=6, to=500, textvariable=self.samples, width=6, command=self._schedule_redraw).grid(row=0, column=1, padx=(6,0))
        ttk.Label(h, text="(больше — плавнее кривая)").grid(row=0, column=2, sticky="w", padx=(8,0))
        btns = tk.Frame(left); btns.grid(row=row, column=0, sticky="we", pady=(6,0)); row += 1
        tk.Button(btns, text="Очистить", command=self._clear).grid(row=0, column=0, sticky="w")
        tk.Button(btns, text="Демо-точки", command=self._demo).grid(row=0, column=1, sticky="w", padx=(6,0))
        info = ("Сегменты: (0..3), (3..6), (6..9), ... — т.е. нужно 4, 7, 10, ... точек.\n"
                "Режимы: Добавление — клик по холсту; Перемещение — перетаскивание точки; "
                "Удаление — клик по точке.\n"
                "Backspace/Delete — удалить выбранную; Ctrl+Z — отмена последнего добавления.")
        ttk.Label(left, text=info, foreground="#555", justify="left").grid(row=row, column=0, sticky="we")
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_motion)
        self.bind("<Delete>", self._delete_selected)
        self.bind("<BackSpace>", self._delete_selected)
        self.bind("<Control-z>", self._undo)
        self._redraw_pending = False
        self._schedule_redraw()

    def _clear(self):
        self.points.clear()
        self.selected = None
        self._schedule_redraw()

    def _demo(self):
        w = max(100, self.canvas.winfo_width()); h = max(100, self.canvas.winfo_height())
        self.points = [
            (PADDING, h*0.7),
            (w*0.25, h*0.1),
            (w*0.45, h*0.9),
            (w*0.5,  h*0.6),
            (w*0.65, h*0.3),
            (w*0.85, h*0.9),
            (w-PADDING, h*0.4),
        ]
        self.selected = None
        self._schedule_redraw()

    def _undo(self, e=None):
        if self.points:
            self.points.pop()
            if self.selected is not None and self.selected >= len(self.points):
                self.selected = None
            self._schedule_redraw()

    def _on_click(self, ev):
        x, y = ev.x, ev.y
        if self.mode.get() == "add":
            self.points.append((x, y))
            self.selected = len(self.points) - 1
            self.dragging = False
            self._schedule_redraw()
            return
        idx = self._hit_index(x, y)
        if self.mode.get() == "delete":
            if idx is not None:
                self.points.pop(idx)
                self.selected = None
                self._schedule_redraw()
            return
        if idx is not None:
            self.selected = idx
            self.dragging = True
        else:
            self.selected = None
            self.dragging = False
        self._schedule_redraw()

    def _on_drag(self, ev):
        if self.mode.get() != "move" or not self.dragging or self.selected is None:
            return
        self.points[self.selected] = (ev.x, ev.y)
        self._schedule_redraw()

    def _on_release(self, ev):
        self.dragging = False

    def _on_motion(self, ev):
        idx = self._hit_index(ev.x, ev.y)
        if self.mode.get() == "delete":
            self.canvas.config(cursor="X_cursor" if idx is not None else "")
        elif self.mode.get() == "move":
            self.canvas.config(cursor="hand2" if idx is not None else "")
        else:
            self.canvas.config(cursor="crosshair")

    def _delete_selected(self, e=None):
        if self.selected is not None and 0 <= self.selected < len(self.points):
            self.points.pop(self.selected)
            self.selected = None
            self._schedule_redraw()

    def _hit_index(self, x, y):
        for i, (px, py) in enumerate(self.points):
            if (px - x)**2 + (py - y)**2 <= HIT_R**2:
                return i
        return None

    def _schedule_redraw(self):
        if self._redraw_pending:
            return
        self._redraw_pending = True
        self.after_idle(self._redraw_now)

    def _segments(self):
        segs = []
        n = len(self.points)
        i = 0
        while i + 3 < n:
            P0, P1, P2, P3 = self.points[i], self.points[i+1], self.points[i+2], self.points[i+3]
            segs.append((P0, P1, P2, P3))
            i += 3
        return segs

    def _redraw_now(self):
        self._redraw_pending = False
        c = self.canvas
        c.delete("all")
        if self.show_poly.get() and len(self.points) >= 2:
            for i in range(len(self.points) - 1):
                x1, y1 = self.points[i]
                x2, y2 = self.points[i+1]
                c.create_line(x1, y1, x2, y2, fill="#bbbbbb", dash=(3, 3))
        segs = self._segments()
        samples = max(6, int(self.samples.get()))
        for (P0, P1, P2, P3) in segs:
            prev = P0
            for s in range(1, samples+1):
                t = s / samples
                cur = bezier_cubic(P0, P1, P2, P3, t)
                c.create_line(prev[0], prev[1], cur[0], cur[1], width=2)
                prev = cur
        if self.show_pts.get():
            for i, (x, y) in enumerate(self.points):
                fill = "#1f77b4"
                outline = "black"
                r = PT_R
                if i == self.selected:
                    fill = "#ff7f0e"; r = PT_R + 1
                c.create_oval(x-r, y-r, x+r, y+r, fill=fill, outline=outline)
        n = len(self.points)
        need = (4 - (n % 3)) % 3
        msg = f"Точек: {n}. Сегментов: {max(0, (n-1)//3)}."
        if need:
            msg += f" Добавьте ещё {need} точк(и) для нового сегмента."
        c.create_text(10, 10, anchor="nw", text=msg, fill="#444")

if __name__ == "__main__":
    BezierGUI().mainloop()
