/**
 * GameLoader — Interprets a JSON game config and creates a Phaser 3 game.
 *
 * Supports game types: platformer, catch, topdown, target
 *
 * Sprite system (hybrid):
 *   config.sprites = {
 *     player:     { id, type: "pixelmap"|"image", width, height, data, image_url, frame_count },
 *     platform:   { ... },
 *     coin:       { ... },
 *     enemy:      { ... },
 *     background: { ... }
 *   }
 *   - If sprite exists → renders as textured sprite
 *   - If no sprite → falls back to colored rectangles (original behavior)
 */
const GameLoader = {
    /**
     * @param {Object} config - Game config JSON from DB (with resolved sprites)
     * @param {string} containerId - DOM element ID for Phaser canvas
     * @param {HandInput} handInput - HandInput instance for finger control
     * @param {Function} onGameOver - Callback when game ends (won/lost)
     * @returns {Phaser.Game}
     */
    load(config, containerId, handInput, onGameOver) {
        const physics = config.physics || { type: 'arcade', gravity: { x: 0, y: 300 } };
        const world = config.world || { width: 400, height: 600 };

        // ── Level system ──
        // If the config declares `levels`, snapshot the base sections so each level
        // can be re-derived as (base + level overrides) on every (re)start. The base
        // objects are kept as the SAME references the scenes capture, so applyLevel()
        // can mutate them in place and the running scene sees the level's values.
        if (Array.isArray(config.levels) && config.levels.length > 0) {
            config.entities = config.entities || {};
            config.rules = config.rules || {};
            config.world = config.world || {};
            config.physics = config.physics || {};
            config.__levelBase = {
                entities: deepClone(config.entities),
                rules: deepClone(config.rules),
                world: deepClone(config.world),
                physics: deepClone(config.physics),
                events: deepClone(config.events),
            };
        }

        const phaserConfig = {
            type: Phaser.WEBGL,
            parent: containerId,
            width: world.width || 400,
            height: world.height || 600,
            backgroundColor: world.backgroundColor || '#1a0a2e',
            physics: {
                default: 'arcade',
                arcade: {
                    gravity: physics.gravity || { x: 0, y: 300 },
                    debug: physics.debug || false,
                },
            },
            scene: [
                createBootScene(config, handInput),
                createStartScene(config, handInput),
                createLevelIntroScene(config, handInput),
                createPlayScene(config, handInput),
                createGameOverScene(config, handInput, onGameOver),
            ],
            pixelArt: false,
            scale: {
                mode: Phaser.Scale.FIT,
                autoCenter: Phaser.Scale.CENTER_BOTH,
            },
        };

        return new Phaser.Game(phaserConfig);
    },
};

// ═══════════════════════════════════════════════════════════════
//  Level system helpers (reusable, config-driven)
// ═══════════════════════════════════════════════════════════════

/** Structured deep clone via JSON (config is always JSON-serializable). */
function deepClone(o) {
    return o === undefined ? undefined : JSON.parse(JSON.stringify(o));
}

/**
 * Deep-merge `override` onto `base`. Objects merge recursively; arrays and
 * primitives REPLACE. Always returns a fresh value (never mutates inputs).
 */
function mergeDeep(base, override) {
    if (override === undefined) return deepClone(base);
    if (override === null || typeof override !== 'object' || Array.isArray(override)) {
        return deepClone(override);
    }
    const out = (base && typeof base === 'object' && !Array.isArray(base)) ? Object.assign({}, base) : {};
    for (const k of Object.keys(override)) {
        out[k] = mergeDeep(out[k], override[k]);
    }
    return out;
}

/** Replace the CONTENTS of `target` with `source`, keeping the same reference. */
function assignInPlace(target, source) {
    if (!target || typeof target !== 'object') return;
    for (const k of Object.keys(target)) delete target[k];
    Object.assign(target, source || {});
}

/**
 * Rebuild config sections for level `index` as (base snapshot + level overrides),
 * mutating the live config objects in place so the running scene picks them up.
 */
function applyLevel(config, index) {
    const base = config.__levelBase;
    if (!base) return;
    const levels = Array.isArray(config.levels) ? config.levels : [];
    const lvl = levels[index] || {};

    // Rules deep-merge, but win/lose conditions REPLACE wholesale when a level
    // redefines them (so switching e.g. score → survive doesn't keep a stale `target`).
    const mergedRules = mergeDeep(base.rules || {}, lvl.rules || {});
    if (lvl.rules && lvl.rules.winCondition) mergedRules.winCondition = deepClone(lvl.rules.winCondition);
    if (lvl.rules && lvl.rules.loseCondition) mergedRules.loseCondition = deepClone(lvl.rules.loseCondition);

    assignInPlace(config.entities, mergeDeep(base.entities || {}, lvl.entities || {}));
    assignInPlace(config.rules, mergedRules);
    assignInPlace(config.world, mergeDeep(base.world || {}, lvl.world || {}));
    assignInPlace(config.physics, mergeDeep(base.physics || {}, lvl.physics || {}));
    config.events = lvl.events ? deepClone(lvl.events) : deepClone(base.events);
}

/**
 * Big animated "3 · 2 · 1 · ¡YA!" countdown overlay. Calls onDone() when finished.
 * Reusable at the start of every round/level ("timer al inicio de cada partida").
 */
function runCountdown(scene, seconds, onDone, opts) {
    opts = opts || {};
    const total = Math.floor(seconds || 0);
    if (total < 1) { onDone(); return; }

    const W = scene.scale.width;
    const H = scene.scale.height;
    const txt = scene.add.text(W / 2, H / 2, '', {
        fontFamily: 'Arial, sans-serif',
        fontSize: opts.size || '72px',
        fontWeight: 'bold',
        color: opts.color || '#ffd23f',
        stroke: '#000000',
        strokeThickness: 7,
        align: 'center',
    }).setOrigin(0.5).setScrollFactor(0).setDepth(1000);

    let n = total;
    const tick = () => {
        const last = n <= 0;
        txt.setText(last ? (opts.goText || '¡YA!') : String(n));
        txt.setColor(last ? (opts.goColor || '#3ddc97') : (opts.color || '#ffd23f'));
        txt.setScale(0.3);
        txt.setAlpha(1);
        scene.tweens.add({ targets: txt, scale: 1, duration: 300, ease: 'Back.out' });
        scene.tweens.add({ targets: txt, alpha: 0, delay: 550, duration: 400 });
        if (last) {
            scene.time.delayedCall(900, () => { txt.destroy(); onDone(); });
            return;
        }
        n--;
        scene.time.delayedCall(1000, tick);
    };
    tick();
}

/**
 * BootScene — Preloads image-type sprites, then starts PlayScene.
 */
function createBootScene(config, handInput) {
    const sprites = config.sprites || {};

    return class BootScene extends Phaser.Scene {
        constructor() {
            super('BootScene');
        }

        preload() {
            // Preload image-type sprites
            if (typeof SpriteRenderer !== 'undefined') {
                SpriteRenderer.preloadImages(this, sprites);
            }
        }

        create() {
            // Generate pixelmap textures
            if (typeof SpriteRenderer !== 'undefined') {
                SpriteRenderer.createTextures(this, sprites);
            }
            // Generate particle textures
            if (!this.textures.exists('particle-glow')) {
                const g = this.make.graphics({add: false});
                g.fillStyle(0xffffff);
                g.fillCircle(8, 8, 8);
                g.generateTexture('particle-glow', 16, 16);
                g.destroy();
            }
            if (!this.textures.exists('particle-star')) {
                const g = this.make.graphics({add: false});
                g.fillStyle(0xffffff);
                g.fillRect(3, 0, 2, 8);
                g.fillRect(0, 3, 8, 2);
                g.fillRect(1, 1, 6, 6);
                g.generateTexture('particle-star', 8, 8);
                g.destroy();
            }
            // Level progression state (shared across scenes for this game).
            this.registry.set('currentLevel', 0);
            this.registry.set('totalScore', 0);
            this.scene.start('StartScene');
        }
    };
}

/**
 * Shared overlay-screen renderer used by StartScene and GameOverScene.
 * Draws a semi-transparent backdrop, title, subtitle, and a blinking prompt.
 *
 * @param {Phaser.Scene} scene
 * @param {Object} opts - { title, titleColor, subtitle, subtitleColor, prompt, promptColor, backgroundColor, backgroundAlpha, handInput, onTrigger }
 */
