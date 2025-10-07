#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox

class Polygon:
    def __init__(self, vertices):
        self.vertices = vertices[:]
        self.canvasIds = []

class App:
    def __init__(self, root):
        root.title("Lab 4")
        self.root = root

        toolbar = tk.Frame(root)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        self.btnFinish = tk.Button(toolbar, text="Завершить полигон", command=self.finishPolygon)
        self.btnClear = tk.Button(toolbar, text="Очистить сцену", command=self.clearScene)

        self.btnFinish.pack(side=tk.LEFT, padx=5, pady=5)
        self.btnClear.pack(side=tk.LEFT, padx=5, pady=5)

        self.canvas = tk.Canvas(root, bg="white", width=1000, height=650)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.polygons = []
        self.currentVertices = []
        self.previewIds = []
        self.lastMouse = None

        self.canvas.bind("<Button-1>", self.onLeftClick)
        self.canvas.bind("<Double-Button-1>", self.onDoubleLeftClick)
        self.canvas.bind("<Motion>", self.onMouseMove)

        self.redraw()

    def redraw(self):
        self.canvas.delete("all")
        for poly in self.polygons:
            self.drawPolygon(poly.vertices, "#1f77b4")
        self.drawPreview()

    def drawPolygon(self, vertices, color="#1f77b4"):
        n = len(vertices)
        if n == 0:
            return
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
        if not self.currentVertices:
            self.currentVertices = [(x, y)]
        else:
            self.currentVertices.append((x, y))
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
        self.polygons.append(Polygon(self.currentVertices))
        self.currentVertices = []
        self.redraw()

    def clearScene(self):
        self.polygons.clear()
        self.currentVertices.clear()
        self.redraw()

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
