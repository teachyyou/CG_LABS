import math
import numpy as np
from PIL import Image

class Face:
    def __init__(self, indices, tex_coords=None):
        self.indices = list(indices)
        self.tex_coords = tex_coords if tex_coords else []

class Polyhedron:
    def __init__(self, vertices: np.ndarray, faces: list, color="#5a9bd8", name="obj", vertex_normals=None, tex_coords=None):
        self.V = np.array(vertices, dtype=float)
        self.faces = [Face(f.indices if hasattr(f, 'indices') else f, f.tex_coords if hasattr(f, 'tex_coords') else None) for f in faces]
        self.color = color
        self.name = name
        self.vertex_normals = vertex_normals if vertex_normals is not None else self._compute_vertex_normals()
        self.tex_coords = tex_coords if tex_coords is not None else self._compute_default_tex_coords()

    def _compute_vertex_normals(self):
        normals = np.zeros_like(self.V)
        for face in self.faces:
            if len(face.indices) < 3:
                continue
            v0, v1, v2 = self.V[face.indices[0]], self.V[face.indices[1]], self.V[face.indices[2]]
            normal = np.cross(v1 - v0, v2 - v0)
            nrm = np.linalg.norm(normal)
            if nrm > 0:
                normal = normal / nrm
            for idx in face.indices:
                normals[idx] += normal
        for i in range(len(normals)):
            nrm = np.linalg.norm(normals[i])
            if nrm > 0:
                normals[i] = normals[i] / nrm
            else:
                normals[i] = np.array([0.0, 0.0, 1.0])
        return normals

    def _compute_default_tex_coords(self):
        tex_coords = []
        for vertex in self.V:
            x, y, _ = vertex
            u = (x + 1) / 2
            v = (y + 1) / 2
            tex_coords.append([u, v])
        return np.array(tex_coords)

    def copy(self):
        q = Polyhedron(self.V.copy(), [Face(f.indices[:], f.tex_coords[:] if f.tex_coords else None) for f in self.faces], color=self.color, name=self.name, vertex_normals=self.vertex_normals.copy() if self.vertex_normals is not None else None, tex_coords=self.tex_coords.copy() if self.tex_coords is not None else None)
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
        if self.vertex_normals is not None:
            rot_matrix = M[:3, :3]
            for i in range(len(self.vertex_normals)):
                self.vertex_normals[i] = rot_matrix @ self.vertex_normals[i]
                nrm = np.linalg.norm(self.vertex_normals[i])
                if nrm > 0:
                    self.vertex_normals[i] /= nrm

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
    nrm = np.linalg.norm(axis)
    if nrm == 0: return np.eye(4)
    x, y, z = axis / nrm
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
    else: R = matrix_rotate_z(angle_rad)
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
    verts = np.array([[1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1]], dtype=float)
    verts = verts / np.linalg.norm(verts[0])
    faces = [[0, 1, 2], [0, 3, 1], [0, 2, 3], [1, 3, 2]]
    tex_coords = [[0.5, 1.0], [0.0, 0.0], [1.0, 0.0], [0.5, 0.5]]
    poly_faces = []
    for face in faces:
        poly_face = Face(face)
        poly_face.tex_coords = [tex_coords[i] for i in face]
        poly_faces.append(poly_face)
    return Polyhedron(verts, poly_faces, color=color, name="Тетраэдр")

def make_cube(color="#5a9bd8"):
    s = 1.0
    verts = np.array([[x, y, z] for x in (-s, s) for y in (-s, s) for z in (-s, s)], dtype=float)
    faces = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 2, 6, 4], [1, 5, 7, 3], [0, 4, 5, 1], [2, 3, 7, 6]]
    cube_tex_coords = [
        [0, 1], [1, 1], [1, 0], [0, 0],
        [0, 1], [1, 1], [1, 0], [0, 0],
        [0, 1], [1, 1], [1, 0], [0, 0],
        [0, 1], [1, 1], [1, 0], [0, 0],
        [0, 1], [1, 1], [1, 0], [0, 0],
        [0, 1], [1, 1], [1, 0], [0, 0]
    ]
    poly_faces = []
    for i, face in enumerate(faces):
        poly_face = Face(face)
        poly_face.tex_coords = [cube_tex_coords[i * 4 + j] for j in range(len(face))]
        poly_faces.append(poly_face)
    return Polyhedron(verts, poly_faces, color=color, name="Куб")

