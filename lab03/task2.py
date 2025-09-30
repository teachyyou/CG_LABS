"""
task2_lines.py
Задание 2:
Рисование отрезка целочисленным алгоритмом Брезенхема и алгоритмом Ву.
Левый клик задает начало и конец отрезка (два клика). Переключатель выбирает алгоритм.
"""
import tkinter as tk
from PIL import Image, ImageTk
import math

W, H = 600, 700
BG = (255, 255, 255)

def pil_to_tk(img):
    return ImageTk.PhotoImage(img)

# ---------- Алгоритм Брезенхема ----------
def bresenham(img, x0, y0, x1, y1, color=(0,0,0)):
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    if dy <= dx:
        err = 2*dy - dx
        for _ in range(dx+1):
            if 0 <= x < img.width and 0 <= y < img.height:
                img.putpixel((x,y), color)
            if err > 0:
                y += sy
                err -= 2*dx
            x += sx
            err += 2*dy
    else:
        err = 2*dx - dy
        for _ in range(dy+1):
            if 0 <= x < img.width and 0 <= y < img.height:
                img.putpixel((x,y), color)
            if err > 0:
                x += sx
                err -= 2*dy
            y += sy
            err += 2*dx

# ---------- Алгоритм Ву ----------
def ipart(x): return int(math.floor(x))
def roundi(x): return ipart(x+0.5)
def fpart(x): return x - math.floor(x)
def rfpart(x): return 1 - fpart(x)

def wu_line(img, x0, y0, x1, y1, color=(0,0,0)):
    steep = abs(y1 - y0) > abs(x1 - x0)
    if steep:
        x0,y0 = y0,x0
        x1,y1 = y1,x1
    if x0 > x1:
        x0,x1 = x1,x0
        y0,y1 = y1,y0
    dx = x1 - x0
    dy = y1 - y0
    gradient = dy / dx if dx != 0 else 1

    # первый конец
    xend = roundi(x0)
    yend = y0 + gradient * (xend - x0)
    xgap = rfpart(x0 + 0.5)
    xpxl1 = xend
    ypxl1 = ipart(yend)
    if steep:
        plot(img, ypxl1,   xpxl1, multiply_color(color, rfpart(yend)*xgap))
        plot(img, ypxl1+1, xpxl1, multiply_color(color, fpart(yend)*xgap))
    else:
        plot(img, xpxl1, ypxl1,   multiply_color(color, rfpart(yend)*xgap))
        plot(img, xpxl1, ypxl1+1, multiply_color(color, fpart(yend)*xgap))
    intery = yend + gradient

    # второй конец
    xend = roundi(x1)
    yend = y1 + gradient * (xend - x1)
    xgap = fpart(x1 + 0.5)
    xpxl2 = xend
    ypxl2 = ipart(yend)
    if steep:
        plot(img, ypxl2,   xpxl2, multiply_color(color, rfpart(yend)*xgap))
        plot(img, ypxl2+1, xpxl2, multiply_color(color, fpart(yend)*xgap))
    else:
        plot(img, xpxl2, ypxl2,   multiply_color(color, rfpart(yend)*xgap))
        plot(img, xpxl2, ypxl2+1, multiply_color(color, fpart(yend)*xgap))

    # основной цикл
    if steep:
        for x in range(xpxl1+1, xpxl2):
            y = intery
            plot(img, ipart(y),   x, multiply_color(color, rfpart(y)))
            plot(img, ipart(y)+1, x, multiply_color(color, fpart(y)))
            intery += gradient
    else:
        for x in range(xpxl1+1, xpxl2):
            y = intery
            plot(img, x, ipart(y),   multiply_color(color, rfpart(y)))
            plot(img, x, ipart(y)+1, multiply_color(color, fpart(y)))
            intery += gradient

def multiply_color(color, alpha):
    r,g,b = color
    a = max(0,min(1,alpha))
    return (int(r*a + 255*(1-a)), int(g*a + 255*(1-a)), int(b*a + 255*(1-a)))

def plot(img, x, y, color):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((int(x), int(y)), color)


class App:
    def __init__(self, master):
        self.master = master
        master.title("Task2: Bresenham and Wu")
        self.canvas = tk.Canvas(master, width=W, height=H, bg='white')
        self.canvas.pack(side='left')
        self.img = Image.new('RGB', (W,H), BG)
        self.tkimg = pil_to_tk(self.img)
        self.canvas_img = self.canvas.create_image(0,0,anchor='nw',image=self.tkimg)

        ctrl = tk.Frame(master)
        ctrl.pack(side='right', fill='y')
        self.alg = 'bresenham'
        tk.Button(ctrl,text='Bresenham',command=self.set_bres).pack(fill='x')
        tk.Button(ctrl,text='Wu',command=self.set_wu).pack(fill='x')
        tk.Button(ctrl,text='Clear',command=self.clear).pack(fill='x')
        tk.Label(ctrl,text='Кликните дважды, чтобы нарисовать отрезок.').pack()

        self.p0 = None
        self.canvas.bind("<Button-1>", self.on_click)

    def set_bres(self): self.alg='bresenham'
    def set_wu(self): self.alg='wu'
    def clear(self):
        self.img.paste(BG, (0,0,W,H))
        self.update()

    def on_click(self, event):
        if self.p0 is None:
            self.p0 = (event.x, event.y)
        else:
            x0,y0 = self.p0
            x1,y1 = event.x, event.y
            if self.alg == 'bresenham':
                bresenham(self.img, x0,y0,x1,y1,(0,0,0))
            else:
                wu_line(self.img, x0,y0,x1,y1,(0,0,0))
            self.p0 = None
            self.update()

    def update(self):
        self.tkimg = pil_to_tk(self.img)
        self.canvas.itemconfigure(self.canvas_img, image=self.tkimg)
        self.master.update_idletasks()

if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()
