import math
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
from engine import (
    Face, Polyhedron, Lighting, Texture,
    matrix_translate, matrix_scale, matrix_rotate_x, matrix_rotate_y, matrix_rotate_z,
    matrix_reflect_plane, matrix_rotate_axis_through_point,
    project_perspective, project_orthographic, isometric_rotation_matrix,
    make_tetrahedron, make_cube, make_octahedron, make_icosahedron, make_dodecahedron,
    compute_face_normal_outward, look_at
)

class PolyhedronApp:
    def __init__(self, root):
        self.root = root
        root.title("Лабораторная 9 - Освещение и Текстурирование")
        self.canvas_w = 720
        self.canvas_h = 720
        self.objA = make_cube("#5a9bd8")
        self.projection_mode = 'perspective'
        self.camera_distance = 5.0
        self.scale = 180.0
        self.offset = np.array([self.canvas_w / 2, self.canvas_h / 2])
        self.bg_color = "#1e1e1e"
        self.front_outline = "#e6e6e6"
        self.back_outline = "#7aa2c0"
        self.cull_enabled = False
        self.zbuffer_enabled = False
        self.render_scale = 1.0
        self.overlay_wire_enabled = True
        self.overlay_wire_front_only = True
        self.wire_on_fill_color = "#ffffff"
        self.wire_on_fill_width = 1
        self.look_vec = np.array([0.0, 0.0, -1.0])
        self.camera_enabled = False
        self.cam_pos = np.array([0.0, 0.0, 6.0], dtype=float)
        self.cam_target = np.array([0.0, 0.0, 0.0], dtype=float)
        self.cam_fov_deg = 60.0
        self.cam_orbit_enabled = True
        self.cam_orbit_speed_deg = 2.0
        self.cam_orbit_radius = 6.0
        self.cam_up = np.array([0.0, 1.0, 0.0], dtype=float)
        self.cam_angle_deg = 0.0
        self.light_orbit_enabled = True
        self.light_orbit_radius = 6.0
        self.light_orbit_speed_deg = 12.0
        self.light_orbit_angle_deg = 0.0
        self.light_orbit_y = 2.0
        self.anim_enabled = True
        self.lighting = Lighting()
        self.shading_mode = 'none'
        self.texture = Texture()
        self.create_default_texture()
        main = ttk.Frame(root); main.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(main, width=self.canvas_w, height=self.canvas_h, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ctrl = ttk.Frame(main, width=560); ctrl.pack(side=tk.RIGHT, fill=tk.Y, padx=6, pady=6)
        self.nb = ttk.Notebook(ctrl); self.nb.pack(fill=tk.BOTH, expand=True)
        tab_a = ttk.Frame(self.nb); self.nb.add(tab_a, text="Объект")
        self._build_object_tab(tab_a, which="A")
        tab_tr = ttk.Frame(self.nb); self.nb.add(tab_tr, text="Сцена")
        self._build_scene_tab(tab_tr)
        tab_cam = ttk.Frame(self.nb); self.nb.add(tab_cam, text="Камера")
        self._build_camera_tab(tab_cam)
        tab_light = ttk.Frame(self.nb); self.nb.add(tab_light, text="Освещение и Текстуры")
        self._build_lighting_tab(tab_light)
        self.fit_in_view()
        self.img_handle = None
        self.draw()
        self.tick()

    def create_default_texture(self):
        size = 64
        img = Image.new("RGB", (size, size))
        pixels = img.load()
        for i in range(size):
            for j in range(size):
                if (i // 8 + j // 8) % 2 == 0:
                    pixels[i, j] = (200, 100, 50)
                else:
                    pixels[i, j] = (50, 100, 200)
        self.texture.texture_image = img
        self.texture.texture_data = img.load()
        self.texture.texture_width, self.texture.texture_height = img.size
        self.texture.use_texture = True

    def _build_lighting_tab(self, frame):
        frame.columnconfigure(1, weight=1)
        light_frame = ttk.LabelFrame(frame, text="Настройки освещения")
        light_frame.grid(row=0, column=0, columnspan=2, sticky="we", padx=4, pady=4)
        ttk.Label(light_frame, text="Позиция источника:").grid(row=0, column=0, sticky="w", padx=4, pady=2)
        light_pos_frame = ttk.Frame(light_frame)
        light_pos_frame.grid(row=0, column=1, columnspan=3, sticky="we", padx=4, pady=2)
        self.light_x = ttk.Entry(light_pos_frame, width=6); self.light_x.insert(0, "2.0")
        self.light_y_e = ttk.Entry(light_pos_frame, width=6); self.light_y_e.insert(0, "2.0")
        self.light_z = ttk.Entry(light_pos_frame, width=6); self.light_z.insert(0, "5.0")
        self.light_x.pack(side=tk.LEFT, padx=2); self.light_y_e.pack(side=tk.LEFT, padx=2); self.light_z.pack(side=tk.LEFT, padx=2)
        ttk.Label(light_frame, text="Интенсивности:").grid(row=1, column=0, sticky="w", padx=4, pady=2)
        intens_frame = ttk.Frame(light_frame)
        intens_frame.grid(row=1, column=1, columnspan=3, sticky="we", padx=4, pady=2)
        ttk.Label(intens_frame, text="Фоновая:").pack(side=tk.LEFT)
        self.ambient_intens = ttk.Entry(intens_frame, width=6); self.ambient_intens.insert(0, "0.3")
        self.ambient_intens.pack(side=tk.LEFT, padx=2)
        ttk.Label(intens_frame, text="Диффузная:").pack(side=tk.LEFT)
        self.diffuse_intens = ttk.Entry(intens_frame, width=6); self.diffuse_intens.insert(0, "0.7")
        self.diffuse_intens.pack(side=tk.LEFT, padx=2)
        ttk.Label(light_frame, text="Режим затенения:").grid(row=2, column=0, sticky="w", padx=4, pady=2)
        self.shading_var = tk.StringVar(value="none")
        shading_menu = ttk.OptionMenu(light_frame, self.shading_var, "none", "none", "gouraud", "phong", command=self.change_shading_mode)
        shading_menu.grid(row=2, column=1, sticky="we", padx=4, pady=2)
        ttk.Button(light_frame, text="Применить освещение", command=self.apply_lighting_params).grid(row=2, column=2, columnspan=2, sticky="we", padx=4, pady=2)
        orbit_frame = ttk.LabelFrame(frame, text="Орбита источника")
        orbit_frame.grid(row=1, column=0, columnspan=2, sticky="we", padx=4, pady=4)
        self.light_orbit_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(orbit_frame, text="Вращать источник по кругу (XZ)", variable=self.light_orbit_var, command=self.toggle_light_orbit).grid(row=0, column=0, sticky="w", padx=4, pady=2)
        tex_frame = ttk.LabelFrame(frame, text="Текстурирование")
        tex_frame.grid(row=2, column=0, columnspan=2, sticky="we", padx=4, pady=4)
        self.texture_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tex_frame, text="Использовать текстуру", variable=self.texture_var, command=self.toggle_texture).grid(row=0, column=0, columnspan=2, sticky="w", padx=4, pady=2)
        ttk.Button(tex_frame, text="Загрузить текстуру", command=self.load_texture_dialog).grid(row=1, column=0, sticky="we", padx=4, pady=2)
        ttk.Button(tex_frame, text="Сбросить текстуру", command=self.reset_texture).grid(row=1, column=1, sticky="we", padx=4, pady=2)

    def change_shading_mode(self, _=None):
        self.shading_mode = self.shading_var.get()
        self.draw()

    def apply_lighting_params(self):
        try:
            lx = float(self.light_x.get()); ly = float(self.light_y_e.get()); lz = float(self.light_z.get())
            ambient = float(self.ambient_intens.get()); diffuse = float(self.diffuse_intens.get())
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Параметры освещения должны быть числами"); return
        self.lighting.light_pos = np.array([lx, ly, lz], dtype=float)
        self.light_orbit_y = ly
        self.lighting.ambient_intensity = ambient
        self.lighting.diffuse_intensity = diffuse
        self.draw()

    def toggle_texture(self):
        self.texture.use_texture = self.texture_var.get()
        self.draw()

    def toggle_light_orbit(self):
        self.light_orbit_enabled = self.light_orbit_var.get()

    def load_texture_dialog(self):
        path = filedialog.askopenfilename(title="Загрузить текстуру", filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp *.gif"), ("Все файлы", "*.*")])
        if path:
            if self.texture.load_texture(path):
                self.draw()
            else:
                messagebox.showerror("Ошибка", "Не удалось загрузить текстуру")

    def reset_texture(self):
        self.create_default_texture()
        self.draw()

    def _build_object_tab(self, frame, which="A"):
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Модель:").grid(row=0, column=0, sticky="w", padx=4, pady=(6, 2))
        var = tk.StringVar(value="Куб")
        setattr(self, f"poly_var_{which}", var)
        ttk.OptionMenu(frame, var, "Куб", "Тетраэдр", "Куб", "Октаэдр", "Икосаэдр", "Додекаэдр", command=lambda *_: self.change_poly(which)).grid(row=0, column=1, sticky="we", padx=4, pady=(6, 2))
        io = ttk.Frame(frame); io.grid(row=1, column=0, columnspan=2, sticky="we", padx=4, pady=(2, 2))
        io.columnconfigure(0, weight=1); io.columnconfigure(1, weight=1)
        ttk.Button(io, text="Загрузить OBJ", command=lambda: self.load_obj_dialog(which)).grid(row=0, column=0, sticky="we", padx=(0, 2))
        ttk.Button(io, text="Сохранить OBJ", command=lambda: self.save_obj_dialog(which)).grid(row=0, column=1, sticky="we", padx=(2, 0))
        ttk.Separator(frame).grid(row=2, column=0, columnspan=2, sticky="we", padx=4, pady=6)
        left = ttk.Frame(frame); left.grid(row=3, column=0, columnspan=2, sticky="we", padx=4)
        for i in range(6): left.columnconfigure(i, weight=1)
        ttk.Label(left, text="Смещение tx ty tz").grid(row=0, column=0, columnspan=6, sticky="w")
        tx = ttk.Entry(left, width=7); ty = ttk.Entry(left, width=7); tz = ttk.Entry(left, width=7)
        tx.insert(0, "0"); ty.insert(0, "0"); tz.insert(0, "0")
        tx.grid(row=1, column=0); ty.grid(row=1, column=1); tz.grid(row=1, column=2)
        ttk.Button(left, text="Применить", command=lambda: self.apply_translate_obj(which, tx, ty, tz)).grid(row=1, column=3, columnspan=3, sticky="we", padx=(6, 0))
        ttk.Label(left, text="Масштаб sx sy sz").grid(row=2, column=0, columnspan=6, sticky="w", pady=(6, 0))
        sx = ttk.Entry(left, width=7); sy = ttk.Entry(left, width=7); sz = ttk.Entry(left, width=7)
        sx.insert(0, "1"); sy.insert(0, "1"); sz.insert(0, "1")
        sx.grid(row=3, column=0); sy.grid(row=3, column=1); sz.grid(row=3, column=2)
        ttk.Button(left, text="Применить", command=lambda: self.apply_scale_obj(which, sx, sy, sz)).grid(row=3, column=3, columnspan=3, sticky="we", padx=(6, 0))
        ttk.Label(left, text="Поворот (град) ax ay az").grid(row=4, column=0, columnspan=6, sticky="w", pady=(6, 0))
        ax = ttk.Entry(left, width=7); ay = ttk.Entry(left, width=7); az = ttk.Entry(left, width=7)
        ax.insert(0, "0"); ay.insert(0, "0"); az.insert(0, "0")
        ax.grid(row=5, column=0); ay.grid(row=5, column=1); az.grid(row=5, column=2)
        ttk.Button(left, text="Применить", command=lambda: self.apply_rotation_obj(which, ax, ay, az)).grid(row=5, column=3, columnspan=3, sticky="we", padx=(6, 0))
        ttk.Label(left, text="Масштаб от центра (k)").grid(row=6, column=0, columnspan=3, sticky="w", pady=(6, 0))
        k_e = ttk.Entry(left, width=7); k_e.insert(0, "1")
        k_e.grid(row=6, column=3, sticky="we")
        ttk.Button(left, text="Применить", command=lambda: self.apply_scale_about_center_obj(which, k_e)).grid(row=6, column=4, columnspan=2, sticky="we", padx=(6, 0))
        ttk.Label(left, text="Вращение вокруг оси через центр:").grid(row=7, column=0, columnspan=6, sticky="w", pady=(6, 0))
        axis_var = tk.StringVar(value="y")
        ttk.OptionMenu(left, axis_var, "y", "x", "y", "z").grid(row=8, column=0, sticky="we")
        ang_e = ttk.Entry(left, width=7); ang_e.insert(0, "0")
        ang_e.grid(row=8, column=1, sticky="we")
        ttk.Button(left, text="Повернуть", command=lambda: self.apply_rotate_around_center_obj(which, axis_var, ang_e)).grid(row=8, column=3, columnspan=3, sticky="we", padx=(6, 0))
        ttk.Button(frame, text="Сброс объекта", command=lambda: self.reset_object(which)).grid(row=9, column=0, columnspan=2, sticky="we", padx=4, pady=(10, 6))

    def _build_scene_tab(self, frame):
        for i in range(2): frame.columnconfigure(i, weight=1)
        ttk.Label(frame, text="Проекция:").grid(row=0, column=0, sticky="w", padx=4, pady=(6, 2))
        self.proj_var = tk.StringVar(value="Перспективная")
        ttk.OptionMenu(frame, self.proj_var, "Перспективная", "Перспективная", "Изометрическая", command=self.change_projection).grid(row=0, column=1, sticky="we", padx=4, pady=(6, 2))
        vf = ttk.LabelFrame(frame, text="Вектор обзора (для изометрической)")
        vf.grid(row=1, column=0, columnspan=2, sticky="we", padx=4, pady=(6, 4))
        for i in range(6): vf.columnconfigure(i, weight=1)
        ttk.Label(vf, text="lx").grid(row=0, column=0); ttk.Label(vf, text="ly").grid(row=0, column=2); ttk.Label(vf, text="lz").grid(row=0, column=4)
        self.lx_e = ttk.Entry(vf, width=8); self.ly_e = ttk.Entry(vf, width=8); self.lz_e = ttk.Entry(vf, width=8)
        self.lx_e.insert(0, "0"); self.ly_e.insert(0, "0"); self.lz_e.insert(0, "-1")
        self.lx_e.grid(row=0, column=1, padx=2); self.ly_e.grid(row=0, column=3, padx=2); self.lz_e.grid(row=0, column=5, padx=2)
        ttk.Button(vf, text="Применить", command=self.apply_look_vec).grid(row=1, column=0, columnspan=6, sticky="we", pady=(4, 0))
        flags = ttk.Frame(frame); flags.grid(row=2, column=0, columnspan=2, sticky="we", padx=4, pady=(6, 2))
        for i in range(7): flags.columnconfigure(i, weight=1)
        self.cull_var = tk.BooleanVar(value=False)
        self.zbuf_var = tk.BooleanVar(value=False)
        self.anim_var = tk.BooleanVar(value=True)
        self.overlay_wire_var = tk.BooleanVar(value=True)
        self.overlay_wire_mode = tk.StringVar(value="Только фронт")
        ttk.Checkbutton(flags, text="Отсекать нелицевые (каркас)", variable=self.cull_var, command=self.toggle_cull).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(flags, text="Z-буфер (заливка)", variable=self.zbuf_var, command=self.toggle_zbuf).grid(row=0, column=1, sticky="w")
        ttk.Checkbutton(flags, text="Вращать объект", variable=self.anim_var, command=self.toggle_anim).grid(row=0, column=2, sticky="w")
        ttk.Label(flags, text="Качество Z-буфера:").grid(row=0, column=3, sticky="e")
        self.quality_var = tk.StringVar(value="100%")
        ttk.OptionMenu(flags, self.quality_var, "100%", "100%", "50%", "33%", "25%", command=self.change_quality).grid(row=0, column=4, sticky="we")
        ttk.Checkbutton(flags, text="Каркас поверх заливки", variable=self.overlay_wire_var, command=self.toggle_overlay_wire).grid(row=0, column=5, sticky="w")
        ttk.OptionMenu(flags, self.overlay_wire_mode, "Только фронт", "Только фронт", "Все ребра", command=self.change_overlay_mode).grid(row=0, column=6, sticky="we")
        ttk.Separator(frame).grid(row=3, column=0, columnspan=2, sticky="we", padx=4, pady=6)
        left = ttk.Frame(frame); left.grid(row=4, column=0, columnspan=2, sticky="we", padx=4)
        for i in range(6): left.columnconfigure(i, weight=1)
        ttk.Label(left, text="Смещение tx ty tz").grid(row=0, column=0, columnspan=6, sticky="w")
        self.tx = ttk.Entry(left, width=7); self.ty = ttk.Entry(left, width=7); self.tz = ttk.Entry(left, width=7)
        self.tx.insert(0, "0"); self.ty.insert(0, "0"); self.tz.insert(0, "0")
        self.tx.grid(row=1, column=0); self.ty.grid(row=1, column=1); self.tz.grid(row=1, column=2)
        ttk.Button(left, text="Применить", command=self.apply_translate_scene).grid(row=1, column=3, columnspan=3, sticky="we", padx=(6, 0))
        ttk.Label(left, text="Масштаб sx sy sz").grid(row=2, column=0, columnspan=6, sticky="w", pady=(6, 0))
        self.sx = ttk.Entry(left, width=7); self.sy = ttk.Entry(left, width=7); self.sz = ttk.Entry(left, width=7)
        self.sx.insert(0, "1"); self.sy.insert(0, "1"); self.sz.insert(0, "1")
        self.sx.grid(row=3, column=0); self.sy.grid(row=3, column=1); self.sz.grid(row=3, column=2)
        ttk.Button(left, text="Применить", command=self.apply_scale_scene).grid(row=3, column=3, columnspan=3, sticky="we", padx=(6, 0))
        ttk.Label(left, text="Поворот (град) ax ay az").grid(row=4, column=0, columnspan=6, sticky="w", pady=(6, 0))
        self.ax = ttk.Entry(left, width=7); self.ay = ttk.Entry(left, width=7); self.az = ttk.Entry(left, width=7)
        self.ax.insert(0, "0"); self.ay.insert(0, "0"); self.az.insert(0, "0")
        self.ax.grid(row=5, column=0); self.ay.grid(row=5, column=1); self.az.grid(row=5, column=2)
        ttk.Button(left, text="Применить", command=self.apply_rotation_scene).grid(row=5, column=3, columnspan=3, sticky="we", padx=(6, 0))
        ttk.Label(left, text="Отражение в плоскости:").grid(row=6, column=0, columnspan=3, sticky="w", pady=(6, 0))
        self.plane_var = tk.StringVar(value="xy")
        ttk.OptionMenu(left, self.plane_var, "xy", "xy", "yz", "xz").grid(row=6, column=3, sticky="we")
        ttk.Button(left, text="Отразить", command=self.apply_reflect_scene).grid(row=6, column=4, columnspan=2, sticky="we")
        ttk.Label(left, text="Масштаб от центра (k)").grid(row=7, column=0, columnspan=3, sticky="w", pady=(6, 0))
        self.factor_e = ttk.Entry(left, width=7); self.factor_e.insert(0, "1")
        self.factor_e.grid(row=7, column=3, sticky="we")
        ttk.Button(left, text="Применить", command=self.apply_scale_about_center_scene).grid(row=7, column=4, columnspan=2, sticky="we")
        ttk.Label(left, text="Вращение вокруг оси через центр сцены:").grid(row=8, column=0, columnspan=6, sticky="w", pady=(6, 0))
        self.axis_var = tk.StringVar(value="y")
        ttk.OptionMenu(left, self.axis_var, "y", "x", "y", "z").grid(row=9, column=0, sticky="we")
        self.angle_axis_e = ttk.Entry(left, width=7); self.angle_axis_e.insert(0, "0")
        self.angle_axis_e.grid(row=9, column=1, sticky="we")
        ttk.Button(left, text="Повернуть", command=self.apply_rotate_around_center_scene).grid(row=9, column=3, columnspan=3, sticky="we", padx=(6, 0))
        ttk.Button(frame, text="Сброс сцены", command=self.reset_scene).grid(row=10, column=0, columnspan=2, sticky="we", padx=4, pady=(10, 6))

    def _build_camera_tab(self, frame):
        for i in range(4): frame.columnconfigure(i, weight=1)
        self.cam_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Использовать камеру", variable=self.cam_enabled_var, command=self.toggle_camera).grid(row=0, column=0, columnspan=2, sticky="w", padx=4, pady=(6, 2))
        self.cam_orbit_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Вращать камеру вокруг цели", variable=self.cam_orbit_var, command=self.toggle_cam_orbit).grid(row=0, column=2, columnspan=2, sticky="w", padx=4, pady=(6, 2))
        posf = ttk.LabelFrame(frame, text="Положение камеры (cx, cy, cz)")
        posf.grid(row=1, column=0, columnspan=4, sticky="we", padx=4, pady=4)
        for i in range(6): posf.columnconfigure(i, weight=1)
        ttk.Label(posf, text="cx").grid(row=0, column=0); ttk.Label(posf, text="cy").grid(row=0, column=2); ttk.Label(posf, text="cz").grid(row=0, column=4)
        self.cx_e = ttk.Entry(posf, width=10); self.cy_e = ttk.Entry(posf, width=10); self.cz_e = ttk.Entry(posf, width=10)
        self.cx_e.insert(0, str(self.cam_pos[0])); self.cy_e.insert(0, str(self.cam_pos[1])); self.cz_e.insert(0, str(self.cam_pos[2]))
        self.cx_e.grid(row=0, column=1, padx=2); self.cy_e.grid(row=0, column=3, padx=2); self.cz_e.grid(row=0, column=5, padx=2)
        tgf = ttk.LabelFrame(frame, text="Цель камеры (tx, ty, tz)")
        tgf.grid(row=2, column=0, columnspan=4, sticky="we", padx=4, pady=4)
        for i in range(6): tgf.columnconfigure(i, weight=1)
        ttk.Label(tgf, text="tx").grid(row=0, column=0); ttk.Label(tgf, text="ty").grid(row=0, column=2); ttk.Label(tgf, text="tz").grid(row=0, column=4)
        self.tx_e2 = ttk.Entry(tgf, width=10); self.ty_e2 = ttk.Entry(tgf, width=10); self.tz_e2 = ttk.Entry(tgf, width=10)
        self.tx_e2.insert(0, "0"); self.ty_e2.insert(0, "0"); self.tz_e2.insert(0, "0")
        self.tx_e2.grid(row=0, column=1, padx=2); self.ty_e2.grid(row=0, column=3, padx=2); self.tz_e2.grid(row=0, column=5, padx=2)
        pf = ttk.LabelFrame(frame, text="Параметры проекции")
        pf.grid(row=3, column=0, columnspan=4, sticky="we", padx=4, pady=4)
        for i in range(6): pf.columnconfigure(i, weight=1)
        ttk.Label(pf, text="FOV°").grid(row=0, column=0)
        self.fov_e = ttk.Entry(pf, width=10); self.fov_e.insert(0, str(self.cam_fov_deg))
        self.fov_e.grid(row=0, column=1, padx=2)
        ttk.Label(pf, text="Радиус орбиты").grid(row=0, column=2)
        self.rad_e = ttk.Entry(pf, width=10); self.rad_e.insert(0, str(self.cam_orbit_radius))
        self.rad_e.grid(row=0, column=3, padx=2)
        ttk.Label(pf, text="Скорость°/кадр").grid(row=0, column=4)
        self.spd_e = ttk.Entry(pf, width=10); self.spd_e.insert(0, str(self.cam_orbit_speed_deg))
        self.spd_e.grid(row=0, column=5, padx=2)
        ttk.Button(frame, text="Применить", command=self.apply_camera_params).grid(row=4, column=0, columnspan=4, sticky="we", padx=4, pady=(6, 6))

    def change_poly(self, which):
        obj = self.objA
        name = getattr(self, f"poly_var_{which}").get()
        if name == "Тетраэдр": new = make_tetrahedron(obj.color)
        elif name == "Куб": new = make_cube(obj.color)
        elif name == "Октаэдр": new = make_octahedron(obj.color)
        elif name == "Икосаэдр": new = make_icosahedron(obj.color)
        elif name == "Додекаэдр": new = make_dodecahedron(obj.color)
        else: new = make_cube(obj.color)
        new.name = name
        self.objA = new
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
        elif q == "33%": self.render_scale = 1.0 / 3.0
        elif q == "25%": self.render_scale = 0.25
        else: self.render_scale = 1.0
        self.draw()

    def fit_in_view(self):
        c = self.objA.center()
        T = matrix_translate(-c[0], -c[1], -c[2])
        self.objA.apply_matrix(T)
        self.cam_target = np.array([0.0, 0.0, 0.0], dtype=float)

    def reset_object(self, which):
        self.objA = make_cube("#5a9bd8")
        self.poly_var_A.set("Куб")
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
        self.objA = make_cube("#5a9bd8")
        self.camera_enabled = False; self.cam_enabled_var.set(False)
        self.cam_pos = np.array([0.0, 0.0, 6.0], dtype=float)
        self.cam_target = np.array([0.0, 0.0, 0.0], dtype=float)
        self.cam_fov_deg = 60.0; self.cam_angle_deg = 0.0
        self.cam_orbit_radius = 6.0; self.cam_orbit_speed_deg = 2.0; self.cam_orbit_var.set(True); self.cam_orbit_enabled = True
        self.cx_e.delete(0, tk.END); self.cx_e.insert(0, str(self.cam_pos[0]))
        self.cy_e.delete(0, tk.END); self.cy_e.insert(0, str(self.cam_pos[1]))
        self.cz_e.delete(0, tk.END); self.cz_e.insert(0, str(self.cam_pos[2]))
        self.tx_e2.delete(0, tk.END); self.tx_e2.insert(0, "0")
        self.ty_e2.delete(0, tk.END); self.ty_e2.insert(0, "0")
        self.tz_e2.delete(0, tk.END); self.tz_e2.insert(0, "0")
        self.fov_e.delete(0, tk.END); self.fov_e.insert(0, str(self.cam_fov_deg))
        self.rad_e.delete(0, tk.END); self.rad_e.insert(0, str(self.cam_orbit_radius))
        self.spd_e.delete(0, tk.END); self.spd_e.insert(0, str(self.cam_orbit_speed_deg))
        self.light_orbit_enabled = True; self.light_orbit_var.set(True)
        self.light_orbit_radius = 6.0; self.light_orbit_speed_deg = 12.0; self.light_orbit_angle_deg = 0.0
        self.lighting.light_pos = np.array([2.0, 2.0, 5.0], dtype=float)
        self.light_x.delete(0, tk.END); self.light_x.insert(0, "2.0")
        self.light_y_e.delete(0, tk.END); self.light_y_e.insert(0, "2.0")
        self.light_z.delete(0, tk.END); self.light_z.insert(0, "5.0")
        self.fit_in_view(); self.draw()

    def _get_obj(self, which):
        return self.objA

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

    def apply_translate_scene(self):
        try:
            tx = float(self.tx.get()); ty = float(self.ty.get()); tz = float(self.tz.get())
        except ValueError:
            messagebox.showerror("Ошибка ввода", "tx, ty, tz должны быть числами"); return
        M = matrix_translate(tx, ty, tz)
        self.objA.apply_matrix(M)
        self.draw()

    def apply_scale_scene(self):
        try:
            sx = float(self.sx.get()); sy = float(self.sy.get()); sz = float(self.sz.get())
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Коэффициенты масштаба должны быть числами"); return
        M = matrix_scale(sx, sy, sz)
        self.objA.apply_matrix(M)
        self.draw()

    def apply_rotation_scene(self):
        try:
            ax = math.radians(float(self.ax.get())); ay = math.radians(float(self.ay.get())); az = math.radians(float(self.az.get()))
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Углы поворота должны быть числами"); return
        M = matrix_rotate_z(az) @ matrix_rotate_y(ay) @ matrix_rotate_x(ax)
        self.objA.apply_matrix(M)
        self.draw()

    def apply_reflect_scene(self):
        M = matrix_reflect_plane(self.plane_var.get())
        self.objA.apply_matrix(M)
        self.draw()

    def apply_scale_about_center_scene(self):
        try:
            f = float(self.factor_e.get())
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Коэффициент должен быть числом"); return
        allV = self.objA.V
        c = np.mean(allV, axis=0)
        M = matrix_translate(-c[0], -c[1], -c[2]) @ matrix_scale(f, f, f) @ matrix_translate(c[0], c[1], c[2])
        self.objA.apply_matrix(M)
        self.draw()

    def apply_rotate_around_center_scene(self):
        try:
            angle = math.radians(float(self.angle_axis_e.get()))
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Угол должен быть числом"); return
        allV = self.objA.V; c = np.mean(allV, axis=0)
        axis = self.axis_var.get()
        M = matrix_rotate_axis_through_point(axis, angle, c)
        self.objA.apply_matrix(M)
        self.draw()
        
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
            if np.dot(n, view_vec) > 0:
                front.append(f)
            else:
                back.append(f)
        return front, back

    def classify_faces_isometric(self, V_iso, faces):
        obj_center_iso = np.mean(V_iso, axis=0)
        front, back = [], []
        for f in faces:
            n = compute_face_normal_outward(V_iso, f.indices, obj_center_iso)
            if np.allclose(n, 0.0): continue
            if np.dot(n, self.look_vec) < 0:
                front.append(f)
            else:
                back.append(f)
        return front, back

    def classify_faces_camera(self, V_eye, faces):
        obj_center_eye = np.mean(V_eye, axis=0)
        front, back = [], []
        for f in faces:
            idx = np.array(f.indices)
            centroid_eye = np.mean(V_eye[idx], axis=0)
            n_eye = compute_face_normal_outward(V_eye, f.indices, obj_center_eye)
            if np.allclose(n_eye, 0.0): continue
            view_vec = -centroid_eye
            if np.dot(n_eye, view_vec) > 0:
                front.append(f)
            else:
                back.append(f)
        return front, back

    def _draw_face_wire(self, V3, face, mode, outline, width):
        if mode == 'persp':
            pts2 = project_perspective(V3, camera_distance=self.camera_distance)
        elif mode == 'ortho':
            pts2 = project_orthographic(V3)
        else:
            pts2 = V3[:, :2]
        coords = []
        for idx in face.indices:
            x, y = pts2[idx]
            coords.extend([float(x * self.scale + self.offset[0]), float(y * self.scale + self.offset[1])])
        self.canvas.create_polygon(coords, fill="", outline=outline, width=width)

    def _draw_face_wire_camera(self, V_eye, face, f, outline=None, width=2):
        idx = face.indices
        pts = V_eye[idx]
        ze = pts[:, 2]
        if np.any(ze >= -1e-6):
            return
        x = pts[:, 0]; y = pts[:, 1]; zpos = -ze
        x2 = (x * f) / (zpos + 1e-12)
        y2 = (y * f) / (zpos + 1e-12)
        coords = []
        for i in range(len(idx)):
            sx = float(x2[i] * self.scale + self.offset[0])
            sy = float(y2[i] * self.scale + self.offset[1])
            coords.extend([sx, sy])
        self.canvas.create_polygon(coords, fill="", outline=(outline if outline is not None else self.front_outline), width=width)
