import math
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
class Face:
    def __init__(self, indices):
        self.indices = list(indices)

class Polyhedron:
    def __init__(self, vertices: np.ndarray, faces: list):
        self.V = np.array(vertices, dtype=float)  # Nx3
        self.faces = [Face(f) for f in faces]

    def copy(self):
        return Polyhedron(self.V.copy(), [f.indices[:] for f in self.faces])

    def center(self):
        return np.mean(self.V, axis=0)

    def apply_matrix(self, M: np.ndarray):
        N = self.V.shape[0]
        hom = np.hstack([self.V, np.ones((N,1))])
        transformed = (M @ hom.T).T
        w = transformed[:, 3:4]
        w[w == 0] = 1.0
        self.V = transformed[:, :3] / w

# Polyhedron factory functions

def make_tetrahedron():
    verts = np.array([
        [ 1,  1,  1],
        [ 1, -1, -1],
        [-1,  1, -1],
        [-1, -1,  1]
    ], dtype=float)
    verts = verts / np.linalg.norm(verts[0])
    faces = [[0,1,2],[0,3,1],[0,2,3],[1,3,2]]
    return Polyhedron(verts, faces)

def make_cube():
    s = 1.0
    verts = np.array([[x,y,z] for x in (-s,s) for y in (-s,s) for z in (-s,s)], dtype=float)
    faces = [ [0,1,3,2], [4,6,7,5], [0,2,6,4], [1,5,7,3], [0,4,5,1], [2,3,7,6] ]
    return Polyhedron(verts, faces)

def make_octahedron():
    verts = np.array([[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]], dtype=float)
    faces = [[0,2,4],[2,1,4],[1,3,4],[3,0,4],[2,0,5],[1,2,5],[3,1,5],[0,3,5]]
    return Polyhedron(verts, faces)