function createOverlayScreen(scene, opts) {
    const W = scene.scale.width;
    const H = scene.scale.height;

    // Background overlay
    const bgColor = Phaser.Display.Color.HexStringToColor(opts.backgroundColor || '#1a0a2e').color;
    const bg = scene.add.rectangle(W / 2, H / 2, W, H, bgColor, opts.backgroundAlpha ?? 0.92);
    bg.setDepth(900);

    // Decorative gradient-like lines
    const lineColor = Phaser.Display.Color.HexStringToColor(opts.titleColor || '#3ddc97').color;
    const topLine = scene.add.rectangle(W / 2, H / 2 - 70, W * 0.7, 2, lineColor, 0.5).setDepth(901);
    const botLine = scene.add.rectangle(W / 2, H / 2 + 70, W * 0.7, 2, lineColor, 0.5).setDepth(901);

    // Title with shadow
    const titleShadow = scene.add.text(W / 2 + 2, H / 2 - 33, opts.title || '', {
        fontFamily: 'Arial, sans-serif',
        fontSize: opts.titleSize || '18px',
        fontWeight: 'bold',
        color: '#000000',
        align: 'center',
        wordWrap: { width: W * 0.85 },
    }).setOrigin(0.5).setDepth(900).setAlpha(0.3);

    const title = scene.add.text(W / 2, H / 2 - 35, opts.title || '', {
        fontFamily: 'Arial, sans-serif',
        fontSize: opts.titleSize || '18px',
        fontWeight: 'bold',
        color: opts.titleColor || '#3ddc97',
        align: 'center',
        wordWrap: { width: W * 0.85 },
    }).setOrigin(0.5).setDepth(901);

    // Subtitle
    if (opts.subtitle) {
        scene.add.text(W / 2, H / 2 + 12, opts.subtitle, {
            fontFamily: 'Arial, sans-serif',
            fontSize: opts.subtitleSize || '11px',
            color: opts.subtitleColor || '#ffd23f',
            align: 'center',
            wordWrap: { width: W * 0.85 },
        }).setOrigin(0.5).setDepth(901);
    }

    // Prompt text (blinking)
    const promptText = scene.add.text(W / 2, H / 2 + 50, opts.prompt || 'SPACE / Cierra un dedo', {
        fontFamily: 'Arial, sans-serif',
        fontSize: opts.promptSize || '11px',
        color: opts.promptColor || '#a8a0c0',
        align: 'center',
    }).setOrigin(0.5).setDepth(901).setAlpha(0);

    // Delay before allowing trigger (prevents accidental skips)
    scene.time.delayedCall(opts.delay ?? 600, () => {
        promptText.setAlpha(1);
        scene.tweens.add({ targets: promptText, alpha: 0.3, duration: 800, yoyo: true, repeat: -1 });

        let triggered = false;
        const fire = () => {
            if (triggered) return;
            triggered = true;
            opts.onTrigger();
        };

        // SPACE key
        scene.input.keyboard.on('keydown-SPACE', fire);
        // Click / tap
        scene.input.on('pointerdown', fire);
        // Hand input: any finger closed
        if (opts.handInput) {
            scene._overlayFingerCheck = scene.time.addEvent({
                delay: 100,
                loop: true,
                callback: () => {
                    // Cualquier dedo cerrado en cualquier mano dispara la pantalla.
                    const hi = opts.handInput;
                    if (hi.anyFingerClosed ? hi.anyFingerClosed()
                        : (hi.getFingers() || []).some(f => f === 1)) fire();
                },
            });
        }
    });
}

function createStartScene(config, handInput) {
    const screens = config.screens || {};
    const startCfg = screens.start || {};

    return class StartScene extends Phaser.Scene {
        constructor() {
            super('StartScene');
        }

        create() {
            createOverlayScreen(this, {
                title: startCfg.title || config.metadata?.name || 'READY?',
                titleColor: startCfg.titleColor,
                titleSize: startCfg.titleSize,
                subtitle: startCfg.subtitle || null,
                subtitleColor: startCfg.subtitleColor,
                subtitleSize: startCfg.subtitleSize,
                prompt: startCfg.prompt || 'SPACE / Cierra un dedo',
                promptColor: startCfg.promptColor,
                promptSize: startCfg.promptSize,
                backgroundColor: startCfg.backgroundColor || config.world?.backgroundColor || '#1a0a2e',
                backgroundAlpha: startCfg.backgroundAlpha ?? 1,
                delay: startCfg.delay ?? 300,
                handInput,
                onTrigger: () => {
                    // Fresh run: start at level 0 with a clean cumulative score.
                    this.registry.set('currentLevel', 0);
                    this.registry.set('totalScore', 0);
                    this.scene.start('PlayScene');
                },
            });
        }
    };
}

/**
 * LevelIntroScene — "NIVEL X" announcement shown between levels. Waits for
 * SPACE / tap / finger, then starts the next level's PlayScene (which runs its
 * own start-of-round countdown). Fully styleable via config.screens.levelIntro
 * and per-level `level.intro`.
 */
function createLevelIntroScene(config, handInput) {
    const screens = config.screens || {};
    const introCfg = screens.levelIntro || {};

    return class LevelIntroScene extends Phaser.Scene {
        constructor() {
            super('LevelIntroScene');
        }

        init(data) {
            this._data = data || {};
        }

        create() {
            const levels = Array.isArray(config.levels) ? config.levels : [];
            const idx = this.registry.get('currentLevel') || 0;
            const lvl = levels[idx] || {};
            const lvlIntro = lvl.intro || {};

            const title = lvlIntro.title || `NIVEL ${idx + 1}`;
            let subtitle = lvlIntro.subtitle || lvl.name || '';
            if (this._data.fromWin && this._data.completedName) {
                subtitle = `${this._data.completedName}  ✓\n${subtitle}`.trim();
            }

            createOverlayScreen(this, {
                title,
                titleColor: lvlIntro.titleColor || introCfg.titleColor || '#3ddc97',
                titleSize: lvlIntro.titleSize || introCfg.titleSize || '22px',
                subtitle: subtitle || null,
                subtitleColor: lvlIntro.subtitleColor || introCfg.subtitleColor || '#ffd23f',
                subtitleSize: lvlIntro.subtitleSize || introCfg.subtitleSize,
                prompt: lvlIntro.prompt || introCfg.prompt || 'SPACE / Toca para empezar',
                promptColor: lvlIntro.promptColor || introCfg.promptColor,
                promptSize: lvlIntro.promptSize || introCfg.promptSize,
                backgroundColor: lvlIntro.backgroundColor || introCfg.backgroundColor
                    || config.world?.backgroundColor || '#1a0a2e',
                backgroundAlpha: introCfg.backgroundAlpha ?? 1,
                delay: introCfg.delay ?? 400,
                handInput,
                onTrigger: () => this.scene.start('PlayScene'),
            });
        }
    };
}

