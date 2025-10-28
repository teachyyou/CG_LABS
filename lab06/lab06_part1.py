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

if __name__ == "__main__":
    main()