import math
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class Face:
    def __init__(self, indices):
        self.indices = list(indices)

class Polyhedron:
    def __init__(self, vertices: np.ndarray, faces: list, color="#5a9bd8", name="obj"):
        self.V = np.array(vertices, dtype=float)
        self.faces = [Face(f) for f in faces]
        self.color = color
        self.name = name
    def copy(self):
        q = Polyhedron(self.V.copy(), [f.indices[:] for f in self.faces], color=self.color, name=self.name)
        return q
    def center(self):
        return np.mean(self.V, axis=0)
    def apply_matrix(self, M: np.ndarray):
        N = self.V.shape[0]
        hom = np.hstack([self.V, np.ones((N, 1))])
        transformed = (M @ hom.T).T
        w = transformed[:, 3:4]
        w[w == 0] = 1.0
        self.V = transformed[:, :3] / w

def matrix_translate(tx, ty, tz):
    M = np.eye(4)
    M[0, 3] = tx; M[1, 3] = ty; M[2, 3] = tz
    return M

def matrix_scale(sx, sy, sz):
    M = np.eye(4)
    M[0, 0] = sx; M[1, 1] = sy; M[2, 2] = sz
    return M

def matrix_rotate_x(angle_rad):
    c = math.cos(angle_rad); s = math.sin(angle_rad)
    M = np.eye(4)
    M[1, 1] = c; M[1, 2] = -s; M[2, 1] = s; M[2, 2] = c
    return M

def matrix_rotate_y(angle_rad):
    c = math.cos(angle_rad); s = math.sin(angle_rad)
    M = np.eye(4)
    M[0, 0] = c; M[0, 2] = s; M[2, 0] = -s; M[2, 2] = c
    return M

def matrix_rotate_z(angle_rad):
    c = math.cos(angle_rad); s = math.sin(angle_rad)
    M = np.eye(4)
    M[0, 0] = c; M[0, 1] = -s; M[1, 0] = s; M[1, 1] = c
    return M

def matrix_reflect_plane(plane):
    if plane == 'xy': return matrix_scale(1, 1, -1)
    if plane == 'yz': return matrix_scale(-1, 1, 1)
    if plane == 'xz': return matrix_scale(1, -1, 1)

def rotation_matrix_axis_angle(axis, angle_rad):
    axis = np.array(axis, dtype=float)
    norm = np.linalg.norm(axis)
    if norm == 0: return np.eye(4)
    x, y, z = axis / norm
    c = math.cos(angle_rad); s = math.sin(angle_rad); C = 1 - c
    R3 = np.array([
        [x * x * C + c,     x * y * C - z * s, x * z * C + y * s],
        [y * x * C + z * s, y * y * C + c,     y * z * C - x * s],
        [z * x * C - y * s, z * y * C + x * s, z * z * C + c    ]
    ])
    M = np.eye(4); M[:3, :3] = R3
    return M

def matrix_rotate_axis_through_point(axis_letter, angle_rad, point):
    axis_letter = axis_letter.lower()
    T1 = matrix_translate(-point[0], -point[1], -point[2])
    if axis_letter == 'x': R = matrix_rotate_x(angle_rad)
    elif axis_letter == 'y': R = matrix_rotate_y(angle_rad)
    elif axis_letter == 'z': R = matrix_rotate_z(angle_rad)
    T2 = matrix_translate(point[0], point[1], point[2])
    return T2 @ R @ T1

def project_perspective(points3, camera_distance=5.0):
    pts = np.array(points3, dtype=float)
    z = pts[:, 2]; d = camera_distance
    denom = (d - z); denom[denom == 0] = 1e-6
    factor = d / denom
    x2 = pts[:, 0] * factor; y2 = pts[:, 1] * factor
    return np.vstack([x2, y2]).T

def project_orthographic(points3):
    return points3[:, :2]

def isometric_rotation_matrix():
    alpha = math.radians(35.2643897)
    beta = math.radians(45.0)
    Rx = matrix_rotate_x(alpha); Rz = matrix_rotate_z(beta)
    return (Rz @ Rx)[:3, :3]

def make_tetrahedron(color="#5a9bd8"):
    verts = np.array([[1,1,1],[1,-1,-1],[-1,1,-1],[-1,-1,1]], dtype=float)
    verts = verts / np.linalg.norm(verts[0])
    faces = [[0,1,2],[0,3,1],[0,2,3],[1,3,2]]
    return Polyhedron(verts, faces, color=color, name="Тетраэдр")

def make_cube(color="#5a9bd8"):
    s = 1.0
    verts = np.array([[x,y,z] for x in (-s,s) for y in (-s,s) for z in (-s,s)], dtype=float)
    faces = [[0,1,3,2],[4,6,7,5],[0,2,6,4],[1,5,7,3],[0,4,5,1],[2,3,7,6]]
    return Polyhedron(verts, faces, color=color, name="Куб")

def make_octahedron(color="#5a9bd8"):
    verts = np.array([[ 1,0,0],[-1,0,0],[0, 1,0],[0,-1,0],[0,0, 1],[0,0,-1]], dtype=float)
    faces = [[0,2,4],[2,1,4],[1,3,4],[3,0,4],[2,0,5],[1,2,5],[3,1,5],[0,3,5]]
    return Polyhedron(verts, faces, color=color, name="Октаэдр")

