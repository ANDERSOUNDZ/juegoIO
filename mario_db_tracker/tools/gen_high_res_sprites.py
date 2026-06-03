#!/usr/bin/env python3
"""
gen_high_res_sprites.py — Genera sprites PNG de alta resolución
y los sube a la API de PIXO Therapy como type: "image".

Reemplaza los sprites pixelmap actuales (16-20px) con versiones
PNG renderizadas a 32-64px con más detalle, sombras y colores.

Uso:
    python tools/gen_high_res_sprites.py
    python tools/gen_high_res_sprites.py --base-url http://localhost:5000
"""

import argparse
import base64
import io
import json
import sys
import urllib.request
import http.cookiejar
from PIL import Image, ImageDraw


# ─── COLOR PALETTE ────────────────────────────────────────────

C = {
    "mario_red":     (220, 32, 32),
    "mario_blue":    (32, 32, 248),
    "mario_skin":    (248, 216, 160),
    "mario_brown":   (104, 64, 32),
    "mario_white":   (248, 248, 248),
    "mario_black":   (0, 0, 0),
    "mario_yellow":  (248, 184, 0),

    "shell_green":   (48, 176, 48),
    "shell_dark":    (24, 128, 24),
    "shell_light":   (88, 216, 88),
    "shell_yellow":  (216, 216, 0),
    "shell_skin":    (248, 216, 160),

    "brick_body":    (200, 75, 49),
    "brick_shadow":  (122, 46, 29),
    "brick_light":   (232, 122, 90),
    "brick_mortar":  (46, 26, 10),

    "gold":          (255, 210, 63),
    "gold_light":    (255, 243, 160),
    "gold_shadow":   (184, 131, 10),

    "bg_dark":       (26, 10, 46),
    "pipe_green":    (48, 176, 48),
    "pipe_dark":     (24, 128, 24),
}


def _px(img, x, y, color):
    """Set a pixel with optional anti-aliased edge."""
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), color)


def _fill(img, x1, y1, x2, y2, color):
    """Fill a rectangle."""
    draw = ImageDraw.Draw(img)
    draw.rectangle([x1, y1, x2, y2], fill=color)


def _circle(img, cx, cy, r, color):
    draw = ImageDraw.Draw(img)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)


def _hollow_rect(img, x, y, w, h, color):
    draw = ImageDraw.Draw(img)
    draw.rectangle([x, y, x + w - 1, y + h - 1], outline=color)


# ─── SPRITE GENERATORS ───────────────────────────────────────

