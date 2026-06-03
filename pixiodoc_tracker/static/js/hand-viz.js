class HandViz {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.data = null;
        this.running = false;
        this.time = 0;
        this.hoveredFinger = -1;
        this.particles = [];
        this._boundLoop = () => this._loop();

        this.canvas.addEventListener('mousemove', (e) => this._onMouseMove(e));
        this.canvas.addEventListener('mouseleave', () => { this.hoveredFinger = -1; });
        this.canvas.addEventListener('click', (e) => this._onClick(e));

        this._resize();
        window.addEventListener('resize', () => this._resize());
    }

    setData(data) {
        this.data = data;
    }

    start() {
        if (this.running) return;
        this.running = true;
        this._loop();
    }

    stop() {
        this.running = false;
    }

    _resize() {
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width = rect.width || 320;
        this.canvas.height = rect.height || 400;
    }

    _loop() {
        if (!this.running) return;
        this.time += 0.016;
        this._draw();
        requestAnimationFrame(this._boundLoop);
    }

    _draw() {
        const ctx = this.ctx;
        const W = this.canvas.width;
        const H = this.canvas.height;
        ctx.clearRect(0, 0, W, H);

        const scale = Math.min(W, H) * 0.65;
        const ox = W * 0.5;
        const oy = H * 0.52;

        const lm = this._getLandmarks();

        this._spawnParticles(lm);
        this._updateParticles();
        this._drawSkeleton(ctx, lm, ox, oy, scale);
        this._drawJoints(ctx, lm, ox, oy, scale);
        this._drawParticles(ctx);
        this._drawLegend(ctx);
        this._drawTooltip(ctx, lm, ox, oy, scale);
    }

    _getLandmarks() {
        const base = [
            [0.50, 0.82],
            [0.48, 0.64], [0.44, 0.54], [0.38, 0.46], [0.32, 0.40],
            [0.52, 0.60], [0.56, 0.46], [0.58, 0.34], [0.60, 0.24],
            [0.50, 0.58], [0.50, 0.44], [0.50, 0.32], [0.50, 0.22],
            [0.48, 0.60], [0.44, 0.48], [0.42, 0.38], [0.40, 0.30],
            [0.46, 0.62], [0.40, 0.52], [0.36, 0.44], [0.32, 0.38],
        ];
        return base.map((p, i) => ({ x: p[0], y: p[1], idx: i }));
    }

    _getFingerForLandmark(idx) {
        if (idx >= 1 && idx <= 4) return 0;
        if (idx >= 5 && idx <= 8) return 1;
        if (idx >= 9 && idx <= 12) return 2;
        if (idx >= 13 && idx <= 16) return 3;
        if (idx >= 17 && idx <= 20) return 4;
        return -1;
    }

    _getFingerStatus(fi) {
        if (!this.data || !this.data.metrics) return 'normal';
        const m = this.data.metrics[String(fi)];
        if (!m || !m.has_data) return 'normal';
        if (m.rom < 0.05 || m.fatigue > 30 || m.tremor > 0.02) return 'critical';
        if (m.rom < 0.10 || m.fatigue > 20 || m.tremor > 0.015) return 'warning';
        return 'normal';
    }

    _getColor(status) {
        if (status === 'critical') return '#ff5c8a';
        if (status === 'warning') return '#ffd23f';
        return '#3ddc97';
    }

    _getGlowColor(status) {
        if (status === 'critical') return 'rgba(255,92,138,0.4)';
        if (status === 'warning') return 'rgba(255,210,63,0.4)';
        return 'rgba(61,220,151,0.2)';
    }

    _drawSkeleton(ctx, lm, ox, oy, scale) {
        const connections = [
            [0,1],[1,2],[2,3],[3,4],
            [0,5],[5,6],[6,7],[7,8],
            [0,9],[9,10],[10,11],[11,12],
            [0,13],[13,14],[14,15],[15,16],
            [0,17],[17,18],[18,19],[19,20],
            [5,9],[9,13],[13,17],
        ];

        for (const [a, b] of connections) {
            const fi = this._getFingerForLandmark(a);
            const status = fi >= 0 ? this._getFingerStatus(fi) : 'normal';
            const pulse = status === 'critical' ? 0.6 + Math.sin(this.time * 4 + fi) * 0.4 : 1;

            ctx.beginPath();
            ctx.moveTo(lm[a].x * scale + ox, lm[a].y * scale + oy);
            ctx.lineTo(lm[b].x * scale + ox, lm[b].y * scale + oy);
            ctx.strokeStyle = this._getColor(status);
            ctx.globalAlpha = pulse;
            ctx.lineWidth = 3;
            ctx.stroke();

            // Glow para critical
            if (status === 'critical') {
                ctx.strokeStyle = this._getGlowColor(status);
                ctx.lineWidth = 8;
                ctx.stroke();
            }
            ctx.globalAlpha = 1;
        }
    }

    _drawJoints(ctx, lm, ox, oy, scale) {
        for (let i = 0; i < lm.length; i++) {
            const fi = this._getFingerForLandmark(i);
            const status = fi >= 0 ? this._getFingerStatus(fi) : 'normal';
            const pulse = status === 'critical' ? 1 + Math.sin(this.time * 3 + fi) * 0.3 : 1;
            const isHover = fi === this.hoveredFinger;
            const radius = (isHover ? 8 : 5) * pulse;
            const x = lm[i].x * scale + ox;
            const y = lm[i].y * scale + oy;

            // Glow
            const grad = ctx.createRadialGradient(x, y, 0, x, y, radius * 3);
            grad.addColorStop(0, this._getGlowColor(status));
            grad.addColorStop(1, 'transparent');
            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.arc(x, y, radius * 3, 0, Math.PI * 2);
            ctx.fill();

            // Joint
            ctx.beginPath();
            ctx.arc(x, y, radius, 0, Math.PI * 2);
            ctx.fillStyle = status === 'critical'
                ? `hsl(348, 100%, ${60 + Math.sin(this.time * 4 + i) * 20}%)`
                : this._getColor(status);
            ctx.fill();
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 1.5;
            ctx.stroke();

            // Label en hover
            if (isHover && fi >= 0) {
                const names = ['Pulgar', 'Indice', 'Medio', 'Anular', 'Menique'];
                ctx.fillStyle = '#fff';
                ctx.font = 'bold 11px sans-serif';
                ctx.fillText(names[fi], x + 12, y + 4);
            }
        }
    }

    _spawnParticles(lm) {
        if (!this.data || !this.data.metrics) return;
        for (let fi = 0; fi < 5; fi++) {
            const status = this._getFingerStatus(fi);
            if (status === 'normal') continue;

            if (Math.random() < 0.15) {
                const tipIndices = [4, 8, 12, 16, 20];
                const tip = lm[tipIndices[fi]];
                this.particles.push({
                    x: tip.x,
                    y: tip.y,
                    vx: (Math.random() - 0.5) * 0.005,
                    vy: -Math.random() * 0.008 - 0.002,
                    life: 1,
                    decay: 0.01 + Math.random() * 0.02,
                    size: 2 + Math.random() * 3,
                    color: status === 'critical' ? '#ff5c8a' : '#ffd23f',
                });
            }
        }
    }

    _updateParticles() {
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const p = this.particles[i];
            p.x += p.vx;
            p.y += p.vy;
            p.life -= p.decay;
            if (p.life <= 0) {
                this.particles.splice(i, 1);
            }
        }
        if (this.particles.length > 100) {
            this.particles.splice(0, this.particles.length - 100);
        }
    }

    _drawParticles(ctx) {
        const W = this.canvas.width;
        const H = this.canvas.height;
        const scale = Math.min(W, H) * 0.65;
        const ox = W * 0.5;
        const oy = H * 0.52;

        for (const p of this.particles) {
            ctx.beginPath();
            ctx.arc(p.x * scale + ox, p.y * scale + oy, p.size * p.life, 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.globalAlpha = p.life * 0.6;
            ctx.fill();
        }
        ctx.globalAlpha = 1;
    }

    _drawLegend(ctx) {
        const x = 10;
        let y = this.canvas.height - 60;
        ctx.font = '9px monospace';

        const items = [
            { label: 'Normal', color: '#3ddc97' },
            { label: 'Alerta', color: '#ffd23f' },
            { label: 'Critico', color: '#ff5c8a' },
        ];
        for (const item of items) {
            ctx.fillStyle = item.color;
            ctx.fillRect(x, y, 10, 10);
            ctx.fillStyle = '#a8a0c0';
            ctx.fillText(item.label, x + 14, y + 9);
            y += 16;
        }
    }

    _drawTooltip(ctx, lm, ox, oy, scale) {
        if (this.hoveredFinger < 0 || !this.data || !this.data.metrics) return;
        const m = this.data.metrics[String(this.hoveredFinger)];
        if (!m) return;

        const tipIndices = [4, 8, 12, 16, 20];
        const tip = lm[tipIndices[this.hoveredFinger]];
        const tx = tip.x * scale + ox + 15;
        const ty = tip.y * scale + oy - 10;

        const lines = [
            `${m.name}`,
            `ROM: ${m.rom.toFixed(4)}`,
            `Fatiga: ${m.fatigue}%`,
            `Temblor: ${m.tremor.toFixed(4)}`,
            `Reaccion: ${m.reaction_time != null ? m.reaction_time + 's' : '-'}`,
        ];

        const lineH = 15;
        const pw = 140;
        const ph = lines.length * lineH + 12;

        ctx.fillStyle = 'rgba(10,4,32,0.92)';
        ctx.beginPath();
        ctx.roundRect(tx, ty, pw, ph, 6);
        ctx.fill();
        ctx.strokeStyle = this._getColor(this._getFingerStatus(this.hoveredFinger));
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.roundRect(tx, ty, pw, ph, 6);
        ctx.stroke();

        ctx.font = '10px monospace';
        ctx.fillStyle = '#ffd23f';
        ctx.fillText(lines[0], tx + 8, ty + 14);

        ctx.font = '9px monospace';
        for (let i = 1; i < lines.length; i++) {
            ctx.fillStyle = '#a8a0c0';
            ctx.fillText(lines[i], tx + 8, ty + 14 + i * lineH);
        }
    }

    _onMouseMove(e) {
        const rect = this.canvas.getBoundingClientRect();
        const mx = (e.clientX - rect.left) / rect.width;
        const my = (e.clientY - rect.top) / rect.height;

        const lm = this._getLandmarks();
        const tipIndices = [4, 8, 12, 16, 20];

        this.hoveredFinger = -1;
        for (let fi = 0; fi < 5; fi++) {
            const p = lm[tipIndices[fi]];
            const dx = mx - p.x;
            const dy = my - p.y;
            if (dx * dx + dy * dy < 0.003) {
                this.hoveredFinger = fi;
                break;
            }
        }
    }

    _onClick(e) {
        if (this.hoveredFinger < 0) return;
        if (this._onFingerClick) this._onFingerClick(this.hoveredFinger);
    }

    onFingerClick(cb) {
        this._onFingerClick = cb;
    }
}
