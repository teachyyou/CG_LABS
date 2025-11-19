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

    def load_obj_dialog(self, which):
        path = filedialog.askopenfilename(title="Открыть OBJ", filetypes=[("Wavefront OBJ", "*.obj"), ("Все файлы", "*.*")])
        if not path: return
        try:
            poly = self.load_obj(path)
        except Exception as e:
            messagebox.showerror("Ошибка загрузки", str(e)); return
        poly.color = self.objA.color
        self.objA = poly
        self.fit_in_view(); self.draw()

    def save_obj_dialog(self, which):
        path = filedialog.asksaveasfilename(defaultextension=".obj", filetypes=[("Wavefront OBJ", "*.obj"), ("Все файлы", "*.*")], title="Сохранить OBJ")
        if not path: return
        try:
            self.save_obj(path, self._get_obj(which))
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", str(e))

    def load_obj(self, path):
        verts = []; faces = []; tex_coords = []; normals = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith("#"): continue
                parts = s.split(); tag = parts[0].lower()
                if tag == "v" and len(parts) >= 4:
                    x = float(parts[1]); y = float(parts[2]); z = float(parts[3])
                    verts.append([x, y, z])
                elif tag == "vt" and len(parts) >= 3:
                    u = float(parts[1]); v = float(parts[2])
                    tex_coords.append([u, v])
                elif tag == "vn" and len(parts) >= 4:
                    x = float(parts[1]); y = float(parts[2]); z = float(parts[3])
                    normals.append([x, y, z])
                elif tag == "f" and len(parts) >= 4:
                    idxs = []; tex_idxs = []; norm_idxs = []
                    for tok in parts[1:]:
                        if "/" in tok:
                            parts_vert = tok.split("/")
                            vert_idx = parts_vert[0]
                            tex_idx = parts_vert[1] if len(parts_vert) > 1 and parts_vert[1] else "0"
                            norm_idx = parts_vert[2] if len(parts_vert) > 2 and parts_vert[2] else "0"
                        else:
                            vert_idx = tok; tex_idx = "0"; norm_idx = "0"
                        if vert_idx == "" or vert_idx == "0": continue
                        i_vert = int(vert_idx)
                        if i_vert < 0: i_vert = len(verts) + 1 + i_vert
                        idxs.append(i_vert - 1)
                        if tex_idx != "0" and tex_idx != "":
                            i_tex = int(tex_idx)
                            if i_tex < 0: i_tex = len(tex_coords) + 1 + i_tex
                            tex_idxs.append(i_tex - 1)
                        else:
                            tex_idxs.append(0)
                        if norm_idx != "0" and norm_idx != "":
                            i_norm = int(norm_idx)
                            if i_norm < 0: i_norm = len(normals) + 1 + i_norm
                            norm_idxs.append(i_norm - 1)
                        else:
                            norm_idxs.append(0)
                    if len(idxs) >= 3:
                        face = Face(idxs)
                        if tex_idxs and len(tex_idxs) == len(idxs):
                            face.tex_coords = [tex_coords[i] if i < len(tex_coords) else [0, 0] for i in tex_idxs]
                        faces.append(face)
        if len(verts) == 0 or len(faces) == 0:
            raise ValueError("Пустая модель или отсутствуют грани")
        vertex_normals = None
        if normals and len(normals) > 0:
            vertex_normals = np.array(normals, dtype=float)
        tex_coords_array = None
        if tex_coords and len(tex_coords) > 0:
            tex_coords_array = np.array(tex_coords, dtype=float)
        return Polyhedron(np.array(verts, dtype=float), faces, vertex_normals=vertex_normals, tex_coords=tex_coords_array)

    def save_obj(self, path, poly: Polyhedron):
        with open(path, "w", encoding="utf-8") as f:
            for v in poly.V:
                f.write(f"v {v[0]} {v[1]} {v[2]}\n")
            if poly.tex_coords is not None:
                for tc in poly.tex_coords:
                    f.write(f"vt {tc[0]} {tc[1]}\n")
            if poly.vertex_normals is not None:
                for vn in poly.vertex_normals:
                    f.write(f"vn {vn[0]} {vn[1]} {vn[2]}\n")
            for face in poly.faces:
                idxs = []
                for i, idx in enumerate(face.indices):
                    vert_idx = str(idx + 1)
                    tex_idx = ""
                    norm_idx = ""
                    if face.tex_coords and i < len(face.tex_coords):
                        tex_idx = str(i + 1)
                    if poly.vertex_normals is not None:
                        norm_idx = str(idx + 1)
                    if tex_idx and norm_idx:
                        idxs.append(f"{vert_idx}/{tex_idx}/{norm_idx}")
                    elif tex_idx:
                        idxs.append(f"{vert_idx}/{tex_idx}")
                    elif norm_idx:
                        idxs.append(f"{vert_idx}//{norm_idx}")
                    else:
                        idxs.append(vert_idx)
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

    def _color_to_rgb(self, color):
        if isinstance(color, str) and color.startswith("#"):
            return (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))
        return (90, 155, 216)

    def _apply_lighting_to_color(self, base_color, intensity):
        r, g, b = base_color
        r = int(r * intensity); g = int(g * intensity); b = int(b * intensity)
        return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

    def _rgb_to_hex(self, rgb):
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def _project_point_current(self, p):
        if self.camera_enabled:
            f = 1.0 / math.tan(math.radians(self.cam_fov_deg) * 0.5)
            Vview = look_at(self.cam_pos, self.cam_target, self.cam_up)
            hom = np.hstack([p, 1.0])
            eye = (Vview @ hom.T).T[:3]
            if eye[2] >= -1e-6:
                return None
            x2 = (eye[0] * f) / (-eye[2] + 1e-12)
            y2 = (eye[1] * f) / (-eye[2] + 1e-12)
            sx = float(x2 * self.scale + self.offset[0])
            sy = float(y2 * self.scale + self.offset[1])
            return sx, sy
        else:
            if self.projection_mode == 'perspective':
                x2, y2 = project_perspective(np.array([p]), camera_distance=self.camera_distance)[0]
            else:
                R = isometric_rotation_matrix()
                p = (R @ np.array(p).reshape(3, 1)).ravel()
                x2, y2 = p[0], p[1]
            sx = float(x2 * self.scale + self.offset[0])
            sy = float(y2 * self.scale + self.offset[1])
            return sx, sy

    def _draw_axes(self):
        axis_len = 2.0
        origin = np.array([0.0, 0.0, 0.0], dtype=float)
        axes = {
            'X': (origin, np.array([axis_len, 0.0, 0.0], dtype=float), "#ff6b6b"),
            'Y': (origin, np.array([0.0, axis_len, 0.0], dtype=float), "#6bff6b"),
            'Z': (origin, np.array([0.0, 0.0, axis_len], dtype=float), "#6bb7ff"),
        }
        for label, (p0, p1, color) in axes.items():
            s0 = self._project_point_current(p0)
            s1 = self._project_point_current(p1)
            if s0 is None or s1 is None:
                continue
            x0, y0 = s0; x1, y1 = s1
            self.canvas.create_line(x0, y0, x1, y1, fill=color, dash=(4, 3), width=1)
            self.canvas.create_text(x1 + 8, y1, text=label, fill=color, anchor="w", font=("TkDefaultFont", 10, "bold"))

    def render_zbuffer(self):
        if self.camera_enabled:
            return self.render_zbuffer_camera()
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
            sx = (pts2[:, 0] * scale_r + offset_r[0]).astype(np.float32)
            sy = (pts2[:, 1] * scale_r + offset_r[1]).astype(np.float32)
            return sx, sy

        def tri_rasterize(sx, sy, zdepth, color, tex_coords=None, normals=None, positions=None):
            minx = max(int(np.floor(min(sx))), 0); maxx = min(int(np.ceil(max(sx))), Wr - 1)
            miny = max(int(np.floor(min(sy))), 0); maxy = min(int(np.ceil(max(sy))), Hr - 1)
            if minx > maxx or miny > maxy: return
            x1, y1, z1 = sx[0], sy[0], zdepth[0]
            x2, y2, z2 = sx[1], sy[1], zdepth[1]
            x3, y3, z3 = sx[2], sy[2], zdepth[2]
            denom = ((y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3))
            if abs(denom) < 1e-8: return
            A1 = (y2 - y3); B1 = (x3 - x2)
            A2 = (y3 - y1); B2 = (x1 - x3)
            Cx = x3; Cy = y3
            for y in range(miny, maxy + 1):
                py = y + 0.5
                for x in range(minx, maxx + 1):
                    px = x + 0.5
                    w1 = (A1 * (px - Cx) + B1 * (py - Cy)) / denom
                    w2 = (A2 * (px - Cx) + B2 * (py - Cy)) / denom
                    w3 = 1.0 - w1 - w2
                    if w1 < 0 or w2 < 0 or w3 < 0: continue
                    z = w1 * z1 + w2 * z2 + w3 * z3
                    if z < zbuf[y, x]:
                        zbuf[y, x] = z
                        if self.shading_mode == 'phong' and normals is not None and positions is not None:
                            interp_normal = w1 * normals[0] + w2 * normals[1] + w3 * normals[2]
                            nrm = np.linalg.norm(interp_normal)
                            if nrm > 0: interp_normal = interp_normal / nrm
                            interp_pos = w1 * positions[0] + w2 * positions[1] + w3 * positions[2]
                            view_dir = -interp_pos / (np.linalg.norm(interp_pos) + 1e-12)
                            intensity = self.lighting.phong_shading(interp_normal, view_dir, interp_pos)
                            final_color = self._apply_lighting_to_color(color, intensity)
                        elif self.shading_mode == 'gouraud' and normals is not None:
                            i1 = self.lighting.lambert_shading(normals[0])
                            i2 = self.lighting.lambert_shading(normals[1])
                            i3 = self.lighting.lambert_shading(normals[2])
                            interp_intensity = w1 * i1 + w2 * i2 + w3 * i3
                            final_color = self._apply_lighting_to_color(color, interp_intensity)
                        else:
                            final_color = color
                        if self.texture.use_texture and tex_coords is not None:
                            u = w1 * tex_coords[0][0] + w2 * tex_coords[1][0] + w3 * tex_coords[2][0]
                            v = w1 * tex_coords[0][1] + w2 * tex_coords[1][1] + w3 * tex_coords[2][1]
                            tex_color = self.texture.get_color(u, v)
                            if self.shading_mode != 'none':
                                if self.shading_mode == 'phong' and normals is not None and positions is not None:
                                    intensity = self.lighting.phong_shading(interp_normal, view_dir, interp_pos)
                                elif self.shading_mode == 'gouraud' and normals is not None:
                                    intensity = interp_intensity
                                else:
                                    intensity = 1.0
                                tex_color = (int(tex_color[0] * intensity), int(tex_color[1] * intensity), int(tex_color[2] * intensity))
                            rgb[y, x] = tex_color
                        else:
                            rgb[y, x] = final_color

        obj = self.objA
        V = obj.V.copy()
        if self.projection_mode == 'perspective':
            pts2 = project_perspective(V, camera_distance=d)
            depth = (d - V[:, 2])
        else:
            R = isometric_rotation_matrix()
            V = (R @ V.T).T
            pts2 = project_orthographic(V)
            depth = (-V[:, 2])
        sx_all, sy_all = to_screen(pts2)
        base_color = self._color_to_rgb(obj.color)
        for f in obj.faces:
            idx = f.indices
            if len(idx) < 3: continue
            i0 = idx[0]
            for t in range(1, len(idx) - 1):
                i1 = idx[t]; i2 = idx[t + 1]
                sx = np.array([sx_all[i0], sx_all[i1], sx_all[i2]], dtype=np.float32)
                sy = np.array([sy_all[i0], sy_all[i1], sy_all[i2]], dtype=np.float32)
                zdepth = np.array([depth[i0], depth[i1], depth[i2]], dtype=np.float32)
                tex_coords = None; normals = None; positions = None
                if f.tex_coords and len(f.tex_coords) >= len(idx):
                    tex_coords = [f.tex_coords[0], f.tex_coords[t], f.tex_coords[t + 1]]
                if obj.vertex_normals is not None:
                    normals = [obj.vertex_normals[i0], obj.vertex_normals[i1], obj.vertex_normals[i2]]
                if self.shading_mode == 'phong':
                    positions = [V[i0], V[i1], V[i2]]
                tri_rasterize(sx, sy, zdepth, base_color, tex_coords, normals, positions)
        header = f"P6 {Wr} {Hr} 255\n".encode("ascii")
        data = rgb.tobytes()
        ppm = header + data
        img_small = tk.PhotoImage(data=ppm, format="PPM")
        if s == 1.0:
            return img_small
        zoom = int(round(1.0 / s))
        img_zoom = img_small.zoom(zoom, zoom)
        return img_zoom

    def render_zbuffer_camera(self):
        Wc, Hc = self.canvas_w, self.canvas_h
        s = self.render_scale
        Wr = max(1, int(Wc * s))
        Hr = max(1, int(Hc * s))
        zbuf = np.full((Hr, Wr), np.inf, dtype=float)
        rgb = np.zeros((Hr, Wr, 3), dtype=np.uint8)
        f = 1.0 / math.tan(math.radians(self.cam_fov_deg) * 0.5)
        scale_r = self.scale * s
        offset_r = np.array([Wr / 2.0, Hr / 2.0], dtype=float)

        def to_screen_from_xy(x2, y2):
            sx = (x2 * scale_r + offset_r[0]).astype(np.float32)
            sy = (y2 * scale_r + offset_r[1]).astype(np.float32)
            return sx, sy

        def tri_rasterize(sx, sy, zdepth, color, tex_coords=None, normals=None, positions=None):
            minx = max(int(np.floor(min(sx))), 0); maxx = min(int(np.ceil(max(sx))), Wr - 1)
            miny = max(int(np.floor(min(sy))), 0); maxy = min(int(np.ceil(max(sy))), Hr - 1)
            if minx > maxx or miny > maxy: return
            x1, y1, z1 = sx[0], sy[0], zdepth[0]
            x2, y2, z2 = sx[1], sy[1], zdepth[1]
            x3, y3, z3 = sx[2], sy[2], zdepth[2]
            denom = ((y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3))
            if abs(denom) < 1e-8: return
            A1 = (y2 - y3); B1 = (x3 - x2)
            A2 = (y3 - y1); B2 = (x1 - x3)
            Cx = x3; Cy = y3
            for y in range(miny, maxy + 1):
                py = y + 0.5
                for x in range(minx, maxx + 1):
                    px = x + 0.5
                    w1 = (A1 * (px - Cx) + B1 * (py - Cy)) / denom
                    w2 = (A2 * (px - Cx) + B2 * (py - Cy)) / denom
                    w3 = 1.0 - w1 - w2
                    if w1 < 0 or w2 < 0 or w3 < 0: continue
                    z = w1 * z1 + w2 * z2 + w3 * z3
                    if z < zbuf[y, x]:
                        zbuf[y, x] = z
                        if self.shading_mode == 'phong' and normals is not None and positions is not None:
                            interp_normal = w1 * normals[0] + w2 * normals[1] + w3 * normals[2]
                            nrmv = np.linalg.norm(interp_normal)
                            if nrmv > 0: interp_normal = interp_normal / nrmv
                            view_dir = -positions[0] / (np.linalg.norm(positions[0]) + 1e-12)
                            intensity = self.lighting.phong_shading(interp_normal, view_dir, positions[0])
                            final_color = self._apply_lighting_to_color(color, intensity)
                        elif self.shading_mode == 'gouraud' and normals is not None:
                            i1 = self.lighting.lambert_shading(normals[0])
                            i2 = self.lighting.lambert_shading(normals[1])
                            i3 = self.lighting.lambert_shading(normals[2])
                            interp_intensity = w1 * i1 + w2 * i2 + w3 * i3
                            final_color = self._apply_lighting_to_color(color, interp_intensity)
                        else:
                            final_color = color
                        if self.texture.use_texture and tex_coords is not None:
                            u = w1 * tex_coords[0][0] + w2 * tex_coords[1][0] + w3 * tex_coords[2][0]
                            v = w1 * tex_coords[0][1] + w2 * tex_coords[1][1] + w3 * tex_coords[2][1]
                            tex_color = self.texture.get_color(u, v)
                            if self.shading_mode != 'none':
                                if self.shading_mode == 'phong' and normals is not None and positions is not None:
                                    intensity = self.lighting.phong_shading(interp_normal, view_dir, positions[0])
                                elif self.shading_mode == 'gouraud' and normals is not None:
                                    intensity = interp_intensity
                                else:
                                    intensity = 1.0
                                tex_color = (int(tex_color[0] * intensity), int(tex_color[1] * intensity), int(tex_color[2] * intensity))
                            rgb[y, x] = tex_color
                        else:
                            rgb[y, x] = final_color

        Vview = look_at(self.cam_pos, self.cam_target, self.cam_up)
        obj = self.objA
        V = obj.V
        N = V.shape[0]
        hom = np.hstack([V, np.ones((N, 1))])
        eye = (Vview @ hom.T).T[:, :3]
        ze = eye[:, 2]
        mask = ze < -1e-6
        if np.any(mask):
            xproj = (eye[:, 0] * f) / (-ze + 1e-12)
            yproj = (eye[:, 1] * f) / (-ze + 1e-12)
            depth = -ze
            sx_all, sy_all = to_screen_from_xy(xproj, yproj)
            base_color = self._color_to_rgb(obj.color)
            for fce in obj.faces:
                idx = fce.indices
                if len(idx) < 3: continue
                i0 = idx[0]
                for t in range(1, len(idx) - 1):
                    i1 = idx[t]; i2 = idx[t + 1]
                    if not (mask[i0] and mask[i1] and mask[i2]): continue
                    sx = np.array([sx_all[i0], sx_all[i1], sx_all[i2]], dtype=np.float32)
                    sy = np.array([sy_all[i0], sy_all[i1], sy_all[i2]], dtype=np.float32)
                    zdepth = np.array([depth[i0], depth[i1], depth[i2]], dtype=np.float32)
                    tex_coords = None; normals = None; positions = None
                    if fce.tex_coords and len(fce.tex_coords) >= len(idx):
                        tex_coords = [fce.tex_coords[0], fce.tex_coords[t], fce.tex_coords[t + 1]]
                    if obj.vertex_normals is not None:
                        normals = [obj.vertex_normals[i0], obj.vertex_normals[i1], obj.vertex_normals[i2]]
                    if self.shading_mode == 'phong':
                        positions = [eye[i0], eye[i1], eye[i2]]
                    tri_rasterize(sx, sy, zdepth, base_color, tex_coords, normals, positions)
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
        self._draw_axes()
        if self.zbuffer_enabled:
            self.img_handle = self.render_zbuffer()
            self.canvas.create_image(0, 0, image=self.img_handle, anchor="nw")
            if self.overlay_wire_enabled and not self.camera_enabled:
                obj = self.objA
                V = obj.V.copy()
                if self.projection_mode == 'perspective':
                    if self.overlay_wire_front_only:
                        front, _ = self.classify_faces_perspective(V, obj.faces)
                        for f in front:
                            self._draw_face_wire(V, f, mode='persp', outline=self.wire_on_fill_color, width=self.wire_on_fill_width)
                    else:
                        front, back = self.classify_faces_perspective(V, obj.faces)
                        for f in back:
                            self._draw_face_wire(V, f, mode='persp', outline=self.back_outline, width=1)
                        for f in front:
                            self._draw_face_wire(V, f, mode='persp', outline=self.wire_on_fill_color, width=self.wire_on_fill_width)
                else:
                    R = isometric_rotation_matrix()
                    V = (R @ obj.V.T).T
                    if self.overlay_wire_front_only:
                        front, _ = self.classify_faces_isometric(V, obj.faces)
                        for f in front:
                            self._draw_face_wire(V, f, mode='ortho', outline=self.wire_on_fill_color, width=self.wire_on_fill_width)
                    else:
                        front, back = self.classify_faces_isometric(V, obj.faces)
                        for f in back:
                            self._draw_face_wire(V, f, mode='ortho', outline=self.back_outline, width=1)
                        for f in front:
                            self._draw_face_wire(V, f, mode='ortho', outline=self.wire_on_fill_color, width=self.wire_on_fill_width)
            if self.overlay_wire_enabled and self.camera_enabled:
                f = 1.0 / math.tan(math.radians(self.cam_fov_deg) * 0.5)
                Vview = look_at(self.cam_pos, self.cam_target, self.cam_up)
                obj = self.objA
                V = obj.V
                hom = np.hstack([V, np.ones((V.shape[0], 1))])
                eye = (Vview @ hom.T).T[:, :3]
                if self.overlay_wire_front_only:
                    front, _ = self.classify_faces_camera(eye, obj.faces)
                    for face in front:
                        self._draw_face_wire_camera(eye, face, f, outline=self.wire_on_fill_color, width=self.wire_on_fill_width)
                else:
                    front, back = self.classify_faces_camera(eye, obj.faces)
                    for face in back:
                        self._draw_face_wire_camera(eye, face, f, outline=self.back_outline, width=1)
                    for face in front:
                        self._draw_face_wire_camera(eye, face, f, outline=self.wire_on_fill_color, width=self.wire_on_fill_width)
            return
        if self.camera_enabled:
            f = 1.0 / math.tan(math.radians(self.cam_fov_deg) * 0.5)
            Vview = look_at(self.cam_pos, self.cam_target, self.cam_up)
            obj = self.objA
            V = obj.V
            hom = np.hstack([V, np.ones((V.shape[0], 1))])
            eye = (Vview @ hom.T).T[:, :3]
            front, back = self.classify_faces_camera(eye, obj.faces)
            def depth_key(face):
                return np.mean(eye[np.array(face.indices), 2])
            if not self.cull_enabled:
                for face in sorted(back, key=depth_key, reverse=True):
                    self._draw_face_wire_camera(eye, face, f, outline=self.back_outline, width=1)
                for face in sorted(front, key=depth_key, reverse=True):
                    self._draw_face_wire_camera(eye, face, f, outline=self.front_outline, width=2)
            else:
                for face in sorted(front, key=depth_key, reverse=True):
                    self._draw_face_wire_camera(eye, face, f, outline=self.front_outline, width=2)
            return
        obj = self.objA
        if self.projection_mode == 'perspective':
            V = obj.V.copy()
            front, back = self.classify_faces_perspective(V, obj.faces)
            def depth_key(fa): return np.mean(V[np.array(fa.indices), 2])
            if not self.cull_enabled:
                for fce in sorted(back, key=depth_key, reverse=True):
                    self._draw_face_wire(V, fce, mode='persp', outline=self.back_outline, width=1)
                for fce in sorted(front, key=depth_key, reverse=True):
                    self._draw_face_wire(V, fce, mode='persp', outline=self.front_outline, width=2)
            else:
                for fce in sorted(front, key=depth_key, reverse=True):
                    self._draw_face_wire(V, fce, mode='persp', outline=self.front_outline, width=2)
        else:
            R = isometric_rotation_matrix()
            V = (R @ obj.V.T).T
            front, back = self.classify_faces_isometric(V, obj.faces)
            def depth_key(fa): return np.mean(V[np.array(fa.indices), 2])
            if not self.cull_enabled:
                for fce in sorted(back, key=depth_key, reverse=True):
                    self._draw_face_wire(V, fce, mode='ortho', outline=self.back_outline, width=1)
                for fce in sorted(front, key=depth_key, reverse=True):
                    self._draw_face_wire(V, fce, mode='ortho', outline=self.front_outline, width=2)
            else:
                for fce in sorted(front, key=depth_key, reverse=True):
                    self._draw_face_wire(V, fce, mode='ortho', outline=self.front_outline, width=2)

    def tick(self):
        did_draw = False
        if self.camera_enabled and self.cam_orbit_enabled:
            try:
                r = float(self.rad_e.get())
            except Exception:
                r = self.cam_orbit_radius
            try:
                spd = float(self.spd_e.get())
            except Exception:
                spd = self.cam_orbit_speed_deg
            self.cam_orbit_radius = r
            self.cam_orbit_speed_deg = spd
            self.cam_angle_deg = (self.cam_angle_deg + self.cam_orbit_speed_deg) % 360.0
            ang = math.radians(self.cam_angle_deg)
            cx = self.cam_target[0] + r * math.cos(ang)
            cz = self.cam_target[2] + r * math.sin(ang)
            cy = self.cam_pos[1]
            self.cam_pos = np.array([cx, cy, cz], dtype=float)
            did_draw = True
        if self.light_orbit_enabled:
            self.light_orbit_angle_deg = (self.light_orbit_angle_deg + 12.0) % 360.0
            ang = math.radians(self.light_orbit_angle_deg)
            lx = self.light_orbit_radius * math.cos(ang)
            lz = self.light_orbit_radius * math.sin(ang)
            ly = self.light_orbit_y
            self.lighting.light_pos = np.array([lx, ly, lz], dtype=float)
            did_draw = True
        if self.anim_enabled:
            allV = self.objA.V
            c = np.mean(allV, axis=0)
            M = matrix_translate(-c[0], -c[1], -c[2]) @ matrix_rotate_y(math.radians(2.0)) @ matrix_translate(c[0], c[1], c[2])
            self.objA.apply_matrix(M)
            did_draw = True
        if did_draw:
            self.draw()
        self.root.after(33, self.tick)

    def toggle_camera(self):
        self.camera_enabled = self.cam_enabled_var.get()
        self.draw()

    def toggle_cam_orbit(self):
        self.cam_orbit_enabled = self.cam_orbit_var.get()

    def apply_camera_params(self):
        try:
            cx = float(self.cx_e.get()); cy = float(self.cy_e.get()); cz = float(self.cz_e.get())
            tx = float(self.tx_e2.get()); ty = float(self.ty_e2.get()); tz = float(self.tz_e2.get())
            fov = float(self.fov_e.get()); rad = float(self.rad_e.get()); spd = float(self.spd_e.get())
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Неверные параметры камеры"); return
        self.cam_pos = np.array([cx, cy, cz], dtype=float)
        self.cam_target = np.array([tx, ty, tz], dtype=float)
        self.cam_fov_deg = max(5.0, min(170.0, fov))
        self.cam_orbit_radius = max(0.1, rad)
        self.cam_orbit_speed_deg = spd
        self.draw()