def gen_mario_64():
    """Generate 64x64 Mario spritesheet with 4 frames."""
    W, H, F = 64, 64, 4
    sheet = Image.new("RGBA", (W * F, H), (0, 0, 0, 0))

    for frame in range(F):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))

        # Body (centered in 64-wide canvas)
        ox, oy = 22, 4  # offset to center the 20-wide character in 64-wide canvas

        # Hat
        _fill(img, ox + 4, oy, ox + 16, oy + 4, C["mario_red"])
        _fill(img, ox + 3, oy + 4, ox + 17, oy + 8, C["mario_red"])
        _fill(img, ox + 2, oy + 8, ox + 18, oy + 12, C["mario_red"])
        _fill(img, ox + 1, oy + 12, ox + 19, oy + 14, C["mario_red"])

        # Face
        _fill(img, ox + 2, oy + 14, ox + 18, oy + 16, C["mario_skin"])
        _fill(img, ox + 3, oy + 16, ox + 17, oy + 18, C["mario_skin"])
        # Eyes
        _fill(img, ox + 5, oy + 16, ox + 7, oy + 17, C["mario_white"])
        _fill(img, ox + 13, oy + 16, ox + 15, oy + 17, C["mario_white"])
        _px(img, ox + 6, oy + 16, C["mario_black"])
        _px(img, ox + 14, oy + 16, C["mario_black"])
        # Mustache
        _fill(img, ox + 4, oy + 18, ox + 16, oy + 19, C["mario_black"])
        _fill(img, ox + 3, oy + 19, ox + 17, oy + 20, C["mario_black"])

        # Shirt (red)
        _fill(img, ox + 3, oy + 20, ox + 17, oy + 22, C["mario_red"])
        _fill(img, ox + 2, oy + 22, ox + 18, oy + 26, C["mario_red"])
        # Buttons (yellow)
        _px(img, ox + 7, oy + 23, C["mario_yellow"])
        _px(img, ox + 13, oy + 23, C["mario_yellow"])

        # Overalls (blue)
        _fill(img, ox + 1, oy + 26, ox + 19, oy + 28, C["mario_blue"])
        _fill(img, ox + 2, oy + 28, ox + 18, oy + 30, C["mario_blue"])
        _fill(img, ox + 2, oy + 30, ox + 18, oy + 40, C["mario_blue"])
        # Suspenders (blue)
        _fill(img, ox + 4, oy + 22, ox + 6, oy + 28, C["mario_blue"])
        _fill(img, ox + 14, oy + 22, ox + 16, oy + 28, C["mario_blue"])

        # Legs + shoes depend on frame
        if frame == 0:  # Standing
            _fill(img, ox + 5, oy + 40, ox + 7, oy + 50, C["mario_brown"])
            _fill(img, ox + 13, oy + 40, ox + 15, oy + 50, C["mario_brown"])
            _fill(img, ox + 4, oy + 50, ox + 8, oy + 54, C["mario_brown"])
            _fill(img, ox + 12, oy + 50, ox + 16, oy + 54, C["mario_brown"])
            # Shoe detail
            _fill(img, ox + 4, oy + 52, ox + 8, oy + 54, C["mario_black"])
            _fill(img, ox + 12, oy + 52, ox + 16, oy + 54, C["mario_black"])
        elif frame == 1:  # Walk (left leg forward)
            _fill(img, ox + 2, oy + 40, ox + 4, oy + 50, C["mario_brown"])
            _fill(img, ox + 14, oy + 40, ox + 16, oy + 48, C["mario_brown"])
            _fill(img, ox + 1, oy + 50, ox + 5, oy + 54, C["mario_brown"])
            _fill(img, ox + 13, oy + 48, ox + 17, oy + 52, C["mario_brown"])
            _px(img, ox + 0, oy + 53, C["mario_black"])
            _px(img, ox + 1, oy + 54, C["mario_black"])
        elif frame == 2:  # Walk (right leg forward)
            _fill(img, ox + 4, oy + 40, ox + 6, oy + 48, C["mario_brown"])
            _fill(img, ox + 14, oy + 40, ox + 18, oy + 50, C["mario_brown"])
            _fill(img, ox + 3, oy + 48, ox + 7, oy + 52, C["mario_brown"])
            _fill(img, ox + 15, oy + 50, ox + 19, oy + 54, C["mario_brown"])
        else:  # Jump
            _fill(img, ox + 3, oy + 40, ox + 6, oy + 46, C["mario_brown"])
            _fill(img, ox + 14, oy + 40, ox + 17, oy + 46, C["mario_brown"])
            _fill(img, ox + 2, oy + 46, ox + 7, oy + 50, C["mario_brown"])
            _fill(img, ox + 13, oy + 46, ox + 18, oy + 50, C["mario_brown"])
            # Arms up
            _fill(img, ox + 0, oy + 24, ox + 2, oy + 26, C["mario_skin"])
            _fill(img, ox + 18, oy + 24, ox + 20, oy + 26, C["mario_skin"])

        # Outline (black border)
        for y in range(H):
            for x in range(W):
                c = img.getpixel((x, y))
                if c[3] > 0:  # non-transparent
                    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < W and 0 <= ny < H:
                            nc = img.getpixel((nx, ny))
                            if nc[3] == 0:
                                _px(img, nx, ny, (0, 0, 0, 64))

        sheet.paste(img, (frame * W, 0))

    return sheet