function createPlayScene(config, handInput) {
    const entities = config.entities || {};
    const controls = config.controls || {};
    const rules = config.rules || {};
    const world = config.world || {};
    const sprites = config.sprites || {};
    const fingerMap = controls.fingerMap || { '0': 'jump', '1': 'right', '2': 'left', '3': 'up', '4': 'down' };
    // ── Multi-mano (solo juegos Phaser) ──
    // `controls.hands` = nº de manos que soporta el juego (1 por defecto).
    // `controls.fingerMaps[h]` = mapeo dedo→acción de la mano h; si falta, usa fingerMap.
    const numHands = Math.max(1, parseInt(controls.hands, 10) || 1);
    const fingerMapsCfg = Array.isArray(controls.fingerMaps) ? controls.fingerMaps : null;
    const gameType = config.metadata?.type || 'platformer';

    return class PlayScene extends Phaser.Scene {
        constructor() {
            super('PlayScene');
        }

        create() {
            // ── Apply the current level's overrides onto the live config ──
            // (no-op for games without a `levels` array — identical legacy behavior).
            this._levelIndex = this.registry.get('currentLevel') || 0;
            applyLevel(config, this._levelIndex);

            // Reset state on every (re)start
            this.score = 0;
            this.lives = rules.lives || 1;
            this.gameTimer = null;
            this.timeLeft = rules.timer || undefined;
            this._levelDone = false;
            this._frozen = false;
            const W = this.scale.width;
            const H = this.scale.height;

            // Per-level physics gravity + background color
            if (config.physics?.gravity && this.physics?.world) {
                this.physics.world.gravity.x = config.physics.gravity.x || 0;
                this.physics.world.gravity.y = config.physics.gravity.y || 0;
            }
            if (world.backgroundColor) {
                this.cameras.main.setBackgroundColor(world.backgroundColor);
            }

            // ── Background parallax layers ──
            this._createBackground();

            // ── Player ──
            const playerCfg = entities.player || {};
            const spawn = playerCfg.spawn || { x: W / 2, y: H - 60 };
            const playerTex = this._getSpriteKey('player');

            if (playerTex) {
                this.player = this.add.sprite(spawn.x, spawn.y, playerTex, 0);
                this.player.setDisplaySize(playerCfg.width || 20, playerCfg.height || 26);
            } else {
                this.player = this.add.rectangle(
                    spawn.x, spawn.y,
                    playerCfg.width || 20, playerCfg.height || 26,
                    Phaser.Display.Color.HexStringToColor(playerCfg.color || '#3ddc97').color
                );
            }
            if (this.player.setPipeline) this.player.setPipeline('Light2D');

            this.physics.add.existing(this.player);
            this.player.body.setCollideWorldBounds(
                playerCfg.physics?.collideWorldBounds !== false
            );
            if (playerCfg.physics?.bounce) {
                this.player.body.setBounce(playerCfg.physics.bounce);
            }
            // Adjust body size for sprites (body may differ from display)
            this.player.body.setSize(playerCfg.width || 20, playerCfg.height || 26);

            this.playerSpeed = playerCfg.speed || 200;
            this.jumpForce = playerCfg.jumpForce || -400;

            // Player animation (if spritesheet with multiple frames)
            this._setupPlayerAnims(playerTex);

            // Expose per-hand fingerMaps for live config changes.
            // `_fingerMaps[h]` controla la mano h; `_fingerMap` es un alias a la
            // mano 0 (compatibilidad con el editor de controles de una sola mano).
            this._numHands = numHands;
            this._fingerMaps = [];
            for (let h = 0; h < numHands; h++) {
                const m = (fingerMapsCfg && fingerMapsCfg[h]) ? fingerMapsCfg[h] : fingerMap;
                this._fingerMaps.push(Object.assign({}, m));
            }
            this._fingerMap = this._fingerMaps[0];
            // Config-driven: avisa al tracker cuántas manos rastrear.
            if (handInput && handInput.setNumHands) handInput.setNumHands(numHands);

            // Create platforms
            this._createPlatforms();

            // Create collectibles
            this._createCollectibles();

            // Create enemies
            this._createEnemies();

            // Collisions — per-object oneWay check
            const oneWayCheck = (player, obj) => {
                if (obj.getData('oneWay')) {
                    return player.body.velocity.y >= 0 && player.body.bottom <= obj.body.top + 10;
                }
                return true;
            };

            if (this.platforms) {
                this.physics.add.collider(this.player, this.platforms, null, oneWayCheck);
                if (this.enemies) {
                    this.physics.add.collider(this.enemies, this.platforms);
                }
            }

            if (this.collectibles) {
                this.physics.add.overlap(this.player, this.collectibles, (player, item) => {
                    const cx = item.x, cy = item.y;
                    item.destroy();
                    this.score += (entities.collectibles?.scoreValue || 100);
                    this._totalCollected++;
                    this._updateHUD();
                    if (this._coinEmitter) {
                        this._coinEmitter.emitParticleAt(cx, cy, 8);
                    }
                });
            }

            if (this.enemies) {
                this.physics.add.overlap(this.player, this.enemies, (player, enemy) => {
                    const ex = enemy.x, ey = enemy.y;
                    this.lives--;
                    if (this._enemyEmitter) {
                        this._enemyEmitter.emitParticleAt(ex, ey, 12);
                    }
                    this.cameras.main.shake(120, 0.008);
                    if (this.lives <= 0) {
                        this.scene.start('GameOverScene', { score: this.score });
                    } else {
                        this.tweens.add({
                            targets: this.player,
                            alpha: 0.3,
                            duration: 100,
                            yoyo: true,
                            repeat: 3,
                        });
                        enemy.destroy();
                        this._updateHUD();
                    }
                });
            }

            // Camera
            this._autoScroll = world.camera?.autoScroll || null;
            if (this._autoScroll) {
                this.cameras.main.scrollY = 0;
            } else if (world.camera?.follow === 'player') {
                this.cameras.main.startFollow(this.player, true, 0.1, 0.1);
                if (world.camera.scrollY) {
                    this.cameras.main.setDeadzone(W, H * 0.3);
                }
            }
            this.physics.world.setBounds(0, -10000, W, 20000 + H);
            this.cameras.main.fadeIn(500, 0, 0, 0);
            // ── Lighting ──
            try {
                this.lights.enable().setAmbientColor(0x222244);
                this._playerLight = this.lights.addLight(
                    this.player.x, this.player.y, 180, 0xffdd99, 1.2
                );
                this._coinLights = [];
            } catch (e) {
                this._playerLight = null;
            }

            // ── Particle emitters ──
            if (this.textures.exists('particle-glow')) {
                this._coinEmitter = this.add.particles(0, 0, 'particle-glow', {
                    speed: { min: 40, max: 120 },
                    angle: { min: 0, max: 360 },
                    lifespan: { min: 300, max: 600 },
                    scale: { start: 0.6, end: 0 },
                    alpha: { start: 1, end: 0 },
                    tint: 0xffd700,
                    emitting: false,
                });
                this._enemyEmitter = this.add.particles(0, 0, 'particle-star', {
                    speed: { min: 60, max: 180 },
                    angle: { min: 0, max: 360 },
                    lifespan: { min: 400, max: 800 },
                    scale: { start: 1, end: 0 },
                    alpha: { start: 1, end: 0 },
                    tint: 0xff4444,
                    emitting: false,
                });
                this._jumpEmitter = this.add.particles(0, 0, 'particle-glow', {
                    speed: { min: 10, max: 40 },
                    angle: { min: 200, max: 340 },
                    lifespan: { min: 200, max: 400 },
                    scale: { start: 0.4, end: 0 },
                    alpha: { start: 0.6, end: 0 },
                    tint: 0xaaaacc,
                    emitting: false,
                });
            } else {
                this._coinEmitter = null;
                this._enemyEmitter = null;
                this._jumpEmitter = null;
            }

            // Timer
            if (rules.timer) {
                this.timeLeft = rules.timer;
                this.time.addEvent({
                    delay: 1000,
                    callback: () => {
                        if (this._frozen) return;  // paused during the countdown
                        this.timeLeft--;
                        this._updateHUD();
                        if (this.timeLeft <= 0) {
                            // Surviving until the clock runs out is a WIN if the
                            // level asks for it; otherwise time-out is a loss.
                            if (rules.winCondition?.type === 'survive') {
                                this._completeLevel();
                            } else {
                                this.scene.start('GameOverScene', { score: this.score });
                            }
                        }
                    },
                    loop: true,
                });
            }

            // HUD
            const hudBg = this.add.rectangle(W / 2, 0, W, 36, 0x000000, 0.55).setOrigin(0.5, 0).setScrollFactor(0).setDepth(99);
            this.hudText = this.add.text(12, 8, '', {
                fontFamily: 'Arial, sans-serif',
                fontSize: '13px',
                fontWeight: 'bold',
                color: '#ffd23f',
                stroke: '#000000',
                strokeThickness: 1,
            }).setScrollFactor(0).setDepth(100);
            this._updateHUD();

            // Keyboard fallback
            this.cursors = this.input.keyboard.createCursorKeys();
            this.spaceKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.SPACE);
            this.interactKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.E);

            // Inventory
            this._inventory = null;
            this._inventoryText = this.add.text(this.scale.width - 10, 10, '', {
                fontFamily: '"Press Start 2P"',
                fontSize: '8px',
                color: '#4fc3f7',
            }).setScrollFactor(0).setDepth(100).setOrigin(1, 0);

            // Create zones (interactable areas)
            this._createZones();

            // Event system
            this._elapsedTime = 0;
            this._totalCollected = 0;
            this._initEvents();

            // ── Start-of-round countdown ("timer al inicio de cada partida") ──
            // Freezes physics until 3·2·1·¡YA! finishes. Runs on every level entry
            // and retry. Configure via level.countdown / config.countdown.
            const cd = this._levelCountdown();
            if (cd > 0) {
                this._frozen = true;
                this.physics.pause();
                const cdCfg = (config.screens && config.screens.countdown) || {};
                runCountdown(this, cd, () => {
                    this._frozen = false;
                    this.physics.resume();
                }, cdCfg);
            }
        }

        update(time, delta) {
            if (!this.player || !this.player.body) return;
            if (this._frozen) return;
            this._elapsedTime += delta / 1000;
            this._checkEvents();

            // Get actions from hand input OR keyboard
            const handActions = handInput ? handInput.getMappedActions(this._fingerMaps) : {};
            const kbLeft = this.cursors.left.isDown;
            const kbRight = this.cursors.right.isDown;
            const kbUp = this.cursors.up.isDown;
            const kbDown = this.cursors.down.isDown;
            const kbJump = this.spaceKey.isDown;

            const moveLeft = handActions.left || kbLeft;
            const moveRight = handActions.right || kbRight;
            const moveUp = handActions.up || kbUp;
            const moveDown = handActions.down || kbDown;
            const jump = handActions.jump || kbJump;
            const interact = handActions.interact || Phaser.Input.Keyboard.JustDown(this.interactKey);

            // Apply movement based on game type
            this.player.body.setVelocityX(0);
            if (moveLeft) this.player.body.setVelocityX(-this.playerSpeed);
            if (moveRight) this.player.body.setVelocityX(this.playerSpeed);

            if (gameType === 'topdown') {
                // Top-down: 4-directional movement, no gravity
                this.player.body.setVelocityY(0);
                if (moveUp) this.player.body.setVelocityY(-this.playerSpeed);
                if (moveDown) this.player.body.setVelocityY(this.playerSpeed);

                // Diagonal normalization
                if ((moveLeft || moveRight) && (moveUp || moveDown)) {
                    this.player.body.velocity.normalize().scale(this.playerSpeed);
                }
            } else {
                // Platformer/runner/catch: jump-based
                if (jump && this.player.body.onFloor()) {
                    this.player.body.setVelocityY(this.jumpForce);
                    if (this._jumpEmitter) {
                        this._jumpEmitter.emitParticleAt(this.player.x, this.player.y + 12, 5);
                    }
                }
            }

            // Player animation
            const isMoving = moveLeft || moveRight || moveUp || moveDown;
            this._animatePlayer(moveLeft, moveRight, isMoving);

            // Enemy AI
            if (this.enemies) {
                this.enemies.children.iterate(enemy => {
                    if (!enemy || !enemy.body || !enemy.active) return;
                    if (enemy.getData('ai') === 'patrol') {
                        if (enemy.body.blocked.left || enemy.x <= enemy.getData('minX')) {
                            enemy.body.setVelocityX(enemy.getData('speed'));
                        } else if (enemy.body.blocked.right || enemy.x >= enemy.getData('maxX')) {
                            enemy.body.setVelocityX(-enemy.getData('speed'));
                        }
                    } else if (enemy.getData('ai') === 'chase') {
                        const dx = this.player.x - enemy.x;
                        const dy = this.player.y - enemy.y;
                        const spd = enemy.getData('speed');
                        if (gameType === 'topdown') {
                            // 2D chase: normalize direction vector
                            const dist = Math.sqrt(dx * dx + dy * dy);
                            if (dist > 0) {
                                enemy.body.setVelocity((dx / dist) * spd, (dy / dist) * spd);
                            }
                        } else {
                            enemy.body.setVelocityX(dx > 0 ? spd : -spd);
                        }
                    }
                });
            }

            // Win condition check (level-aware)
            if (this._checkWin()) this._completeLevel();

            // Auto-scroll camera
            if (this._autoScroll) {
                const dt = this.game.loop.delta / 1000; // seconds
                this.cameras.main.scrollY += (this._autoScroll.y || 0) * dt;
                this.cameras.main.scrollX += (this._autoScroll.x || 0) * dt;
            }

            // Lose conditions
            const camTop = this.cameras.main.scrollY;
            const camBot = camTop + this.scale.height;

            if (rules.loseCondition?.type === 'fall_off') {
                if (this.player.y > camBot + 100) {
                    this.scene.start('GameOverScene', { score: this.score });
                }
            } else if (rules.loseCondition?.type === 'off_screen') {
                // Lose if player exits camera viewport (any direction)
                if (this.player.y < camTop - 50 || this.player.y > camBot + 50) {
                    this.scene.start('GameOverScene', { score: this.score });
                }
            }

            // Infinite generation for platformers
            if (this.platforms && entities.platforms?.layout === 'procedural') {
                this._generateMore();
            }

            // Score from distance
            if (config.metadata?.type === 'platformer') {
                const altScore = Math.floor(Math.max(0, -this.player.y) / 5);
                this.score = Math.max(this.score, altScore);
                this._updateHUD();
            } else if (config.metadata?.type === 'runner') {
                const distScore = Math.floor(Math.max(0, this.player.y) / 5);
                this.score = Math.max(this.score, distScore);
                this._updateHUD();
            }

            // Zones (interactable areas)
            this._updateZones(interact);

            // Parallax background scroll
            this._scrollBackground();

            // Update player light position
            if (this._playerLight && this.player.active) {
                this._playerLight.x = this.player.x;
                this._playerLight.y = this.player.y;
            }
        }

        // ── Level system ──

        /** Resolve the countdown (seconds) shown before this round starts. */
        _levelCountdown() {
            const levels = Array.isArray(config.levels) ? config.levels : [];
            const lvl = levels[this._levelIndex] || {};
            if (typeof lvl.countdown === 'number') return lvl.countdown;
            if (config.levelDefaults && typeof config.levelDefaults.countdown === 'number') {
                return config.levelDefaults.countdown;
            }
            if (typeof config.countdown === 'number') return config.countdown;
            return 0;
        }

        /** True when the current level's win condition is satisfied. */
        _checkWin() {
            const wc = rules.winCondition;
            if (!wc) return false;
            switch (wc.type) {
                case 'score':
                    return this.score >= (wc.target || 0);
                case 'collect_count':
                    return this._totalCollected >= (wc.target || wc.value || 0);
                case 'collect_all':
                    return this.collectibles
                        ? (this._totalCollected > 0 && this.collectibles.countActive() === 0)
                        : false;
                case 'time':
                    return this._elapsedTime >= (wc.seconds || wc.target || 0);
                // 'survive' is resolved by the game timer when it reaches 0.
                default:
                    return false;
            }
        }

        /** Advance to the next level, or finish the game after the last one. */
        _completeLevel() {
            if (this._levelDone) return;
            this._levelDone = true;

            const levels = Array.isArray(config.levels) ? config.levels : [];
            const idx = this.registry.get('currentLevel') || 0;
            const accumulated = (this.registry.get('totalScore') || 0) + this.score;

            if (levels.length && idx < levels.length - 1) {
                // More levels remain → announce the next one.
                this.registry.set('totalScore', accumulated);
                this.registry.set('currentLevel', idx + 1);
                this.scene.start('LevelIntroScene', {
                    fromWin: true,
                    completedName: (levels[idx] && levels[idx].name) || `Nivel ${idx + 1}`,
                });
            } else {
                // Last level (or single-level game) → full win.
                this.scene.start('GameOverScene', { score: accumulated, won: true });
            }
        }

        // ── Sprite helpers ──

        _getSpriteKey(role) {
            const sprite = sprites[role];
            if (!sprite) return null;
            if (typeof SpriteRenderer !== 'undefined') {
                const key = SpriteRenderer.getTextureKey(sprite);
                if (key && this.textures.exists(key)) return key;
            }
            return null;
        }

        _setupPlayerAnims(textureKey) {
            if (!textureKey) return;
            const sprite = sprites.player;
            if (!sprite || (sprite.frame_count || 1) <= 1) return;

            const fc = sprite.frame_count;

            // Create anims: idle (frame 0), run (frames 1..fc-2), jump (last frame)
            // Guard against re-creation on scene restart
            if (fc >= 4) {
                if (!this.anims.exists('player-idle')) {
                    this.anims.create({
                        key: 'player-idle',
                        frames: [{ key: textureKey, frame: 0 }],
                        frameRate: 1,
                    });
                }
                if (!this.anims.exists('player-run')) {
                    this.anims.create({
                        key: 'player-run',
                        frames: this.anims.generateFrameNumbers(textureKey, { start: 1, end: fc - 2 }),
                        frameRate: 8,
                        repeat: -1,
                    });
                }
                if (!this.anims.exists('player-jump')) {
                    this.anims.create({
                        key: 'player-jump',
                        frames: [{ key: textureKey, frame: fc - 1 }],
                        frameRate: 1,
                    });
                }
            } else if (fc >= 2) {
                if (!this.anims.exists('player-idle')) {
                    this.anims.create({
                        key: 'player-idle',
                        frames: [{ key: textureKey, frame: 0 }],
                        frameRate: 1,
                    });
                }
                if (!this.anims.exists('player-run')) {
                    this.anims.create({
                        key: 'player-run',
                        frames: this.anims.generateFrameNumbers(textureKey, { start: 0, end: fc - 1 }),
                        frameRate: 8,
                        repeat: -1,
                    });
                }
            }
        }

        _animatePlayer(moveLeft, moveRight, isMoving) {
            const tex = this._getSpriteKey('player');
            if (!tex || !this.player.anims) return;

            // Flip sprite based on direction
            if (moveLeft) this.player.setFlipX(true);
            else if (moveRight) this.player.setFlipX(false);

            if (gameType === 'topdown') {
                if (isMoving && this.anims.exists('player-run')) {
                    this.player.anims.play('player-run', true);
                } else if (this.anims.exists('player-idle')) {
                    this.player.anims.play('player-idle', true);
                }
            } else {
                if (!this.player.body.onFloor() && this.anims.exists('player-jump')) {
                    this.player.anims.play('player-jump', true);
                } else if ((moveLeft || moveRight) && this.anims.exists('player-run')) {
                    this.player.anims.play('player-run', true);
                } else if (this.anims.exists('player-idle')) {
                    this.player.anims.play('player-idle', true);
                }
            }
        }

        // ── Background ──

        _createBackground() {
            const W = this.scale.width;
            const H = this.scale.height;
            this._bgLayers = [];

            const bgRoles = ['bg_far', 'bg_mid', 'background', 'bg_near'];
            const scrollFactors = [0.1, 0.2, 0.3, 0.6];

            for (let i = 0; i < bgRoles.length; i++) {
                const role = bgRoles[i];
                const bgSprite = sprites[role];
                if (!bgSprite) continue;
                const bgKey = this._getSpriteKey(role);
                if (!bgKey) continue;

                const layer = this.add.tileSprite(W / 2, H / 2, W, H, bgKey);
                layer.setScrollFactor(0);
                layer.setDepth(-10 + i);
                layer.setAlpha(1 - i * 0.15);
                this._bgLayers.push({ obj: layer, scrollFactor: scrollFactors[i] });
            }

            if (this._bgLayers.length > 0) return;

            // Fallback procedural background for topdown
            if (gameType === 'topdown') {
                this._createProceduralBackground(W, H);
            }
        }

        _createProceduralBackground(W, H) {
            const gfx = this.add.graphics();
            gfx.setDepth(-10);

            const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];

            // Base ground
            gfx.fillStyle(0x1a2e1a);
            gfx.fillRect(0, 0, W, H);

            // Dirt patches
            const dirtColors = [0x2d1f0e, 0x3a2a14, 0x1e1508];
            for (let i = 0; i < 15; i++) {
                gfx.fillStyle(pick(dirtColors), 0.4);
                const dx = 20 + Math.random() * (W - 40);
                const dy = 20 + Math.random() * (H - 40);
                const rw = 20 + Math.random() * 40;
                const rh = 15 + Math.random() * 25;
                gfx.fillRoundedRect(dx - rw / 2, dy - rh / 2, rw, rh, 6);
            }

            // Grass tufts
            const grassColors = [0x2d5a1e, 0x3a7a2e, 0x1e4a14, 0x4a8c3f];
            for (let i = 0; i < 50; i++) {
                gfx.fillStyle(pick(grassColors), 0.6);
                const gx = Math.random() * W;
                const gy = Math.random() * H;
                gfx.fillRect(gx, gy, 3 + Math.random() * 6, 1 + Math.random() * 3);
            }

            // Small flowers
            const flowerColors = [0xff6b1a, 0xffd23f, 0xc84b31, 0x9b59b6];
            for (let i = 0; i < 10; i++) {
                gfx.fillStyle(pick(flowerColors), 0.7);
                const fx = 25 + Math.random() * (W - 50);
                const fy = 25 + Math.random() * (H - 50);
                gfx.fillCircle(fx, fy, 2);
                // Tiny leaf
                gfx.fillStyle(0x2d5a1e, 0.5);
                gfx.fillRect(fx + 2, fy + 1, 3, 1);
            }

            // Dirt path trails
            gfx.lineStyle(3, 0x3a2a14, 0.25);
            for (let i = 0; i < 2; i++) {
                const sx = Math.random() * W;
                const sy = Math.random() * H;
                gfx.beginPath();
                gfx.moveTo(sx, sy);
                for (let j = 0; j < 5; j++) {
                    gfx.lineTo(
                        sx + (Math.random() - 0.5) * 150,
                        sy + (Math.random() - 0.5) * 150
                    );
                }
                gfx.strokePath();
            }

            // Small stones
            for (let i = 0; i < 6; i++) {
                gfx.fillStyle(0x555555, 0.3);
                gfx.fillCircle(
                    20 + Math.random() * (W - 40),
                    20 + Math.random() * (H - 40),
                    1.5 + Math.random() * 2
                );
            }
        }

        _scrollBackground() {
            if (!this._bgLayers || !this._bgLayers.length) return;
            const camX = this.cameras.main.scrollX;
            const camY = this.cameras.main.scrollY;
            for (const layer of this._bgLayers) {
                if (layer.obj && layer.obj.tilePositionY !== undefined) {
                    layer.obj.tilePositionY = camY * layer.scrollFactor;
                    layer.obj.tilePositionX = camX * layer.scrollFactor;
                }
            }
        }

        // ── Zones (interactable areas) ──

        _createZones() {
            const zonesCfg = entities.zones;
            if (!zonesCfg || !Array.isArray(zonesCfg) || zonesCfg.length === 0) return;

            this._zones = [];
            for (const zCfg of zonesCfg) {
                const states = zCfg.states || {};
                const initialState = zCfg.initialState || Object.keys(states)[0] || 'default';
                const stateData = states[initialState] || {};
                const color = stateData.color
                    ? Phaser.Display.Color.HexStringToColor(stateData.color).color
                    : 0x5b3a29;

                // Visual
                const rect = this.add.rectangle(zCfg.x, zCfg.y, zCfg.w || 40, zCfg.h || 40, color);
                rect.setStrokeStyle(2, 0x000000, 0.4);

                // Label (hidden by default)
                const label = this.add.text(zCfg.x, zCfg.y - (zCfg.h || 40) / 2 - 10, '', {
                    fontFamily: '"Press Start 2P"',
                    fontSize: '6px',
                    color: '#ffffff',
                    stroke: '#000000',
                    strokeThickness: 2,
                    backgroundColor: 'rgba(0,0,0,0.6)',
                    padding: { x: 3, y: 2 },
                }).setOrigin(0.5).setDepth(50).setVisible(false);

                const zone = {
                    id: zCfg.id,
                    cfg: zCfg,
                    rect,
                    label,
                    currentState: initialState,
                    states,
                    autoTimer: null,
                    nearby: false,
                };

                // Set initial label
                label.setText(stateData.label || zCfg.id);

                // Start autoNext timer if initial state has one
                if (stateData.autoNext) {
                    zone.autoTimer = this.time.delayedCall(stateData.autoNext * 1000, () => {
                        this._advanceZoneState(zone);
                    });
                }

                this._zones.push(zone);
            }
        }

        _updateZones(interact) {
            if (!this._zones || !this.player) return;

            const px = this.player.x;
            const py = this.player.y;
            const interactDist = 40;

            for (const zone of this._zones) {
                const dx = px - zone.rect.x;
                const dy = py - zone.rect.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                const isNear = dist < interactDist + Math.max(zone.cfg.w || 40, zone.cfg.h || 40) / 2;

                if (isNear && !zone.nearby) {
                    zone.nearby = true;
                    zone.label.setVisible(true);
                    zone.rect.setStrokeStyle(2, 0xffd23f, 0.8);
                } else if (!isNear && zone.nearby) {
                    zone.nearby = false;
                    zone.label.setVisible(false);
                    zone.rect.setStrokeStyle(2, 0x000000, 0.4);
                }

                if (isNear && interact) {
                    this._interactWithZone(zone);
                }
            }
        }

        _interactWithZone(zone) {
            const stateData = zone.states[zone.currentState];
            if (!stateData || !stateData.onInteract) return;

            const action = stateData.onInteract;

            switch (action.type) {
                case 'give_item': {
                    this._inventory = action.item;
                    this._updateInventoryHUD();
                    this._executeAction({
                        type: 'flash_text',
                        text: `+${action.item.toUpperCase()}`,
                        color: '#4fc3f7',
                        size: '8px',
                        duration: 1000,
                    });
                    break;
                }

                case 'need_item': {
                    if (this._inventory !== action.item) {
                        this._executeAction({
                            type: 'flash_text',
                            text: `Necesitas: ${action.item}`,
                            color: '#ff5c8a',
                            size: '7px',
                            duration: 1200,
                        });
                        return;
                    }
                    if (action.consume) this._inventory = null;
                    this._updateInventoryHUD();
                    this._advanceZoneState(zone);
                    break;
                }

                case 'next_state': {
                    this._advanceZoneState(zone);
                    break;
                }

                case 'harvest': {
                    this.score += (action.score || 100);
                    this._updateHUD();
                    this._executeAction({
                        type: 'flash_text',
                        text: `+${action.score || 100}`,
                        color: '#3ddc97',
                        size: '10px',
                        duration: 1200,
                    });
                    const resetTo = action.resetTo || 'empty';
                    this._setZoneState(zone, resetTo);
                    break;
                }

                case 'unlock': {
                    const cost = action.cost || 0;
                    if (this.score < cost) {
                        this._executeAction({
                            type: 'flash_text',
                            text: `Necesitas ${cost} pts`,
                            color: '#ff5c8a',
                            size: '7px',
                            duration: 1200,
                        });
                        return;
                    }
                    this.score -= cost;
                    this._updateHUD();
                    this._advanceZoneState(zone);
                    this._executeAction({
                        type: 'flash_text',
                        text: 'Desbloqueado!',
                        color: '#ffd23f',
                        size: '9px',
                        duration: 1500,
                    });
                    break;
                }
            }
        }

        _advanceZoneState(zone) {
            const stateNames = Object.keys(zone.states);
            const idx = stateNames.indexOf(zone.currentState);
            const nextIdx = idx + 1;
            if (nextIdx < stateNames.length) {
                this._setZoneState(zone, stateNames[nextIdx]);
            }
        }

        _setZoneState(zone, stateName) {
            if (!zone.states[stateName]) return;

            // Cancel existing auto timer
            if (zone.autoTimer) {
                zone.autoTimer.remove(false);
                zone.autoTimer = null;
            }

            zone.currentState = stateName;
            const stateData = zone.states[stateName];

            // Update visual
            if (stateData.color) {
                const c = Phaser.Display.Color.HexStringToColor(stateData.color).color;
                zone.rect.setFillStyle(c);
            }

            // Update label
            zone.label.setText(stateData.label || stateName);

            // Auto-advance timer
            if (stateData.autoNext) {
                zone.autoTimer = this.time.delayedCall(stateData.autoNext * 1000, () => {
                    this._advanceZoneState(zone);
                });
            }
        }

        _updateInventoryHUD() {
            if (!this._inventoryText) return;
            if (this._inventory) {
                const icons = { water: 'AGUA', seeds: 'SEMILLA', wood: 'MADERA' };
                this._inventoryText.setText(icons[this._inventory] || this._inventory.toUpperCase());
            } else {
                this._inventoryText.setText('');
            }
        }

        // ── Event System ──

        _initEvents() {
            this._eventWatchers = [];
            this._eventTimers = [];
            const evts = config.events;
            if (!evts || !Array.isArray(evts)) return;

            for (const evt of evts) {
                const trigger = evt.trigger;
                const actions = evt.actions;
                if (!trigger || !actions) continue;

                if (trigger.type === 'timer') {
                    const delaySec = trigger.delay || 10;
                    const startAfter = (trigger.startAfter || 0) * 1000;
                    const setup = () => {
                        const timerEvt = this.time.addEvent({
                            delay: delaySec * 1000,
                            callback: () => this._executeActions(actions),
                            loop: trigger.repeat === true,
                        });
                        this._eventTimers.push(timerEvt);
                    };
                    if (startAfter > 0) {
                        this.time.delayedCall(startAfter, setup);
                    } else {
                        setup();
                    }
                } else {
                    // Conditional watcher — checked every frame in _checkEvents
                    this._eventWatchers.push({
                        trigger,
                        actions,
                        fired: false,
                    });
                }
            }
        }

        _checkEvents() {
            if (!this._eventWatchers) return;
            for (const w of this._eventWatchers) {
                if (w.fired) continue;
                let met = false;
                const t = w.trigger;

                switch (t.type) {
                    case 'score':
                        met = this.score >= t.value;
                        break;
                    case 'time':
                        met = this._elapsedTime >= t.seconds;
                        break;
                    case 'lives':
                        met = this.lives <= t.value;
                        break;
                    case 'enemy_count':
                        met = this.enemies
                            ? this.enemies.countActive() <= t.value
                            : true;
                        break;
                    case 'collect_count':
                        met = this._totalCollected >= t.value;
                        break;
                }

                if (met) {
                    w.fired = true;
                    this._executeActions(w.actions);
                }
            }
        }

        _executeActions(actions) {
            if (!actions || !Array.isArray(actions)) return;
            for (const a of actions) {
                this._executeAction(a);
            }
        }

        _executeAction(a) {
            const W = this.scale.width;
            const H = this.scale.height;

            switch (a.type) {
                // ── Spawn entities ──
                case 'spawn': {
                    const count = a.count || 1;
                    for (let i = 0; i < count; i++) {
                        const sx = a.x ?? (30 + Math.random() * (W - 60));
                        const sy = a.y ?? (30 + Math.random() * (H - 60));
                        if (a.entity === 'enemies') {
                            this._spawnEnemy(sx, sy, {
                                speed: a.speed,
                                ai: a.ai,
                                color: a.color,
                                width: a.width,
                                height: a.height,
                            });
                        } else if (a.entity === 'collectibles') {
                            this._spawnCoin(sx, sy);
                        }
                    }
                    break;
                }

                // ── Set property on target ──
                case 'set_property': {
                    if (a.target === 'player') {
                        if (a.property === 'speed') this.playerSpeed = a.value;
                        else if (a.property === 'scale') this.player.setScale(a.value);
                        else if (a.property === 'jumpForce') this.jumpForce = a.value;
                    } else if (a.target === 'enemies' && this.enemies) {
                        this.enemies.children.iterate(e => {
                            if (!e || !e.active) return;
                            if (a.property === 'speed') e.setData('speed', a.value);
                            else if (a.property === 'ai') e.setData('ai', a.value);
                            else if (a.property === 'scale') e.setScale(a.value);
                        });
                    }
                    break;
                }

                // ── Flash text on screen ──
                case 'flash_text': {
                    const txt = this.add.text(W / 2, H / 2, a.text || '', {
                        fontFamily: '"Press Start 2P"',
                        fontSize: a.size || '12px',
                        color: a.color || '#ffffff',
                        stroke: '#000000',
                        strokeThickness: 3,
                    }).setOrigin(0.5).setScrollFactor(0).setDepth(200);

                    this.tweens.add({
                        targets: txt,
                        alpha: { from: 1, to: 0 },
                        y: txt.y - 30,
                        duration: a.duration || 2000,
                        ease: 'Power2',
                        onComplete: () => txt.destroy(),
                    });
                    break;
                }

                // ── Camera shake ──
                case 'shake_camera': {
                    this.cameras.main.shake(
                        a.duration || 200,
                        a.intensity || 0.01
                    );
                    break;
                }

                // ── Tint entities ──
                case 'tint': {
                    const color = typeof a.color === 'string'
                        ? Phaser.Display.Color.HexStringToColor(a.color).color
                        : a.color;
                    const dur = a.duration || 2000;

                    const applyTint = (obj) => {
                        if (!obj || !obj.active) return;
                        if (obj.setTint) obj.setTint(color);
                        this.time.delayedCall(dur, () => {
                            if (obj.active && obj.clearTint) obj.clearTint();
                        });
                    };

                    if (a.target === 'player') {
                        applyTint(this.player);
                    } else if (a.target === 'enemies' && this.enemies) {
                        this.enemies.children.iterate(applyTint);
                    } else if (a.target === 'collectibles' && this.collectibles) {
                        this.collectibles.children.iterate(applyTint);
                    }
                    break;
                }

                // ── Modify score ──
                case 'add_score': {
                    this.score += (a.value || 0);
                    this._updateHUD();
                    break;
                }

                // ── Modify lives ──
                case 'add_lives': {
                    this.lives += (a.value || 0);
                    this._updateHUD();
                    break;
                }

                // ── Modify game timer ──
                case 'set_timer': {
                    if (this.timeLeft !== undefined) {
                        this.timeLeft += (a.value || 0);
                        this._updateHUD();
                    }
                    break;
                }

                // ── Change background color ──
                case 'change_background': {
                    if (a.color) {
                        this.cameras.main.setBackgroundColor(a.color);
                    }
                    break;
                }
            }
        }

        // ── Spawn single enemy (reusable) ──

        _spawnEnemy(x, y, overrides) {
            const enemyCfg = entities.enemies || {};
            const ov = overrides || {};
            const speed = ov.speed || enemyCfg.speed || 60;
            const ai = ov.ai || enemyCfg.ai || 'patrol';
            const W = this.scale.width;

            if (!this.enemies) {
                this.enemies = this.physics.add.group();
                // Setup collisions for newly created group
                if (this.platforms) {
                    this.physics.add.collider(this.enemies, this.platforms);
                }
                this.physics.add.overlap(this.player, this.enemies, (player, enemy) => {
                    this.lives--;
                    if (this.lives <= 0) {
                        this.scene.start('GameOverScene', { score: this.score });
                    } else {
                        this.tweens.add({
                            targets: this.player,
                            alpha: 0.3,
                            duration: 100,
                            yoyo: true,
                            repeat: 3,
                        });
                        enemy.destroy();
                        this._updateHUD();
                    }
                });
            }

            const enemyTex = this._getSpriteKey('enemy');
            const colorHex = ov.color || enemyCfg.color || '#ff5c8a';
            const color = Phaser.Display.Color.HexStringToColor(colorHex).color;
            const ew = ov.width || enemyCfg.width || 16;
            const eh = ov.height || enemyCfg.height || 16;

            let enemy;
            if (enemyTex) {
                enemy = this.add.sprite(x, y, enemyTex);
                enemy.setDisplaySize(ew, eh);
            } else {
                enemy = this.add.rectangle(x, y, ew, eh, color);
            }

            this.physics.add.existing(enemy);
            enemy.body.setCollideWorldBounds(true);
            if (gameType === 'topdown') {
                enemy.body.setBounce(1, 1);
                enemy.body.setAllowGravity(false);
                if (ai === 'patrol') {
                    const angle = Math.random() * Math.PI * 2;
                    enemy.body.setVelocity(Math.cos(angle) * speed, Math.sin(angle) * speed);
                }
            } else {
                enemy.body.setBounce(1, 0);
                enemy.body.setVelocityX(speed * (Math.random() > 0.5 ? 1 : -1));
                enemy.body.setAllowGravity(true);
            }
            enemy.setData('ai', ai);
            enemy.setData('speed', speed);
            enemy.setData('minX', 20);
            enemy.setData('maxX', W - 20);
            if (enemy.setPipeline) enemy.setPipeline('Light2D');
            this.enemies.add(enemy);
            return enemy;
        }

        // ── HUD ──

        _updateHUD() {
            let text = `Score: ${this.score}`;
            if (this.lives > 1) text += `  Lives: ${this.lives}`;
            if (this.timeLeft !== undefined) text += `  Time: ${this.timeLeft}`;
            if (this.hudText) this.hudText.setText(text);
        }

        // ── Platforms ──

        _createPlatforms() {
            const platCfg = entities.platforms;
            if (!platCfg) return;

            this.platforms = this.physics.add.staticGroup();
            const W = this.scale.width;
            const H = this.scale.height;
            const color = Phaser.Display.Color.HexStringToColor(platCfg.color || '#c84b31').color;
            const platW = platCfg.width || 80;
            const platH = platCfg.height || 14;
            const isOneWay = platCfg.oneWay !== false;
            const platTex = this._getSpriteKey('platform');

            if (platCfg.layout === 'procedural') {
                const proc = platCfg.procedural || {};
                const count = proc.count || 15;
                const minGap = proc.minGap || 40;
                const maxGap = proc.maxGap || 80;
                const isRunner = config.metadata?.type === 'runner';

                if (isRunner) {
                    // Runner: starting platform under spawn, then generate downward
                    const spawnY = (entities.player?.spawn?.y) || 80;
                    const startPlat = this._createPlatformObj(W / 2, spawnY + 30, W, platH, color, platTex);
                    this.platforms.add(startPlat);
                    startPlat.body.updateFromGameObject();
                    startPlat.setData('oneWay', false);

                    this._lastPlatY = spawnY + 30;
                    for (let i = 0; i < count; i++) {
                        this._lastPlatY += minGap + Math.random() * (maxGap - minGap);
                        const w = (proc.minWidth || 60) + Math.random() * ((proc.maxWidth || 140) - (proc.minWidth || 60));
                        const x = Math.random() * (W - w) + w / 2;
                        const p = this._createPlatformObj(x, this._lastPlatY, w, platH, color, platTex);
                        this.platforms.add(p);
                        p.body.updateFromGameObject();
                        p.setData('oneWay', isOneWay);
                    }
                } else {
                    // Platformer: ground + generate upward
                    // Ground
                    for (let x = 0; x < W; x += 32) {
                        const ground = this._createPlatformObj(x + 16, H - 10, 32, 20, color, platTex);
                        this.platforms.add(ground);
                        ground.body.updateFromGameObject();
                        ground.setData('oneWay', false);
                    }

                    this._lastPlatY = H - 60;
                    for (let i = 0; i < count; i++) {
                        this._lastPlatY -= minGap + Math.random() * (maxGap - minGap);
                        const w = (proc.minWidth || 60) + Math.random() * ((proc.maxWidth || 140) - (proc.minWidth || 60));
                        const x = Math.random() * (W - w) + w / 2;
                        const p = this._createPlatformObj(x, this._lastPlatY, w, platH, color, platTex);
                        this.platforms.add(p);
                        p.body.updateFromGameObject();
                        p.setData('oneWay', isOneWay);
                    }
                }
            } else if (platCfg.positions) {
                platCfg.positions.forEach(pos => {
                    const p = this._createPlatformObj(pos.x, pos.y, pos.w || platW, pos.h || platH, color, platTex);
                    this.platforms.add(p);
                    p.body.updateFromGameObject();
                    p.setData('oneWay', pos.oneWay !== undefined ? pos.oneWay : isOneWay);
                });
            }
        }

        _createPlatformObj(x, y, w, h, color, textureKey) {
            if (textureKey && w >= h && h <= 20) {
                return this.add.tileSprite(x, y, w, h, textureKey);
            }

            // For topdown: draw styled wall as texture, return a rectangle with that texture
            if (gameType === 'topdown') {
                const key = `wall_${w}x${h}`;
                if (!this.textures.exists(key)) {
                    const gfx = this.add.graphics();
                    // Shadow
                    gfx.fillStyle(0x000000, 0.3);
                    gfx.fillRect(2, 2, w, h);
                    // Body
                    gfx.fillStyle(0x3a2a14);
                    gfx.fillRect(0, 0, w, h);
                    // Inner
                    gfx.fillStyle(0x5b3a29);
                    gfx.fillRect(2, 2, w - 4, h - 4);
                    // Top highlight
                    gfx.fillStyle(0x8b6b4a, 0.6);
                    gfx.fillRect(0, 0, w, 2);
                    gfx.generateTexture(key, w + 2, h + 2);
                    gfx.destroy();
                }
                const img = this.add.image(x, y, key);
                img.setDisplaySize(w, h);
                return img;
            }

            return this.add.rectangle(x, y, w, h, color);
        }

        _generateMore() {
            if (!this.platforms || !this.player) return;
            const proc = entities.platforms?.procedural || {};
            const minGap = proc.minGap || 40;
            const maxGap = proc.maxGap || 80;
            const W = this.scale.width;
            const color = Phaser.Display.Color.HexStringToColor(entities.platforms?.color || '#c84b31').color;
            const platH = entities.platforms?.height || 14;
            const isOneWay = entities.platforms?.oneWay !== false;
            const platTex = this._getSpriteKey('platform');
            const isRunner = config.metadata?.type === 'runner';

            if (isRunner) {
                // Generate platforms BELOW camera (scrolling down)
                const targetY = this.cameras.main.scrollY + this.scale.height + 200;
                while (this._lastPlatY < targetY) {
                    this._lastPlatY += minGap + Math.random() * (maxGap - minGap);
                    const w = (proc.minWidth || 60) + Math.random() * ((proc.maxWidth || 140) - (proc.minWidth || 60));
                    const x = Math.random() * (W - w) + w / 2;
                    const p = this._createPlatformObj(x, this._lastPlatY, w, platH, color, platTex);
                    this.platforms.add(p);
                    p.body.updateFromGameObject();
                    p.setData('oneWay', isOneWay);

                    const spawnRate = entities.collectibles?.spawnRate || 0.3;
                    if (this.collectibles && Math.random() < spawnRate) {
                        this._spawnCoin(x, this._lastPlatY - 20);
                    }
                }
            } else {
                // Generate platforms ABOVE camera (climbing up)
                while (this._lastPlatY > this.cameras.main.scrollY - 200) {
                    this._lastPlatY -= minGap + Math.random() * (maxGap - minGap);
                    const w = (proc.minWidth || 60) + Math.random() * ((proc.maxWidth || 140) - (proc.minWidth || 60));
                    const x = Math.random() * (W - w) + w / 2;
                    const p = this._createPlatformObj(x, this._lastPlatY, w, platH, color, platTex);
                    this.platforms.add(p);
                    p.body.updateFromGameObject();
                    p.setData('oneWay', isOneWay);

                    const spawnRate = entities.collectibles?.spawnRate || 0.3;
                    if (this.collectibles && Math.random() < spawnRate) {
                        this._spawnCoin(x, this._lastPlatY - 20);
                    }
                }
            }

            // Hybrid culling: hide nearby off-screen, destroy far away
            const H = this.scale.height;
            const viewTop = this.cameras.main.scrollY - 200;
            const viewBot = this.cameras.main.scrollY + H + 200;
            const destroyAbove = this.cameras.main.scrollY - H * 3;
            const destroyBelow = this.cameras.main.scrollY + H * 3;

            this.platforms.children.iterate(p => {
                if (!p) return;

                // Too far in either direction — destroy to free memory
                if (p.y > destroyBelow || p.y < destroyAbove) {
                    p.destroy();
                    return;
                }

                const inView = p.y >= viewTop && p.y <= viewBot;

                if (!inView && p.visible) {
                    p.setVisible(false);
                    p.body.enable = false;
                } else if (inView && !p.visible) {
                    p.setVisible(true);
                    p.body.enable = true;
                }
            });
        }

        // ── Collectibles ──

        _createCollectibles() {
            const collCfg = entities.collectibles;
            if (!collCfg) return;

            this.collectibles = this.physics.add.group({ allowGravity: false });

            // Setup coin animation if sprite exists
            const coinTex = this._getSpriteKey('coin');
            if (coinTex) {
                const coinSprite = sprites.coin;
                const fc = coinSprite?.frame_count || 1;
                if (fc > 1 && !this.anims.exists('coin-spin')) {
                    this.anims.create({
                        key: 'coin-spin',
                        frames: this.anims.generateFrameNumbers(coinTex, { start: 0, end: fc - 1 }),
                        frameRate: 8,
                        repeat: -1,
                    });
                }
            }

            // Fixed positions from studio editor
            if (collCfg.positions && collCfg.positions.length > 0) {
                for (const pos of collCfg.positions) {
                    this._spawnCoin(pos.x, pos.y);
                }
            }

            // For topdown/catch: spawn collectibles across the map
            if (gameType === 'topdown' || gameType === 'catch') {
                const W = this.scale.width;
                const H = this.scale.height;
                const count = collCfg.initialCount || Math.floor((collCfg.spawnRate || 0.3) * 30);
                for (let i = 0; i < count; i++) {
                    const cx = 30 + Math.random() * (W - 60);
                    const cy = 30 + Math.random() * (H - 60);
                    this._spawnCoin(cx, cy);
                }

                // Respawn collectibles periodically
                if (collCfg.spawnRate) {
                    this.time.addEvent({
                        delay: 3000,
                        callback: () => {
                            if (this.collectibles.countActive() < count) {
                                const rx = 30 + Math.random() * (W - 60);
                                const ry = 30 + Math.random() * (H - 60);
                                this._spawnCoin(rx, ry);
                            }
                        },
                        loop: true,
                    });
                }
            }
        }

        _spawnCoin(x, y) {
            const coinTex = this._getSpriteKey('coin');
            const collCfg = entities.collectibles || {};
            let coin;

            if (coinTex) {
                coin = this.add.sprite(x, y, coinTex, 0);
                coin.setDisplaySize(12, 12);
                if (this.anims.exists('coin-spin')) {
                    coin.anims.play('coin-spin');
                }
            } else {
                coin = this.add.circle(x, y, 6,
                    Phaser.Display.Color.HexStringToColor(collCfg.color || '#ffd23f').color);
            }
            if (coin.setPipeline) coin.setPipeline('Light2D');

            this.physics.add.existing(coin);
            coin.body.setAllowGravity(false);
            this.collectibles.add(coin);

            // Add a small light over each coin
            if (this.lights && typeof this.lights.addLight === 'function') {
                try {
                    const cl = this.lights.addLight(x, y, 60, 0xffdd44, 0.6);
                    if (this._coinLights) this._coinLights.push(cl);
                } catch (e) {}
            }

            return coin;
        }

        // ── Enemies ──

        _createEnemies() {
            const enemyCfg = entities.enemies;
            if (!enemyCfg || (!enemyCfg.count && !enemyCfg.positions?.length)) return;

            this.enemies = this.physics.add.group();
            const W = this.scale.width;
            const H = this.scale.height;
            const color = Phaser.Display.Color.HexStringToColor(enemyCfg.color || '#ff5c8a').color;
            const speed = enemyCfg.speed || 60;
            const enemyTex = this._getSpriteKey('enemy');

            for (let i = 0; i < enemyCfg.count; i++) {
                let x, y;
                if (gameType === 'topdown') {
                    // Scatter enemies across the map, avoiding player spawn area
                    const spawnX = entities.player?.spawn?.x || W / 2;
                    const spawnY = entities.player?.spawn?.y || H / 2;
                    do {
                        x = 40 + Math.random() * (W - 80);
                        y = 40 + Math.random() * (H - 80);
                    } while (Math.abs(x - spawnX) < 80 && Math.abs(y - spawnY) < 80);
                } else {
                    x = 50 + Math.random() * (W - 100);
                    y = H - 60 - (i + 1) * 120;
                }

                let enemy;
                if (enemyTex) {
                    enemy = this.add.sprite(x, y, enemyTex);
                    enemy.setDisplaySize(enemyCfg.width || 16, enemyCfg.height || 16);
                } else {
                    enemy = this.add.rectangle(x, y, enemyCfg.width || 16, enemyCfg.height || 16, color);
                }

                this.physics.add.existing(enemy);
                enemy.body.setCollideWorldBounds(true);
                if (gameType === 'topdown') {
                    enemy.body.setBounce(1, 1);
                    // Give patrol enemies random 2D velocity
                    if ((enemyCfg.ai || 'patrol') === 'patrol') {
                        const angle = Math.random() * Math.PI * 2;
                        enemy.body.setVelocity(Math.cos(angle) * speed, Math.sin(angle) * speed);
                    }
                } else {
                    enemy.body.setBounce(1, 0);
                    enemy.body.setVelocityX(speed * (Math.random() > 0.5 ? 1 : -1));
                }
                enemy.body.setAllowGravity(gameType === 'topdown' ? false : true);
                    enemy.setData('ai', enemyCfg.ai || 'patrol');
                    enemy.setData('speed', speed);
                    enemy.setData('minX', 20);
                    enemy.setData('maxX', W - 20);
                    if (enemy.setPipeline) enemy.setPipeline('Light2D');
                    this.enemies.add(enemy);
            }

            // Fixed positions from studio editor
            if (enemyCfg.positions && enemyCfg.positions.length > 0) {
                for (const pos of enemyCfg.positions) {
                    let enemy;
                    if (enemyTex) {
                        enemy = this.add.sprite(pos.x, pos.y, enemyTex);
                        enemy.setDisplaySize(enemyCfg.width || 16, enemyCfg.height || 16);
                    } else {
                        enemy = this.add.rectangle(pos.x, pos.y, enemyCfg.width || 16, enemyCfg.height || 16, color);
                    }
                this.physics.add.existing(enemy);
                enemy.body.setCollideWorldBounds(true);
                if (gameType === 'topdown') {
                    enemy.body.setBounce(1, 1);
                    enemy.body.setAllowGravity(false);
                    if ((enemyCfg.ai || 'patrol') === 'patrol') {
                        const angle = Math.random() * Math.PI * 2;
                        enemy.body.setVelocity(Math.cos(angle) * speed, Math.sin(angle) * speed);
                    }
                } else {
                    enemy.body.setBounce(1, 0);
                    enemy.body.setVelocityX(speed * (Math.random() > 0.5 ? 1 : -1));
                }
                enemy.body.setAllowGravity(gameType === 'topdown' ? false : true);
                enemy.setData('ai', enemyCfg.ai || 'patrol');
                enemy.setData('speed', speed);
                enemy.setData('minX', 20);
                enemy.setData('maxX', W - 20);
                if (enemy.setPipeline) enemy.setPipeline('Light2D');
                this.enemies.add(enemy);
                }
            }
        }
    };
}

