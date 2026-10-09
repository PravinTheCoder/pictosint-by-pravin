#!/usr/bin/env python3
"""
PICTOSINT by Pravin — independent GEO + SATELLITE ENGINE v2.1

Fixes:
- Does NOT depend on Geo-Sleuth.
- Does NOT send OCR garbage to geocoding.
- Uses optional CLIP zero-shot visual landmark scoring.
- Uses OCR only as supporting evidence.
- Automatically resolves coordinates for strong landmark matches.
- Automatically downloads satellite imagery and builds a sheet.
- HTML report explicitly shows why candidates were/weren't generated.
"""

import argparse, hashlib, json, math, re, sys
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

try:
    from PIL import Image, ImageDraw, ImageOps
except ImportError:
    print("[!] Install dependencies first: pip install -r requirements.txt")
    sys.exit(1)

from pyfiglet import Figlet

BANNER = r"""
██████╗ ██╗ ██████╗████████╗ ██████╗ ███████╗██╗███╗   ██╗████████╗
██╔══██╗██║██╔════╝╚══██╔══╝██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝
██████╔╝██║██║         ██║   ██║   ██║ ███████╗██║██╔██╗ ██║   ██║
██╔═══╝ ██║██║         ██║   ██║   ██║ ╚════██║██║██║╚██╗██║   ██║
██║      ██║╚██████╗   ██║   ╚██████╔╝ ███████║██║██║ ╚████║   ██║
╚═╝      ╚═╝ ╚═════╝   ╚═╝    ╚═════╝   ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝

                 by pravinthehacker

       PICTOSINT - GEO + SATELLITE ENGINE

       LinkedIn: linkedin.com/in/pravin-s-575102252
         GitHub:   github.com/PravinTheCoder
"""
     

KNOWN = {
    "Taj Mahal": ("Taj Mahal, Agra, Uttar Pradesh, India", 27.175144, 78.042142),
    "Big Ben": ("Big Ben, Westminster, London, United Kingdom", 51.500704, -0.124572),
    "Westminster Bridge": ("Westminster Bridge, London, United Kingdom", 51.500854, -0.121785),
    "Eiffel Tower": ("Eiffel Tower, Paris, France", 48.858370, 2.294481),
    "India Gate": ("India Gate, New Delhi, India", 28.612900, 77.229500),
    "Gateway of India": ("Gateway of India, Mumbai, India", 18.922000, 72.834700),
    "Charminar": ("Charminar, Hyderabad, India", 17.361600, 78.474700),
    "Chennai Central": ("Chennai Central Railway Station, Chennai, India", 13.082700, 80.270700),
}

VISUAL_LABELS = [
    "a photograph of the Taj Mahal in Agra India",
    "a photograph of Big Ben in London England",
    "a photograph of Westminster Bridge in London England",
    "a photograph of the Eiffel Tower in Paris France",
    "a photograph of India Gate in New Delhi India",
    "a photograph of the Gateway of India in Mumbai India",
    "a photograph of Charminar in Hyderabad India",
    "a photograph of Chennai Central Railway Station in Chennai India",
    "an ordinary street in Chennai India",
    "an ordinary street in London England",
    "an ordinary street in Agra India",
    "a generic landscape",
]

LABEL_TO_PLACE = {
    VISUAL_LABELS[0]: "Taj Mahal",
    VISUAL_LABELS[1]: "Big Ben",
    VISUAL_LABELS[2]: "Westminster Bridge",
    VISUAL_LABELS[3]: "Eiffel Tower",
    VISUAL_LABELS[4]: "India Gate",
    VISUAL_LABELS[5]: "Gateway of India",
    VISUAL_LABELS[6]: "Charminar",
    VISUAL_LABELS[7]: "Chennai Central",
}

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1024*1024), b""):
            h.update(b)
    return h.hexdigest()

