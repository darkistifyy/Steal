import binascii
import textwrap
from io import BytesIO

import numpy as np
import scipy.cluster
import scipy.cluster.vq
from PIL import Image, ImageDraw, ImageFont


def caption_image(image_file, caption, font="impact.ttf"):
    """Captions an image.

    Args:
            image_file: A BytesIO object containing the image file.
            caption: The caption text.
            font: The font to use for the caption.

    Returns:
            A BytesIO object containing the captioned image.
    """

    my_bytes = BytesIO(image_file)
    my_bytes.seek(0)
    img = Image.open(my_bytes)
    draw = ImageDraw.Draw(img)

    font_size = int(img.width / 16)
    font = ImageFont.truetype("impact.ttf", font_size)

    caption = textwrap.fill(text=caption, width=img.width / (font_size / 2))

    caption_w, caption_h = img.size

    draw.text(
        ((img.width - caption_w) / 2, (img.height - caption_h) / 8),  # position
        caption,  # text
        (255, 255, 255),  # color
        font=font,  # font
        stroke_width=2,  # text outline width
        stroke_fill=(0, 0, 0),
    )  # text outline color

    with BytesIO() as img_bytes:
        img.save(img_bytes, format=img.format)
        return img_bytes.getvalue()


def compress_image(img):
    mybytes = BytesIO(img)
    mybytes.seek(0)
    img = Image.open(mybytes)
    with BytesIO() as img_bytes:
        img = img.save(
            img_bytes, save_all=True, format=img.format, quality=15, optimize=True
        )
        return img_bytes.getvalue()


NUM_CLUSTERS = 5


def dom_color(img):
    my_bytes = BytesIO(img)
    my_bytes.seek(0)
    im = Image.open(my_bytes)

    im = im.convert("RGBA")
    im = im.resize((150, 150))

    ar = np.asarray(im)
    shape = ar.shape

    mask = ar[:, :, 3] > 0
    ar = ar[mask]

    ar = ar[:, :3].astype(float)

    codes, dist = scipy.cluster.vq.kmeans(ar, NUM_CLUSTERS)

    vecs, dist = scipy.cluster.vq.vq(ar, codes)
    counts, bins = np.histogram(vecs, len(codes))

    index_max = np.argmax(counts)
    peak = codes[index_max]
    colour = binascii.hexlify(bytearray(int(c) for c in peak)).decode("ascii")
    return colour