def make_icosahedron():
    t = (1.0 + math.sqrt(5.0)) / 2.0
    verts = np.array([
        [-1,  t,  0],[ 1,  t, 0],[-1, -t, 0],[1,-t,0],
        [0,-1, t],[0,1,t],[0,-1,-t],[0,1,-t],
        [ t,0,-1],[ t,0,1],[-t,0,-1],[-t,0,1]
    ], dtype=float)
    verts /= np.max(np.linalg.norm(verts, axis=1))
    faces = [
        [0,11,5],[0,5,1],[0,1,7],[0,7,10],[0,10,11],
        [1,5,9],[5,11,4],[11,10,2],[10,7,6],[7,1,8],
        [3,9,4],[3,4,2],[3,2,6],[3,6,8],[3,8,9],
        [4,9,5],[2,4,11],[6,2,10],[8,6,7],[9,8,1]
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
        pts = centers[incident]  # (5,3)

        n = v / np.linalg.norm(v)

        ref = np.array([1.0, 0.0, 0.0])
        if abs(np.dot(ref, n)) > 0.9:
            ref = np.array([0.0, 1.0, 0.0])
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

class PolyhedronApp:
    def __init__(self, root):
        self.root = root
        root.title("Polyhedron Explorer (tkinter, split authors)")
        self.canvas_w = 700; self.canvas_h = 700

        self.poly = make_tetrahedron()
        self.projection_mode = 'perspective'
        self.camera_distance = 5.0
        self.scale = 180.0
        self.offset = np.array([self.canvas_w/2, self.canvas_h/2])
        self.bg = "#1e1e1e"
        self.face_fill = "#5a9bd8"
        self.edge_color = "#e6e6e6"

        main = ttk.Frame(root)
        main.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(main, width=self.canvas_w, height=self.canvas_h, bg=self.bg, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ctrl = ttk.Frame(main, width=260)
        ctrl.pack(side=tk.RIGHT, fill=tk.Y, padx=6, pady=6)

        ttk.Label(ctrl, text="Polyhedron:").pack(anchor=tk.W)
        self.poly_var = tk.StringVar(value="Tetrahedron")
        poly_menu = ttk.OptionMenu(ctrl, self.poly_var, "Tetrahedron", "Tetrahedron","Cube","Octahedron","Icosahedron","Dodecahedron", command=self.change_poly)
        poly_menu.pack(fill=tk.X)

        ttk.Label(ctrl, text="Projection:").pack(anchor=tk.W, pady=(8,0))
        self.proj_var = tk.StringVar(value="Perspective")
        proj_menu = ttk.OptionMenu(ctrl, self.proj_var, "Perspective", "Perspective", "Isometric", command=self.change_projection)
        proj_menu.pack(fill=tk.X)

        frm = ttk.Frame(ctrl); frm.pack(fill=tk.X, pady=(8,0))
        ttk.Label(frm, text="Translate tx ty tz").grid(row=0, column=0, columnspan=3, sticky=tk.W)
        self.tx = ttk.Entry(frm, width=8); self.ty = ttk.Entry(frm, width=8); self.tz = ttk.Entry(frm, width=8)
        self.tx.insert(0,"0"); self.ty.insert(0,"0"); self.tz.insert(0,"0")
        self.tx.grid(row=1,column=0); self.ty.grid(row=1,column=1); self.tz.grid(row=1,column=2)
        ttk.Button(frm, text="Apply", command=self.apply_translate).grid(row=2,column=0,columnspan=3,sticky="we", pady=2)
        ttk.Label(frm, text="Scale sx sy sz").grid(row=3, column=0, columnspan=3, sticky=tk.W)
        self.sx = ttk.Entry(frm, width=8); self.sy = ttk.Entry(frm, width=8); self.sz = ttk.Entry(frm, width=8)
        self.sx.insert(0,"1"); self.sy.insert(0,"1"); self.sz.insert(0,"1")
        self.sx.grid(row=4,column=0); self.sy.grid(row=4,column=1); self.sz.grid(row=4,column=2)
        ttk.Button(frm, text="Apply", command=self.apply_scale).grid(row=5,column=0,columnspan=3,sticky="we", pady=2)
        ttk.Label(frm, text="Rotate (deg) ax ay az").grid(row=6, column=0, columnspan=3, sticky=tk.W)
        self.ax = ttk.Entry(frm, width=8); self.ay = ttk.Entry(frm, width=8); self.az = ttk.Entry(frm, width=8)
        self.ax.insert(0,"0"); self.ay.insert(0,"0"); self.az.insert(0,"0")
        self.ax.grid(row=7,column=0); self.ay.grid(row=7,column=1); self.az.grid(row=7,column=2)
        ttk.Button(frm, text="Apply", command=self.apply_rotation).grid(row=8,column=0,columnspan=3,sticky="we", pady=2)

        ttk.Label(ctrl, text="Reflect plane:").pack(anchor=tk.W, pady=(8,0))
        self.plane_var = tk.StringVar(value="xy")
        ttk.OptionMenu(ctrl, self.plane_var, "xy","xy","yz","xz").pack(fill=tk.X)
        ttk.Button(ctrl, text="Reflect", command=self.apply_reflect).pack(fill=tk.X, pady=4)

        ttk.Label(ctrl, text="Scale about center (factor):").pack(anchor=tk.W, pady=(8,0))
        self.factor_e = ttk.Entry(ctrl); self.factor_e.insert(0,"1"); self.factor_e.pack(fill=tk.X)
        ttk.Button(ctrl, text="Apply", command=self.apply_scale_about_center).pack(fill=tk.X, pady=4)

        ttk.Label(ctrl, text="Rotate around center-parallel axis:").pack(anchor=tk.W, pady=(8,0))
        sub = ttk.Frame(ctrl); sub.pack(fill=tk.X)
        self.axis_var = tk.StringVar(value="x")
        ttk.OptionMenu(sub, self.axis_var, "x","x","y","z").grid(row=0,column=0)
        self.angle_axis_e = ttk.Entry(sub, width=10); self.angle_axis_e.insert(0,"0"); self.angle_axis_e.grid(row=0,column=1,padx=4)
        ttk.Button(ctrl, text="Apply", command=self.apply_rotate_around_center_parallel).pack(fill=tk.X,pady=4)

        ttk.Label(ctrl, text="Rotate about line: p1 -> p2  angle(deg)").pack(anchor=tk.W, pady=(8,0))
        linefrm = ttk.Frame(ctrl); linefrm.pack(fill=tk.X)
        self.p1x = ttk.Entry(linefrm, width=6); self.p1y = ttk.Entry(linefrm, width=6); self.p1z = ttk.Entry(linefrm, width=6)
        self.p2x = ttk.Entry(linefrm, width=6); self.p2y = ttk.Entry(linefrm, width=6); self.p2z = ttk.Entry(linefrm, width=6)
        self.p1x.insert(0,"0"); self.p1y.insert(0,"0"); self.p1z.insert(0,"0")
        self.p2x.insert(0,"1"); self.p2y.insert(0,"0"); self.p2z.insert(0,"0")
        ttk.Label(linefrm, text="p1:").grid(row=0,column=0); self.p1x.grid(row=0,column=1); self.p1y.grid(row=0,column=2); self.p1z.grid(row=0,column=3)
        ttk.Label(linefrm, text="p2:").grid(row=1,column=0); self.p2x.grid(row=1,column=1); self.p2y.grid(row=1,column=2); self.p2z.grid(row=1,column=3)
        self.angle_line_e = ttk.Entry(ctrl); self.angle_line_e.insert(0,"0"); self.angle_line_e.pack(fill=tk.X, pady=(4,0))
        ttk.Button(ctrl, text="Apply rotation about line", command=self.apply_rotate_about_line).pack(fill=tk.X, pady=4)

        ttk.Button(ctrl, text="Reset & Fit", command=self.reset).pack(fill=tk.X, pady=(10,0))

        self.fit_in_view()
        self.draw()

    def change_poly(self, _=None):
        name = self.poly_var.get()
        if name == "Tetrahedron": p = make_tetrahedron()
        elif name == "Cube": p = make_cube()
        elif name == "Octahedron": p = make_octahedron()
        elif name == "Icosahedron": p = make_icosahedron()
        elif name == "Dodecahedron": p = make_dodecahedron()
        else: p = make_tetrahedron()
        self.poly = p
        self.fit_in_view()
        self.draw()

    def change_projection(self, _=None):
        self.projection_mode = "perspective" if self.proj_var.get()=="Perspective" else "isometric"
        self.draw()

    def fit_in_view(self):
        c = self.poly.center()
        M = matrix_translate(-c[0], -c[1], -c[2])
        self.poly.apply_matrix(M)

    def reset(self):
        self.change_poly()
        self.scale = 180.0
        self.camera_distance = 5.0
        self.draw()

    def apply_translate(self):
        try:
            tx = float(self.tx.get()); ty = float(self.ty.get()); tz = float(self.tz.get())
        except ValueError:
            messagebox.showerror("Input error", "Translate values must be numbers")
            return
        M = matrix_translate(tx, ty, tz)
        self.poly.apply_matrix(M)
        self.draw()

    def apply_scale(self):
        try:
            sx = float(self.sx.get()); sy = float(self.sy.get()); sz = float(self.sz.get())
        except ValueError:
            messagebox.showerror("Input error", "Scale values must be numbers")
            return
        M = matrix_scale(sx, sy, sz)
        self.poly.apply_matrix(M)
        self.draw()

    def apply_rotation(self):
        try:
            ax = math.radians(float(self.ax.get())); ay = math.radians(float(self.ay.get())); az = math.radians(float(self.az.get()))
        except ValueError:
            messagebox.showerror("Input error", "Rotation angles must be numbers")
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
            messagebox.showerror("Input error", "Factor must be a number")
            return
        c = self.poly.center()
        M = matrix_translate(-c[0], -c[1], -c[2]) @ matrix_scale(f,f,f) @ matrix_translate(c[0], c[1], c[2])
        self.poly.apply_matrix(M)
        self.draw()

    def apply_rotate_around_center_parallel(self):
        try:
            angle = math.radians(float(self.angle_axis_e.get()))
        except ValueError:
            messagebox.showerror("Input error", "Angle must be a number")
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
            messagebox.showerror("Input error", "Line coordinates/angle must be numbers")
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
        for z, f in depths:
            coords = []
            for idx in f.indices:
                x, y = pts_pix[idx]
                coords.extend([float(x), float(y)])
            self.canvas.create_polygon(coords, fill=self.face_fill, outline=self.edge_color, width=1)
			
def main():
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use('clam')
    except Exception:
        pass
    app = PolyhedronApp(root)
    root.mainloop()
	
if __name__ == "__main__":
    main()