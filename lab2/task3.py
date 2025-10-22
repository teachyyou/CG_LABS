from pathlib import Path
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog


def rgbToHsv(arr01):
    r, g, b = arr01[..., 0], arr01[..., 1], arr01[..., 2]
    maxc = np.max(arr01, axis=-1)
    minc = np.min(arr01, axis=-1)
    v = maxc
    c = maxc - minc
    s = np.where(maxc == 0, 0, c / np.where(maxc == 0, 1, maxc))
    h = np.zeros_like(v)
    mask = c != 0
    rc = np.where(mask, (maxc - r) / c, 0)
    gc = np.where(mask, (maxc - g) / c, 0)
    bc = np.where(mask, (maxc - b) / c, 0)
    condR = (maxc == r) & mask
    condG = (maxc == g) & mask
    condB = (maxc == b) & mask
    h = np.where(condR, (bc - gc) / 6.0, h)
    h = np.where(condG, (2.0 + rc - bc) / 6.0, h)
    h = np.where(condB, (4.0 + gc - rc) / 6.0, h)
    h = np.mod(h, 1.0)
    return np.stack([h, s, v], axis=-1)


def hsvToRgb(hsv):
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    i = np.floor(h * 6.0).astype(int)
    f = h * 6.0 - i
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)
    i = np.mod(i, 6)
    r = np.choose(i, [v, q, p, p, t, v])
    g = np.choose(i, [t, v, v, q, p, p])
    b = np.choose(i, [p, p, t, v, v, q])
    return np.stack([r, g, b], axis=-1)


def toUint8(arr01):
    return np.clip(arr01 * 255.0 + 0.5, 0, 255).astype(np.uint8)


class HSVEditor:
    def __init__(self, master, imagePath):
        self.master = master
        self.master.title("HSV Editor")

        self.imgRgb = Image.open(imagePath).convert("RGB")
        self.arr01 = np.asarray(self.imgRgb).astype(np.float32) / 255.0
        self.hsvBase = rgbToHsv(self.arr01)

        self.canvas = tk.Label(self.master)
        self.canvas.pack()

        self.hueSlider = tk.Scale(master, from_=-180, to=180, orient="horizontal", label="Hue shift (°)", command=self.updateImage)
        self.hueSlider.pack(fill="x")

        self.satSlider = tk.Scale(master, from_=0, to=200, orient="horizontal", label="Saturation (%)", command=self.updateImage)
        self.satSlider.set(100)
        self.satSlider.pack(fill="x")

        self.valSlider = tk.Scale(master, from_=0, to=200, orient="horizontal", label="Value (%)", command=self.updateImage)
        self.valSlider.set(100)
        self.valSlider.pack(fill="x")

        self.saveButton = tk.Button(master, text="Save", command=self.saveImage)
        self.saveButton.pack()

        self.currentImg = None
        self.updateImage()

    def updateImage(self, _=None):
        hShift = self.hueSlider.get() / 360.0
        sScale = self.satSlider.get() / 100.0
        vScale = self.valSlider.get() / 100.0

        h = np.mod(self.hsvBase[..., 0] + hShift, 1.0)
        s = np.clip(self.hsvBase[..., 1] * sScale, 0.0, 1.0)
        v = np.clip(self.hsvBase[..., 2] * vScale, 0.0, 1.0)
        adj = np.stack([h, s, v], axis=-1)
        rgb = hsvToRgb(adj)
        u8 = toUint8(rgb)

        self.currentImg = Image.fromarray(u8)
        preview = self.currentImg.resize((400, 400))
        self.tkImg = ImageTk.PhotoImage(preview)
        self.canvas.configure(image=self.tkImg)

    def saveImage(self):
        savePath = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if savePath:
            self.currentImg.save(savePath)
            print("Saved:", savePath)


def runTask3():
    root = tk.Tk()
    app = HSVEditor(root, "1.png")
    root.mainloop()


if __name__ == "__main__":
    runTask3()
