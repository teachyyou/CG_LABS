from pathlib import Path
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt


def loadImage(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def rgbToGrayNtsc(arr01: np.ndarray) -> np.ndarray:
    R, G, B = arr01[..., 0], arr01[..., 1], arr01[..., 2]
    return 0.299 * R + 0.587 * G + 0.114 * B


def rgbToGraySrgb(arr01: np.ndarray) -> np.ndarray:
    R, G, B = arr01[..., 0], arr01[..., 1], arr01[..., 2]
    return 0.2126 * R + 0.7152 * G + 0.0722 * B


def toUint8(gray01: np.ndarray) -> np.ndarray:
    return np.clip(gray01 * 255.0 + 0.5, 0, 255).astype(np.uint8)


def saveHistogram(grayU8: np.ndarray, title: str, outPath: Path) -> None:
    data = grayU8.ravel()
    plt.figure()
    plt.hist(data, bins=256, range=(0, 255))
    plt.title(title)
    plt.xlabel("Intensity (0-255)")
    plt.ylabel("Pixel count")
    plt.tight_layout()
    plt.savefig(outPath, dpi=150)
    plt.close()


def main():
    inputImagePath = Path("1.png")
    outputDir = Path("out")
    outputDir.mkdir(parents=True, exist_ok=True)

    imgRgb = loadImage(inputImagePath)
    arr01 = np.asarray(imgRgb).astype(np.float32) / 255.0

    grayNtsc = toUint8(rgbToGrayNtsc(arr01))
    graySrgb = toUint8(rgbToGraySrgb(arr01))

    imgNtsc = Image.fromarray(grayNtsc)
    imgSrgb = Image.fromarray(graySrgb)

    diffArray = np.abs(grayNtsc.astype(np.int16) - graySrgb.astype(np.int16)).astype(np.uint8)
    imgDiff = Image.fromarray(diffArray)

    fileNtsc = outputDir / "grayscale_ntsc.png"
    fileSrgb = outputDir / "grayscale_srgb.png"
    fileDiff = outputDir / "grayscale_difference.png"

    imgNtsc.save(fileNtsc)
    imgSrgb.save(fileSrgb)
    imgDiff.save(fileDiff)

    fileHistNtsc = outputDir / "histogram_ntsc.png"
    fileHistSrgb = outputDir / "histogram_srgb.png"

    saveHistogram(grayNtsc, "Histogram: Grayscale NTSC", fileHistNtsc)
    saveHistogram(graySrgb, "Histogram: Grayscale sRGB", fileHistSrgb)

    print("Файлы сохранены:")
    print(" -", fileNtsc)
    print(" -", fileSrgb)
    print(" -", fileDiff)
    print(" -", fileHistNtsc)
    print(" -", fileHistSrgb)


if __name__ == "__main__":
    main()