def make_icosahedron(color="#5a9bd8"):
    t = (1.0 + math.sqrt(5.0)) / 2.0
    verts = np.array([
        [-1, t, 0],[ 1, t, 0],[-1,-t, 0],[ 1,-t, 0],
        [ 0,-1, t],[ 0, 1, t],[ 0,-1,-t],[ 0, 1,-t],
        [ t, 0,-1],[ t, 0, 1],[-t, 0,-1],[-t, 0, 1]
    ], dtype=float)
    verts /= np.max(np.linalg.norm(verts, axis=1))
    faces = [
        [0,11,5],[0,5,1],[0,1,7],[0,7,10],[0,10,11],
        [1,5,9],[5,11,4],[11,10,2],[10,7,6],[7,1,8],
        [3,9,4],[3,4,2],[3,2,6],[3,6,8],[3,8,9],
        [4,9,5],[2,4,11],[6,2,10],[8,6,7],[9,8,1]
    ]
    return Polyhedron(verts, faces, color=color, name="Икосаэдр")

def make_dodecahedron(color="#5a9bd8"):
    ico = make_icosahedron(color)
    centers = []
    for f in ico.faces:
        pts = ico.V[np.array(f.indices)]
        centers.append(np.mean(pts, axis=0))
    centers = np.array(centers)
    centers /= np.max(np.linalg.norm(centers, axis=1))
    ico_faces = [f.indices for f in ico.faces]
    dfaces = []
    for vi, v in enumerate(ico.V):
        incident = [fi for fi, face in enumerate(ico_faces) if vi in face]
        pts = centers[incident]
        n = v / np.linalg.norm(v)
        ref = np.array([1, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1, 0])
        x_axis = np.cross(ref, n); x_axis /= np.linalg.norm(x_axis)
        y_axis = np.cross(n, x_axis)
        cen = np.mean(pts, axis=0); local = pts - cen
        angs = [math.atan2(np.dot(p, y_axis), np.dot(p, x_axis)) for p in local]
        incident_sorted = [i for _, i in sorted(zip(angs, incident))]
        dfaces.append(incident_sorted)
    centers /= np.max(np.linalg.norm(centers, axis=1))
    return Polyhedron(centers, dfaces, color=color, name="Додекаэдр")

def compute_face_normal_basic(V, idxs):
    if len(idxs) < 3: return np.array([0.0,0.0,0.0])
    v0, v1, v2 = V[idxs[0]], V[idxs[1]], V[idxs[2]]
    n = np.cross(v1 - v0, v2 - v0)
    ln = np.linalg.norm(n)
    if ln == 0: return np.array([0.0, 0.0, 0.0])
    return n / ln

def compute_face_normal_outward(V, idxs, obj_center):
    n = compute_face_normal_basic(V, idxs)
    if np.allclose(n, 0.0): return n
    centroid = np.mean(V[np.array(idxs)], axis=0)
    dir_out = centroid - obj_center
    if np.dot(n, dir_out) < 0: n = -n
    return n

