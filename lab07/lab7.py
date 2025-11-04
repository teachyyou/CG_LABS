import math
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class Face:
    def __init__(self, indices):
        self.indices = list(indices)

class Polyhedron:
    def __init__(self, vertices: np.ndarray, faces: list):
        self.V = np.array(vertices, dtype=float)
        self.faces = [Face(f) for f in faces]
    def copy(self):
        return Polyhedron(self.V.copy(), [f.indices[:] for f in self.faces])
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
    M[0, 3] = tx
    M[1, 3] = ty
    M[2, 3] = tz
    return M

def matrix_scale(sx, sy, sz):
    M = np.eye(4)
    M[0, 0] = sx
    M[1, 1] = sy
    M[2, 2] = sz
    return M

def matrix_rotate_x(angle_rad):
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    M = np.eye(4)
    M[1, 1] = c
    M[1, 2] = -s
    M[2, 1] = s
    M[2, 2] = c
    return M

def matrix_rotate_y(angle_rad):
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    M = np.eye(4)
    M[0, 0] = c
    M[0, 2] = s
    M[2, 0] = -s
    M[2, 2] = c
    return M

def matrix_rotate_z(angle_rad):
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    M = np.eye(4)
    M[0, 0] = c
    M[0, 1] = -s
    M[1, 0] = s
    M[1, 1] = c
    return M

def matrix_reflect_plane(plane):
    if plane == 'xy':
        return matrix_scale(1, 1, -1)
    if plane == 'yz':
        return matrix_scale(-1, 1, 1)
    if plane == 'xz':
        return matrix_scale(1, -1, 1)

def rotation_matrix_axis_angle(axis, angle_rad):
    axis = np.array(axis, dtype=float)
    norm = np.linalg.norm(axis)
    if norm == 0:
        return np.eye(4)
    x, y, z = axis / norm
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    C = 1 - c
    R3 = np.array([
        [x * x * C + c,     x * y * C - z * s, x * z * C + y * s],
        [y * x * C + z * s, y * y * C + c,     y * z * C - x * s],
        [z * x * C - y * s, z * y * C + x * s, z * z * C + c    ]
    ])
    M = np.eye(4)
    M[:3, :3] = R3
    return M

def matrix_rotate_about_line(p1, p2, angle_rad):
    p1 = np.array(p1, dtype=float)
    axis = np.array(p2, dtype=float) - p1
    R = rotation_matrix_axis_angle(axis, angle_rad)
    T1 = matrix_translate(-p1[0], -p1[1], -p1[2])
    T2 = matrix_translate(p1[0], p1[1], p1[2])
    return T2 @ R @ T1

def matrix_rotate_axis_through_point(axis_letter, angle_rad, point):
    axis_letter = axis_letter.lower()
    T1 = matrix_translate(-point[0], -point[1], -point[2])
    if axis_letter == 'x':
        R = matrix_rotate_x(angle_rad)
    elif axis_letter == 'y':
        R = matrix_rotate_y(angle_rad)
    elif axis_letter == 'z':
        R = matrix_rotate_z(angle_rad)
    T2 = matrix_translate(point[0], point[1], point[2])
    return T2 @ R @ T1

def project_perspective(points3, camera_distance=5.0):
    pts = np.array(points3, dtype=float)
    z = pts[:, 2]
    d = camera_distance
    denom = (d - z)
    denom[denom == 0] = 1e-6
    factor = d / denom
    x2 = pts[:, 0] * factor
    y2 = pts[:, 1] * factor
    return np.vstack([x2, y2]).T

def project_orthographic(points3):
    return points3[:, :2]

def isometric_rotation_matrix():
    alpha = math.radians(35.2643897)
    beta = math.radians(45.0)
    Rx = matrix_rotate_x(alpha)
    Rz = matrix_rotate_z(beta)
    return (Rz @ Rx)[:3, :3]

