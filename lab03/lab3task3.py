import tkinter as tk
from tkinter import colorchooser
from PIL import Image, ImageTk

W, H = 600, 700
BG = (255,255,255)

def pil_to_tk(img):
    return ImageTk.PhotoImage(img)

def edge_function(a, b, c):
    return (c[0]-a[0])*(b[1]-a[1]) - (c[1]-a[1])*(b[0]-a[0])

def barycentric_rasterize(img, A, B, C, colorA, colorB, colorC):
    minx = max(min(A[0],B[0],C[0]), 0)
    maxx = min(max(A[0],B[0],C[0]), img.width-1)
    miny = max(min(A[1],B[1],C[1]), 0)
    maxy = min(max(A[1],B[1],C[1]), img.height-1)
    area = edge_function(A,B,C)
    if area == 0: return
    for y in range(int(miny), int(maxy)+1):
        for x in range(int(minx), int(maxx)+1):
            P = (x+0.5, y+0.5)
            w0 = edge_function(B,C,P)
            w1 = edge_function(C,A,P)
            w2 = edge_function(A,B,P)
            if (w0>=0 and w1>=0 and w2>=0) or (w0<=0 and w1<=0 and w2<=0):
                a = w0/area
                b = w1/area
                c = w2/area
                r = int(a*colorA[0] + b*colorB[0] + c*colorC[0])
                g = int(a*colorA[1] + b*colorB[1] + c*colorC[1])
                bcol = int(a*colorA[2] + b*colorB[2] + c*colorC[2])
                img.putpixel((x,y),(r,g,bcol))

class App:
    def __init__(self, master):
        self.master = master
        master.title("Task3: Triangle gradient fill")
        self.canvas = tk.Canvas(master, width=W, height=H, bg='white')
        self.canvas.pack(side='left')
        self.img = Image.new('RGB',(W,H),BG)
        self.tkimg = pil_to_tk(self.img)
        self.canvas_img = self.canvas.create_image(0,0,anchor='nw',image=self.tkimg)

        ctrl = tk.Frame(master)
        ctrl.pack(side='right', fill='y')
        tk.Button(ctrl,text='Clear',command=self.clear).pack(fill='x')
        tk.Label(ctrl,text='Кликните три раза, выбирая цвет каждой вершины.').pack()

        self.verts = []
        self.colors = []
        self.canvas.bind("<Button-1>", self.on_click)

    def clear(self):
        self.verts = []
        self.colors = []
        self.img.paste(BG,(0,0,W,H))
        self.update()

    def on_click(self, event):
        col = colorchooser.askcolor()[0]
        if not col: return
        col = tuple(map(int,col))
        self.verts.append((event.x,event.y))
        self.colors.append(col)
        x,y = event.x, event.y
        for dx in (-2,-1,0,1,2):
            for dy in (-2,-1,0,1,2):
                nx,ny = x+dx, y+dy
                if 0<=nx<self.img.width and 0<=ny<self.img.height:
                    self.img.putpixel((nx,ny), col)
        if len(self.verts) == 3:
            A,B,C = self.verts
            barycentric_rasterize(self.img, A,B,C, self.colors[0], self.colors[1], self.colors[2])
        self.update()

    def update(self):
        self.tkimg = pil_to_tk(self.img)
        self.canvas.itemconfigure(self.canvas_img, image=self.tkimg)
        self.master.update_idletasks()

if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()