def make_octahedron(color="#5a9bd8"):
    verts = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]], dtype=float)
    faces = [[0, 2, 4], [2, 1, 4], [1, 3, 4], [3, 0, 4], [2, 0, 5], [1, 2, 5], [3, 1, 5], [0, 3, 5]]
    tex_coords = [[0.5, 1.0], [0.0, 0.5], [1.0, 0.5], [0.5, 0.0], [0.5, 0.5], [0.5, 0.5]]
    poly_faces = []
    for face in faces:
        poly_face = Face(face)
        poly_face.tex_coords = [tex_coords[i] for i in face]
        poly_faces.append(poly_face)
    return Polyhedron(verts, poly_faces, color=color, name="Октаэдр")

def make_icosahedron(color="#5a9bd8"):
    t = (1.0 + math.sqrt(5.0)) / 2.0
    verts = np.array([
        [-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0],
        [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
        [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]
    ], dtype=float)
    verts /= np.max(np.linalg.norm(verts, axis=1))
    faces = [
        [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
        [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
        [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
    ]
    tex_coords = []
    for vertex in verts:
        x, y, z = vertex
        u = math.atan2(x, z) / (2 * math.pi) + 0.5
        v = math.asin(y) / math.pi + 0.5
        tex_coords.append([u, v])
    poly_faces = []
    for face in faces:
        poly_face = Face(face)
        poly_face.tex_coords = [tex_coords[i] for i in face]
        poly_faces.append(poly_face)
    return Polyhedron(verts, poly_faces, color=color, name="Икосаэдр")

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
    tex_coords = []
    for vertex in centers:
        x, y, z = vertex
        u = math.atan2(x, z) / (2 * math.pi) + 0.5
        v = math.asin(y) / math.pi + 0.5
        tex_coords.append([u, v])
    poly_faces = []
    for face in dfaces:
        poly_face = Face(face)
        poly_face.tex_coords = [tex_coords[i] for i in face]
        poly_faces.append(poly_face)
    return Polyhedron(centers, poly_faces, color=color, name="Додекаэдр")

def compute_face_normal_basic(V, idxs):
    if len(idxs) < 3: return np.array([0.0, 0.0, 0.0])
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

def look_at(camera_pos, target, up=np.array([0, 1, 0], dtype=float)):
    f = target - camera_pos
    fn = f / (np.linalg.norm(f) + 1e-12)
    s = np.cross(fn, up); s = s / (np.linalg.norm(s) + 1e-12)
    u = np.cross(s, fn)
    M = np.eye(4)
    M[0, :3] = s
    M[1, :3] = u
    M[2, :3] = -fn
    T = np.eye(4)
    T[:3, 3] = -camera_pos
    return M @ T

class Lighting:
    def __init__(self):
        self.light_pos = np.array([2.0, 2.0, 5.0], dtype=float)
        self.light_color = np.array([1.0, 1.0, 1.0], dtype=float)
        self.ambient_intensity = 0.3
        self.diffuse_intensity = 0.7
        self.specular_intensity = 0.5
        self.shininess = 32.0

    def lambert_shading(self, normal, view_dir=None):
        light_dir = self.light_pos
        light_dir = light_dir / np.linalg.norm(light_dir)
        diffuse = max(0.0, np.dot(normal, light_dir))
        ambient = self.ambient_intensity
        final_intensity = ambient + self.diffuse_intensity * diffuse
        return np.clip(final_intensity, 0.0, 1.0)
        
    def phong_shading(self, normal, view_dir, position):
        light_dir = self.light_pos - position
        light_dir = light_dir / np.linalg.norm(light_dir)
        diffuse = max(0.0, np.dot(normal, light_dir))
        reflect_dir = 2 * np.dot(normal, light_dir) * normal - light_dir
        reflect_dir = reflect_dir / (np.linalg.norm(reflect_dir) + 1e-12)
        specular = max(0.0, np.dot(view_dir, reflect_dir))
        specular = self.specular_intensity * (specular ** self.shininess)
        ambient = self.ambient_intensity
        final_intensity = ambient + self.diffuse_intensity * diffuse + specular
        return np.clip(final_intensity, 0.0, 1.0)
