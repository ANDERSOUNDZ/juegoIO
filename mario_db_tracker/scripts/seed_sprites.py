"""
Seed the sprites table with the legacy PIXO game pixel art.
Generates pixelmap data matching the legacy canvas drawing routines.

Run: python scripts/seed_sprites.py
"""
import json
import psycopg2

DB = dict(host='localhost', port=5432, database='mario_db', user='postgres', password='admin')


def make_hero_frames():
    """Generate 4 frames (idle, run1, run2, jump) for Pixo hero — 20x26px."""
    # Palette indices:
    # 0=cap(#3ddc97) 1=capDark(#1f7a4f) 2=star(#ffd23f) 3=hair(#5a2a8a)
    # 4=skin(#f4c896) 5=skinShade(#c89868) 6=eyes(#1a0a2e) 7=cheek(#ff8a8a)
    # 8=shirt(#ffd23f) 9=shirtDark(#b8830a) a=overalls(#7a3ac8) b=overallsDark(#4a1a8a)
    # c=boot(#2a1a0a) d=buttonLight(#fff3a0)
    palette = [
        '#3ddc97',  # 0 cap
        '#1f7a4f',  # 1 capDark
        '#ffd23f',  # 2 star
        '#5a2a8a',  # 3 hair
        '#f4c896',  # 4 skin
        '#c89868',  # 5 skinShade
        '#1a0a2e',  # 6 eyes
        '#ff8a8a',  # 7 cheek
        '#ffd23f',  # 8 shirt (same as star but separate semantic)
        '#b8830a',  # 9 shirtDark
        '#7a3ac8',  # a overalls
        '#4a1a8a',  # b overallsDark
        '#2a1a0a',  # c boot
        '#fff3a0',  # d buttonLight
    ]

    # Build each frame as a 20x26 grid
    # Using the legacy drawHero logic pixel by pixel

    def empty():
        return [['.' for _ in range(20)] for _ in range(26)]

    def px(grid, x, y, w, h, idx):
        for dy in range(h):
            for dx in range(w):
                gy, gx = y + dy, x + dx
                if 0 <= gy < 26 and 0 <= gx < 20:
                    grid[gy][gx] = format(idx, 'x')

    def draw_common(grid):
        """Parts shared across all frames."""
        # hair shadow
        px(grid, 3, 5, 14, 3, 3)
        # cap
        px(grid, 3, 0, 14, 4, 0)
        px(grid, 2, 4, 16, 3, 0)
        px(grid, 1, 4, 1, 3, 1)
        px(grid, 17, 4, 1, 3, 1)
        # cap brim
        px(grid, 10, 6, 8, 2, 1)
        # cap star
        px(grid, 8, 1, 3, 2, 2)
        px(grid, 7, 2, 5, 1, 2)
        # face
        px(grid, 5, 7, 11, 5, 4)
        px(grid, 5, 12, 11, 1, 5)
        # eyes
        px(grid, 8, 9, 2, 2, 6)
        px(grid, 13, 9, 2, 2, 6)
        # cheeks
        px(grid, 6, 11, 2, 1, 7)
        px(grid, 13, 11, 2, 1, 7)
        # neck
        px(grid, 8, 13, 5, 1, 5)
        # overalls body
        px(grid, 5, 14, 11, 7, 0xa)
        # straps
        px(grid, 7, 13, 2, 2, 0xa)
        px(grid, 12, 13, 2, 2, 0xa)
        # shirt chest gap
        px(grid, 9, 14, 3, 4, 8)
        # buttons
        px(grid, 7, 16, 1, 1, 0xd)
        px(grid, 13, 16, 1, 1, 0xd)
        # overalls shadow
        px(grid, 5, 20, 11, 1, 0xb)

    def draw_arms(grid, arm_off=0):
        px(grid, 2, 14 + arm_off, 3, 5, 8)
        px(grid, 16, 14 - arm_off, 3, 5, 8)
        px(grid, 2, 18 + arm_off, 3, 1, 9)
        px(grid, 16, 18 - arm_off, 3, 1, 9)
        # hands
        px(grid, 2, 19 + arm_off, 3, 2, 4)
        px(grid, 16, 19 - arm_off, 3, 2, 4)

    frames = []

    # Frame 0: idle
    g = empty()
    draw_common(g)
    draw_arms(g, 0)
    # idle legs
    px(g, 5, 21, 4, 4, 0xa)
    px(g, 11, 21, 4, 4, 0xa)
    px(g, 4, 25, 5, 1, 0xc)
    px(g, 11, 25, 5, 1, 0xc)
    frames.append({'grid': [''.join(row) for row in g]})

    # Frame 1: run phase 1
    g = empty()
    draw_common(g)
    draw_arms(g, 0)
    px(g, 5, 21, 4, 5, 0xa)
    px(g, 11, 21, 4, 4, 0xa)
    px(g, 4, 25, 5, 1, 0xc)
    px(g, 11, 24, 5, 2, 0xc)
    frames.append({'grid': [''.join(row) for row in g]})

    # Frame 2: run phase 2
    g = empty()
    draw_common(g)
    draw_arms(g, 1)
    px(g, 5, 21, 4, 4, 0xa)
    px(g, 11, 21, 4, 5, 0xa)
    px(g, 5, 24, 5, 2, 0xc)
    px(g, 11, 25, 5, 1, 0xc)
    frames.append({'grid': [''.join(row) for row in g]})

    # Frame 3: jump
    g = empty()
    draw_common(g)
    draw_arms(g, 0)
    px(g, 5, 21, 4, 4, 0xa)
    px(g, 11, 21, 4, 4, 0xa)
    px(g, 5, 24, 4, 2, 0xc)
    px(g, 11, 24, 4, 2, 0xc)
    frames.append({'grid': [''.join(row) for row in g]})

    return palette, frames


