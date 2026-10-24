import sys
from PIL import Image, ImageDraw, ImageFilter
S = 180; dest = sys.argv[1]
img = Image.new("RGBA", (S, S), (21, 26, 44, 255))
# foil pack body
pack = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(pack)
x0, x1, y0, y1 = 48, 132, 22, 158
grad = Image.new("RGBA", (x1 - x0, y1 - y0))
for y in range(y1 - y0):
    t = y / (y1 - y0)
    c = (int(47 + 120 * t), int(107 + 40 * (1 - t)), int(255 - 60 * t), 255)
    ImageDraw.Draw(grad).line([(0, y), (x1 - x0, y)], fill=c)
mask = Image.new("L", (x1 - x0, y1 - y0), 0); md = ImageDraw.Draw(mask)
md.rounded_rectangle((0, 8, x1 - x0, y1 - y0 - 8), radius=6, fill=255)
for i in range(0, x1 - x0, 7):  # crimped top and bottom edges
    md.polygon([(i, 8), (i + 3.5, 0), (i + 7, 8)], fill=255)
    md.polygon([(i, y1 - y0 - 8), (i + 3.5, y1 - y0), (i + 7, y1 - y0 - 8)], fill=255)
pack.paste(grad, (x0, y0), mask)
sh = pack.split()[3].filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * .6))
shadow = Image.new("RGBA", (S, S), (0, 0, 0, 255)); shadow.putalpha(sh)
img = Image.alpha_composite(img, shadow)
img = Image.alpha_composite(img, pack)
d = ImageDraw.Draw(img)
d.line([(x0 + 4, y0 + 18), (x1 - 4, y0 + 18)], fill=(255, 255, 255, 90), width=2)
d.line([(x0 + 4, y1 - 18), (x1 - 4, y1 - 18)], fill=(255, 255, 255, 90), width=2)
cx, cy, r = 90, 90, 26  # Poké Ball
d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, 255))
d.pieslice((cx - r, cy - r, cx + r, cy + r), 180, 360, fill=(226, 61, 55, 255))
d.rectangle((cx - r, cy - 3, cx + r, cy + 3), fill=(21, 26, 44, 255))
d.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=(21, 26, 44, 255)); d.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=(255, 255, 255, 255))
img.convert("RGB").save(dest, optimize=True); print("ok")
