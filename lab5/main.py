import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import math, random, re

# ------------------------- L-system core -------------------------

class StochasticRule:
    def __init__(self):
        self.variants = []
    def add(self, repl, w=None):
        self.variants.append((repl, float(w) if w is not None else None))
    def choose(self, rng):
        if not self.variants:
            return ""
        weights = [w for _, w in self.variants]
        if any(w is not None for w in weights):
            total_spec = sum(w for w in weights if w is not None)
            n_none = sum(1 for w in weights if w is None)
            if n_none:
                rem = max(0.0, 1.0 - total_spec)
                fill = rem / n_none if n_none > 0 else 0.0
                use_w = [(w if w is not None else fill) for w in weights]
            else:
                use_w = weights
        else:
            n = len(weights)
            use_w = [1.0 / n] * n
        r = rng.random() * sum(use_w)
        s = 0.0
        for (repl, _), w in zip(self.variants, use_w):
            s += w
            if r <= s:
                return repl
        return self.variants[-1][0]

class LSystem:
    RULE_RE = re.compile(r'^\s*([A-Za-z])\s*(?:->|=)\s*(.+?)\s*$')
    WEIGHT_RE = re.compile(r'^(.*?)(?:\{\s*([0-9]*\.?[0-9]+)\s*\})?$')

    def __init__(self, axiom="F", angle_deg=60.0, heading_deg=0.0, rules=None):
        self.axiom = axiom
        self.angle = float(angle_deg)
        self.heading0 = float(heading_deg)
        self.rules = rules or {}

    @staticmethod
    def parse_rules(lines):
        rules = {}
        for ln in lines:
            ln = ln.strip()
            if not ln or ln.startswith('#') or ln.startswith('//'):
                continue
            m = LSystem.RULE_RE.match(ln)
            if not m:
                continue
            sym, right = m.group(1), m.group(2)
            variants = [v.strip() for v in right.split('|')]
            sr = StochasticRule()
            for v in variants:
                wm = LSystem.WEIGHT_RE.match(v)
                repl = (wm.group(1) or "").strip()
                w = wm.group(2)
                sr.add(repl, w)
            rules[sym] = sr
        return rules

    @classmethod
    def from_file(cls, path):
        with open(path, 'r', encoding='utf-8') as f:
            lines = [line.rstrip('\n') for line in f]
        if not lines:
            raise ValueError("Пустой файл L-системы")
        header = lines[0].strip()
        parts = header.split()
        if len(parts) < 3:
            raise ValueError("Первая строка должна быть: <аксиома> <угол> <направление>")
        axiom = parts[0]
        angle = float(parts[1].replace(',', '.'))
        heading = float(parts[2].replace(',', '.'))
        rules = cls.parse_rules(lines[1:])
        return cls(axiom, angle, heading, rules)

    def expand(self, iterations, seed=None):
        rng = random.Random(seed)
        s = self.axiom
        for _ in range(iterations):
            out = []
            for ch in s:
                rule = self.rules.get(ch)
                if rule:
                    out.append(rule.choose(rng))
                else:
                    out.append(ch)
            s = "".join(out)
        return s

def interpret(lsys_string, angle_deg, heading0_deg, step,
              angle_jitter_deg=0.0, length_jitter_pct=0.0, seed=None):
    rng = random.Random(seed)
    angle = math.radians(angle_deg)
    heading = math.radians(heading0_deg)
    x, y = 0.0, 0.0
    stack = []
    segments = []
    pts = [(x, y)]

    def jitter_angle():
        if angle_jitter_deg > 0:
            return math.radians(rng.uniform(-angle_jitter_deg, angle_jitter_deg))
        return 0.0

    def jitter_len():
        if length_jitter_pct > 0:
            k = 1.0 + rng.uniform(-length_jitter_pct, length_jitter_pct) / 100.0
            return k
        return 1.0

    for ch in lsys_string:
        if ch in 'Ff':
            L = step * jitter_len()
            nx = x + math.cos(heading) * L
            ny = y + math.sin(heading) * L
            if ch == 'F':
                segments.append((x, y, nx, ny))
            x, y = nx, ny
            pts.append((x, y))
        elif ch == '+':
            heading += angle + jitter_angle()
        elif ch == '-':
            heading -= angle + jitter_angle()
        elif ch == '|':
            heading += math.pi
        elif ch == '[':
            stack.append((x, y, heading))
        elif ch == ']':
            if stack:
                x, y, heading = stack.pop()
                pts.append((x, y))
    return segments, pts