def make_brick():
    """16x16 brick tile."""
    palette = ['#c84b31', '#7a2e1d', '#e87a5a']
    g = [['.' for _ in range(16)] for _ in range(16)]

    def px(x, y, w, h, idx):
        for dy in range(h):
            for dx in range(w):
                gy, gx = y + dy, x + dx
                if 0 <= gy < 16 and 0 <= gx < 16:
                    g[gy][gx] = format(idx, 'x')

    # base
    px(0, 0, 16, 16, 0)
    # light top
    px(0, 0, 16, 2, 2)
    # dark bottom
    px(0, 13, 16, 3, 1)
    # mortar horizontal
    px(0, 8, 16, 1, 1)
    # mortar vertical
    for bx in range(0, 16, 8):
        px(bx, 0, 1, 16, 1)

    return palette, [{'grid': [''.join(row) for row in g]}]


def make_block():
    """16x16 ? block tile."""
    palette = ['#ffd23f', '#b8830a', '#fff3a0']
    g = [['.' for _ in range(16)] for _ in range(16)]

    def px(x, y, w, h, idx):
        for dy in range(h):
            for dx in range(w):
                gy, gx = y + dy, x + dx
                if 0 <= gy < 16 and 0 <= gx < 16:
                    g[gy][gx] = format(idx, 'x')

    px(0, 0, 16, 16, 0)  # base gold
    px(0, 0, 16, 2, 2)   # light top
    px(0, 13, 16, 3, 1)  # dark bottom
    px(0, 0, 2, 16, 2)   # light left
    px(14, 0, 2, 16, 1)  # dark right
    # ? mark
    cx = 8
    px(cx - 3, 3, 6, 2, 1)
    px(cx + 1, 5, 2, 2, 1)
    px(cx - 1, 7, 2, 2, 1)
    px(cx - 1, 10, 2, 2, 1)

    return palette, [{'grid': [''.join(row) for row in g]}]


def make_coin():
    """12x12 coin, 6 frames of spin."""
    palette = ['#ffd23f', '#fff3a0', '#b8830a', '#ffffff']
    import math
    frames = []
    W, H = 12, 12
    for f in range(6):
        g = [['.' for _ in range(W)] for _ in range(H)]
        phase = (f / 6) * math.pi
        s = abs(math.sin(phase))
        w = max(2, int(s * 10))
        ox = (W - w) // 2

        for dy in range(H):
            for dx in range(w):
                gx = ox + dx
                if 0 <= gx < W:
                    if dy < 2:
                        g[dy][gx] = '1'  # light top
                    elif dy >= H - 2:
                        g[dy][gx] = '2'  # dark bottom
                    else:
                        g[dy][gx] = '0'  # gold body
        # sparkle
        if s > 0.8:
            sx = ox + 2
            if sx + 1 < W:
                g[0][sx] = '3'
                g[0][sx + 1] = '3'

        frames.append({'grid': [''.join(row) for row in g]})

    return palette, frames


def make_enemy():
    """16x16 enemy sprite."""
    palette = ['#ff5c8a', '#ffffff', '#1a0a2e', '#cc3366']
    g = [['.' for _ in range(16)] for _ in range(16)]

    def px(x, y, w, h, idx):
        for dy in range(h):
            for dx in range(w):
                gy, gx = y + dy, x + dx
                if 0 <= gy < 16 and 0 <= gx < 16:
                    g[gy][gx] = format(idx, 'x')

    # body
    px(2, 4, 12, 10, 0)
    px(4, 2, 8, 2, 0)
    # eyes
    px(4, 6, 3, 3, 1)
    px(9, 6, 3, 3, 1)
    px(5, 7, 2, 2, 2)
    px(10, 7, 2, 2, 2)
    # feet
    px(1, 13, 5, 3, 3)
    px(10, 13, 5, 3, 3)

    return palette, [{'grid': [''.join(row) for row in g]}]


