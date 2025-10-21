import tkinter as tk
from tkinter import ttk
import random

PADDING = 40

class MidpointGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Midpoint Displacement — 2D горный массив")
        self.geometry("1100x700")
        self.minsize(900, 600)

        self._build_ui()
        self._points_by_level = []
        self._redraw_pending = False

        self._rebuild_all()
        self.bind("<Configure>", lambda e: self._schedule_redraw())

    # ---------- UI ----------
    def _build_ui(self):
        left = tk.Frame(self, padx=8, pady=8)
        left.pack(side=tk.LEFT, fill=tk.Y)

        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        row = 0
        ttk.Label(left, text="Midpoint Displacement (2D)").grid(row=row, column=0, sticky="w"); row += 1
        ttk.Separator(left).grid(row=row, column=0, sticky="we", pady=6); row += 1

        self.iter_max = tk.IntVar(value=8)
        self.step_view = tk.IntVar(value=0)
        self.roughness = tk.DoubleVar(value=0.5)
        self.disp0 = tk.DoubleVar(value=160.0)
        self.y0_rel = tk.DoubleVar(value=0.55)
        self.y1_rel = tk.DoubleVar(value=0.55)
        self.seed = tk.StringVar(value="")
        self.show_history = tk.BooleanVar(value=True)
        self.line_width = tk.DoubleVar(value=2.0)

        g1 = tk.Frame(left); g1.grid(row=row, column=0, sticky="we"); row += 1
        ttk.Label(g1, text="Итерации (max)").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(g1, from_=0, to=16, textvariable=self.iter_max, width=5,
                    command=self._rebuild_all).grid(row=0, column=1, padx=(4,0))
        ttk.Label(g1, text="Просмотр шага").grid(row=0, column=2, sticky="w", padx=(10,4))
        self.step_scale = ttk.Scale(g1, from_=0, to=self.iter_max.get(),
                                    variable=self.step_view,
                                    command=lambda e: self._schedule_redraw())
        self.step_scale.grid(row=0, column=3, sticky="we")
        g1.grid_columnconfigure(3, weight=1)

        g2 = tk.Frame(left); g2.grid(row=row, column=0, sticky="we"); row += 1
        ttk.Label(g2, text="Roughness").grid(row=0, column=0, sticky="w")
        ttk.Entry(g2, textvariable=self.roughness, width=8).grid(row=0, column=1, padx=(4,10))
        ttk.Label(g2, text="Disp0").grid(row=0, column=2, sticky="w")
        ttk.Entry(g2, textvariable=self.disp0, width=8).grid(row=0, column=3, padx=(4,10))
        ttk.Label(g2, text="Толщина").grid(row=0, column=4, sticky="w")
        ttk.Entry(g2, textvariable=self.line_width, width=6).grid(row=0, column=5, padx=(4,0))

        g3 = tk.Frame(left); g3.grid(row=row, column=0, sticky="we"); row += 1
        ttk.Label(g3, text="Y0 (0..1)").grid(row=0, column=0, sticky="w")
        ttk.Entry(g3, textvariable=self.y0_rel, width=6).grid(row=0, column=1, padx=(4,10))
        ttk.Label(g3, text="Y1 (0..1)").grid(row=0, column=2, sticky="w")
        ttk.Entry(g3, textvariable=self.y1_rel, width=6).grid(row=0, column=3, padx=(4,10))
        ttk.Label(g3, text="Seed").grid(row=0, column=4, sticky="w")
        ttk.Entry(g3, textvariable=self.seed, width=12).grid(row=0, column=5, padx=(4,10))
        ttk.Checkbutton(g3, text="Показывать историю", variable=self.show_history,
                        command=self._schedule_redraw).grid(row=0, column=6, sticky="w")

        ttk.Separator(left).grid(row=row, column=0, sticky="we", pady=6); row += 1
        tk.Button(left, text="Перегенерировать", command=self._rebuild_all).grid(row=row, column=0, sticky="we"); row += 1


    # ---------- Logic ----------
    def _rng(self):
        s = self.seed.get().strip()
        if not s:
            return random.Random()
        try:
            return random.Random(int(s))
        except:
            return random.Random(hash(s))

    def _rebuild_all(self):
        try:
            iter_max = int(self.iter_max.get())
            rough = float(self.roughness.get())
            disp0 = float(self.disp0.get())
            y0r = float(self.y0_rel.get())
            y1r = float(self.y1_rel.get())
        except Exception:
            return

        rng = self._rng()

        w = max(100, self.canvas.winfo_width())
        h = max(100, self.canvas.winfo_height())

        xL, xR = PADDING, w - PADDING
        yL = h * y0r
        yR = h * y1r

        points = [(xL, yL), (xR, yR)]
        levels = [points[:]]

        disp = disp0
        for _ in range(iter_max):
            new_pts = [points[0]]
            for i in range(len(points) - 1):
                xA, yA = points[i]
                xB, yB = points[i + 1]
                xm = 0.5 * (xA + xB)
                ym = 0.5 * (yA + yB) + rng.uniform(-disp, disp)
                new_pts.append((xm, ym))
                new_pts.append((xB, yB))
            points = new_pts
            levels.append(points[:])
            disp *= rough

        self._points_by_level = levels
        self.step_scale.configure(to=len(levels) - 1)
        if self.step_view.get() > len(levels) - 1:
            self.step_view.set(len(levels) - 1)

        self._schedule_redraw()

    # ---------- Drawing ----------
    def _schedule_redraw(self):
        if self._redraw_pending:
            return
        self._redraw_pending = True
        self.after_idle(self._redraw_now)

    def _redraw_now(self):
        self._redraw_pending = False
        c = self.canvas
        c.delete("all")

        if not self._points_by_level:
            return

        k = int(self.step_view.get())
        lw = max(1.0, float(self.line_width.get()))

        if self.show_history.get():
            for i in range(k):
                pts = self._points_by_level[i]
                for j in range(len(pts) - 1):
                    x1, y1 = pts[j]
                    x2, y2 = pts[j + 1]
                    c.create_line(x1, y1, x2, y2, fill="#bbbbbb")

        pts = self._points_by_level[k]
        for j in range(len(pts) - 1):
            x1, y1 = pts[j]
            x2, y2 = pts[j + 1]
            c.create_line(x1, y1, x2, y2, width=lw)

if __name__ == "__main__":
    MidpointGUI().mainloop()