def plausible_text(s):
    s = re.sub(r"\s+", " ", s.strip())
    if len(s) < 3 or len(s) > 100:
        return False
    alnum = sum(c.isalnum() for c in s)
    weird = sum(not(c.isalnum() or c in " -'.,/&()") for c in s)
    if alnum < 3 or weird > max(2, len(s)//4):
        return False
    if re.search(r"(.)\1{3,}", s.lower()):
        return False
    return True

def ocr(image):
    try:
        import pytesseract
    except ImportError:
        return []
    w, h = image.size
    scales = [3, 5] if max(w, h) < 1200 else [2, 3]
    found = []
    for scale in scales:
        im = image.resize((w*scale, h*scale), Image.Resampling.LANCZOS)
        im = ImageOps.autocontrast(im.convert("L"))
        for psm in (6, 11):
            d = pytesseract.image_to_data(
                im, config=f"--psm {psm}",
                output_type=pytesseract.Output.DICT
            )
            for i, raw in enumerate(d["text"]):
                s = re.sub(r"\s+", " ", raw or "").strip()
                try: conf = float(d["conf"][i])
                except Exception: conf = -1
                if conf >= 50 and plausible_text(s):
                    found.append((s, conf))
    out, seen = [], set()
    for s, c in sorted(found, key=lambda x: -x[1]):
        k = s.lower()
        if k not in seen:
            seen.add(k)
            out.append((s, c))
    return out[:40]

def clip_detect(image_path):
    """
    Optional visual landmark detector.
    Uses CLIP zero-shot classification. First run may download a model.
    If unavailable, the rest of PICTOSINT still runs.
    """
    try:
        from transformers import CLIPProcessor, CLIPModel
        import torch
    except Exception as e:
        return [], f"CLIP unavailable: {e}"

    try:
        model_name = "openai/clip-vit-base-patch32"
        processor = CLIPProcessor.from_pretrained(model_name)
        model = CLIPModel.from_pretrained(model_name)
        image = Image.open(image_path).convert("RGB")
        inputs = processor(text=VISUAL_LABELS, images=image,
                           return_tensors="pt", padding=True)
        with torch.no_grad():
            out = model(**inputs)
        probs = out.logits_per_image.softmax(dim=1)[0].tolist()
        ranked = sorted(zip(VISUAL_LABELS, probs), key=lambda x: -x[1])
        return ranked[:6], None
    except Exception as e:
        return [], f"CLIP failed: {e}"

def nominatim(q, limit=5):
    u = "https://nominatim.openstreetmap.org/search?format=jsonv2&limit=%d&q=%s" % (
        limit, quote(q))
    try:
        req = Request(u, headers={"User-Agent": "PICTOSINT-by-Pravin/2.1"})
        with urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"    [!] Geocoder failed: {e}")
        return []

