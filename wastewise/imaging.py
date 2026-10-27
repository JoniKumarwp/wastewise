from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError
from .config import COLORS, MAX_FILE_BYTES, MAX_IMAGE_PIXELS

def load_image(data: bytes):
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("Choose an image smaller than 20 MB.")
    try:
        with Image.open(BytesIO(data)) as source:
            if source.width * source.height > MAX_IMAGE_PIXELS:
                raise ValueError("Choose an image with at most 24 megapixels.")
            return ImageOps.exif_transpose(source).convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("This file is not a readable JPG, PNG or WebP image.") from exc

def png_bytes(image):
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()

def _font(size):
    candidates = [Path(__file__).resolve().parents[1]/"assets"/"DejaVuSans.ttf",
                  Path("C:/Windows/Fonts/arial.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
    for p in candidates:
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default(size=size)

def annotate(image, rows, shape="Rectangle", show_score=True):
    output = image.copy()
    draw = ImageDraw.Draw(output)
    size = max(11, min(20, round(min(image.size)/65)))
    font = _font(size)
    line = max(2, round(min(image.size)/240))
    for row in rows:
        color = COLORS.get(row["category"], COLORS["Needs review"])
        x1, y1, x2, y2 = row["box"]
        if shape == "Ellipse":
            draw.ellipse((x1,y1,x2,y2), outline=color, width=line)
        else:
            draw.rectangle((x1,y1,x2,y2), outline=color, width=line)
    # Draw labels after every outline, so later outlines cannot cross the text.
    # Choose nearby positions that reduce overlap with labels already placed.
    occupied=[]
    def overlap(a,b):
        return max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
    for number,row in enumerate(rows,1):
        color=COLORS.get(row["category"],COLORS["Needs review"])
        x1,y1,x2,y2=row["box"]
        title=f'{number}. {row["name"].split(" / ")[0]}'
        second=row["category"]+(f' · {row["score"]:.2f}' if show_score else "")
        while draw.textlength(title,font=font)+12>image.width and len(title)>12:
            title=title[:-5]+"..."
        tw=round(max(draw.textlength(title,font=font),draw.textlength(second,font=font)))+12
        th=2*size+12
        positions=[(x1,y1-th-2),(x1,y2+2),(x2+3,y1),(x1-tw-3,y1),(x1+2,y1+2)]
        for shift in [th,-th,2*th,-2*th,3*th,-3*th]:
            positions.extend([(x1,y1-th-2+shift),(x2+3,y1+shift)])
        candidates=[]
        for px,py in positions:
            tx=max(0,min(px,image.width-tw));ty=max(0,min(py,image.height-th))
            rect=(tx,ty,tx+tw,ty+th)
            cost=100*sum(overlap(rect,r) for r in occupied)+abs(tx-x1)+abs(ty-y1)
            candidates.append((cost,rect))
        _,rect=min(candidates,key=lambda pair:pair[0]);occupied.append(rect)
        tx,ty,_,_=rect
        if abs(tx-x1)+abs(ty-y1)>th+5:
            draw.line([(x1,y1),(max(tx,min(x1,tx+tw)),max(ty,min(y1,ty+th)))],fill=color,width=1)
        draw.rounded_rectangle(rect,radius=3,fill=color)
        draw.text((tx+6,ty+3),title,fill="white",font=font,anchor="lt")
        draw.text((tx+6,ty+size+7),second,fill="white",font=font,anchor="lt")
    return output