def make_tetrahedron():
    verts = np.array([
        [1, 1, 1],
        [1, -1, -1],
        [-1, 1, -1],
        [-1, -1, 1]
    ], dtype=float)
    verts = verts / np.linalg.norm(verts[0])
    faces = [[0, 1, 2], [0, 3, 1], [0, 2, 3], [1, 3, 2]]
    return Polyhedron(verts, faces)

def make_cube():
    s = 1.0
    verts = np.array([[x, y, z] for x in (-s, s) for y in (-s, s) for z in (-s, s)], dtype=float)
    faces = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 2, 6, 4], [1, 5, 7, 3], [0, 4, 5, 1], [2, 3, 7, 6]]
    return Polyhedron(verts, faces)

def make_octahedron():
    verts = np.array([
        [ 1, 0, 0], [-1, 0, 0],
        [ 0, 1, 0], [ 0,-1, 0],
        [ 0, 0, 1], [ 0, 0,-1]
    ], dtype=float)
    faces = [[0, 2, 4], [2, 1, 4], [1, 3, 4], [3, 0, 4], [2, 0, 5], [1, 2, 5], [3, 1, 5], [0, 3, 5]]
    return Polyhedron(verts, faces)

def make_icosahedron():
    t = (1.0 + math.sqrt(5.0)) / 2.0
    verts = np.array([
        [-1,  t, 0], [ 1,  t, 0], [-1, -t, 0], [ 1, -t, 0],
        [ 0, -1, t], [ 0,  1, t], [ 0, -1,-t], [ 0,  1,-t],
        [ t,  0,-1], [ t,  0, 1], [-t,  0,-1], [-t,  0, 1]
    ], dtype=float)
    verts /= np.max(np.linalg.norm(verts, axis=1))
    faces = [
        [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
        [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
        [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
    ]
    return Polyhedron(verts, faces)

def make_dodecahedron():
    ico = make_icosahedron()
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
        x_axis = np.cross(ref, n)
        x_axis /= np.linalg.norm(x_axis)
        y_axis = np.cross(n, x_axis)
        cen = np.mean(pts, axis=0)
        local = pts - cen
        angs = [math.atan2(np.dot(p, y_axis), np.dot(p, x_axis)) for p in local]
        incident_sorted = [i for _, i in sorted(zip(angs, incident))]
        dfaces.append(incident_sorted)
    centers /= np.max(np.linalg.norm(centers, axis=1))
    return Polyhedron(centers, dfaces)

def build_revolution(points, axis_letter, segments):
    axis_letter = axis_letter.lower()
    points = np.array(points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3 or len(points) < 2:
        raise ValueError("Нужны как минимум две 3D точки")
    if segments < 3:
        raise ValueError("Количество разбиений ≥ 3")
    if axis_letter == 'x':
        Rf = matrix_rotate_x
    elif axis_letter == 'y':
        Rf = matrix_rotate_y
    elif axis_letter == 'z':
        Rf = matrix_rotate_z
    else:
        raise ValueError("Ось должна быть x, y или z")
    verts = []
    for k in range(segments):
        ang = 2 * math.pi * k / segments
        R = Rf(ang)
        P = np.hstack([points, np.ones((points.shape[0], 1))])
        Pr = (R @ P.T).T[:, :3]
        verts.append(Pr)
    V = np.vstack(verts)
    faces = []
    m = points.shape[0]
    for k in range(segments):
        kn = (k + 1) % segments
        for i in range(m - 1):
            a = k * m + i
            b = k * m + i + 1
            c = kn * m + i + 1
            d = kn * m + i
            faces.append([a, b, c, d])
    return Polyhedron(V, faces)

def build_surface(func_name, x0, x1, y0, y1, nx, ny):
    if nx < 1 or ny < 1:
        raise ValueError("Число разбиений по X и Y должно быть ≥ 1")
    xs = np.linspace(x0, x1, nx + 1)
    ys = np.linspace(y0, y1, ny + 1)
    X, Y = np.meshgrid(xs, ys, indexing="xy")
    if func_name == "sinc":
        R = np.sqrt(X**2 + Y**2)
        Z = np.sinc(R/np.pi)
    elif func_name == "сфера-кусок":
        R2 = X**2 + Y**2
        Z = np.sqrt(np.maximum(0.0, 1.0 - R2))
    elif func_name == "седло":
        Z = X**2 - Y**2
    elif func_name == "параболоид":
        Z = X**2 + Y**2
    elif func_name == "волны":
        Z = np.sin(X) * np.cos(Y)
    else:
        raise ValueError("Неизвестная функция")
    V = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
    faces = []
    nxv = nx + 1
    for j in range(ny):
        for i in range(nx):
            a = j * nxv + i
            b = j * nxv + i + 1
            c = (j + 1) * nxv + i + 1
            d = (j + 1) * nxv + i
            faces.append([a, b, c, d])
    return Polyhedron(V, faces)

class PolyhedronApp:
    def __init__(self, root):
        self.root = root
        root.title("Лабораторная 7")
        self.canvas_w = 720
        self.canvas_h = 720
        self.poly = make_tetrahedron()
        self.projection_mode = 'perspective'
        self.camera_distance = 5.0
        self.scale = 180.0
        self.offset = np.array([self.canvas_w / 2, self.canvas_h / 2])
        self.bg_color = "#1e1e1e"
        self.face_fill = "#5a9bd8"
        self.edge_color = "#e6e6e6"
        main = ttk.Frame(root)
        main.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(
            main,
            width=self.canvas_w,
            height=self.canvas_h,
            bg=self.bg_color,
            highlightthickness=0
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ctrl = ttk.Frame(main, width=420)
        ctrl.pack(side=tk.RIGHT, fill=tk.Y, padx=6, pady=6)
        self.nb = ttk.Notebook(ctrl)
        self.nb.pack(fill=tk.BOTH, expand=True)

        tab_model = ttk.Frame(self.nb)
        self.nb.add(tab_model, text="Фигура")
        ttk.Label(tab_model, text="Многогранник:").grid(row=0, column=0, sticky="w", padx=4, pady=(6, 2))
        self.poly_var = tk.StringVar(value="Тетраэдр")
        poly_menu = ttk.OptionMenu(
            tab_model, self.poly_var, "Тетраэдр",
            "Тетраэдр", "Куб", "Октаэдр", "Икосаэдр", "Додекаэдр",
            command=self.change_poly
        )
        poly_menu.grid(row=0, column=1, sticky="we", padx=4, pady=(6, 2))
        ttk.Label(tab_model, text="Проекция:").grid(row=1, column=0, sticky="w", padx=4, pady=2)
        self.proj_var = tk.StringVar(value="Перспективная")
        proj_menu = ttk.OptionMenu(
            tab_model, self.proj_var, "Перспективная",
            "Перспективная", "Изометрическая",
            command=self.change_projection
        )
        proj_menu.grid(row=1, column=1, sticky="we", padx=4, pady=2)
        btnfrm = ttk.Frame(tab_model)
        btnfrm.grid(row=2, column=0, columnspan=2, sticky="we", padx=4, pady=(10,2))
        btnfrm.columnconfigure(0, weight=1)
        btnfrm.columnconfigure(1, weight=1)
        ttk.Button(btnfrm, text="Загрузить OBJ", command=self.load_obj_dialog).grid(row=0, column=0, sticky="we", padx=(0,2))
        ttk.Button(btnfrm, text="Сохранить OBJ", command=self.save_obj_dialog).grid(row=0, column=1, sticky="we", padx=(2,0))
        tab_model.columnconfigure(1, weight=1)

        tab_tr = ttk.Frame(self.nb)
        self.nb.add(tab_tr, text="Преобразования")
        tab_tr.columnconfigure(0, weight=1, uniform="cols")
        tab_tr.columnconfigure(1, weight=1, uniform="cols")

        left = ttk.Frame(tab_tr)
        left.grid(row=0, column=0, sticky="nsew", padx=(4, 2), pady=4)
        ttk.Label(left, text="Смещение tx ty tz").grid(row=0, column=0, columnspan=3, sticky="w")
        self.tx = ttk.Entry(left, width=7)
        self.ty = ttk.Entry(left, width=7)
        self.tz = ttk.Entry(left, width=7)
        self.tx.insert(0, "0")
        self.ty.insert(0, "0")
        self.tz.insert(0, "0")
        self.tx.grid(row=1, column=0, pady=1)
        self.ty.grid(row=1, column=1, pady=1)
        self.tz.grid(row=1, column=2, pady=1)
        ttk.Button(left, text="Применить", command=self.apply_translate).grid(
            row=2, column=0, columnspan=3, sticky="we", pady=(2, 6)
        )
        ttk.Label(left, text="Масштаб sx sy sz").grid(row=3, column=0, columnspan=3, sticky="w")
        self.sx = ttk.Entry(left, width=7)
        self.sy = ttk.Entry(left, width=7)
        self.sz = ttk.Entry(left, width=7)
        self.sx.insert(0, "1")
        self.sy.insert(0, "1")
        self.sz.insert(0, "1")
        self.sx.grid(row=4, column=0, pady=1)
        self.sy.grid(row=4, column=1, pady=1)
        self.sz.grid(row=4, column=2, pady=1)
        ttk.Button(left, text="Применить", command=self.apply_scale).grid(
            row=5, column=0, columnspan=3, sticky="we", pady=(2, 6)
        )
        ttk.Label(left, text="Поворот (град) ax ay az").grid(row=6, column=0, columnspan=3, sticky="w")
        self.ax = ttk.Entry(left, width=7)
        self.ay = ttk.Entry(left, width=7)
        self.az = ttk.Entry(left, width=7)
        self.ax.insert(0, "0")
        self.ay.insert(0, "0")
        self.az.insert(0, "0")
        self.ax.grid(row=7, column=0, pady=1)
        self.ay.grid(row=7, column=1, pady=1)
        self.az.grid(row=7, column=2, pady=1)
        ttk.Button(left, text="Применить", command=self.apply_rotation).grid(
            row=8, column=0, columnspan=3, sticky="we", pady=(2, 6)
        )
        ttk.Label(left, text="Отражение в плоскости:").grid(row=9, column=0, columnspan=3, sticky="w")
        self.plane_var = tk.StringVar(value="xy")
        ttk.OptionMenu(left, self.plane_var, "xy", "xy", "yz", "xz").grid(
            row=10, column=0, columnspan=2, sticky="we", pady=1
        )
        ttk.Button(left, text="Отразить", command=self.apply_reflect).grid(row=10, column=2, sticky="we", pady=1)

        right = ttk.Frame(tab_tr)
        right.grid(row=0, column=1, sticky="nsew", padx=(2, 4), pady=4)
        ttk.Label(right, text="Масштаб от центра (k):").grid(row=0, column=0, columnspan=2, sticky="w")
        self.factor_e = ttk.Entry(right, width=10)
        self.factor_e.insert(0, "1")
        self.factor_e.grid(row=1, column=0, sticky="we", pady=1)
        ttk.Button(right, text="Применить", command=self.apply_scale_about_center).grid(row=1, column=1, sticky="we", pady=1)
        ttk.Label(right, text="Вращение вокруг оси через центр:").grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self.axis_var = tk.StringVar(value="x")
        ttk.OptionMenu(right, self.axis_var, "x", "x", "y", "z").grid(row=3, column=0, sticky="we", pady=1)
        self.angle_axis_e = ttk.Entry(right, width=10)
        self.angle_axis_e.insert(0, "0")
        self.angle_axis_e.grid(row=3, column=1, sticky="we", pady=1)
        ttk.Button(right, text="Повернуть", command=self.apply_rotate_around_center_parallel).grid(
            row=4, column=0, columnspan=2, sticky="we", pady=(2, 6)
        )
        ttk.Label(right, text="Вращение вокруг прямой p1→p2:").grid(row=5, column=0, columnspan=2, sticky="w")
        linefrm = ttk.Frame(right)
        linefrm.grid(row=6, column=0, columnspan=2, sticky="we", pady=2)
        for i in range(4):
            linefrm.columnconfigure(i, weight=1)
        self.p1x = ttk.Entry(linefrm, width=6)
        self.p1y = ttk.Entry(linefrm, width=6)
        self.p1z = ttk.Entry(linefrm, width=6)
        self.p2x = ttk.Entry(linefrm, width=6)
        self.p2y = ttk.Entry(linefrm, width=6)
        self.p2z = ttk.Entry(linefrm, width=6)
        self.p1x.insert(0, "0")
        self.p1y.insert(0, "0")
        self.p1z.insert(0, "0")
        self.p2x.insert(0, "1")
        self.p2y.insert(0, "0")
        self.p2z.insert(0, "0")
        ttk.Label(linefrm, text="p1:").grid(row=0, column=0, sticky="e")
        self.p1x.grid(row=0, column=1)
        self.p1y.grid(row=0, column=2)
        self.p1z.grid(row=0, column=3)
        ttk.Label(linefrm, text="p2:").grid(row=1, column=0, sticky="e")
        self.p2x.grid(row=1, column=1)
        self.p2y.grid(row=1, column=2)
        self.p2z.grid(row=1, column=3)
        ttk.Label(right, text="Угол (°):").grid(row=7, column=0, sticky="w")
        self.angle_line_e = ttk.Entry(right)
        self.angle_line_e.insert(0, "0")
        self.angle_line_e.grid(row=7, column=1, sticky="we", pady=1)
        ttk.Button(right, text="Повернуть вокруг прямой", command=self.apply_rotate_about_line).grid(
            row=8, column=0, columnspan=2, sticky="we", pady=(2, 6)
        )
        ttk.Button(right, text="Сброс и подгонка", command=self.reset).grid(
            row=9, column=0, columnspan=2, sticky="we", pady=(10, 0)
        )

        tab_rev = ttk.Frame(self.nb)
        self.nb.add(tab_rev, text="Фигура вращения")
        tab_rev.columnconfigure(0, weight=1)
        tab_rev.columnconfigure(1, weight=1)
        ttk.Label(tab_rev, text="Образующая (x y z по строке):").grid(row=0, column=0, columnspan=2, sticky="w", padx=4, pady=(6,2))
        self.gen_text = tk.Text(tab_rev, height=10, width=40)
        self.gen_text.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=4)
        sample = "\n".join(["0 0 -1","0 0 1","0.5 0 1","0.5 0 -1","0 0 -1"])
        self.gen_text.delete("1.0", tk.END)
        self.gen_text.insert("1.0", sample)
        ttk.Label(tab_rev, text="Ось:").grid(row=2, column=0, sticky="w", padx=4, pady=(6,2))
        self.rev_axis_var = tk.StringVar(value="z")
        ttk.OptionMenu(tab_rev, self.rev_axis_var, "z", "x", "y", "z").grid(row=2, column=1, sticky="we", padx=4, pady=(6,2))
        ttk.Label(tab_rev, text="Разбиений (≥3):").grid(row=3, column=0, sticky="w", padx=4, pady=2)
        self.rev_segments_e = ttk.Entry(tab_rev)
        self.rev_segments_e.insert(0, "24")
        self.rev_segments_e.grid(row=3, column=1, sticky="we", padx=4, pady=2)
        actfrm = ttk.Frame(tab_rev)
        actfrm.grid(row=4, column=0, columnspan=2, sticky="we", padx=4, pady=(6,4))
        actfrm.columnconfigure(0, weight=1)
        actfrm.columnconfigure(1, weight=1)
        ttk.Button(actfrm, text="Построить", command=self.build_revolution_ui).grid(row=0, column=0, sticky="we", padx=(0,2))
        ttk.Button(actfrm, text="Сохранить OBJ", command=self.save_obj_dialog).grid(row=0, column=1, sticky="we", padx=(2,0))

        tab_surf = ttk.Frame(self.nb)
        self.nb.add(tab_surf, text="Поверхность f(x,y)")
        for i in range(2):
            tab_surf.columnconfigure(i, weight=1)
        ttk.Label(tab_surf, text="Функция:").grid(row=0, column=0, sticky="w", padx=4, pady=(6,2))
        self.func_var = tk.StringVar(value="волны")
        ttk.OptionMenu(tab_surf, self.func_var, "волны", "волны", "sinc", "сфера-кусок", "седло", "параболоид").grid(row=0, column=1, sticky="we", padx=4, pady=(6,2))
        rngfrm = ttk.Frame(tab_surf)
        rngfrm.grid(row=1, column=0, columnspan=2, sticky="we", padx=4, pady=2)
        for i in range(4):
            rngfrm.columnconfigure(i, weight=1)
        ttk.Label(rngfrm, text="x0").grid(row=0, column=0, sticky="we")
        ttk.Label(rngfrm, text="x1").grid(row=0, column=1, sticky="we")
        ttk.Label(rngfrm, text="y0").grid(row=0, column=2, sticky="we")
        ttk.Label(rngfrm, text="y1").grid(row=0, column=3, sticky="we")
        self.x0e = ttk.Entry(rngfrm); self.x1e = ttk.Entry(rngfrm); self.y0e = ttk.Entry(rngfrm); self.y1e = ttk.Entry(rngfrm)
        self.x0e.insert(0, "-3"); self.x1e.insert(0, "3"); self.y0e.insert(0, "-3"); self.y1e.insert(0, "3")
        self.x0e.grid(row=1, column=0, padx=1); self.x1e.grid(row=1, column=1, padx=1); self.y0e.grid(row=1, column=2, padx=1); self.y1e.grid(row=1, column=3, padx=1)
        ttk.Label(tab_surf, text="Разбиения nx, ny (≥1):").grid(row=2, column=0, sticky="w", padx=4, pady=2)
        divfrm = ttk.Frame(tab_surf)
        divfrm.grid(row=2, column=1, sticky="we", padx=4, pady=2)
        divfrm.columnconfigure(0, weight=1); divfrm.columnconfigure(1, weight=1)
        self.nxe = ttk.Entry(divfrm); self.nye = ttk.Entry(divfrm)
        self.nxe.insert(0, "50"); self.nye.insert(0, "50")
        self.nxe.grid(row=0, column=0, sticky="we", padx=(0,2)); self.nye.grid(row=0, column=1, sticky="we", padx=(2,0))
        act2 = ttk.Frame(tab_surf)
        act2.grid(row=3, column=0, columnspan=2, sticky="we", padx=4, pady=(6,4))
        act2.columnconfigure(0, weight=1); act2.columnconfigure(1, weight=1)
        ttk.Button(act2, text="Построить", command=self.build_surface_ui).grid(row=0, column=0, sticky="we", padx=(0,2))
        ttk.Button(act2, text="Сохранить OBJ", command=self.save_obj_dialog).grid(row=0, column=1, sticky="we", padx=(2,0))

        self.fit_in_view()
        self.draw()

    def change_poly(self, _=None):
        name = self.poly_var.get()
        if name == "Тетраэдр":
            p = make_tetrahedron()
        elif name == "Куб":
            p = make_cube()
        elif name == "Октаэдр":
            p = make_octahedron()
        elif name == "Икосаэдр":
            p = make_icosahedron()
        elif name == "Додекаэдр":
            p = make_dodecahedron()
        else:
            p = make_tetrahedron()
        self.poly = p
        self.fit_in_view()
        self.draw()

    def change_projection(self, _=None):
        self.projection_mode = "perspective" if self.proj_var.get() == "Перспективная" else "isometric"
        self.draw()

    def fit_in_view(self):
        c = self.poly.center()
        M = matrix_translate(-c[0], -c[1], -c[2])
        self.poly.apply_matrix(M)

    def reset(self):
        self.change_poly()
        self.scale = 180.0
        self.camera_distance = 5.0
        if hasattr(self, "cam_e"):
            self.cam_e.delete(0, tk.END)
            self.cam_e.insert(0, str(self.camera_distance))
        self.draw()

    def apply_translate(self):
        try:
            tx = float(self.tx.get()); ty = float(self.ty.get()); tz = float(self.tz.get())
        except ValueError:
            messagebox.showerror("Ошибка ввода", "tx, ty, tz должны быть числами")
            return
        M = matrix_translate(tx, ty, tz)
        self.poly.apply_matrix(M)
        self.draw()

    def apply_scale(self):
        try:
            sx = float(self.sx.get()); sy = float(self.sy.get()); sz = float(self.sz.get())
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Коэффициенты масштаба должны быть числами")
            return
        M = matrix_scale(sx, sy, sz)
        self.poly.apply_matrix(M)
        self.draw()

    def apply_rotation(self):
        try:
            ax = math.radians(float(self.ax.get()))
            ay = math.radians(float(self.ay.get()))
            az = math.radians(float(self.az.get()))
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Углы поворота должны быть числами")
            return
        M = matrix_rotate_z(az) @ matrix_rotate_y(ay) @ matrix_rotate_x(ax)
        self.poly.apply_matrix(M)
        self.draw()

    def apply_reflect(self):
        plane = self.plane_var.get()
        M = matrix_reflect_plane(plane)
        self.poly.apply_matrix(M)
        self.draw()

    def apply_scale_about_center(self):
        try:
            f = float(self.factor_e.get())
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Коэффициент должен быть числом")
            return
        c = self.poly.center()
        M = matrix_translate(-c[0], -c[1], -c[2]) @ matrix_scale(f, f, f) @ matrix_translate(c[0], c[1], c[2])
        self.poly.apply_matrix(M)
        self.draw()

    def apply_rotate_around_center_parallel(self):
        try:
            angle = math.radians(float(self.angle_axis_e.get()))
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Угол должен быть числом")
            return
        axis = self.axis_var.get()
        c = self.poly.center()
        M = matrix_rotate_axis_through_point(axis, angle, c)
        self.poly.apply_matrix(M)
        self.draw()

    def apply_rotate_about_line(self):
        try:
            p1 = (float(self.p1x.get()), float(self.p1y.get()), float(self.p1z.get()))
            p2 = (float(self.p2x.get()), float(self.p2y.get()), float(self.p2z.get()))
            angle = math.radians(float(self.angle_line_e.get()))
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Координаты/угол должны быть числами")
            return
        M = matrix_rotate_about_line(p1, p2, angle)
        self.poly.apply_matrix(M)
        self.draw()

    def world_to_canvas(self, pts3):
        if self.projection_mode == 'perspective':
            pts2 = project_perspective(pts3, camera_distance=self.camera_distance)
        else:
            R = isometric_rotation_matrix()
            pts3r = (R @ pts3.T).T
            pts2 = project_orthographic(pts3r)
        pts_pix = pts2 * self.scale + self.offset
        return pts_pix

    def draw(self):
        self.canvas.delete("all")
        if self.poly is None:
            return
        pts3 = self.poly.V.copy()
        pts_pix = self.world_to_canvas(pts3)
        depths = []
        for f in self.poly.faces:
            zavg = np.mean(pts3[np.array(f.indices), 2])
            depths.append((zavg, f))
        depths.sort(key=lambda x: x[0], reverse=True)
        for _, f in depths:
            coords = []
            for idx in f.indices:
                x, y = pts_pix[idx]
                coords.extend([float(x), float(y)])
            self.canvas.create_polygon(coords, fill=self.face_fill, outline=self.edge_color, width=1)

    def load_obj_dialog(self):
        path = filedialog.askopenfilename(title="Открыть OBJ", filetypes=[("Wavefront OBJ", "*.obj"), ("Все файлы", "*.*")])
        if not path:
            return
        try:
            poly = self.load_obj(path)
        except Exception as e:
            messagebox.showerror("Ошибка загрузки", str(e))
            return
        self.poly = poly
        self.fit_in_view()
        self.draw()
        self.poly_var.set("OBJ")

    def save_obj_dialog(self):
        path = filedialog.asksaveasfilename(defaultextension=".obj", filetypes=[("Wavefront OBJ", "*.obj"), ("Все файлы", "*.*")], title="Сохранить OBJ")
        if not path:
            return
        try:
            self.save_obj(path, self.poly)
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", str(e))

    def load_obj(self, path):
        verts = []
        faces = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                parts = s.split()
                tag = parts[0].lower()
                if tag == "v" and len(parts) >= 4:
                    x = float(parts[1]); y = float(parts[2]); z = float(parts[3])
                    verts.append([x, y, z])
                elif tag == "f" and len(parts) >= 4:
                    idxs = []
                    for tok in parts[1:]:
                        if "/" in tok:
                            tok = tok.split("/")[0]
                        if tok == "" or tok == "0":
                            continue
                        i = int(tok)
                        if i < 0:
                            i = len(verts) + 1 + i
                        idxs.append(i - 1)
                    if len(idxs) >= 3:
                        faces.append(idxs)
        if len(verts) == 0 or len(faces) == 0:
            raise ValueError("Пустая модель или отсутствуют грани")
        V = np.array(verts, dtype=float)
        return Polyhedron(V, faces)

    def save_obj(self, path, poly: Polyhedron):
        with open(path, "w", encoding="utf-8") as f:
            for v in poly.V:
                f.write(f"v {v[0]} {v[1]} {v[2]}\n")
            for face in poly.faces:
                idxs = [str(i + 1) for i in face.indices]
                f.write("f " + " ".join(idxs) + "\n")

    def build_revolution_ui(self):
        txt = self.gen_text.get("1.0", tk.END).strip()
        if not txt:
            messagebox.showerror("Ошибка", "Задайте точки образующей")
            return
        pts = []
        for line in txt.replace(",", " ").splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 3:
                messagebox.showerror("Ошибка", f"Строка '{line}' должна содержать x y z")
                return
            try:
                x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
            except ValueError:
                messagebox.showerror("Ошибка", f"Неверный формат числа в строке '{line}'")
                return
            pts.append([x, y, z])
        try:
            segs = int(self.rev_segments_e.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Разбиений должно быть целым числом")
            return
        axis = self.rev_axis_var.get()
        try:
            poly = build_revolution(pts, axis, segs)
        except Exception as e:
            messagebox.showerror("Ошибка построения", str(e))
            return
        self.poly = poly
        self.fit_in_view()
        self.draw()
        self.poly_var.set("Вращение")

    def build_surface_ui(self):
        try:
            x0 = float(self.x0e.get()); x1 = float(self.x1e.get()); y0 = float(self.y0e.get()); y1 = float(self.y1e.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Диапазоны должны быть числами")
            return
        try:
            nx = int(self.nxe.get()); ny = int(self.nye.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Разбиения должны быть целыми")
            return
        if x1 == x0 or y1 == y0:
            messagebox.showerror("Ошибка", "Диапазоны не должны иметь нулевую длину")
            return
        func = self.func_var.get()
        try:
            poly = build_surface(func, x0, x1, y0, y1, nx, ny)
        except Exception as e:
            messagebox.showerror("Ошибка построения", str(e))
            return
        self.poly = poly
        self.fit_in_view()
        self.draw()
        self.poly_var.set("Поверхность")

def main():
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use('clam')
    except Exception:
        pass
    app = PolyhedronApp(root)
    root.minsize(1200, 740)
    root.mainloop()

if __name__ == "__main__":
    main()