def fit_to_canvas(pts, width, height, padding=20):
    if not pts:
        return (0, 0, 1, 0, 0)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    w = maxx - minx if maxx > minx else 1.0
    h = maxy - miny if maxy > miny else 1.0
    sx = (width - 2 * padding) / w
    sy = (height - 2 * padding) / h
    scale = min(sx, sy)
    tx = padding - minx * scale
    ty = padding - miny * scale
    return scale, tx, ty, minx, miny

def transform(seg, scale, tx, ty, height):
    x1, y1, x2, y2 = seg
    X1 = x1 * scale + tx
    Y1 = height - (y1 * scale + ty)
    X2 = x2 * scale + tx
    Y2 = height - (y2 * scale + ty)
    return X1, Y1, X2, Y2

PRESETS = {
    "Кривая Коха (F→F−F++F−F, 60°)": {
        "header": "F 60 0",
        "rules": ["F -> F-F++F-F"],
        "suggest_step": 6.0
    },
    "Квадратный остров Коха (90°)": {
        "header": "F+F+F+F 90 0",
        "rules": ["F -> F+F-F-FF+F+F-F"],
        "suggest_step": 4.0
    },
    "Ковер/треугольник Серпинского (60°)": {
        "header": "FXF--FF--FF 60 0",
        "rules": ["F -> FF", "X -> --FXF++FXF++FXF--"],
        "suggest_step": 6.0
    },
    "Кривая Гильберта (90°)": {
        "header": "X 90 0",
        "rules": [
            "F -> F",
            "X -> -YF+XFX+FY-",
            "Y -> +XF-YFY-FX+"
        ],
        "suggest_step": 6.0
    },
    "Куст 1 (скобочная, 22°)": {
        "header": "F 22 90",
        "rules": ["F -> FF-[-F+F+F]+[+F-F-F]"],
        "suggest_step": 6.0
    },
    "Куст стохастический (20°)": {
        "header": "X 20 90",
        "rules": [
            "F -> FF",
            "X -> F[+X]F[-X]+X {0.5} | F[+X]-X {0.25} | F[-X]+X {0.25}"
        ],
        "suggest_step": 5.0
    },
}

def _lerp(a, b, t):
    return a + (b - a) * t

def _lerp_color(c1, c2, t):
    r = int(_lerp(c1[0], c2[0], t))
    g = int(_lerp(c1[1], c2[1], t))
    b = int(_lerp(c1[2], c2[2], t))
    return f"#{r:02x}{g:02x}{b:02x}"

class FractalTreeTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self._build_ui()
        self.bind("<Configure>", lambda e: self._schedule_redraw())
        self._redraw_pending = False

    def _build_ui(self):
        left = tk.Frame(self, padx=8, pady=8)
        left.pack(side=tk.LEFT, fill=tk.Y)

        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        row = 0
        ttk.Label(left, text="Фрактальное дерево (1.б)").grid(row=row, column=0, sticky="w"); row += 1
        ttk.Separator(left).grid(row=row, column=0, sticky="we", pady=6); row += 1

        self.depth = tk.IntVar(value=10)
        self.base_angle = tk.DoubleVar(value=22.5)
        self.jitter = tk.DoubleVar(value=8.0)
        self.len0 = tk.DoubleVar(value=180.0)
        self.len_decay = tk.DoubleVar(value=0.72)
        self.thick0 = tk.DoubleVar(value=12.0)
        self.thick_decay = tk.DoubleVar(value=0.68)
        self.seed = tk.StringVar(value="")

        g1 = tk.Frame(left); g1.grid(row=row, column=0, sticky="we"); row += 1
        ttk.Label(g1, text="Глубина").grid(row=0, column=0, sticky="w"); ttk.Spinbox(g1, from_=0, to=14, textvariable=self.depth, width=5).grid(row=0, column=1)
        ttk.Label(g1, text="Баз. угол°").grid(row=0, column=2, sticky="w", padx=(8,0)); ttk.Entry(g1, textvariable=self.base_angle, width=7).grid(row=0, column=3)
        ttk.Label(g1, text="Jitter°").grid(row=0, column=4, sticky="w", padx=(8,0)); ttk.Entry(g1, textvariable=self.jitter, width=7).grid(row=0, column=5)

        g2 = tk.Frame(left); g2.grid(row=row, column=0, sticky="we"); row += 1
        ttk.Label(g2, text="Длина0").grid(row=0, column=0, sticky="w"); ttk.Entry(g2, textvariable=self.len0, width=7).grid(row=0, column=1)
        ttk.Label(g2, text="DecayL").grid(row=0, column=2, sticky="w", padx=(8,0)); ttk.Entry(g2, textvariable=self.len_decay, width=7).grid(row=0, column=3)
        ttk.Label(g2, text="Толщ.0").grid(row=0, column=4, sticky="w", padx=(8,0)); ttk.Entry(g2, textvariable=self.thick0, width=7).grid(row=0, column=5)
        ttk.Label(g2, text="DecayT").grid(row=0, column=6, sticky="w", padx=(8,0)); ttk.Entry(g2, textvariable=self.thick_decay, width=7).grid(row=0, column=7)

        g3 = tk.Frame(left); g3.grid(row=row, column=0, sticky="we"); row += 1
        ttk.Label(g3, text="Seed").grid(row=0, column=0, sticky="w"); ttk.Entry(g3, textvariable=self.seed, width=12).grid(row=0, column=1, sticky="w")
        tk.Button(left, text="Сгенерировать", command=self.redraw).grid(row=row, column=0, sticky="we"); row += 1
        ttk.Label(left, text="От коричневого к зелёному, толщина уменьшается, угол ветвей со случайным разбросом.",
                  foreground="#555").grid(row=row, column=0, sticky="w")

    def _rng(self):
        s = self.seed.get().strip()
        if not s:
            return random.Random()
        try:
            return random.Random(int(s))
        except:
            return random.Random(hash(s))

    def _schedule_redraw(self):
        if self._redraw_pending:
            return
        self._redraw_pending = True
        self.after_idle(self._redraw_now)

    def redraw(self):
        self._redraw_pending = True
        self.after_idle(self._redraw_now)

    def _redraw_now(self):
        self._redraw_pending = False
        c = self.canvas
        w, h = max(10, c.winfo_width()), max(10, c.winfo_height())
        c.delete("all")

        try:
            depth = int(self.depth.get())
            base_angle = math.radians(float(self.base_angle.get()))
            jitter = math.radians(float(self.jitter.get()))
            len0 = float(self.len0.get())
            len_decay = float(self.len_decay.get())
            thick0 = float(self.thick0.get())
            thick_decay = float(self.thick_decay.get())
        except Exception:
            return

        rng = self._rng()

        x0 = w / 2
        y0 = h - 30
        heading = -math.pi / 2

        brown = (139, 69, 19)
        green = (34, 139, 34)

        def branch(x, y, length, angle, thickness, level, max_level):
            if level > max_level or thickness < 0.5 or length < 1.0:
                return
            nx = x + math.cos(angle) * length
            ny = y + math.sin(angle) * length
            t = level / max(1, max_level)
            color = _lerp_color(brown, green, t)
            c.create_line(x, y, nx, ny, width=thickness, fill=color, capstyle=tk.ROUND)
            if level == max_level:
                return
            j1 = rng.uniform(-jitter, jitter)
            j2 = rng.uniform(-jitter, jitter)
            a1 = angle - base_angle + j1
            a2 = angle + base_angle + j2
            branch(nx, ny, length * len_decay, a1, thickness * thick_decay, level + 1, max_level)
            branch(nx, ny, length * len_decay, a2, thickness * thick_decay, level + 1, max_level)
            if rng.random() < 0.12:
                j3 = rng.uniform(-jitter, jitter)
                a3 = angle + rng.uniform(-base_angle * 0.5, base_angle * 0.5) + j3
                branch(nx, ny, length * len_decay * 0.9, a3, thickness * thick_decay * 0.9, level + 1, max_level)

        branch(x0, y0, len0, heading, thick0, 0, depth)

class LSystemTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.sidebar = tk.Frame(self, padx=8, pady=8)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        row = 0
        ttk.Label(self.sidebar, text="Файл / пресет").grid(row=row, column=0, sticky="w")
        row += 1
        self.btn_load = ttk.Button(self.sidebar, text="Загрузить .lsys файл", command=self.load_file)
        self.btn_load.grid(row=row, column=0, sticky="we")
        row += 1

        ttk.Label(self.sidebar, text="Пресет из лекции").grid(row=row, column=0, sticky="w")
        row += 1
        self.preset_var = tk.StringVar(value=list(PRESETS.keys())[0])
        self.preset_combo = ttk.Combobox(self.sidebar, textvariable=self.preset_var,
                                         values=list(PRESETS.keys()), state="readonly")
        self.preset_combo.grid(row=row, column=0, sticky="we")
        self.preset_combo.bind("<<ComboboxSelected>>", self.apply_preset)
        row += 1

        ttk.Separator(self.sidebar).grid(row=row, column=0, sticky="we", pady=6)
        row += 1

        ttk.Label(self.sidebar, text="Аксиома / угол / направление").grid(row=row, column=0, sticky="w")
        row += 1
        self.axiom_var = tk.StringVar(value="F")
        ttk.Entry(self.sidebar, textvariable=self.axiom_var).grid(row=row, column=0, sticky="we"); row += 1

        frame_nums = tk.Frame(self.sidebar)
        frame_nums.grid(row=row, column=0, sticky="we")
        self.angle_var = tk.DoubleVar(value=60.0)
        self.heading_var = tk.DoubleVar(value=0.0)
        ttk.Label(frame_nums, text="угол°").grid(row=0, column=0)
        ttk.Entry(frame_nums, textvariable=self.angle_var, width=8).grid(row=0, column=1)
        ttk.Label(frame_nums, text="направление°").grid(row=0, column=2, padx=(8,0))
        ttk.Entry(frame_nums, textvariable=self.heading_var, width=8).grid(row=0, column=3)
        row += 1

        ttk.Label(self.sidebar, text="Правила").grid(row=row, column=0, sticky="w")
        row += 1
        self.txt_rules = tk.Text(self.sidebar, width=36, height=14)
        self.txt_rules.grid(row=row, column=0, sticky="we")
        row += 1

        ttk.Separator(self.sidebar).grid(row=row, column=0, sticky="we", pady=6)
        row += 1

        frame_params = tk.Frame(self.sidebar)
        frame_params.grid(row=row, column=0, sticky="we"); row += 1

        ttk.Label(frame_params, text="Итерации").grid(row=0, column=0)
        self.iters_var = tk.IntVar(value=4)
        ttk.Spinbox(frame_params, from_=0, to=10, textvariable=self.iters_var, width=5).grid(row=0, column=1)

        ttk.Label(frame_params, text="Шаг").grid(row=0, column=2, padx=(8,0))
        self.step_var = tk.DoubleVar(value=6.0)
        ttk.Entry(frame_params, textvariable=self.step_var, width=6).grid(row=0, column=3)

        ttk.Label(frame_params, text="Angle jitter°").grid(row=1, column=0, pady=4)
        self.ajit_var = tk.DoubleVar(value=0.0)
        ttk.Entry(frame_params, textvariable=self.ajit_var, width=5).grid(row=1, column=1)

        ttk.Label(frame_params, text="Length jitter %").grid(row=1, column=2)
        self.ljit_var = tk.DoubleVar(value=0.0)
        ttk.Entry(frame_params, textvariable=self.ljit_var, width=6).grid(row=1, column=3)

        ttk.Label(frame_params, text="Seed").grid(row=2, column=0, pady=(4,0))
        self.seed_var = tk.StringVar(value="")
        ttk.Entry(frame_params, textvariable=self.seed_var, width=12).grid(row=2, column=1, columnspan=3, sticky="w")

        ttk.Separator(self.sidebar).grid(row=row, column=0, sticky="we", pady=6)
        row += 1

        self.btn_render = ttk.Button(self.sidebar, text="Сгенерировать", command=self.render)
        self.btn_render.grid(row=row, column=0, sticky="we"); row += 1

        self.status_var = tk.StringVar(value="Готово")
        ttk.Label(self.sidebar, textvariable=self.status_var, foreground="#555").grid(row=row, column=0, sticky="w")
        row += 1

        self.sidebar.grid_columnconfigure(0, weight=1)

        self.apply_preset()
        self.bind("<Configure>", lambda e: self._maybe_redraw_on_resize())

        self._last_segments = None
        self._last_pts = None
        self._last_params = None

    def apply_preset(self, event=None):
        p = PRESETS[self.preset_var.get()]
        header = p["header"].split()
        self.axiom_var.set(header[0])
        self.angle_var.set(float(header[1]))
        self.heading_var.set(float(header[2]))
        self.step_var.set(p.get("suggest_step", 6.0))
        self.txt_rules.delete("1.0", tk.END)
        self.txt_rules.insert(tk.END, "\n".join(p["rules"]))
        self.status_var.set("Пресет загружен")

    def load_file(self):
        path = filedialog.askopenfilename(title="Выберите L-систему",
                                          filetypes=[("L-system files","*.txt *.lsys"), ("All files","*.*")])
        if not path:
            return
        try:
            lsys = LSystem.from_file(path)
        except Exception as e:
            messagebox.showerror("Ошибка парсинга", str(e))
            return
        self.axiom_var.set(lsys.axiom)
        self.angle_var.set(lsys.angle)
        self.heading_var.set(lsys.heading0)
        out = []
        for sym, sr in lsys.rules.items():
            parts = []
            for repl, w in sr.variants:
                parts.append(repl if w is None else f"{repl} {{{w}}}")
            out.append(f"{sym} -> " + " | ".join(parts))
        self.txt_rules.delete("1.0", tk.END)
        self.txt_rules.insert(tk.END, "\n".join(out))
        self.status_var.set(f"Файл загружен: {path}")

    def _seed_value(self):
        s = self.seed_var.get().strip()
        if not s:
            return None
        try:
            return int(s)
        except:
            return hash(s)

    def build_lsystem(self):
        ax = self.axiom_var.get().strip()
        ang = float(self.angle_var.get())
        hdg = float(self.heading_var.get())
        lines = self.txt_rules.get("1.0", tk.END).splitlines()
        rules = LSystem.parse_rules(lines)
        return LSystem(ax, ang, hdg, rules)

    def render(self):
        try:
            lsys = self.build_lsystem()
            iters = int(self.iters_var.get())
            seed = self._seed_value()
            s = lsys.expand(iters, seed=seed)
            step = float(self.step_var.get())
            segments, pts = interpret(
                s, lsys.angle, lsys.heading0, step,
                angle_jitter_deg=float(self.ajit_var.get()),
                length_jitter_pct=float(self.ljit_var.get()),
                seed=seed
            )
            self._last_segments, self._last_pts = segments, pts
            self._last_params = (lsys.angle, lsys.heading0, step,
                                 float(self.ajit_var.get()), float(self.ljit_var.get()))
            self.draw_current()
            self.status_var.set(f"Итерации: {iters}, сегментов: {len(segments)}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _maybe_redraw_on_resize(self):
        if self._last_segments is None or self._last_pts is None:
            return
        self.after_idle(self.draw_current)

    def draw_current(self):
        self.canvas.delete("all")
        if not self._last_pts:
            return
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        scale, tx, ty, _, _ = fit_to_canvas(self._last_pts, w, h, padding=20)
        for seg in self._last_segments:
            X1, Y1, X2, Y2 = transform(seg, scale, tx, ty, h)
            self.canvas.create_line(X1, Y1, X2, Y2)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Фракталы: L-система и дерево (1.б)")
        self.geometry("1100x700")
        self.minsize(900, 600)

        nb = ttk.Notebook(self)
        self.tab_lsys = LSystemTab(nb)
        self.tab_tree = FractalTreeTab(nb)
        nb.add(self.tab_lsys, text="L-система (1.а)")
        nb.add(self.tab_tree, text="Фрактальное дерево (1.б)")
        nb.pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    App().mainloop()