class PolyhedronApp:
    def __init__(self, root):
        self.root = root
        root.title("Лабораторная — Z-буфер + два объекта")
        self.canvas_w = 720
        self.canvas_h = 720

        self.objA = make_cube("#5a9bd8")
        self.objB = make_cube("#e4a84b")
        self.objB_enabled = False

        self.projection_mode = 'perspective'
        self.camera_distance = 5.0
        self.scale = 180.0
        self.offset = np.array([self.canvas_w / 2, self.canvas_h / 2])
        self.bg_color = "#1e1e1e"

        self.front_outline = "#e6e6e6"
        self.back_outline  = "#7aa2c0"

        self.cull_enabled = False
        self.zbuffer_enabled = False
        self.render_scale = 1.0
        self.anim_enabled = True

        self.overlay_wire_enabled = True              # <-- НОВОЕ: каркас поверх заливки
        self.overlay_wire_front_only = True           # <-- НОВОЕ: только фронтальные / все
        self.wire_on_fill_color = "#ffffff"           # <-- НОВОЕ: цвет линий поверх заливки
        self.wire_on_fill_width = 1                   # <-- НОВОЕ: толщина линий

        self.look_vec = np.array([0.0, 0.0, -1.0])

        main = ttk.Frame(root); main.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(main, width=self.canvas_w, height=self.canvas_h, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ctrl = ttk.Frame(main, width=520); ctrl.pack(side=tk.RIGHT, fill=tk.Y, padx=6, pady=6)
        self.nb = ttk.Notebook(ctrl); self.nb.pack(fill=tk.BOTH, expand=True)

        tab_a = ttk.Frame(self.nb); self.nb.add(tab_a, text="Объект A")
        self._build_object_tab(tab_a, which="A")

        tab_b = ttk.Frame(self.nb); self.nb.add(tab_b, text="Объект B")
        self._build_object_tab(tab_b, which="B")

        tab_tr = ttk.Frame(self.nb); self.nb.add(tab_tr, text="Сцена")
        self._build_scene_tab(tab_tr)

        self.fit_in_view()
        self.img_handle = None
        self.draw()
        self.tick()

    def _build_object_tab(self, frame, which="A"):
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Модель:").grid(row=0, column=0, sticky="w", padx=4, pady=(6,2))
        var = tk.StringVar(value="Куб")
        setattr(self, f"poly_var_{which}", var)
        ttk.OptionMenu(frame, var, "Куб", "Тетраэдр", "Куб", "Октаэдр", "Икосаэдр", "Додекаэдр",
                       command=lambda *_: self.change_poly(which)).grid(row=0, column=1, sticky="we", padx=4, pady=(6,2))

        io = ttk.Frame(frame); io.grid(row=1, column=0, columnspan=2, sticky="we", padx=4, pady=(2,2))
        io.columnconfigure(0, weight=1); io.columnconfigure(1, weight=1)
        ttk.Button(io, text="Загрузить OBJ", command=lambda: self.load_obj_dialog(which)).grid(row=0, column=0, sticky="we", padx=(0,2))
        ttk.Button(io, text="Сохранить OBJ", command=lambda: self.save_obj_dialog(which)).grid(row=0, column=1, sticky="we", padx=(2,0))

        if which == "B":
            on_var = tk.BooleanVar(value=False)
            setattr(self, "objB_on_var", on_var)
            ttk.Checkbutton(frame, text="Включить объект B", variable=on_var, command=self.toggle_objB).grid(row=2, column=0, columnspan=2, sticky="w", padx=4, pady=(4,2))

        sep1 = ttk.Separator(frame); sep1.grid(row=3, column=0, columnspan=2, sticky="we", padx=4, pady=6)

        left = ttk.Frame(frame); left.grid(row=4, column=0, columnspan=2, sticky="we", padx=4)
        for i in range(6): left.columnconfigure(i, weight=1)

        ttk.Label(left, text="Смещение tx ty tz").grid(row=0, column=0, columnspan=6, sticky="w")
        tx = ttk.Entry(left, width=7); ty = ttk.Entry(left, width=7); tz = ttk.Entry(left, width=7)
        tx.insert(0, "0"); ty.insert(0, "0"); tz.insert(0, "0")
        tx.grid(row=1, column=0); ty.grid(row=1, column=1); tz.grid(row=1, column=2)
        ttk.Button(left, text="Применить", command=lambda: self.apply_translate_obj(which, tx, ty, tz)).grid(row=1, column=3, columnspan=3, sticky="we", padx=(6,0))

        ttk.Label(left, text="Масштаб sx sy sz").grid(row=2, column=0, columnspan=6, sticky="w", pady=(6,0))
        sx = ttk.Entry(left, width=7); sy = ttk.Entry(left, width=7); sz = ttk.Entry(left, width=7)
        sx.insert(0, "1"); sy.insert(0, "1"); sz.insert(0, "1")
        sx.grid(row=3, column=0); sy.grid(row=3, column=1); sz.grid(row=3, column=2)
        ttk.Button(left, text="Применить", command=lambda: self.apply_scale_obj(which, sx, sy, sz)).grid(row=3, column=3, columnspan=3, sticky="we", padx=(6,0))

        ttk.Label(left, text="Поворот (град) ax ay az").grid(row=4, column=0, columnspan=6, sticky="w", pady=(6,0))
        ax = ttk.Entry(left, width=7); ay = ttk.Entry(left, width=7); az = ttk.Entry(left, width=7)
        ax.insert(0, "0"); ay.insert(0, "0"); az.insert(0, "0")
        ax.grid(row=5, column=0); ay.grid(row=5, column=1); az.grid(row=5, column=2)
        ttk.Button(left, text="Применить", command=lambda: self.apply_rotation_obj(which, ax, ay, az)).grid(row=5, column=3, columnspan=3, sticky="we", padx=(6,0))

        ttk.Label(left, text="Масштаб от центра (k)").grid(row=6, column=0, columnspan=3, sticky="w", pady=(6,0))
        k_e = ttk.Entry(left, width=7); k_e.insert(0, "1")
        k_e.grid(row=6, column=3, sticky="we")
        ttk.Button(left, text="Применить", command=lambda: self.apply_scale_about_center_obj(which, k_e)).grid(row=6, column=4, columnspan=2, sticky="we", padx=(6,0))

        ttk.Label(left, text="Вращение вокруг оси через центр:").grid(row=7, column=0, columnspan=6, sticky="w", pady=(6,0))
        axis_var = tk.StringVar(value="y")
        ttk.OptionMenu(left, axis_var, "y", "x", "y", "z").grid(row=8, column=0, sticky="we")
        ang_e = ttk.Entry(left, width=7); ang_e.insert(0, "0")
        ang_e.grid(row=8, column=1, sticky="we")
        ttk.Button(left, text="Повернуть", command=lambda: self.apply_rotate_around_center_obj(which, axis_var, ang_e)).grid(row=8, column=3, columnspan=3, sticky="we", padx=(6,0))

        ttk.Button(frame, text="Сброс объекта", command=lambda: self.reset_object(which)).grid(row=9, column=0, columnspan=2, sticky="we", padx=4, pady=(10,6))

    def _build_scene_tab(self, frame):
        for i in range(2): frame.columnconfigure(i, weight=1)

        ttk.Label(frame, text="Проекция:").grid(row=0, column=0, sticky="w", padx=4, pady=(6,2))
        self.proj_var = tk.StringVar(value="Перспективная")
        ttk.OptionMenu(frame, self.proj_var, "Перспективная", "Перспективная", "Изометрическая",
                       command=self.change_projection).grid(row=0, column=1, sticky="we", padx=4, pady=(6,2))

        vf = ttk.LabelFrame(frame, text="Вектор обзора (для изометрической)")
        vf.grid(row=1, column=0, columnspan=2, sticky="we", padx=4, pady=(6,4))
        for i in range(6): vf.columnconfigure(i, weight=1)
        ttk.Label(vf, text="lx").grid(row=0, column=0); ttk.Label(vf, text="ly").grid(row=0, column=2); ttk.Label(vf, text="lz").grid(row=0, column=4)
        self.lx_e = ttk.Entry(vf, width=8); self.ly_e = ttk.Entry(vf, width=8); self.lz_e = ttk.Entry(vf, width=8)
        self.lx_e.insert(0, "0"); self.ly_e.insert(0, "0"); self.lz_e.insert(0, "-1")
        self.lx_e.grid(row=0, column=1, padx=2); self.ly_e.grid(row=0, column=3, padx=2); self.lz_e.grid(row=0, column=5, padx=2)
        ttk.Button(vf, text="Применить", command=self.apply_look_vec).grid(row=1, column=0, columnspan=6, sticky="we", pady=(4,0))

        flags = ttk.Frame(frame); flags.grid(row=2, column=0, columnspan=2, sticky="we", padx=4, pady=(6,2))
        for i in range(7): flags.columnconfigure(i, weight=1)

        self.cull_var = tk.BooleanVar(value=False)
        self.zbuf_var = tk.BooleanVar(value=False)
        self.anim_var = tk.BooleanVar(value=True)
        self.overlay_wire_var = tk.BooleanVar(value=True)               # <-- НОВОЕ
        self.overlay_wire_mode = tk.StringVar(value="Только фронт")     # <-- НОВОЕ

        ttk.Checkbutton(flags, text="Отсекать нелицевые (каркас)", variable=self.cull_var, command=self.toggle_cull).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(flags, text="Z-буфер (заливка)", variable=self.zbuf_var, command=self.toggle_zbuf).grid(row=0, column=1, sticky="w")
        ttk.Checkbutton(flags, text="Вращать", variable=self.anim_var, command=self.toggle_anim).grid(row=0, column=2, sticky="w")

        ttk.Label(flags, text="Качество Z-буфера:").grid(row=0, column=3, sticky="e")
        self.quality_var = tk.StringVar(value="100%")
        ttk.OptionMenu(flags, self.quality_var, "100%", "100%", "50%", "33%", "25%", command=self.change_quality).grid(row=0, column=4, sticky="we")

        # НОВОЕ: Каркас поверх заливки + режим
        ttk.Checkbutton(flags, text="Каркас поверх заливки", variable=self.overlay_wire_var, command=self.toggle_overlay_wire).grid(row=0, column=5, sticky="w")
        ttk.OptionMenu(flags, self.overlay_wire_mode, "Только фронт", "Только фронт", "Все ребра", command=self.change_overlay_mode).grid(row=0, column=6, sticky="we")

        sep = ttk.Separator(frame); sep.grid(row=3, column=0, columnspan=2, sticky="we", padx=4, pady=6)

        left = ttk.Frame(frame); left.grid(row=4, column=0, columnspan=2, sticky="we", padx=4)
        for i in range(6): left.columnconfigure(i, weight=1)

        ttk.Label(left, text="Смещение tx ty tz").grid(row=0, column=0, columnspan=6, sticky="w")
        self.tx = ttk.Entry(left, width=7); self.ty = ttk.Entry(left, width=7); self.tz = ttk.Entry(left, width=7)
        self.tx.insert(0, "0"); self.ty.insert(0, "0"); self.tz.insert(0, "0")
        self.tx.grid(row=1, column=0); self.ty.grid(row=1, column=1); self.tz.grid(row=1, column=2)
        ttk.Button(left, text="Применить", command=self.apply_translate_scene).grid(row=1, column=3, columnspan=3, sticky="we", padx=(6,0))

        ttk.Label(left, text="Масштаб sx sy sz").grid(row=2, column=0, columnspan=6, sticky="w", pady=(6,0))
        self.sx = ttk.Entry(left, width=7); self.sy = ttk.Entry(left, width=7); self.sz = ttk.Entry(left, width=7)
        self.sx.insert(0, "1"); self.sy.insert(0, "1"); self.sz.insert(0, "1")
        self.sx.grid(row=3, column=0); self.sy.grid(row=3, column=1); self.sz.grid(row=3, column=2)
        ttk.Button(left, text="Применить", command=self.apply_scale_scene).grid(row=3, column=3, columnspan=3, sticky="we", padx=(6,0))

        ttk.Label(left, text="Поворот (град) ax ay az").grid(row=4, column=0, columnspan=6, sticky="w", pady=(6,0))
        self.ax = ttk.Entry(left, width=7); self.ay = ttk.Entry(left, width=7); self.az = ttk.Entry(left, width=7)
        self.ax.insert(0, "0"); self.ay.insert(0, "0"); self.az.insert(0, "0")
        self.ax.grid(row=5, column=0); self.ay.grid(row=5, column=1); self.az.grid(row=5, column=2)
        ttk.Button(left, text="Применить", command=self.apply_rotation_scene).grid(row=5, column=3, columnspan=3, sticky="we", padx=(6,0))

        ttk.Label(left, text="Отражение в плоскости:").grid(row=6, column=0, columnspan=3, sticky="w", pady=(6,0))
        self.plane_var = tk.StringVar(value="xy")
        ttk.OptionMenu(left, self.plane_var, "xy", "xy", "yz", "xz").grid(row=6, column=3, sticky="we")
        ttk.Button(left, text="Отразить", command=self.apply_reflect_scene).grid(row=6, column=4, columnspan=2, sticky="we")

        ttk.Label(left, text="Масштаб от центра (k)").grid(row=7, column=0, columnspan=3, sticky="w", pady=(6,0))
        self.factor_e = ttk.Entry(left, width=7); self.factor_e.insert(0, "1")
        self.factor_e.grid(row=7, column=3, sticky="we")
        ttk.Button(left, text="Применить", command=self.apply_scale_about_center_scene).grid(row=7, column=4, columnspan=2, sticky="we")

        ttk.Label(left, text="Вращение вокруг оси через центр сцены:").grid(row=8, column=0, columnspan=6, sticky="w", pady=(6,0))
        self.axis_var = tk.StringVar(value="y")
        ttk.OptionMenu(left, self.axis_var, "y", "x", "y", "z").grid(row=9, column=0, sticky="we")
        self.angle_axis_e = ttk.Entry(left, width=7); self.angle_axis_e.insert(0, "0")
        self.angle_axis_e.grid(row=9, column=1, sticky="we")
        ttk.Button(left, text="Повернуть", command=self.apply_rotate_around_center_scene).grid(row=9, column=3, columnspan=3, sticky="we", padx=(6,0))

        ttk.Button(frame, text="Сброс сцены", command=self.reset_scene).grid(row=10, column=0, columnspan=2, sticky="we", padx=4, pady=(10,6))

    def change_poly(self, which):
        obj = self.objA if which == "A" else self.objB
        name = getattr(self, f"poly_var_{which}").get()
        if name == "Тетраэдр": new = make_tetrahedron(obj.color)
        elif name == "Куб": new = make_cube(obj.color)
        elif name == "Октаэдр": new = make_octahedron(obj.color)
        elif name == "Икосаэдр": new = make_icosahedron(obj.color)
        elif name == "Додекаэдр": new = make_dodecahedron(obj.color)
        else: new = make_cube(obj.color)
        new.name = name
        if which == "A": self.objA = new
        else: self.objB = new
        self.fit_in_view(); self.draw()

    def toggle_objB(self):
        self.objB_enabled = self.objB_on_var.get()
        self.fit_in_view(); self.draw()

    def change_projection(self, _=None):
        self.projection_mode = "perspective" if self.proj_var.get() == "Перспективная" else "isometric"
        self.draw()

    def apply_look_vec(self):
        try:
            lx = float(self.lx_e.get()); ly = float(self.ly_e.get()); lz = float(self.lz_e.get())
        except ValueError:
            messagebox.showerror("Ошибка ввода", "lx, ly, lz должны быть числами"); return
        v = np.array([lx, ly, lz], dtype=float)
        n = np.linalg.norm(v)
        if n == 0:
            messagebox.showerror("Ошибка ввода", "Вектор обзора не должен быть нулевым"); return
        self.look_vec = v / n
        self.draw()

    def toggle_cull(self):
        self.cull_enabled = self.cull_var.get(); self.draw()

    def toggle_zbuf(self):
        self.zbuffer_enabled = self.zbuf_var.get(); self.draw()

    def toggle_anim(self):
        self.anim_enabled = self.anim_var.get()

    def toggle_overlay_wire(self):
        self.overlay_wire_enabled = self.overlay_wire_var.get()
        self.draw()

    def change_overlay_mode(self, *_):
        self.overlay_wire_front_only = (self.overlay_wire_mode.get() == "Только фронт")
        self.draw()

    def change_quality(self, *_):
        q = self.quality_var.get()
        if q == "100%": self.render_scale = 1.0
        elif q == "50%": self.render_scale = 0.5
        elif q == "33%": self.render_scale = 1.0/3.0
        elif q == "25%": self.render_scale = 0.25
        else: self.render_scale = 1.0
        self.draw()

    def fit_in_view(self):
        c = self.objA.center()
        T = matrix_translate(-c[0], -c[1], -c[2])
        self.objA.apply_matrix(T)
        if self.objB_enabled:
            self.objB.apply_matrix(T)

    def reset_object(self, which):
        if which == "A":
            self.objA = make_cube("#5a9bd8")
            self.poly_var_A.set("Куб")
        else:
            self.objB = make_cube("#e4a84b")
            self.poly_var_B.set("Куб")
        self.fit_in_view(); self.draw()

    def reset_scene(self):
        self.proj_var.set("Перспективная"); self.change_projection()
        self.scale = 180.0; self.camera_distance = 5.0
        self.look_vec = np.array([0.0, 0.0, -1.0])
        self.lx_e.delete(0, tk.END); self.lx_e.insert(0, "0")
        self.ly_e.delete(0, tk.END); self.ly_e.insert(0, "0")
        self.lz_e.delete(0, tk.END); self.lz_e.insert(0, "-1")
        self.cull_var.set(False); self.cull_enabled = False
        self.zbuf_var.set(False); self.zbuffer_enabled = False
        self.overlay_wire_var.set(True); self.overlay_wire_enabled = True
        self.overlay_wire_mode.set("Только фронт"); self.overlay_wire_front_only = True
        self.quality_var.set("100%"); self.render_scale = 1.0
        self.anim_var.set(True); self.anim_enabled = True
        self.objB_on_var.set(False); self.objB_enabled = False
        self.objA = make_cube("#5a9bd8")
        self.objB = make_cube("#e4a84b")
        self.fit_in_view(); self.draw()

    def _get_obj(self, which): return self.objA if which == "A" else self.objB

    def apply_translate_obj(self, which, tx_e, ty_e, tz_e):
        try:
            tx = float(tx_e.get()); ty = float(ty_e.get()); tz = float(tz_e.get())
        except ValueError:
            messagebox.showerror("Ошибка ввода", "tx, ty, tz должны быть числами"); return
        M = matrix_translate(tx, ty, tz)
        self._get_obj(which).apply_matrix(M); self.draw()

    def apply_scale_obj(self, which, sx_e, sy_e, sz_e):
        try:
            sx = float(sx_e.get()); sy = float(sy_e.get()); sz = float(sz_e.get())
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Коэффициенты масштаба должны быть числами"); return
        M = matrix_scale(sx, sy, sz)
        self._get_obj(which).apply_matrix(M); self.draw()

    def apply_rotation_obj(self, which, ax_e, ay_e, az_e):
        try:
            ax = math.radians(float(ax_e.get())); ay = math.radians(float(ay_e.get())); az = math.radians(float(az_e.get()))
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Углы поворота должны быть числами"); return
        M = matrix_rotate_z(az) @ matrix_rotate_y(ay) @ matrix_rotate_x(ax)
        self._get_obj(which).apply_matrix(M); self.draw()

    def apply_scale_about_center_obj(self, which, k_e):
        try:
            k = float(k_e.get())
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Коэффициент должен быть числом"); return
        obj = self._get_obj(which); c = obj.center()
        M = matrix_translate(-c[0], -c[1], -c[2]) @ matrix_scale(k, k, k) @ matrix_translate(c[0], c[1], c[2])
        obj.apply_matrix(M); self.draw()

    def apply_rotate_around_center_obj(self, which, axis_var, ang_e):
        try:
            angle = math.radians(float(ang_e.get()))
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Угол должен быть числом"); return
        axis = axis_var.get()
        obj = self._get_obj(which); c = obj.center()
        M = matrix_rotate_axis_through_point(axis, angle, c)
        obj.apply_matrix(M); self.draw()

    def each_obj(self):
        yield self.objA
        if self.objB_enabled: yield self.objB

    def apply_translate_scene(self):
        try:
            tx = float(self.tx.get()); ty = float(self.ty.get()); tz = float(self.tz.get())
        except ValueError:
            messagebox.showerror("Ошибка ввода", "tx, ty, tz должны быть числами"); return
        M = matrix_translate(tx, ty, tz)
        for o in self.each_obj(): o.apply_matrix(M)
        self.draw()

    def apply_scale_scene(self):
        try:
            sx = float(self.sx.get()); sy = float(self.sy.get()); sz = float(self.sz.get())
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Коэффициенты масштаба должны быть числами"); return
        M = matrix_scale(sx, sy, sz)
        for o in self.each_obj(): o.apply_matrix(M)
        self.draw()

    def apply_rotation_scene(self):
        try:
            ax = math.radians(float(self.ax.get())); ay = math.radians(float(self.ay.get())); az = math.radians(float(self.az.get()))
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Углы поворота должны быть числами"); return
        M = matrix_rotate_z(az) @ matrix_rotate_y(ay) @ matrix_rotate_x(ax)
        for o in self.each_obj(): o.apply_matrix(M)
        self.draw()

    def apply_reflect_scene(self):
        M = matrix_reflect_plane(self.plane_var.get())
        for o in self.each_obj(): o.apply_matrix(M)
        self.draw()

    def apply_scale_about_center_scene(self):
        try:
            f = float(self.factor_e.get())
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Коэффициент должен быть числом"); return
        allV = np.vstack([o.V for o in self.each_obj()])
        c = np.mean(allV, axis=0)
        M = matrix_translate(-c[0], -c[1], -c[2]) @ matrix_scale(f, f, f) @ matrix_translate(c[0], c[1], c[2])
        for o in self.each_obj(): o.apply_matrix(M)
        self.draw()

    def apply_rotate_around_center_scene(self):
        try:
            angle = math.radians(float(self.angle_axis_e.get()))
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Угол должен быть числом"); return
        allV = np.vstack([o.V for o in self.each_obj()]); c = np.mean(allV, axis=0)
        axis = self.axis_var.get()
        M = matrix_rotate_axis_through_point(axis, angle, c)
        for o in self.each_obj(): o.apply_matrix(M)
        self.draw()

    def load_obj_dialog(self, which):
        path = filedialog.askopenfilename(title="Открыть OBJ", filetypes=[("Wavefront OBJ", "*.obj"), ("Все файлы", "*.*")])
        if not path: return
        try:
            poly = self.load_obj(path)
        except Exception as e:
            messagebox.showerror("Ошибка загрузки", str(e)); return
        if which == "A":
            poly.color = self.objA.color
            self.objA = poly
        else:
            poly.color = self.objB.color
            self.objB = poly
        self.fit_in_view(); self.draw()

    def save_obj_dialog(self, which):
        path = filedialog.asksaveasfilename(defaultextension=".obj", filetypes=[("Wavefront OBJ", "*.obj"), ("Все файлы", "*.*")], title="Сохранить OBJ")
        if not path: return
        try:
            self.save_obj(path, self._get_obj(which))
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", str(e))

    def load_obj(self, path):
        verts = []; faces = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith("#"): continue
                parts = s.split(); tag = parts[0].lower()
                if tag == "v" and len(parts) >= 4:
                    x = float(parts[1]); y = float(parts[2]); z = float(parts[3])
                    verts.append([x, y, z])
                elif tag == "f" and len(parts) >= 4:
                    idxs = []
                    for tok in parts[1:]:
                        if "/" in tok: tok = tok.split("/")[0]
                        if tok == "" or tok == "0": continue
                        i = int(tok)
                        if i < 0: i = len(verts) + 1 + i
                        idxs.append(i - 1)
                    if len(idxs) >= 3: faces.append(idxs)
        if len(verts) == 0 or len(faces) == 0:
            raise ValueError("Пустая модель или отсутствуют грани")
        return Polyhedron(np.array(verts, dtype=float), faces)

    def save_obj(self, path, poly: Polyhedron):
        with open(path, "w", encoding="utf-8") as f:
            for v in poly.V:
                f.write(f"v {v[0]} {v[1]} {v[2]}\n")
            for face in poly.faces:
                idxs = [str(i + 1) for i in face.indices]
                f.write("f " + " ".join(idxs) + "\n")

    def classify_faces_perspective(self, V_world, faces):
        cam_pos = np.array([0.0, 0.0, self.camera_distance])
        obj_center = np.mean(V_world, axis=0)
        front, back = [], []
        for f in faces:
            idx = np.array(f.indices)
            centroid = np.mean(V_world[idx], axis=0)
            n = compute_face_normal_outward(V_world, f.indices, obj_center)
            if np.allclose(n, 0.0): continue
            view_vec = cam_pos - centroid
            if np.dot(n, view_vec) > 0: front.append(f)
            else: back.append(f)
        return front, back

    def classify_faces_isometric(self, V_iso, faces):
        obj_center_iso = np.mean(V_iso, axis=0)
        front, back = [], []
        for f in faces:
            n = compute_face_normal_outward(V_iso, f.indices, obj_center_iso)
            if np.allclose(n, 0.0): continue
            if np.dot(n, self.look_vec) < 0: front.append(f)
            else: back.append(f)
        return front, back

    def _draw_face_wire(self, V3, face, mode, outline, width):
        if mode == 'persp': pts2 = project_perspective(V3, camera_distance=self.camera_distance)
        else: pts2 = project_orthographic(V3)
        coords = []
        for idx in face.indices:
            x, y = pts2[idx]
            coords.extend([float(x * self.scale + self.offset[0]), float(y * self.scale + self.offset[1])])
        self.canvas.create_polygon(coords, fill="", outline=outline, width=width)

    def render_zbuffer(self):
        Wc, Hc = self.canvas_w, self.canvas_h
        s = self.render_scale
        Wr = max(1, int(Wc * s))
        Hr = max(1, int(Hc * s))

        zbuf = np.full((Hr, Wr), np.inf, dtype=float)
        rgb = np.zeros((Hr, Wr, 3), dtype=np.uint8)
        d = self.camera_distance

        scale_r = self.scale * s
        offset_r = np.array([Wr / 2.0, Hr / 2.0], dtype=float)

        def to_screen(pts2):
            sx = (pts2[:,0] * scale_r + offset_r[0]).astype(np.float32)
            sy = (pts2[:,1] * scale_r + offset_r[1]).astype(np.float32)
            return sx, sy

        def tri_rasterize(sx, sy, zdepth, color):
            minx = max(int(np.floor(min(sx))), 0); maxx = min(int(np.ceil(max(sx))), Wr-1)
            miny = max(int(np.floor(min(sy))), 0); maxy = min(int(np.ceil(max(sy))), Hr-1)
            if minx>maxx or miny>maxy: return
            x1, y1, z1 = sx[0], sy[0], zdepth[0]
            x2, y2, z2 = sx[1], sy[1], zdepth[1]
            x3, y3, z3 = sx[2], sy[2], zdepth[2]
            denom = ( (y2 - y3)*(x1 - x3) + (x3 - x2)*(y1 - y3) )
            if abs(denom) < 1e-8: return
            A1 = (y2 - y3); B1 = (x3 - x2)
            A2 = (y3 - y1); B2 = (x1 - x3)
            Cx = x3; Cy = y3
            for y in range(miny, maxy+1):
                py = y + 0.5
                for x in range(minx, maxx+1):
                    px = x + 0.5
                    w1 = (A1*(px - Cx) + B1*(py - Cy)) / denom
                    w2 = (A2*(px - Cx) + B2*(py - Cy)) / denom
                    w3 = 1.0 - w1 - w2
                    if w1 < 0 or w2 < 0 or w3 < 0: continue
                    z = w1*z1 + w2*z2 + w3*z3
                    if z < zbuf[y, x]:
                        zbuf[y, x] = z
                        rgb[y, x] = color

        def obj_color_tuple(col):
            if isinstance(col, str) and col.startswith("#") and len(col) == 7:
                return (int(col[1:3],16), int(col[3:5],16), int(col[5:7],16))
            return (90,155,216)

        objs = [self.objA] + ([self.objB] if self.objB_enabled else [])

        for obj in objs:
            V = obj.V.copy()
            if self.projection_mode == 'perspective':
                pts2 = project_perspective(V, camera_distance=d)
                depth = (d - V[:,2])
            else:
                R = isometric_rotation_matrix()
                V = (R @ V.T).T
                pts2 = project_orthographic(V)
                depth = (-V[:,2])

            sx_all, sy_all = to_screen(pts2)
            color = np.array(obj_color_tuple(obj.color), dtype=np.uint8)

            for f in obj.faces:
                idx = f.indices
                if len(idx) < 3: continue
                i0 = idx[0]
                for t in range(1, len(idx)-1):
                    i1 = idx[t]; i2 = idx[t+1]
                    sx = np.array([sx_all[i0], sx_all[i1], sx_all[i2]], dtype=np.float32)
                    sy = np.array([sy_all[i0], sy_all[i1], sy_all[i2]], dtype=np.float32)
                    zdepth = np.array([depth[i0], depth[i1], depth[i2]], dtype=np.float32)
                    tri_rasterize(sx, sy, zdepth, color)

        header = f"P6 {Wr} {Hr} 255\n".encode("ascii")
        data = rgb.tobytes()
        ppm = header + data
        img_small = tk.PhotoImage(data=ppm, format="PPM")

        if s == 1.0:
            return img_small
        zoom = int(round(1.0 / s))
        img_zoom = img_small.zoom(zoom, zoom)
        return img_zoom

    def draw(self):
        self.canvas.delete("all")

        if self.zbuffer_enabled:
            self.img_handle = self.render_zbuffer()
            self.canvas.create_image(0, 0, image=self.img_handle, anchor="nw")

            if self.overlay_wire_enabled:
                objs = [self.objA] + ([self.objB] if self.objB_enabled else [])
                if self.projection_mode == 'perspective':
                    for obj in objs:
                        V = obj.V.copy()
                        if self.overlay_wire_front_only:
                            front, _ = self.classify_faces_perspective(V, obj.faces)
                            faces_to_draw = front
                        else:
                            faces_to_draw = obj.faces
                        for f in faces_to_draw:
                            self._draw_face_wire(V, f, mode='persp', outline=self.wire_on_fill_color, width=self.wire_on_fill_width)
                else:
                    R = isometric_rotation_matrix()
                    for obj in objs:
                        V = (R @ obj.V.T).T
                        if self.overlay_wire_front_only:
                            front, _ = self.classify_faces_isometric(V, obj.faces)
                            faces_to_draw = front
                        else:
                            faces_to_draw = obj.faces
                        for f in faces_to_draw:
                            self._draw_face_wire(V, f, mode='ortho', outline=self.wire_on_fill_color, width=self.wire_on_fill_width)
            return

        objs = [self.objA] + ([self.objB] if self.objB_enabled else [])

        if self.projection_mode == 'perspective':
            for obj in objs:
                V = obj.V.copy()
                front, back = self.classify_faces_perspective(V, obj.faces)
                def depth_key(f): return np.mean(V[np.array(f.indices), 2])
                if not self.cull_enabled:
                    for f in sorted(back, key=depth_key, reverse=True):
                        self._draw_face_wire(V, f, mode='persp', outline=self.back_outline,  width=1)
                    for f in sorted(front, key=depth_key, reverse=True):
                        self._draw_face_wire(V, f, mode='persp', outline=self.front_outline, width=2)
                else:
                    for f in sorted(front, key=depth_key, reverse=True):
                        self._draw_face_wire(V, f, mode='persp', outline=self.front_outline, width=2)
        else:
            R = isometric_rotation_matrix()
            for obj in objs:
                V = (R @ obj.V.T).T
                front, back = self.classify_faces_isometric(V, obj.faces)
                def depth_key(f): return np.mean(V[np.array(f.indices), 2])
                if not self.cull_enabled:
                    for f in sorted(back, key=depth_key, reverse=True):
                        self._draw_face_wire(V, f, mode='ortho', outline=self.back_outline,  width=1)
                    for f in sorted(front, key=depth_key, reverse=True):
                        self._draw_face_wire(V, f, mode='ortho', outline=self.front_outline, width=2)
                else:
                    for f in sorted(front, key=depth_key, reverse=True):
                        self._draw_face_wire(V, f, mode='ortho', outline=self.front_outline, width=2)

    def tick(self):
        if self.anim_enabled:
            objs = [self.objA] + ([self.objB] if self.objB_enabled else [])
            if objs:
                allV = np.vstack([o.V for o in objs])
                c = np.mean(allV, axis=0)
                M = matrix_translate(-c[0], -c[1], -c[2]) @ matrix_rotate_y(math.radians(2.0)) @ matrix_translate(c[0], c[1], c[2])
                for o in objs: o.apply_matrix(M)
                self.draw()
        self.root.after(33, self.tick)

def main():
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use('clam')
    except Exception:
        pass
    app = PolyhedronApp(root)
    root.minsize(1220, 740)
    root.mainloop()

if __name__ == "__main__":
    main()