def gen_platform_32():
    """Generate 32x32 brick platform tile."""
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    # Brick pattern
    draw = ImageDraw.Draw(img)
    rows = [
        (0, 4), (4, 8), (8, 12), (12, 16),
        (16, 20), (20, 24), (24, 28), (28, 32),
    ]
    for ri, (y1, y2) in enumerate(rows):
        if ri % 2 == 0:
            bricks = [(0, 15), (17, 32)]
        else:
            bricks = [(8, 24)]
        for bx1, bx2 in bricks:
            bw = bx2 - bx1
            bh = y2 - y1
            draw.rectangle([bx1 + 1, y1 + 1, bx2 - 1, y2 - 1], fill=C["brick_body"])
            draw.rectangle([bx1, y1, bx1 + 1, y2], fill=C["brick_light"])
            draw.rectangle([bx1, y1, bx2, y1 + 1], fill=C["brick_light"])
            draw.rectangle([bx2 - 1, y1, bx2, y2], fill=C["brick_shadow"])
            draw.rectangle([bx1, y2 - 1, bx2, y2], fill=C["brick_shadow"])
    draw.rectangle([1, 3, 14, 6], fill=C["brick_shadow"])  # center detail
    # Mortar lines
    for y in range(0, 33, 4):
        draw.line([(0, y), (32, y)], fill=C["brick_mortar"], width=1)
    draw.line([(16, 0), (16, 4)], fill=C["brick_mortar"], width=1)
    draw.line([(8, 4), (8, 8)], fill=C["brick_mortar"], width=1)
    draw.line([(24, 4), (24, 8)], fill=C["brick_mortar"], width=1)
    draw.line([(0, 8), (16, 8)], fill=C["brick_mortar"], width=1)
    return img