def ll2px(lat, lon, z):
    n = 2**z
    x = (lon+180)/360*n
    y = (1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n
    return x*256, y*256

def tile_url(x,y,z):
    return f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

def tile(x,y,z,out):
    if out.exists() and out.stat().st_size > 1000:
        return True
    try:
        req = Request(tile_url(x,y,z), headers={"User-Agent":"PICTOSINT-by-Pravin/2.1"})
        with urlopen(req, timeout=20) as r:
            b = r.read()
        if len(b) < 1000: return False
        out.write_bytes(b)
        return True
    except Exception:
        return False

def satellite(lat, lon, out, zoom=18, size=768):
    cache = out.parent/"tile-cache"
    cache.mkdir(parents=True, exist_ok=True)
    gx, gy = ll2px(lat, lon, zoom)
    x0, y0 = gx-size/2, gy-size/2
    canvas = Image.new("RGB",(size,size),"gray")
    ok=0
    for tx in range(math.floor(x0/256), math.floor((x0+size)/256)+1):
        for ty in range(math.floor(y0/256), math.floor((y0+size)/256)+1):
            p=cache/f"{zoom}_{tx}_{ty}.jpg"
            if tile(tx,ty,zoom,p):
                try:
                    im=Image.open(p).convert("RGB")
                    canvas.paste(im,(int(tx*256-x0),int(ty*256-y0)))
                    ok+=1
                except Exception: pass
    d=ImageDraw.Draw(canvas)
    c=size//2
    d.line((c-20,c,c+20,c),fill="red",width=3)
    d.line((c,c-20,c,c+20),fill="red",width=3)
    canvas.save(out,quality=92)
    return ok

def sheet(items,out):
    if not items: return None
    size=420; cols=min(3,len(items)); rows=math.ceil(len(items)/cols)
    s=Image.new("RGB",(cols*size,rows*(size+35)),"black")
    d=ImageDraw.Draw(s)
    for i,c in enumerate(items):
        im=Image.open(c["satellite"]).convert("RGB")
        im.thumbnail((size,size))
        x=(i%cols)*size+(size-im.width)//2
        y=(i//cols)*(size+35)
        s.paste(im,(x,y))
        d.text(((i%cols)*size+7,y+size+7),
               f"#{i+1} {c['name'][:45]}",fill="white")
    s.save(out,quality=92)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--zoom",type=int,default=18)
    ap.add_argument("--max-candidates",type=int,default=10)
    ap.add_argument("--no-clip",action="store_true")
    a=ap.parse_args()

    src=Path(a.image).expanduser().resolve()
    if not src.exists():
        print("[!] Image not found:",src); return 2

    digest=sha256(src)
    case=Path.cwd()/f"pictosint-case-{digest[:12]}"
    for d in ("ocr","satellite","reverse"):
        (case/d).mkdir(parents=True,exist_ok=True)

    print(BANNER)
    print("[+] Input:",src)
    print("[+] Case: ",case)
    print("[+] SHA256:",digest)

    im=Image.open(src).convert("RGB")
    o=ocr(im)
    print(f"[+] Reliable OCR clues: {len(o)}")
    for t,c in o[:12]:
        print(f"    - {t} (confidence={c:.0f})")

    visual=[]
    clip_error=None
    if not a.no_clip:
        print("[+] Visual landmark analysis: CLIP zero-shot")
        visual,clip_error=clip_detect(src)
        if visual:
            for label,p in visual:
                print(f"    - {label}: {p*100:.2f}%")
        else:
            print("    [!] No visual model result:",clip_error)

    candidates=[]
    # Strong visual result: only promote a known place when it clearly wins
    if visual:
        best_label,best_prob=visual[0]
        place=LABEL_TO_PLACE.get(best_label)
        second=visual[1][1] if len(visual)>1 else 0
        if place and best_prob >= 0.35 and best_prob >= second*1.25:
            label,lat,lon=KNOWN[place]
            candidates.append({
                "name":label,"lat":lat,"lon":lon,
                "score":round(best_prob*100,2),
                "source":"CLIP visual landmark match",
                "visual_label":best_label
            })

    # OCR supports, but cannot create dozens of junk queries.
    allocr=" ".join(t for t,_ in o).lower()
    for key, (label,lat,lon) in KNOWN.items():
        if key.lower() in allocr and not any(abs(c["lat"]-lat)<.001 for c in candidates):
            candidates.append({
                "name":label,"lat":lat,"lon":lon,
                "score":80,"source":"OCR landmark match"
            })

    # Explicitly useful geographic OCR only.
    for t,c in o:
        if len(t)<5 or len(t)>80: continue
        if not re.search(r"[A-Za-z]{4,}",t): continue
        if len(t.split())==1: continue
        # Only query multiword OCR, never fragments.
        results=nominatim(t,3)
        for r in results:
            try:
                candidates.append({
                    "name":r["display_name"],
                    "lat":float(r["lat"]),
                    "lon":float(r["lon"]),
                    "score":min(60,c),
                    "source":"Nominatim from filtered OCR"
                })
            except Exception: pass

    # Deduplicate and rank.
    uniq=[]; seen=set()
    for c in sorted(candidates,key=lambda x:-x["score"]):
        k=(round(c["lat"],4),round(c["lon"],4))
        if k not in seen:
            seen.add(k); uniq.append(c)
    candidates=uniq[:a.max_candidates]

    print(f"[+] Geographic candidates: {len(candidates)}")
    if not candidates:
        print("[!] No candidates were produced.")
        print("[i] This is now an honest failure instead of inventing locations.")
        print("[i] Install CLIP dependencies and rerun for visual landmark detection:")
        print("    pip install -r requirements.txt")
    else:
        for i,c in enumerate(candidates,1):
            print(f"    {i:02d}. {c['name']} [{c['lat']:.6f}, {c['lon']:.6f}]")

    sats=[]
    for i,c in enumerate(candidates,1):
        out=case/"satellite"/f"candidate_{i:02d}.jpg"
        print(f"[+] Satellite {i}/{len(candidates)}: {c['name'][:65]}")
        n=satellite(c["lat"],c["lon"],out,a.zoom)
        c["satellite"]=str(out); c["satellite_tiles"]=n
        sats.append(c)
        print(f"    [+] {out} ({n} tiles)")

    sh=sheet(sats,case/"satellite"/"satellite_candidates.jpg")

    report={
        "tool":"PICTOSINT by Pravin","version":"2.1",
        "source_image":str(src),"source_sha256":digest,
        "ocr":[{"text":t,"confidence":c} for t,c in o],
        "visual_candidates":[{"label":x,"probability":p} for x,p in visual],
        "clip_error":clip_error,
        "candidates":candidates,
        "satellite_sheet":str(sh) if sh else None,
        "status":"satellite_generated" if sats else "no_candidate",
        "verification_policy":"Visual and geographic matches are hypotheses. Satellite geometry must be manually verified."
    }
    (case/"pictosint-report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")

    html=["<!doctype html><html><head><meta charset='utf-8'>",
          "<title>PICTOSINT by Pravin</title>",
          "<style>body{font-family:Arial;background:#181a20;color:#eee;margin:30px}"
          ".card{background:#242731;padding:15px;margin:15px 0;border-radius:8px}"
          "img{max-width:768px;width:100%;height:auto}.muted{color:#aaa}</style></head><body>",
          "<h1>PICTOSINT by Pravin</h1>",
          f"<p>Image: {src.name}</p>",
          "<h2>Visual analysis</h2>"]
    if visual:
        html.append("<ul>")
        for lab,p in visual:
            html.append(f"<li>{lab}: {p*100:.2f}%</li>")
        html.append("</ul>")
    else:
        html.append("<p class='muted'>No visual-model result.</p>")
    html.append("<h2>Satellite candidates</h2>")
    if not candidates:
        html.append("<div class='card'><b>No candidate was generated.</b><br>"
                    "This is intentional: the engine will not invent a location.</div>")
    for i,c in enumerate(candidates,1):
        html.append("<div class='card'>")
        html.append(f"<h3>#{i} {c['name']}</h3>")
        html.append(f"<p>{c['lat']}, {c['lon']} — {c['source']}</p>")
        html.append(f"<img src='satellite/{Path(c['satellite']).name}'>")
        html.append("</div>")
    html.append("</body></html>")
    (case/"report.html").write_text("".join(html),encoding="utf-8")

    print(f"[+] Satellite sheet: {sh or 'not generated'}")
    print(f"[+] HTML report: {case/'report.html'}")
    print(f"[+] JSON report: {case/'pictosint-report.json'}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
