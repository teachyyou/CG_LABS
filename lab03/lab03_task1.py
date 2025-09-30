"""
task1_fill.py
Задание 1:
1a) Рекурсивный алгоритм заливки на основе серий пикселов (scanline fill).
1b) Рекурсивный алгоритм заливки на основе серий пикселов рисунком из файла (pattern).
1c) Выделение границы связной области (Moore-Neighbor tracing).

Инструкция по использованию в окне программы.
"""
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import sys
sys.setrecursionlimit(10000)

W, H = 600, 700
BG = (255,255,255)

def pil_to_tk(img):
    return ImageTk.PhotoImage(img)

class App:
    def __init__(self, master):
        self.master = master
        master.title("Task1: Fill & Boundary (draw shape with mouse)")
        self.canvas = tk.Canvas(master, width=W, height=H, bg='white')
        self.canvas.pack(side='left')
        self.img = Image.new('RGB', (W,H), BG)
        self.draw = ImageDraw.Draw(self.img)
        self.tkimg = pil_to_tk(self.img)
        self.canvas_img = self.canvas.create_image(0,0,anchor='nw',image=self.tkimg)
        self.drawing = False
        self.last = None
        self.boundary_color = (0,0,0)
        self.fill_color = (255,0,0)
        self.pattern = None

        ctrl = tk.Frame(master)
        ctrl.pack(side='right', fill='y')
        tk.Label(ctrl, text="Инструменты").pack()
        tk.Button(ctrl, text="Выбрать цвет заливки", command=self.choose_color).pack(fill='x')
        tk.Button(ctrl, text="Загрузить паттерн (image)", command=self.load_pattern).pack(fill='x')
        tk.Button(ctrl, text="Режим рисования границы", command=self.set_draw_mode).pack(fill='x')
        tk.Button(ctrl, text="Режим заливки (цвет)", command=self.set_fill_mode).pack(fill='x')
        tk.Button(ctrl, text="Режим заливки (паттерн)", command=self.set_pattern_mode).pack(fill='x')
        tk.Button(ctrl, text="Выделение границы (click on boundary)", command=self.set_boundary_mode).pack(fill='x')
        tk.Button(ctrl, text="Очистить", command=self.clear).pack(fill='x')
        tk.Label(ctrl, text="Инструкция: рисуйте границу левой кнопкой. Закройте контур.\nЗатем выберите режим заливки и кликните внутри области.").pack()
        self.mode = 'draw'  # draw, fillcolor, fillpattern, boundary
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def set_draw_mode(self): self.mode='draw'
    def set_fill_mode(self): self.mode='fillcolor'
    def set_pattern_mode(self): 
        if self.pattern is None:
            messagebox.showinfo("Pattern not loaded","Load a pattern first.")
            return
        self.mode='fillpattern'
    def set_boundary_mode(self): self.mode='boundary'
    def choose_color(self):
        c = colorchooser.askcolor()[0]
        if c:
            self.fill_color = tuple(map(int,c))

    def load_pattern(self):
        path = filedialog.askopenfilename(filetypes=[("Image","*.png;*.jpg;*.bmp;*.gif")])
        if not path:
            return
        p = Image.open(path).convert('RGB')
        self.pattern = p
        messagebox.showinfo("Pattern loaded", f"Pattern size: {p.size}")

    def clear(self):
        self.img.paste(BG, (0,0,W,H))
        self.draw = ImageDraw.Draw(self.img)
        self.update_canvas()

    def on_click(self,event):
        x,y = event.x, event.y
        if self.mode == 'draw':
            self.drawing = True
            self.last = (x,y)
            self.draw.ellipse((x-1,y-1,x+1,y+1), fill=self.boundary_color)
            self.update_canvas()
        elif self.mode == 'fillcolor':
            target = self.img.getpixel((x,y))
            if target == self.fill_color:
                return
            self.scanline_fill_recursive(x,y,target,self.fill_color)
            self.update_canvas()
        elif self.mode == 'fillpattern':
            target = self.img.getpixel((x,y))
            if self.pattern is None:
                return
            self.scanline_fill_recursive_pattern(x,y,target,self.pattern)
            self.update_canvas()
        elif self.mode == 'boundary':
            px = self.img.getpixel((x,y))
            if px != self.boundary_color:
                messagebox.showinfo("Info","Click on a boundary pixel (current boundary color black).")
                return
            contour = self.moore_trace((x,y), self.boundary_color)
            for (cx,cy) in contour:
                if 0<=cx<W and 0<=cy<H:
                    self.img.putpixel((cx,cy),(255,0,0))
            self.update_canvas()

    def on_drag(self,event):
        if self.mode!='draw' or not self.drawing: return
        x,y = event.x, event.y
        x0,y0 = self.last
        self.draw.line((x0,y0,x,y), fill=self.boundary_color, width=1)
        self.last=(x,y)
        self.update_canvas()
    def on_release(self,event):
        if self.mode=='draw':
            self.drawing=False
            self.last=None

    def scanline_fill_recursive(self, x, y, target_color, new_color):
        W,H = self.img.size
        try:
            if x<0 or x>=W or y<0 or y>=H: return
            if self.img.getpixel((x,y)) != target_color: return
            xl = x
            while xl>=0 and self.img.getpixel((xl,y))==target_color:
                xl-=1
            xl+=1
            xr = x
            while xr<W and self.img.getpixel((xr,y))==target_color:
                xr+=1
            xr-=1
            for xi in range(xl,xr+1):
                self.img.putpixel((xi,y), new_color)
            for xi in range(xl,xr+1):
                if y-1>=0 and self.img.getpixel((xi,y-1))==target_color:
                    self.scanline_fill_recursive(xi,y-1,target_color,new_color)
                if y+1<H and self.img.getpixel((xi,y+1))==target_color:
                    self.scanline_fill_recursive(xi,y+1,target_color,new_color)
        except RecursionError:
            self.scanline_fill_iterative(x,y,target_color,new_color)

    def scanline_fill_iterative(self,xs,ys,target_color,new_color):
        W,H = self.img.size
        stack = [(xs,ys)]
        while stack:
            x,y = stack.pop()
            if not (0<=x<W and 0<=y<H): continue
            if self.img.getpixel((x,y))!=target_color: continue
            xl = x
            while xl>=0 and self.img.getpixel((xl,y))==target_color:
                xl-=1
            xl+=1
            xr = x
            while xr<W and self.img.getpixel((xr,y))==target_color:
                xr+=1
            xr-=1
            for xi in range(xl,xr+1):
                self.img.putpixel((xi,y), new_color)
            for xi in range(xl,xr+1):
                if y-1>=0 and self.img.getpixel((xi,y-1))==target_color:
                    stack.append((xi,y-1))
                if y+1<H and self.img.getpixel((xi,y+1))==target_color:
                    stack.append((xi,y+1))

    def scanline_fill_recursive_pattern(self, x, y, target_color, pattern_img):
        W,H = self.img.size
        pw,ph = pattern_img.size
        def get_pattern_color(px,py):
            return pattern_img.getpixel((px%pw, py%ph))
        try:
            if x<0 or x>=W or y<0 or y>=H: return
            if self.img.getpixel((x,y)) != target_color: return
            xl = x
            while xl>=0 and self.img.getpixel((xl,y))==target_color:
                xl-=1
            xl+=1
            xr = x
            while xr<W and self.img.getpixel((xr,y))==target_color:
                xr+=1
            xr-=1
            for xi in range(xl,xr+1):
                self.img.putpixel((xi,y), get_pattern_color(xi,y))
            for xi in range(xl,xr+1):
                if y-1>=0 and self.img.getpixel((xi,y-1))==target_color:
                    self.scanline_fill_recursive_pattern(xi,y-1,target_color,pattern_img)
                if y+1<H and self.img.getpixel((xi,y+1))==target_color:
                    self.scanline_fill_recursive_pattern(xi,y+1,target_color,pattern_img)
        except RecursionError:
            stack=[(x,y)]
            while stack:
                x,y=stack.pop()
                if not (0<=x<W and 0<=y<H): continue
                if self.img.getpixel((x,y))!=target_color: continue
                xl = x
                while xl>=0 and self.img.getpixel((xl,y))==target_color:
                    xl-=1
                xl+=1
                xr = x
                while xr<W and self.img.getpixel((xr,y))==target_color:
                    xr+=1
                xr-=1
                for xi in range(xl,xr+1):
                    self.img.putpixel((xi,y), get_pattern_color(xi,y))
                for xi in range(xl,xr+1):
                    if y-1>=0 and self.img.getpixel((xi,y-1))==target_color:
                        stack.append((xi,y-1))
                    if y+1<H and self.img.getpixel((xi,y+1))==target_color:
                        stack.append((xi,y+1))

    def moore_trace(self, start, border_color):
        W,H = self.img.size
        dirs = [(-1,0),(-1,-1),(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1)]
        x0,y0 = start
        contour = []
        b = (x0, y0+1)
        curr = (x0,y0)
        while True:
            contour.append(curr)
            cx,cy = curr
            try:
                i = dirs.index((b[0]-cx, b[1]-cy))
            except ValueError:
                i = 0
            found = False
            for k in range(8):
                ni = (i+1+k)%8
                nx = cx + dirs[ni][0]
                ny = cy + dirs[ni][1]
                if 0<=nx<W and 0<=ny<H and self.img.getpixel((nx,ny))==border_color:
                    b = (cx + dirs[(ni-1)%8][0], cy + dirs[(ni-1)%8][1])
                    curr = (nx,ny)
                    found = True
                    break
            if not found: break
            if curr == start: break
            if len(contour) > 100000: break
        return contour

    def update_canvas(self):
        self.tkimg = pil_to_tk(self.img)
        self.canvas.itemconfigure(self.canvas_img, image=self.tkimg)
        self.master.update_idletasks()

if __name__=='__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()