def gen_coin_32():
    """Generate 32x32 spinning coin with 6 frames."""
    W, H, F = 32, 32, 6
    sheet = Image.new("RGBA", (W * F, H), (0, 0, 0, 0))
    for frame in range(F):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cx, cy = 16, 16
        # Width varies by frame (spinning effect)
        widths = [6, 10, 18, 24, 18, 10]
        rw = widths[frame]
        # Draw coin
        _fill(img, cx - rw // 2, cy - 11, cx + rw // 2, cy - 8, C["gold_light"])
        _fill(img, cx - rw // 2, cy - 8, cx + rw // 2, cy + 8, C["gold"])
        _fill(img, cx - rw // 2, cy + 8, cx + rw // 2, cy + 11, C["gold_shadow"])
        # Highlight
        if rw > 10:
            _fill(img, cx - rw // 2 + 2, cy - 6, cx - rw // 2 + 4, cy + 2, C["gold_light"])
        if rw > 16:
            _fill(img, cx - 2, cy - 2, cx + 2, cy + 2, C["gold_shadow"])
        # Outline
        _hollow_rect(img, cx - rw // 2, cy - 11, rw, 22, C["gold_shadow"])
        sheet.paste(img, (frame * W, 0))
    return sheet


def gen_shellcreeper_32():
    """Generate 32x32 Shellcreeper with 2 frames."""
    W, H, F = 32, 32, 2
    sheet = Image.new("RGBA", (W * F, H), (0, 0, 0, 0))
    for frame in range(F):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        # Shell (green dome)
        _fill(img, 6, 4, 26, 6, C["shell_light"])
        _fill(img, 5, 6, 27, 8, C["shell_green"])
        _fill(img, 4, 8, 28, 10, C["shell_green"])
        _fill(img, 5, 10, 27, 18, C["shell_green"])
        _fill(img, 6, 18, 26, 20, C["shell_dark"])
        # Shell center line
        _fill(img, 14, 6, 18, 20, C["shell_dark"])
        # Face
        _fill(img, 10, 10, 13, 12, C["shell_skin"])
        _fill(img, 19, 10, 22, 12, C["shell_skin"])
        # Eyes
        _px(img, 11, 10, C["mario_white"])
        _px(img, 12, 10, C["mario_black"])
        _px(img, 20, 10, C["mario_white"])
        _px(img, 21, 10, C["mario_black"])
        # Feet
        foot_y = 22
        if frame == 0:
            _fill(img, 8, foot_y, 12, foot_y + 4, C["shell_yellow"])
            _fill(img, 20, foot_y, 24, foot_y + 4, C["shell_yellow"])
        else:
            _fill(img, 6, foot_y, 10, foot_y + 4, C["shell_yellow"])
            _fill(img, 22, foot_y, 26, foot_y + 4, C["shell_yellow"])
        # Outline
        _hollow_rect(img, 5, 4, 22, 18, C["shell_dark"])
        sheet.paste(img, (frame * W, 0))
    return sheet


def gen_bg_64():
    """Generate 64x64 background tile with pipes."""
    img = Image.new("RGBA", (64, 64), C["bg_dark"])
    draw = ImageDraw.Draw(img)
    # Stars
    import random
    random.seed(42)
    for _ in range(20):
        sx = random.randint(0, 63)
        sy = random.randint(0, 63)
        bright = random.randint(180, 255)
        img.putpixel((sx, sy), (bright, bright, bright, 255))
        if random.random() > 0.7:
            img.putpixel((sx + 1, sy), (bright, bright, bright, 200))
            img.putpixel((sx, sy + 1), (bright, bright, bright, 200))
    # Pipe
    _fill(img, 8, 48, 24, 64, C["pipe_green"])
    _fill(img, 6, 44, 26, 48, C["pipe_green"])
    _fill(img, 8, 44, 10, 48, C["pipe_light"] if "pipe_light" in C else C["pipe_green"])
    _fill(img, 6, 44, 8, 48, C["pipe_dark"])
    _fill(img, 24, 44, 26, 48, C["pipe_dark"])
    _fill(img, 8, 48, 10, 64, C["pipe_dark"])
    # Second pipe
    _fill(img, 40, 52, 56, 64, C["pipe_green"])
    _fill(img, 38, 48, 58, 52, C["pipe_green"])
    _fill(img, 40, 48, 42, 52, C["pipe_dark"])
    _fill(img, 38, 48, 40, 52, C["pipe_green"])
    _fill(img, 56, 48, 58, 52, C["pipe_dark"])
    return img


# ─── UPLOAD ───────────────────────────────────────────────────

def img_to_png_data_uri(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


class ApiClient:
    def __init__(self, base_url, email, password):
        self.base_url = base_url.rstrip("/")
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj)
        )
        self._req("POST", "/api/auth/login", {"email": email, "password": password})
        print(f"  Sesion iniciada como {email}")

    def _req(self, method, path, body=None):
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode() if body else None
        r = urllib.request.Request(url, data=data, method=method,
                                   headers={"Content-Type": "application/json"} if body else {})
        try:
            resp = self.opener.open(r)
            return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            err = e.read().decode(errors="replace")
            print(f"  ERROR {method} {path}: {err}")
            sys.exit(1)

    def get_sprites(self):
        return self._req("GET", "/api/sprites")

    def create_sprite(self, name, category, image_url, width, height, frame_count=1):
        data = {
            "name": name, "category": category, "type": "image",
            "width": width, "height": height,
            "image_url": image_url, "frame_count": frame_count,
        }
        r = self._req("POST", "/api/sprites", data)
        print(f"  Creado sprite '{name}' -> ID {r['id']}")
        return r["id"]


# ─── MAIN ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Genera y sube sprites HD a PIXO Therapy")
    parser.add_argument("--base-url", default="http://localhost:5000")
    parser.add_argument("--email", default="admin@pixo.com")
    parser.add_argument("--password", default="admin")
    args = parser.parse_args()

    print("=" * 60)
    print("  PIXO Therapy — Generacion de Sprites HD")
    print("=" * 60)
    print()

    client = ApiClient(args.base_url, args.email, args.password)

    # Generate all sprites
    print("Generando sprites...")
    sprites = [
        ("Mario HD", "player", *gen_mario_64().size, 4, gen_mario_64()),
        ("Plataforma HD", "platform", 32, 32, 1, gen_platform_32()),
        ("Moneda HD", "coin", 32, 32, 6, gen_coin_32()),
        ("Shellcreeper HD", "enemy", 32, 32, 2, gen_shellcreeper_32()),
        ("Fondo HD", "background", 64, 64, 1, gen_bg_64()),
    ]

    # Check existing
    existing = client.get_sprites()
    existing_names = {s["name"] for s in existing}

    sprite_ids = {}
    for name, cat, w, h, fc, img in sprites:
        if name in existing_names:
            for s in existing:
                if s["name"] == name:
                    sprite_ids[cat] = s["id"]
                    print(f"  '{name}' ya existe (ID {s['id']}), reutilizando")
                    break
        else:
            print(f"  Generando {name}...")
            uri = img_to_png_data_uri(img)
            sid = client.create_sprite(name, cat, uri, w, h, fc)
            sprite_ids[cat] = sid

    print()

    # Update Mario game config with HD sprites
    existing_games = client._req("GET", "/api/games")
    mario_game = next((g for g in existing_games if g["name"] == "Mario Bros Terapeutico"), None)
    if mario_game:
        gid = mario_game["id"]
        # Fetch full config separately (list endpoint omits config)
        config = client._req("GET", f"/api/games/{gid}").get("config", {})
        config["sprites"] = {
            "player": {"sprite_id": sprite_ids.get("player")},
            "platform": {"sprite_id": sprite_ids.get("platform")},
            "coin": {"sprite_id": sprite_ids.get("coin")},
            "enemy": {"sprite_id": sprite_ids.get("enemy")},
            "background": {"sprite_id": sprite_ids.get("background")},
        }
        client._req("PUT", f"/api/games/{gid}", {"config": config})
        print(f"Juego Mario Bros actualizado con sprites HD (ID {gid})")
    else:
        print("Juego Mario Bros no encontrado. Creandolo...")
        # Re-run create_mario_game to recreate the game
        import subprocess, sys
        subprocess.run([sys.executable, "tools/create_mario_game.py",
                       "--base-url", args.base_url,
                       "--email", args.email,
                       "--password", args.password])

    # Also update the default game
    def_game = next((g for g in existing_games if g["name"] == "Plataformas Terapeuticas"), None)
    if def_game:
        gid = def_game["id"]
        config = client._req("GET", f"/api/games/{gid}").get("config", {})
        if not config.get("sprites"):
            config["sprites"] = {}
        config["sprites"]["player"] = {"sprite_id": sprite_ids.get("player")}
        config["sprites"]["platform"] = {"sprite_id": sprite_ids.get("platform")}
        config["sprites"]["coin"] = {"sprite_id": sprite_ids.get("coin")}
        config["sprites"]["enemy"] = {"sprite_id": sprite_ids.get("enemy")}
        client._req("PUT", f"/api/games/{gid}", {"config": config})
        print(f"Juego Plataformas Terapeuticas actualizado con sprites HD (ID {gid})")

    print()
    print("=" * 60)
    print("  Sprites HD creados exitosamente!")
    print(f"  IDs: player={sprite_ids.get('player')}, "
          f"platform={sprite_ids.get('platform')}, "
          f"coin={sprite_ids.get('coin')}, "
          f"enemy={sprite_ids.get('enemy')}, "
          f"background={sprite_ids.get('background')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
