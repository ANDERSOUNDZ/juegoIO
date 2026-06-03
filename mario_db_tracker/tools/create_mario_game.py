#!/usr/bin/env python3
"""
create_mario_game.py — Crea los sprites y el juego de Mario Bros Terapéutico
en la plataforma PIXO Therapy via API REST.

Uso:
    python tools/create_mario_game.py
    python tools/create_mario_game.py --base-url http://localhost:5000
    python tools/create_mario_game.py --email admin@pixo.com --password admin
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
import http.cookiejar


# ─── SPRITE DATA ─────────────────────────────────────────────────

def mario_sprite():
    """Mario Bros player sprite — 20x26, 4 frames (idle, walk x2, jump)"""
    return {
        "name": "Mario Bros",
        "category": "player",
        "type": "pixelmap",
        "width": 20,
        "height": 26,
        "frame_count": 4,
        "data": {
            "palette": [
                "#dc2020",   # 0: red (hat/shirt)
                "#2020f8",   # 1: blue (overalls)
                "#f8d8a0",   # 2: skin
                "#684020",   # 3: brown (shoes)
                "#f8f8f8",   # 4: white (eyes)
                "#000000",   # 5: black (outline/mustache)
                "#f8b800",   # 6: yellow (buttons)
            ],
            "frames": [
                # Frame 0 — standing / idle
                {"grid": [
                    "....0000000000....",  # hat top
                    "...000000000000...",  # hat
                    "...000000000000...",  # hat
                    "..00000000000000..",  # hat brim
                    "..22000000000022..",  # face
                    "..22000000000022..",  # face
                    "..22440000004422..",  # eyes white
                    "..22555555555522..",  # mustache
                    "..22000000000022..",  # face bottom
                    "...000000000000...",  # shirt top
                    "...000660066000...",  # shirt buttons
                    "...000660066000...",  # shirt buttons
                    "...000000000000...",  # shirt
                    "..00111111111100..",  # belt/overalls
                    ".0011111111111100.",  # overalls top
                    ".0011111111111100.",  # overalls
                    ".0011111111111100.",  # overalls
                    ".0011111111111100.",  # overalls
                    ".0011111111111100.",  # overalls
                    "..00111111111100..",  # overalls bottom
                    "......33..33......",  # legs
                    "......33..33......",  # legs
                    "......33..33......",  # legs
                    "......33..33......",  # legs
                    "......33..33......",  # legs
                    ".....3333..3333.....",  # shoes
                ]},
                # Frame 1 — walk (left leg forward)
                {"grid": [
                    "....0000000000....",
                    "...000000000000...",
                    "...000000000000...",
                    "..00000000000000..",
                    "..22000000000022..",
                    "..22000000000022..",
                    "..22440000004422..",
                    "..22555555555522..",
                    "..22000000000022..",
                    "...000000000000...",
                    "...000660066000...",
                    "...000660066000...",
                    "...000000000000...",
                    "..00111111111100..",
                    ".0011111111111100.",
                    ".0011111111111100.",
                    ".0011111111111100.",
                    ".0011111111111100.",
                    ".0011111111111100.",
                    "..00111111111100..",
                    ".....33..33.........",
                    ".....33..33.........",
                    ".....33..33.........",
                    ".....33..33.........",
                    "....3333..33........",
                    "....33....3333......",
                ]},
                # Frame 2 — walk (right leg forward)
                {"grid": [
                    "....0000000000....",
                    "...000000000000...",
                    "...000000000000...",
                    "..00000000000000..",
                    "..22000000000022..",
                    "..22000000000022..",
                    "..22440000004422..",
                    "..22555555555522..",
                    "..22000000000022..",
                    "...000000000000...",
                    "...000660066000...",
                    "...000660066000...",
                    "...000000000000...",
                    "..00111111111100..",
                    ".0011111111111100.",
                    ".0011111111111100.",
                    ".0011111111111100.",
                    ".0011111111111100.",
                    ".0011111111111100.",
                    "..00111111111100..",
                    "........33..33......",
                    "........33..33......",
                    "........33..33......",
                    "........33..33......",
                    ".......3333..33.....",
                    ".....3333....33.....",
                ]},
                # Frame 3 — jump
                {"grid": [
                    "....0000000000....",
                    "...000000000000...",
                    "...000000000000...",
                    "..00000000000000..",
                    "..22000000000022..",
                    "..22000000000022..",
                    "..22440000004422..",
                    "..22555555555522..",
                    "..22000000000022..",
                    "...000000000000...",
                    "...000660066000...",
                    "...000660066000...",
                    "...000000000000...",
                    "..00111111111100..",
                    ".0011111111111100.",
                    ".0011111111111100.",
                    ".0011111111111100.",
                    ".0011111111111100.",
                    "..00111111111100..",
                    ".....33......33.....",
                    ".....33......33.....",
                    "....3333....3333....",
                    "....33........33....",
                    "....33........33....",
                    "....................",
                    "....................",
                ]},
            ],
        },
    }


def platform_sprite():
    """Mario Bros platform brick — 16x16, 1 frame"""
    return {
        "name": "Plataforma Mario",
        "category": "platform",
        "type": "pixelmap",
        "width": 16,
        "height": 16,
        "frame_count": 1,
        "data": {
            "palette": [
                "#c84b31",   # 0: brick body
                "#7a2e1d",   # 1: brick shadow
                "#e87a5a",   # 2: brick highlight
                "#2e1a0a",   # 3: mortar
            ],
            "frames": [
                {"grid": [
                    "0111111111111110",
                    "0111111111111110",
                    "0000000000000000",
                    "0111110111111110",
                    "0111110111111110",
                    "0000000000000000",
                    "0111111110111110",
                    "0111111110111110",
                    "0000000000000000",
                    "0111110111111110",
                    "0111110111111110",
                    "0000000000000000",
                    "0111111111111110",
                    "0111111111111110",
                    "0000000000000000",
                    "0111111111111110",
                ]},
            ],
        },
    }


def coin_sprite():
    """Mario coin — 12x12, 6 frames (spinning)"""
    return {
        "name": "Moneda Mario",
        "category": "coin",
        "type": "pixelmap",
        "width": 12,
        "height": 12,
        "frame_count": 6,
        "data": {
            "palette": [
                "#ffd23f",   # 0: gold
                "#fff3a0",   # 1: gold highlight
                "#b8830a",   # 2: gold shadow
                "#ffffff",   # 3: white edge
            ],
            "frames": [
                {"grid": [
                    ".....00.....",
                    "....0000....",
                    "...000000...",
                    "..00000000..",
                    "..00000000..",
                    "..00000000..",
                    "..00000000..",
                    "..00000000..",
                    "..00000000..",
                    "...000000...",
                    "....0000....",
                    ".....00.....",
                ]},
                {"grid": [
                    ".....11.....",
                    "....1111....",
                    "...000000...",
                    "..00000000..",
                    ".0000000000.",
                    ".0000000000.",
                    ".0000000000.",
                    ".0000000000.",
                    ".0000000000.",
                    "...000000...",
                    "....2222....",
                    ".....22.....",
                ]},
                {"grid": [
                    "....1111....",
                    "...111111...",
                    "..00000000..",
                    ".0000000000.",
                    ".0000000000.",
                    ".0000000000.",
                    ".0000000000.",
                    ".0000000000.",
                    ".0000000000.",
                    "..00000000..",
                    "...222222...",
                    "....2222....",
                ]},
                {"grid": [
                    "...111111...",
                    "..11111111..",
                    ".0000000000.",
                    "000000000000",
                    "000000000000",
                    "000000000000",
                    "000000000000",
                    "000000000000",
                    "000000000000",
                    ".0000000000.",
                    "..22222222..",
                    "...222222...",
                ]},
                {"grid": [
                    "....1111....",
                    "...111111...",
                    "..00000000..",
                    ".0000000000.",
                    ".0000000000.",
                    ".0000000000.",
                    ".0000000000.",
                    ".0000000000.",
                    ".0000000000.",
                    "..00000000..",
                    "...222222...",
                    "....2222....",
                ]},
                {"grid": [
                    ".....11.....",
                    "....1111....",
                    "...000000...",
                    "..00000000..",
                    ".0000000000.",
                    ".0000000000.",
                    ".0000000000.",
                    ".0000000000.",
                    ".0000000000.",
                    "...000000...",
                    "....2222....",
                    ".....22.....",
                ]},
            ],
        },
    }


def enemy_sprite():
    """Shellcreeper (green turtle) — 16x16, 2 frames"""
    return {
        "name": "Shellcreeper",
        "category": "enemy",
        "type": "pixelmap",
        "width": 16,
        "height": 16,
        "frame_count": 2,
        "data": {
            "palette": [
                "#30b030",   # 0: shell green
                "#188018",   # 1: shell dark
                "#58d858",   # 2: shell light
                "#f8d8a0",   # 3: body/skin
                "#f8f8f8",   # 4: eye white
                "#000000",   # 5: eye black
                "#d8d800",   # 6: feet yellow
            ],
            "frames": [
                # Frame 0 — walking
                {"grid": [
                    "................",
                    "....022220....",
                    "...02222220...",
                    "...02222220...",
                    "..0222002220..",
                    "..0220002220..",
                    "..0222222220..",
                    "..0022222200..",
                    "...04444440...",
                    "...04555540...",
                    "...04444440...",
                    "....033330....",
                    "....600006....",
                    "...60000006...",
                    "...60000006...",
                    "....66..66....",
                ]},
                # Frame 1 — walking (feet shifted)
                {"grid": [
                    "................",
                    "....022220....",
                    "...02222220...",
                    "...02222220...",
                    "..0222002220..",
                    "..0220002220..",
                    "..0222222220..",
                    "..0022222200..",
                    "...04444440...",
                    "...04555540...",
                    "...04444440...",
                    "....033330....",
                    "....600006....",
                    "...60000006...",
                    "...60000006...",
                    "....66..66....",
                ]},
            ],
        },
    }


def background_sprite():
    """Mario Bros background — dark with pipe decoration, 16x16 tile"""
    return {
        "name": "Fondo Mario",
        "category": "background",
        "type": "pixelmap",
        "width": 16,
        "height": 16,
        "frame_count": 1,
        "data": {
            "palette": [
                "#1a0a2e",   # 0: dark bg
                "#30b030",   # 1: pipe green
                "#188018",   # 2: pipe dark
                "#58d858",   # 3: pipe highlight
            ],
            "frames": [
                {"grid": [
                    "0000000000000000",
                    "0000000000000000",
                    "0000000000000000",
                    "0000000000000000",
                    "0000000000000000",
                    "0000000000000000",
                    "0000000000000000",
                    "0000000000000000",
                    "0000000000000000",
                    "0000000000000000",
                    "0000000000000000",
                    "0000111111000000",
                    "0000111111000000",
                    "0000222222000000",
                    "0000222222000000",
                    "0000111111000000",
                ]},
            ],
        },
    }


# ─── GAME CONFIG ────────────────────────────────────────────────

def build_game_config(sprite_ids):
    """Build the full Mario Bros game config referencing given sprite IDs."""
    return {
        "version": "1.0",
        "metadata": {
            "name": "Mario Bros Terapeutico",
            "type": "platformer",
            "targetFingers": [0, 1, 2, 3, 4],
            "difficulty": "easy",
            "description": (
                "Juego terapeutico inspirado en Mario Bros. "
                "Salta entre plataformas, evita enemigos y colecciona monedas. "
                "Ejercita los 5 dedos: pulgar(salto), indice(derecha), "
                "medio(izquierda), anular(arriba), menique(abajo)."
            ),
            "estimatedDuration": 300,
        },
        "physics": {
            "type": "arcade",
            "gravity": {"x": 0, "y": 400},
            "debug": False,
        },
        "world": {
            "width": 400,
            "height": 600,
            "backgroundColor": "#1a0a2e",
            "camera": {
                "follow": None,
                "scrollY": False,
                "scrollX": False,
            },
        },
        "entities": {
            "player": {
                "spawn": {"x": 200, "y": 520},
                "width": 20,
                "height": 26,
                "color": "#dc2020",
                "speed": 160,
                "jumpForce": -380,
                "physics": {
                    "bounce": 0,
                    "collideWorldBounds": True,
                },
            },
            "platforms": {
                "static": True,
                "color": "#c84b31",
                "width": 80,
                "height": 14,
                "oneWay": True,
                "layout": "positions",
                "positions": [
                    # Tier 1 (top) — left and right
                    {"x": 55, "y": 100, "w": 110, "h": 14},
                    {"x": 345, "y": 100, "w": 110, "h": 14},
                    # Tier 2 (middle) — three platforms
                    {"x": 40, "y": 280, "w": 100, "h": 14},
                    {"x": 200, "y": 280, "w": 100, "h": 14},
                    {"x": 360, "y": 280, "w": 100, "h": 14},
                    # Tier 3 (bottom) — two wide platforms
                    {"x": 70, "y": 440, "w": 140, "h": 14},
                    {"x": 330, "y": 440, "w": 140, "h": 14},
                    # Ground floor
                    {"x": 200, "y": 570, "w": 400, "h": 14},
                ],
            },
            "collectibles": {
                "color": "#ffd23f",
                "spawnRate": 0,
                "scoreValue": 100,
                "positions": [
                    # Above each platform
                    {"x": 55, "y": 82},
                    {"x": 345, "y": 82},
                    {"x": 40, "y": 262},
                    {"x": 200, "y": 262},
                    {"x": 360, "y": 262},
                    {"x": 70, "y": 422},
                    {"x": 330, "y": 422},
                ],
            },
            "enemies": {
                "count": 0,
                "color": "#30b030",
                "width": 16,
                "height": 16,
                "ai": "patrol",
                "speed": 40,
                "positions": [
                    # Enemies on each platform tier
                    {"x": 55, "y": 88},
                    {"x": 345, "y": 88},
                    {"x": 40, "y": 268},
                    {"x": 360, "y": 268},
                    {"x": 70, "y": 428},
                    {"x": 330, "y": 428},
                ],
            },
        },
        "controls": {
            "fingerMap": {
                "0": "jump",
                "1": "right",
                "2": "left",
                "3": "up",
                "4": "down",
            },
            "keyboardFallback": True,
        },
        "rules": {
            "winCondition": {"type": "score", "target": 1000},
            "loseCondition": {"type": "fall_off"},
            "lives": 3,
            "timer": None,
        },
        "sprites": {
            "player": {"sprite_id": sprite_ids["player"]},
            "platform": {"sprite_id": sprite_ids["platform"]},
            "coin": {"sprite_id": sprite_ids["coin"]},
            "enemy": {"sprite_id": sprite_ids["enemy"]},
            "background": {"sprite_id": sprite_ids["background"]},
        },
        "screens": {
            "start": {
                "title": "MARIO BROS",
                "titleColor": "#dc2020",
                "titleSize": "18px",
                "subtitle": "Terapeutico",
                "subtitleColor": "#ffd23f",
                "subtitleSize": "10px",
                "prompt": "Salta! [SPACE / dedo pulgar]",
                "promptColor": "#ffffff",
                "promptSize": "7px",
                "backgroundColor": "#1a0a2e",
                "delay": 400,
            },
            "gameOver": {
                "winTitle": "NIVEL COMPLETADO!",
                "winTitleColor": "#3ddc97",
                "loseTitle": "GAME OVER",
                "loseTitleColor": "#ff5c8a",
                "subtitleColor": "#ffd23f",
                "winPrompt": "SPACE / Cierra un dedo para continuar",
                "losePrompt": "SPACE / Cierra un dedo para reintentar",
                "backgroundColor": "#1a0a2e",
            },
        },
        "events": [
            {
                "trigger": {"type": "timer", "delay": 25, "repeat": True},
                "actions": [
                    {
                        "type": "spawn",
                        "entity": "enemies",
                        "count": 1,
                        "speed": 50,
                        "ai": "patrol",
                        "color": "#30b030",
                    },
                    {
                        "type": "flash_text",
                        "text": "CUIDADO!",
                        "color": "#ff5c8a",
                        "size": "12px",
                        "duration": 1500,
                    },
                ],
            },
            {
                "trigger": {"type": "score", "value": 500},
                "actions": [
                    {
                        "type": "flash_text",
                        "text": "MITAD DEL NIVEL!",
                        "color": "#ffd23f",
                        "size": "10px",
                        "duration": 2000,
                    },
                ],
            },
            {
                "trigger": {"type": "lives", "value": 1},
                "actions": [
                    {
                        "type": "flash_text",
                        "text": "ULTIMA VIDA!",
                        "color": "#ff5c8a",
                        "size": "12px",
                        "duration": 2000,
                    },
                    {
                        "type": "tint",
                        "target": "player",
                        "color": "#ff0000",
                        "duration": 3000,
                    },
                ],
            },
        ],
    }


# ─── HELPERS ────────────────────────────────────────────────────

def fix_sprite_rows(sprite_data):
    """Pad/truncate pixelmap grid rows to match sprite width."""
    w = sprite_data.get("width", 0)
    data = sprite_data.get("data")
    if not data or not w:
        return
    for frame in data.get("frames", []):
        grid = frame.get("grid", [])
        for i, row in enumerate(grid):
            if len(row) < w:
                grid[i] = row + "." * (w - len(row))
            elif len(row) > w:
                grid[i] = row[:w]


# ─── API CLIENT ─────────────────────────────────────────────────

class ApiClient:

class ApiClient:
    def __init__(self, base_url, email, password):
        self.base_url = base_url.rstrip("/")
        self.cookiejar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookiejar)
        )
        self._login(email, password)

    def _request(self, method, path, body=None):
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode("utf-8") if body else None
        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"} if body else {},
        )
        try:
            resp = self.opener.open(req)
            body = resp.read().decode("utf-8")
            if body:
                return json.loads(body)
            return {}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            print(f"  [ERROR] HTTP {e.code} on {method} {path}: {error_body}")
            sys.exit(1)

    def _login(self, email, password):
        print(f"  Iniciando sesion como {email}...")
        self._request("POST", "/api/auth/login", {
            "email": email,
            "password": password,
        })
        print("  OK")

    def get_sprites(self):
        return self._request("GET", "/api/sprites")

    def create_sprite(self, sprite_data):
        print(f"  Creando sprite '{sprite_data['name']}'...")
        result = self._request("POST", "/api/sprites", sprite_data)
        print(f"    -> ID {result['id']}")
        return result

    def create_game(self, name, game_type, config, description=None):
        body = {
            "name": name,
            "game_type": game_type,
            "config": config,
        }
        if description:
            body["description"] = description
        print(f"  Creando juego '{name}'...")
        result = self._request("POST", "/api/games", body)
        print(f"    -> ID {result['id']}")
        return result


# ─── MAIN ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Crea sprites y juego de Mario Bros en PIXO Therapy"
    )
    parser.add_argument(
        "--base-url", default="http://localhost:5000",
        help="URL base de la API (default: http://localhost:5000)"
    )
    parser.add_argument(
        "--email", default="admin@pixo.com",
        help="Email de admin (default: admin@pixo.com)"
    )
    parser.add_argument(
        "--password", default="admin",
        help="Password de admin (default: admin)"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  PIXO Therapy — Creacion de Mario Bros Terapeutico")
    print("=" * 60)
    print()

    # Conectar a la API
    client = ApiClient(args.base_url, args.email, args.password)

    # Verificar sprites existentes
    existing = client.get_sprites()
    existing_names = {s["name"] for s in existing}
    print(f"  Sprites existentes en BD: {len(existing)}")

    # Definir sprites a crear
    sprites_defs = {
        "player": mario_sprite(),
        "platform": platform_sprite(),
        "coin": coin_sprite(),
        "enemy": enemy_sprite(),
        "background": background_sprite(),
    }

    # Crear sprites (saltar si ya existen)
    sprite_ids = {}
    for key, sprite_data in sprites_defs.items():
        name = sprite_data["name"]
        if name in existing_names:
            # Buscar el ID existente
            for s in existing:
                if s["name"] == name:
                    sprite_ids[key] = s["id"]
                    print(f"  Sprite '{name}' ya existe (ID {s['id']}), reutilizando")
                    break
        else:
            fix_sprite_rows(sprite_data)  # Ensure all rows match sprite width
            result = client.create_sprite(sprite_data)
            sprite_ids[key] = result["id"]

    print()

    # Verificar si el juego ya existe
    existing_games = client._request("GET", "/api/games")
    game_name = "Mario Bros Terapeutico"
    existing_game = next(
        (g for g in existing_games if g["name"] == game_name), None
    )

    if existing_game:
        print(f"  Juego '{game_name}' ya existe (ID {existing_game['id']}), "
              f"actualizando...")
        game_config = build_game_config(sprite_ids)
        client._request("PUT", f"/api/games/{existing_game['id']}", {
            "config": game_config,
        })
        game_id = existing_game["id"]
        print(f"  Juego actualizado (ID {game_id})")
    else:
        game_config = build_game_config(sprite_ids)
        result = client.create_game(
            name=game_name,
            game_type="platformer",
            config=game_config,
            description=(
                "Juego terapeutico inspirado en Mario Bros. "
                "Ejercita los 5 dedos en plataformas clasicas."
            ),
        )
        game_id = result["id"]

    print()
    print("=" * 60)
    print(f"  LISTO! Juego creado: {game_name}")
    print(f"  ID: {game_id}")
    print(f"  URL: {args.base_url}/play/{game_id}")
    print(f"  Sprites usados:")
    for key, sid in sprite_ids.items():
        print(f"    {key}: ID {sid}")
    print("=" * 60)


if __name__ == "__main__":
    main()