function createGameOverScene(config, handInput, onGameOver) {
    const screens = config.screens || {};
    const gameOverCfg = screens.gameOver || {};

    return class GameOverScene extends Phaser.Scene {
        constructor() {
            super('GameOverScene');
        }

        init(data) {
            this.finalScore = data.score || 0;
            this.won = data.won || false;
        }

        create() {
            const W = this.scale.width;
            const H = this.scale.height;
            const cfg = this.won
                ? { title: gameOverCfg.winTitle || 'GANASTE!', titleColor: gameOverCfg.winTitleColor || '#3ddc97', prompt: gameOverCfg.winPrompt || 'SPACE / Click para salir' }
                : { title: gameOverCfg.loseTitle || 'GAME OVER', titleColor: gameOverCfg.loseTitleColor || '#ff5c8a', prompt: gameOverCfg.losePrompt || 'SPACE / Cierra un dedo para reiniciar' };

            createOverlayScreen(this, {
                title: cfg.title,
                titleColor: cfg.titleColor,
                titleSize: gameOverCfg.titleSize || '14px',
                subtitle: `Score: ${this.finalScore}`,
                subtitleColor: gameOverCfg.subtitleColor || '#ffd23f',
                subtitleSize: gameOverCfg.subtitleSize,
                prompt: cfg.prompt,
                promptColor: gameOverCfg.promptColor,
                promptSize: gameOverCfg.promptSize,
                backgroundColor: gameOverCfg.backgroundColor || config.world?.backgroundColor || '#1a0a2e',
                backgroundAlpha: gameOverCfg.backgroundAlpha ?? 0.92,
                delay: gameOverCfg.delay ?? 800,
                handInput,
                onTrigger: () => {
                    if (this.won && onGameOver) {
                        onGameOver(this.finalScore, this.won);
                    } else {
                        this.scene.start('PlayScene');
                    }
                },
            });
        }
    };
}