def make_background():
    """400x600 sky background — simplified for pixelmap (just gradient bands + moon)."""
    # This would be huge as a pixelmap, so let's make a smaller tileable version (64x64)
    palette = ['#1a0a2e', '#23104a', '#3a1a5e', '#4a1f7a', '#5a2a8a', '#ffd23f', '#b8830a', '#ffffff']
    W, H = 64, 128
    g = [['.' for _ in range(W)] for _ in range(H)]

    # Sky gradient bands
    band_h = H // 5
    for band in range(5):
        color_idx = band  # 0..4
        for y in range(band * band_h, (band + 1) * band_h):
            for x in range(W):
                if y < H:
                    g[y][x] = format(color_idx, 'x')

    # Stars scattered
    import random
    random.seed(42)
    for _ in range(20):
        sx = random.randint(0, W - 2)
        sy = random.randint(0, H - 2)
        g[sy][sx] = '7'
        g[sy][sx + 1] = '7'

    # Small moon at top right
    for dy in range(6):
        for dx in range(6):
            my, mx = 8 + dy, W - 12 + dx
            if 0 <= my < H and 0 <= mx < W:
                g[my][mx] = '5'
    # moon crater
    g[10][W - 10] = '6'
    g[11][W - 9] = '6'

    return palette, [{'grid': [''.join(row) for row in g]}]


def main():
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    # Check if already seeded
    cur.execute("SELECT count(*) FROM sprites")
    if cur.fetchone()[0] > 0:
        print("Sprites already exist, skipping seed.")
        conn.close()
        return

    sprites = []

    # Hero
    pal, frames = make_hero_frames()
    sprites.append(('Pixo Hero', 'player', 'pixelmap', 20, 26,
                     json.dumps({'palette': pal, 'frames': frames}), None, 4))

    # Brick
    pal, frames = make_brick()
    sprites.append(('Ladrillo Retro', 'platform', 'pixelmap', 16, 16,
                     json.dumps({'palette': pal, 'frames': frames}), None, 1))

    # Block
    pal, frames = make_block()
    sprites.append(('Bloque ?', 'other', 'pixelmap', 16, 16,
                     json.dumps({'palette': pal, 'frames': frames}), None, 1))

    # Coin
    pal, frames = make_coin()
    sprites.append(('Moneda Dorada', 'coin', 'pixelmap', 12, 12,
                     json.dumps({'palette': pal, 'frames': frames}), None, 6))

    # Enemy
    pal, frames = make_enemy()
    sprites.append(('Enemigo Basico', 'enemy', 'pixelmap', 16, 16,
                     json.dumps({'palette': pal, 'frames': frames}), None, 1))

    # Background
    pal, frames = make_background()
    sprites.append(('Cielo Nocturno', 'background', 'pixelmap', 64, 128,
                     json.dumps({'palette': pal, 'frames': frames}), None, 1))

    for s in sprites:
        cur.execute("""
            INSERT INTO sprites (name, category, type, width, height, data, image_url, frame_count, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
        """, s)
        print(f"  Created sprite: {s[0]}")

    conn.commit()

    # Get sprite IDs
    cur.execute("SELECT id, name, category FROM sprites ORDER BY id")
    sprite_map = {}
    for row in cur.fetchall():
        print(f"  -> id={row[0]}: {row[1]} ({row[2]})")
        sprite_map[row[2]] = row[0]

    # Update game id=1 config to reference sprites
    cur.execute("SELECT config FROM games WHERE id = 1")
    row = cur.fetchone()
    if row:
        config = row[0] if isinstance(row[0], dict) else json.loads(row[0])
        config['sprites'] = {
            'player': {'sprite_id': sprite_map.get('player')},
            'platform': {'sprite_id': sprite_map.get('platform')},
            'coin': {'sprite_id': sprite_map.get('coin')},
            'enemy': {'sprite_id': sprite_map.get('enemy')},
            'background': {'sprite_id': sprite_map.get('background')},
        }
        cur.execute("UPDATE games SET config = %s WHERE id = 1", [json.dumps(config)])
        print("\n  Updated game id=1 config with sprite references!")

    conn.commit()
    cur.close()
    conn.close()
    print("\nDone!")


if __name__ == '__main__':
    main()
