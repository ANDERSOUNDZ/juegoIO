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
     * @returns {Phaser.Game}
     */
    load(config, containerId, handInput) {
        const physics = config.physics || { type: 'arcade', gravity: { x: 0, y: 300 } };
        const world = config.world || { width: 400, height: 600 };

        const phaserConfig = {
            type: Phaser.AUTO,
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
                createPlayScene(config, handInput),
                createGameOverScene(config),
            ],
            pixelArt: true,
        };

        return new Phaser.Game(phaserConfig);
    },
};

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
            this.scene.start('PlayScene');
        }
    };
}

function createPlayScene(config, handInput) {
    const entities = config.entities || {};
    const controls = config.controls || {};
    const rules = config.rules || {};
    const world = config.world || {};
    const sprites = config.sprites || {};
    const fingerMap = controls.fingerMap || { '0': 'jump', '1': 'right', '2': 'left' };

    return class PlayScene extends Phaser.Scene {
        constructor() {
            super('PlayScene');
            this.score = 0;
            this.lives = rules.lives || 1;
            this.gameTimer = null;
        }

        create() {
            const W = this.scale.width;
            const H = this.scale.height;

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

            // Expose fingerMap for live config changes
            this._fingerMap = Object.assign({}, fingerMap);

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
                    item.destroy();
                    this.score += (entities.collectibles?.scoreValue || 100);
                    this._updateHUD();
                });
            }

            if (this.enemies) {
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

            // Camera
            this._autoScroll = world.camera?.autoScroll || null;
            if (this._autoScroll) {
                // Auto-scroll: don't follow player, camera moves on its own
                this.cameras.main.scrollY = 0;
            } else if (world.camera?.follow === 'player') {
                this.cameras.main.startFollow(this.player, true, 0.1, 0.1);
                if (world.camera.scrollY) {
                    this.cameras.main.setDeadzone(W, H * 0.3);
                }
            }
            this.physics.world.setBounds(0, -10000, W, 20000 + H);

            // Timer
            if (rules.timer) {
                this.timeLeft = rules.timer;
                this.time.addEvent({
                    delay: 1000,
                    callback: () => {
                        this.timeLeft--;
                        this._updateHUD();
                        if (this.timeLeft <= 0) {
                            this.scene.start('GameOverScene', { score: this.score });
                        }
                    },
                    loop: true,
                });
            }

            // HUD
            this.hudText = this.add.text(10, 10, '', {
                fontFamily: '"Press Start 2P"',
                fontSize: '8px',
                color: '#ffd23f',
            }).setScrollFactor(0).setDepth(100);
            this._updateHUD();

            // Keyboard fallback
            this.cursors = this.input.keyboard.createCursorKeys();
            this.spaceKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.SPACE);
        }

        update() {
            if (!this.player || !this.player.body) return;

            // Get actions from hand input OR keyboard
            const handActions = handInput ? handInput.getMappedActions(this._fingerMap) : {};
            const kbLeft = this.cursors.left.isDown;
            const kbRight = this.cursors.right.isDown;
            const kbJump = this.cursors.up.isDown || this.spaceKey.isDown;

            const moveLeft = handActions.left || kbLeft;
            const moveRight = handActions.right || kbRight;
            const jump = handActions.jump || kbJump;

            // Apply movement
            this.player.body.setVelocityX(0);
            if (moveLeft) this.player.body.setVelocityX(-this.playerSpeed);
            if (moveRight) this.player.body.setVelocityX(this.playerSpeed);

            if (jump && this.player.body.onFloor()) {
                this.player.body.setVelocityY(this.jumpForce);
            }

            // Player animation
            this._animatePlayer(moveLeft, moveRight);

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
                        const spd = enemy.getData('speed');
                        enemy.body.setVelocityX(dx > 0 ? spd : -spd);
                    }
                });
            }

            // Win condition check
            if (rules.winCondition?.type === 'score' && this.score >= rules.winCondition.target) {
                this.scene.start('GameOverScene', { score: this.score, won: true });
            }

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

            // Parallax background scroll
            this._scrollBackground();
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
            if (fc >= 4) {
                this.anims.create({
                    key: 'player-idle',
                    frames: [{ key: textureKey, frame: 0 }],
                    frameRate: 1,
                });
                this.anims.create({
                    key: 'player-run',
                    frames: this.anims.generateFrameNumbers(textureKey, { start: 1, end: fc - 2 }),
                    frameRate: 8,
                    repeat: -1,
                });
                this.anims.create({
                    key: 'player-jump',
                    frames: [{ key: textureKey, frame: fc - 1 }],
                    frameRate: 1,
                });
            } else if (fc >= 2) {
                this.anims.create({
                    key: 'player-idle',
                    frames: [{ key: textureKey, frame: 0 }],
                    frameRate: 1,
                });
                this.anims.create({
                    key: 'player-run',
                    frames: this.anims.generateFrameNumbers(textureKey, { start: 0, end: fc - 1 }),
                    frameRate: 8,
                    repeat: -1,
                });
            }
        }

        _animatePlayer(moveLeft, moveRight) {
            const tex = this._getSpriteKey('player');
            if (!tex || !this.player.anims) return;

            // Flip sprite based on direction
            if (moveLeft) this.player.setFlipX(true);
            else if (moveRight) this.player.setFlipX(false);

            if (!this.player.body.onFloor() && this.anims.exists('player-jump')) {
                this.player.anims.play('player-jump', true);
            } else if ((moveLeft || moveRight) && this.anims.exists('player-run')) {
                this.player.anims.play('player-run', true);
            } else if (this.anims.exists('player-idle')) {
                this.player.anims.play('player-idle', true);
            }
        }

        // ── Background ──

        _createBackground() {
            const W = this.scale.width;
            const H = this.scale.height;
            const bgSprite = sprites.background;
            this._bgLayers = [];

            if (bgSprite) {
                const bgKey = this._getSpriteKey('background');
                if (bgKey) {
                    // Use sprite as tiling background with parallax
                    const bg = this.add.tileSprite(W / 2, H / 2, W, H, bgKey);
                    bg.setScrollFactor(0);
                    bg.setDepth(-10);
                    this._bgLayers.push({ obj: bg, scrollFactor: 0.3 });
                    return;
                }
            }

            // Fallback: no background sprite, use world.backgroundColor (already set in config)
        }

        _scrollBackground() {
            if (!this._bgLayers || !this._bgLayers.length) return;
            const camY = this.cameras.main.scrollY;
            for (const layer of this._bgLayers) {
                if (layer.obj && layer.obj.tilePositionY !== undefined) {
                    layer.obj.tilePositionY = camY * layer.scrollFactor;
                }
            }
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
            if (textureKey) {
                const p = this.add.tileSprite(x, y, w, h, textureKey);
                return p;
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

            this.physics.add.existing(coin);
            coin.body.setAllowGravity(false);
            this.collectibles.add(coin);
        }

        // ── Enemies ──

        _createEnemies() {
            const enemyCfg = entities.enemies;
            if (!enemyCfg || !enemyCfg.count) return;

            this.enemies = this.physics.add.group();
            const W = this.scale.width;
            const H = this.scale.height;
            const color = Phaser.Display.Color.HexStringToColor(enemyCfg.color || '#ff5c8a').color;
            const speed = enemyCfg.speed || 60;
            const enemyTex = this._getSpriteKey('enemy');

            for (let i = 0; i < enemyCfg.count; i++) {
                const x = 50 + Math.random() * (W - 100);
                const y = H - 60 - (i + 1) * 120;
                let enemy;

                if (enemyTex) {
                    enemy = this.add.sprite(x, y, enemyTex);
                    enemy.setDisplaySize(enemyCfg.width || 16, enemyCfg.height || 16);
                } else {
                    enemy = this.add.rectangle(x, y, enemyCfg.width || 16, enemyCfg.height || 16, color);
                }

                this.physics.add.existing(enemy);
                enemy.body.setCollideWorldBounds(true);
                enemy.body.setBounce(1, 0);
                enemy.body.setVelocityX(speed * (Math.random() > 0.5 ? 1 : -1));
                enemy.setData('ai', enemyCfg.ai || 'patrol');
                enemy.setData('speed', speed);
                enemy.setData('minX', 20);
                enemy.setData('maxX', W - 20);
                this.enemies.add(enemy);
            }
        }
    };
}

function createGameOverScene(config) {
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

            this.add.text(W / 2, H / 2 - 40, this.won ? 'GANASTE!' : 'GAME OVER', {
                fontFamily: '"Press Start 2P"',
                fontSize: '16px',
                color: this.won ? '#3ddc97' : '#ff5c8a',
            }).setOrigin(0.5);

            this.add.text(W / 2, H / 2 + 10, `Score: ${this.finalScore}`, {
                fontFamily: '"Press Start 2P"',
                fontSize: '10px',
                color: '#ffd23f',
            }).setOrigin(0.5);

            this.add.text(W / 2, H / 2 + 50, 'Click para reiniciar', {
                fontFamily: '"Press Start 2P"',
                fontSize: '8px',
                color: '#a8a0c0',
            }).setOrigin(0.5);

            this.input.on('pointerdown', () => {
                this.scene.start('PlayScene');
            });
        }
    };
}
