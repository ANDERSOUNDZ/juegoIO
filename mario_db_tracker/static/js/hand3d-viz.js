const HAND_CONNECTIONS = [
    [0,1],[1,2],[2,3],[3,4],
    [0,5],[5,6],[6,7],[7,8],
    [0,9],[9,10],[10,11],[11,12],
    [0,13],[13,14],[14,15],[15,16],
    [0,17],[17,18],[18,19],[19,20],
    [5,9],[9,13],[13,17],
];

const HAND_BASE = [
    [150, 250], [120, 215], [110, 195], [100, 178], [88, 162],
    [125, 205], [130, 175], [133, 150], [135, 128],
    [150, 200], [150, 170], [150, 145], [150, 118],
    [175, 205], [172, 178], [170, 155], [168, 135],
    [195, 210], [188, 192], [180, 175], [173, 160],
];

const FINGER_TIPS = [4, 8, 12, 16, 20];
const FINGER_NAMES = ['Pulgar', 'Indice', 'Medio', 'Anular', 'Menique'];

class Hand3DViz {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.svg = null;
        this.lines = [];
        this.circles = [];
        this.tipCircles = [];
        this.labels = [];
        this.data = null;
        this.running = false;
        this.time = 0;
        this.anim = null;
        this.pulseAnims = [];
        this.hoveredFinger = -1;
        this._boundLoop = () => this._loop();
        this._buildSVG();
    }

    _buildSVG() {
        this.svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        this.svg.setAttribute('viewBox', '40 90 220 200');
        this.svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
        this.svg.setAttribute('width', '100%');
        this.svg.setAttribute('height', '100%');
        this.svg.style.display = 'block';

        // Hand group with centered transform origin
        this.handGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        this.handGroup.style.transformOrigin = '110px 150px';
        this.svg.appendChild(this.handGroup);

        // Lines (bones)
        for (let i = 0; i < HAND_CONNECTIONS.length; i++) {
            const [a, b] = HAND_CONNECTIONS[i];
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', HAND_BASE[a][0]);
            line.setAttribute('y1', HAND_BASE[a][1]);
            line.setAttribute('x2', HAND_BASE[b][0]);
            line.setAttribute('y2', HAND_BASE[b][1]);
            line.setAttribute('stroke', '#3ddc97');
            line.setAttribute('stroke-width', '5');
            line.setAttribute('stroke-linecap', 'round');
            line.setAttribute('data-conn', `${a}-${b}`);
            this.handGroup.appendChild(line);
            this.lines.push(line);
        }

        // Wrist
        const wrist = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        wrist.setAttribute('x', '120');
        wrist.setAttribute('y', '248');
        wrist.setAttribute('width', '60');
        wrist.setAttribute('height', '40');
        wrist.setAttribute('rx', '8');
        wrist.setAttribute('fill', '#2d1b4e');
        wrist.setAttribute('stroke', '#5a3a8a');
        wrist.setAttribute('stroke-width', '2');
        this.handGroup.appendChild(wrist);

        // Palm fill
        const palm = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        const palmPts = [120,248, 120,200, 125,195, 150,190, 175,195, 180,200, 180,248];
        palm.setAttribute('points', palmPts.join(' '));
        palm.setAttribute('fill', '#2d1b4e44');
        palm.setAttribute('stroke', 'none');
        this.handGroup.insertBefore(palm, this.handGroup.firstChild);

        // Circles (joints)
        for (let i = 0; i < HAND_BASE.length; i++) {
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            const fi = _getFingerForJoint(i);
            circle.setAttribute('cx', HAND_BASE[i][0]);
            circle.setAttribute('cy', HAND_BASE[i][1]);
            circle.setAttribute('r', fi >= 0 ? 6 : 4);
            circle.setAttribute('fill', '#3ddc97');
            circle.setAttribute('stroke', '#fff');
            circle.setAttribute('stroke-width', '2');
            circle.setAttribute('data-joint', i);
            circle.setAttribute('data-finger', fi);
            this.handGroup.appendChild(circle);
            this.circles.push(circle);
        }

        // Finger labels (hidden by default, shown on hover)
        for (let fi = 0; fi < 5; fi++) {
            const tip = FINGER_TIPS[fi];
            const [tx, ty] = HAND_BASE[tip];
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', tx + 12);
            text.setAttribute('y', ty + 4);
            text.setAttribute('fill', '#a8a0c0');
            text.setAttribute('font-size', '10');
            text.setAttribute('font-family', 'monospace');
            text.setAttribute('data-finger-label', fi);
            text.setAttribute('opacity', '0');
            text.textContent = FINGER_NAMES[fi];
            this.handGroup.appendChild(text);
            this.labels.push(text);
        }

        // Legend
        const legendY = 268;
        const legendItems = [
            { label: 'Normal', color: '#3ddc97', x: 20 },
            { label: 'Alerta', color: '#ffd23f', x: 100 },
            { label: 'Critico', color: '#ff5c8a', x: 180 },
        ];
        for (const item of legendItems) {
            const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            c.setAttribute('cx', item.x + 5);
            c.setAttribute('cy', legendY);
            c.setAttribute('r', 5);
            c.setAttribute('fill', item.color);
            this.svg.appendChild(c);

            const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            t.setAttribute('x', item.x + 14);
            t.setAttribute('y', legendY + 4);
            t.setAttribute('fill', '#a8a0c0');
            t.setAttribute('font-size', '9');
            t.setAttribute('font-family', 'monospace');
            t.textContent = item.label;
            this.svg.appendChild(t);
        }

        // Hover detection
        this.svg.addEventListener('mousemove', (e) => this._onMouseMove(e));
        this.svg.addEventListener('mouseleave', () => {
            this.hoveredFinger = -1;
            this._updateLabels();
        });

        this.container.appendChild(this.svg);
    }

    setData(data) {
        this.data = data;
        this._applyColors();
    }

    start() {
        if (this.running) return;
        this.running = true;
        this._loop();
    }

    stop() {
        this.running = false;
        if (this.anim) {
            try { this.anim.pause(); } catch(e) {}
            this.anim = null;
        }
        for (const pa of this.pulseAnims) {
            try { pa.pause(); } catch(e) {}
        }
        this.pulseAnims = [];
    }

    _loop() {
        if (!this.running) return;
        this.time += 0.016;

        // Subtle rotation around center
        const angle = Math.sin(this.time * 0.8) * 2.5;
        this.handGroup.style.transform = `rotate(${angle}deg)`;

        this._animatePulse();
        requestAnimationFrame(this._boundLoop);
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

    _applyColors() {
        for (const line of this.lines) {
            const conn = line.getAttribute('data-conn').split('-').map(Number);
            const fi = _getFingerForJoint(conn[0]);
            const status = fi >= 0 ? this._getFingerStatus(fi) : 'normal';
            line.setAttribute('stroke', this._getColor(status));

            // Glow for critical
            if (status === 'critical') {
                line.setAttribute('stroke-width', '7');
            } else if (status === 'warning') {
                line.setAttribute('stroke-width', '6');
            } else {
                line.setAttribute('stroke-width', '5');
            }
        }

        for (const circle of this.circles) {
            const fi = parseInt(circle.getAttribute('data-finger'));
            if (fi >= 0) {
                const status = this._getFingerStatus(fi);
                circle.setAttribute('fill', this._getColor(status));
            }
        }
    }

    _animatePulse() {
        for (let fi = 0; fi < 5; fi++) {
            const status = this._getFingerStatus(fi);
            if (status !== 'critical') continue;

            const tipIdx = FINGER_TIPS[fi];
            const circle = this.circles[tipIdx];
            if (!circle) continue;

            const pulse = 0.6 + Math.sin(this.time * 3 + fi) * 0.4;
            const r = 6 + pulse * 3;
            circle.setAttribute('r', r);

            // Opacity pulse on connected bones
            for (const line of this.lines) {
                const conn = line.getAttribute('data-conn').split('-').map(Number);
                const lfi = _getFingerForJoint(conn[0]);
                if (lfi === fi) {
                    const alpha = 0.5 + Math.sin(this.time * 3 + fi) * 0.5;
                    line.setAttribute('opacity', alpha);
                }
            }
        }
    }

    _updateLabels() {
        for (let fi = 0; fi < 5; fi++) {
            const text = this.labels[fi];
            text.setAttribute('opacity', this.hoveredFinger === fi ? '1' : '0');
            if (this.hoveredFinger === fi && this.data?.metrics) {
                const m = this.data.metrics[String(fi)];
                if (m) {
                    text.textContent = `${m.name} ROM:${m.rom.toFixed(3)} FAT:${m.fatigue}%`;
                }
            }
        }
    }

    _onMouseMove(e) {
        const rect = this.svg.getBoundingClientRect();
        const mx = (e.clientX - rect.left) / rect.width * 300;
        const my = (e.clientY - rect.top) / rect.height * 400;

        this.hoveredFinger = -1;
        for (let fi = 0; fi < 5; fi++) {
            const tip = FINGER_TIPS[fi];
            const [tx, ty] = HAND_BASE[tip];
            const dx = mx - tx;
            const dy = my - ty;
            if (dx * dx + dy * dy < 300) {
                this.hoveredFinger = fi;
                break;
            }
        }
        this._updateLabels();
    }

    onFingerClick(cb) {
        this.svg.addEventListener('click', (e) => {
            if (this.hoveredFinger >= 0) cb(this.hoveredFinger);
        });
    }
}

function _getFingerForJoint(idx) {
    if (idx >= 1 && idx <= 4) return 0;
    if (idx >= 5 && idx <= 8) return 1;
    if (idx >= 9 && idx <= 12) return 2;
    if (idx >= 13 && idx <= 16) return 3;
    if (idx >= 17 && idx <= 20) return 4;
    return -1;
}
