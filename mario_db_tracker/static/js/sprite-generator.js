/**
 * SpriteRenderer — Converts sprite data (pixelmap or image URL) into Phaser 3 textures.
 *
 * Supports two sprite types:
 *   - "pixelmap": { palette: ["#hex"...], frames: [{ grid: ["row"...] }] }
 *     Each char in grid is a hex index (0-f) into palette, "." = transparent
 *   - "image": { image_url: "https://..." }
 *
 * Usage:
 *   // In preload — queue image sprites for loading
 *   SpriteRenderer.preloadImages(scene, sprites);
 *
 *   // In create — generate pixelmap textures
 *   SpriteRenderer.createTextures(scene, sprites);
 *
 *   // Then use: scene.add.sprite(x, y, 'sprite-<id>')
 */
const SpriteRenderer = {

    /**
     * Queue image-type sprites for Phaser preload.
     * @param {Phaser.Scene} scene
     * @param {Object} sprites — { player: {sprite}, platform: {sprite}, ... }
     */
    preloadImages(scene, sprites) {
        if (!sprites) return;
        for (const [role, sprite] of Object.entries(sprites)) {
            if (!sprite || sprite.type !== 'image' || !sprite.image_url) continue;
            const key = `sprite-${sprite.id}`;
            if (scene.textures.exists(key)) continue;

            if (sprite.frame_count > 1) {
                scene.load.spritesheet(key, sprite.image_url, {
                    frameWidth: sprite.width,
                    frameHeight: sprite.height,
                });
            } else {
                scene.load.image(key, sprite.image_url);
            }
        }
    },

    /**
     * Generate canvas textures for pixelmap-type sprites.
     * Call this in create() after preload completes.
     * @param {Phaser.Scene} scene
     * @param {Object} sprites — { player: {sprite}, platform: {sprite}, ... }
     */
    createTextures(scene, sprites) {
        if (!sprites) return;
        for (const [role, sprite] of Object.entries(sprites)) {
            if (!sprite || sprite.type !== 'pixelmap' || !sprite.data) continue;
            this._renderPixelmap(scene, sprite);
        }
    },

    /**
     * Get the Phaser texture key for a sprite.
     * @param {Object|null} sprite
     * @returns {string|null}
     */
    getTextureKey(sprite) {
        if (!sprite) return null;
        return `sprite-${sprite.id}`;
    },

    /**
     * Render a pixelmap sprite into a Phaser canvas texture.
     */
    _renderPixelmap(scene, sprite) {
        const key = `sprite-${sprite.id}`;
        if (scene.textures.exists(key)) return;

        const { palette, frames } = sprite.data;
        if (!palette || !frames || !frames.length) return;

        const W = sprite.width;
        const H = sprite.height;
        const totalWidth = W * frames.length;

        const canvas = scene.textures.createCanvas(key, totalWidth, H);
        const ctx = canvas.context;

        for (let f = 0; f < frames.length; f++) {
            const grid = frames[f].grid;
            if (!grid) continue;
            const ox = f * W;

            for (let y = 0; y < grid.length && y < H; y++) {
                const row = grid[y];
                for (let x = 0; x < row.length && x < W; x++) {
                    const ch = row[x];
                    if (ch === '.') continue; // transparent
                    const idx = parseInt(ch, 16);
                    if (isNaN(idx) || idx >= palette.length) continue;
                    ctx.fillStyle = palette[idx];
                    ctx.fillRect(ox + x, y, 1, 1);
                }
            }
        }

        canvas.refresh();

        // Register individual frames
        if (frames.length > 1) {
            for (let f = 0; f < frames.length; f++) {
                scene.textures.get(key).add(f, 0, f * W, 0, W, H);
            }
        }
    },
};
