#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox
from math import cos, sin, radians

def matMul(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

def matVec(m, v):
    x, y, w = v
    r0 = m[0][0]*x + m[0][1]*y + m[0][2]*w
    r1 = m[1][0]*x + m[1][1]*y + m[1][2]*w
    r2 = m[2][0]*x + m[2][1]*y + m[2][2]*w
    return (r0, r1, r2)

def translate(dx, dy):
    return [[1,0,dx],[0,1,dy],[0,0,1]]

def rotateDeg(angleDeg):
    a = radians(angleDeg)
    c, s = cos(a), sin(a)
    return [[c,-s,0],[s,c,0],[0,0,1]]

def scale(sx, sy):
    return [[sx,0,0],[0,sy,0],[0,0,1]]

def pointInPoly(pt, poly):
    x, y = pt
    inside = False
    for i in range(len(poly)):
        x1,y1 = poly[i]
        x2,y2 = poly[(i+1)%len(poly)]
        if ((y1>y)!=(y2>y)) and (x < (x2-x1)*(y-y1)/(y2-y1+1e-12)+x1):
            inside = not inside
    return inside

def distPointToSegment(px, py, x1, y1, x2, y2):
    vx, vy = x2-x1, y2-y1
    wx, wy = px-x1, py-y1
    c1 = vx*wx + vy*wy
    if c1 <= 0:
        return ((px-x1)**2+(py-y1)**2)**0.5
    c2 = vx*vx + vy*vy
    if c2 <= c1:
        return ((px-x2)**2+(py-y2)**2)**0.5
    b = c1/c2
    bx, by = x1 + b*vx, y1 + b*vy
    return ((px-bx)**2+(py-by)**2)**0.5

def polyCentroid(vertices):
    n = len(vertices)
    if n == 0: return (0,0)
    if n == 1: return vertices[0]
    if n == 2:
        (x1,y1),(x2,y2) = vertices
        return ((x1+x2)/2, (y1+y2)/2)
    A=Cx=Cy=0.0
    for i in range(n):
        x1,y1 = vertices[i]; x2,y2 = vertices[(i+1)%n]
        cross = x1*y2 - x2*y1
        A += cross; Cx += (x1+x2)*cross; Cy += (y1+y2)*cross
    if abs(A) < 1e-12:
        return (sum(x for x,_ in vertices)/n, sum(y for _,y in vertices)/n)
    A *= 0.5
    return (Cx/(6*A), Cy/(6*A))

class Polygon:
    def __init__(self, vertices):
        self.vertices = vertices[:]
        self.canvasIds = []
        self.selected = False
    def bbox(self):
        xs = [p[0] for p in self.vertices]; ys = [p[1] for p in self.vertices]
        return (min(xs), min(ys), max(xs), max(ys))
    def hitTest(self, x, y, tol=6):
        if len(self.vertices) >= 3 and pointInPoly((x,y), self.vertices): return True
        if len(self.vertices) == 1:
            (x1,y1) = self.vertices[0]
            return ((x-x1)**2 + (y-y1)**2)**0.5 <= tol
        m = len(self.vertices)
        for i in range(m if m<=2 else m):
            x1,y1 = self.vertices[i]; x2,y2 = self.vertices[(i+1)%m if m>1 else i]
            if distPointToSegment(x,y,x1,y1,x2,y2) <= tol: return True
        return False
    def applyMatrix(self, M):
        out = []
        for (x,y) in self.vertices:
            X,Y,W = matVec(M,(x,y,1))
            if abs(W) < 1e-12: W = 1.0
            out.append((X/W, Y/W))
        self.vertices = out

class App:
    def __init__(self, root):
        root.title("Polygons — Draw + Affine (Matrices)")
        self.root = root

        toolbar = tk.Frame(root)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        self.btnFinish = tk.Button(toolbar, text="Завершить полигон", command=self.finishPolygon)
        self.btnClear = tk.Button(toolbar, text="Очистить сцену", command=self.clearScene)
        self.btnFinish.pack(side=tk.LEFT, padx=4, pady=5)
        self.btnClear.pack(side=tk.LEFT, padx=4, pady=5)

        sep1 = tk.Label(toolbar, text="  |  "); sep1.pack(side=tk.LEFT)

        tk.Label(toolbar, text="dx:").pack(side=tk.LEFT)
        self.entDx = tk.Entry(toolbar, width=6); self.entDx.insert(0,"0"); self.entDx.pack(side=tk.LEFT)
        tk.Label(toolbar, text="dy:").pack(side=tk.LEFT)
        self.entDy = tk.Entry(toolbar, width=6); self.entDy.insert(0,"0"); self.entDy.pack(side=tk.LEFT)
        tk.Button(toolbar, text="Сместить", command=self.uiTranslate).pack(side=tk.LEFT, padx=4)

        sep2 = tk.Label(toolbar, text="  |  "); sep2.pack(side=tk.LEFT)

        tk.Label(toolbar, text="угол°:").pack(side=tk.LEFT)
        self.entAngle = tk.Entry(toolbar, width=6); self.entAngle.insert(0,"0"); self.entAngle.pack(side=tk.LEFT)
        self.btnPickRot = tk.Button(toolbar, text="Опорная точка", command=lambda:self.setPickMode('rotate'))
        self.btnPickRot.pack(side=tk.LEFT, padx=3)
        tk.Button(toolbar, text="Поворот от точки", command=self.rotateAboutPoint).pack(side=tk.LEFT, padx=3)
        tk.Button(toolbar, text="Поворот от центра", command=self.rotateAboutCenter).pack(side=tk.LEFT, padx=3)

        sep3 = tk.Label(toolbar, text="  |  "); sep3.pack(side=tk.LEFT)

        tk.Label(toolbar, text="sx:").pack(side=tk.LEFT)
        self.entSx = tk.Entry(toolbar, width=6); self.entSx.insert(0,"1"); self.entSx.pack(side=tk.LEFT)
        tk.Label(toolbar, text="sy:").pack(side=tk.LEFT)
        self.entSy = tk.Entry(toolbar, width=6); self.entSy.insert(0,"1"); self.entSy.pack(side=tk.LEFT)
        self.btnPickScale = tk.Button(toolbar, text="Опорная точка", command=lambda:self.setPickMode('scale'))
        self.btnPickScale.pack(side=tk.LEFT, padx=3)
        tk.Button(toolbar, text="Масштаб от точки", command=self.scaleAboutPoint).pack(side=tk.LEFT, padx=3)
        tk.Button(toolbar, text="Масштаб от центра", command=self.scaleAboutCenter).pack(side=tk.LEFT, padx=3)

        self.status = tk.Label(root, text="Готово", anchor="w")
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas = tk.Canvas(root, bg="white", width=1000, height=650)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.polygons = []
        self.currentVertices = []
        self.previewIds = []
        self.lastMouse = None
        self.selectedPoly = None
        self.pickMode = None
        self.pickedPoint = None

        self.canvas.bind("<Button-1>", self.onLeftClick)
        self.canvas.bind("<Double-Button-1>", self.onDoubleLeftClick)
        self.canvas.bind("<Motion>", self.onMouseMove)

        self.redraw()

    def parseFloat(self, entry, defaultValue):
        s = entry.get().strip().replace(',', '.')
        try:
            v = float(s)
        except:
            v = defaultValue
        entry.delete(0, tk.END)
        entry.insert(0, str(v))
        return v

    def redraw(self):
        self.canvas.delete("all")
        for poly in self.polygons:
            poly.canvasIds.clear()
            self.drawPolygon(poly.vertices, "#1f77b4")
            if poly.selected:
                x0,y0,x1,y1 = poly.bbox()
                self.canvas.create_rectangle(x0-6,y0-6,x1+6,y1+6, outline="#2ca02c", dash=(4,2), width=2)
        self.drawPreview()
        if self.pickedPoint is not None:
            x,y = self.pickedPoint
            self.canvas.create_oval(x-4,y-4,x+4,y+4, outline="#d62728", width=2)

    def drawPolygon(self, vertices, color="#1f77b4"):
        n = len(vertices)
        if n == 0: return
        if n == 1:
            x, y = vertices[0]
            r = 4
            self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline=color)
        elif n == 2:
            (x1, y1), (x2, y2) = vertices
            self.canvas.create_line(x1, y1, x2, y2, width=2, fill=color)
            for (x, y) in vertices:
                r = 3
                self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline=color)
        else:
            coords = [c for xy in vertices for c in xy]
            self.canvas.create_polygon(*coords, outline=color, fill="", width=2)
            for (x, y) in vertices:
                r = 3
                self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline=color)

    def drawPreview(self):
        for cid in self.previewIds:
            self.canvas.delete(cid)
        self.previewIds.clear()
        if not self.currentVertices:
            return
        color = "#ff7f0e"
        n = len(self.currentVertices)
        if n == 1:
            x, y = self.currentVertices[0]
            r = 4
            self.previewIds.append(self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline=color))
            if self.lastMouse is not None:
                x2, y2 = self.lastMouse
                self.previewIds.append(self.canvas.create_line(x, y, x2, y2, fill=color, dash=(4, 2), width=2))
        else:
            for i in range(n - 1):
                x1, y1 = self.currentVertices[i]
                x2, y2 = self.currentVertices[i + 1]
                self.previewIds.append(self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2))
            for (x, y) in self.currentVertices:
                r = 3
                self.previewIds.append(self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline=color))
            if self.lastMouse is not None:
                x1, y1 = self.currentVertices[-1]
                x2, y2 = self.lastMouse
                self.previewIds.append(self.canvas.create_line(x1, y1, x2, y2, fill=color, dash=(4, 2), width=2))

    def onLeftClick(self, event):
        x, y = event.x, event.y
        if self.pickMode in ('rotate','scale'):
            self.pickedPoint = (x,y)
            self.pickMode = None
            self.status.config(text=f"Опорная точка: ({x:.1f},{y:.1f})")
            self.redraw()
            return
        if self.currentVertices:
            self.currentVertices.append((x, y))
            self.redraw()
            return
        for poly in reversed(self.polygons):
            if poly.hitTest(x,y):
                self.selectPolygon(poly)
                self.redraw()
                return
        self.currentVertices = [(x, y)]
        self.redraw()

    def onDoubleLeftClick(self, event):
        self.finishPolygon()

    def onMouseMove(self, event):
        self.lastMouse = (event.x, event.y)
        self.drawPreview()

    def finishPolygon(self):
        if not self.currentVertices:
            messagebox.showinfo("Внимание", "Нет вершин для полигона.")
            return
        poly = Polygon(self.currentVertices)
        self.polygons.append(poly)
        self.currentVertices = []
        self.selectPolygon(poly)
        self.redraw()

    def clearScene(self):
        self.polygons.clear()
        self.currentVertices.clear()
        self.selectedPoly = None
        self.pickedPoint = None
        self.pickMode = None
        self.redraw()

    def selectPolygon(self, poly):
        if self.selectedPoly is not None:
            self.selectedPoly.selected = False
        self.selectedPoly = poly
        if poly is not None:
            poly.selected = True

    def getSelected(self):
        if self.selectedPoly is None:
            messagebox.showwarning("Нет выделения","Выберите полигон кликом.")
        return self.selectedPoly

    def uiTranslate(self):
        poly = self.getSelected()
        if not poly: return
        dx = self.parseFloat(self.entDx, 0.0)
        dy = self.parseFloat(self.entDy, 0.0)
        M = translate(dx,dy)
        poly.applyMatrix(M)
        self.redraw()

    def setPickMode(self, kind):
        self.pickMode = kind
        self.pickedPoint = None
        self.status.config(text="Кликните на канве для опорной точки")

    def rotateAboutPoint(self):
        poly = self.getSelected()
        if not poly: return
        ang = self.parseFloat(self.entAngle, 0.0)
        if self.pickedPoint is None:
            messagebox.showinfo("Требуется опорная точка","Нажмите 'Опорная точка' и кликните по канве.")
            return
        px,py = self.pickedPoint
        M = matMul(matMul(translate(px,py), rotateDeg(ang)), translate(-px,-py))
        poly.applyMatrix(M)
        self.redraw()

    def rotateAboutCenter(self):
        poly = self.getSelected()
        if not poly: return
        ang = self.parseFloat(self.entAngle, 0.0)
        cx,cy = polyCentroid(poly.vertices)
        M = matMul(matMul(translate(cx,cy), rotateDeg(ang)), translate(-cx,-cy))
        poly.applyMatrix(M)
        self.redraw()

    def scaleAboutPoint(self):
        poly = self.getSelected()
        if not poly: return
        sx = self.parseFloat(self.entSx, 1.0)
        sy = self.parseFloat(self.entSy, 1.0)
        if self.pickedPoint is None:
            messagebox.showinfo("Требуется опорная точка","Нажмите 'Опорная точка' и кликните по канве.")
            return
        px,py = self.pickedPoint
        M = matMul(matMul(translate(px,py), scale(sx,sy)), translate(-px,-py))
        poly.applyMatrix(M)
        self.redraw()

    def scaleAboutCenter(self):
        poly = self.getSelected()
        if not poly: return
        sx = self.parseFloat(self.entSx, 1.0)
        sy = self.parseFloat(self.entSy, 1.0)
        cx,cy = polyCentroid(poly.vertices)
        M = matMul(matMul(translate(cx,cy), scale(sx,sy)), translate(-cx,-cy))
        poly.applyMatrix(M)
        self.redraw()

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
