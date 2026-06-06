/**
 * play-ui.js — UI de juego compartida (cámara, hand-tracking, sensibilidad,
 * mano de referencia + calibración, mapeo de controles, fullscreen, timer).
 *
 * Es EXACTAMENTE la misma experiencia de controles para todos los juegos: tanto
 * los juegos Phaser como los de emulador (Nostalgist) usan este módulo y la misma
 * API de hand-input.js. Lo único que cambia entre motores es un pequeño "adapter"
 * que se le pasa a PlayUI.init():
 *
 *   PlayUI.init({
 *     actionLabels: [{key,label}, ...],   // acciones que se pueden mapear a dedos
 *     multiHand: bool,                     // ¿respetar controls.hands? (solo Phaser)
 *     computeAllowedActions(cfg): Set,     // opcional: filtra qué acciones se muestran
 *     prepare(cfg): Promise,               // opcional: p.ej. resolver sprites
 *     createGame(cfg, handInput, onGameOver): instance|Promise<instance>,
 *     applyFingerMaps(instance, fingerMapsObjArr, currentFingerMaps),
 *     restart(instance),                   // reiniciar partida
 *     getScore(instance): number,          // score final (0 si no aplica)
 *     onResize(instance),                  // opcional: al entrar/salir fullscreen
 *   });
 *
 * Las plantillas comparten el mismo HTML del overlay de config (mismos IDs).
 */
(function () {
    'use strict';

    // Se leen de window.PLAY_CTX dentro de init() (este módulo carga en <head>,
    // antes de que la plantilla defina PLAY_CTX en su bloque de scripts).
    var GAME_ID, SESSION_ID, PATIENT_ID;

    var fingerNames = ['Pulgar', 'Indice', 'Medio', 'Anular', 'Menique'];
    var FINGER_ABBR = ['PUL', 'IND', 'MED', 'ANU', 'MEN'];
    var CONNECTIONS = [
        [0, 1], [1, 2], [2, 3], [3, 4], [0, 5], [5, 6], [6, 7], [7, 8], [0, 9], [9, 10], [10, 11], [11, 12],
        [0, 13], [13, 14], [14, 15], [15, 16], [0, 17], [17, 18], [18, 19], [19, 20],
    ];
    var HAND_COLORS = ['rgba(0,128,255,0.6)', 'rgba(255,140,0,0.6)', 'rgba(180,80,255,0.6)', 'rgba(80,220,140,0.6)'];

    // ── Estado (compartido) ──
    var adapter = null;
    var actionLabels = [];
    var NUM_HANDS = 1;
    var currentSensitivities = [[50, 50, 50, 50, 50]];
    var currentFingerMaps = [{ 0: 'jump', 1: 'right', 2: 'left', 3: 'none', 4: 'none' }];
    var defaultFingerMaps = [{ 0: 'jump', 1: 'right', 2: 'left', 3: 'none', 4: 'none' }];
    var allowedActionKeys = new Set();
    var sessionStartTime = Date.now();
    var gameInstance = null;
    var cameraEnabled = false;
    var handInput = null;
    var sensActiveHand = 0;   // mano seleccionada en el dropdown de Sensibilidad

    // ── Timer de sesión ──
    setInterval(function () {
        var elapsed = Math.floor((Date.now() - sessionStartTime) / 1000);
        var m = String(Math.floor(elapsed / 60)).padStart(2, '0');
        var s = String(elapsed % 60).padStart(2, '0');
        var el = document.getElementById('session-timer');
        if (el) el.textContent = m + ':' + s;
    }, 1000);

    // ── Indicadores de dedos (una fila de 5 por mano) ──
    function buildFingerIndicators() {
        var wrap = document.getElementById('fingers-hands');
        if (!wrap) return;
        var html = '';
        for (var h = 0; h < NUM_HANDS; h++) {
            if (NUM_HANDS > 1) html += '<div class="hand-label">Mano ' + (h + 1) + '</div>';
            html += '<div class="fingers-row">';
            for (var i = 0; i < 5; i++) {
                html += '<div class="finger-ind" data-hand="' + h + '" data-finger="' + i + '">' + FINGER_ABBR[i] + '</div>';
            }
            html += '</div>';
        }
        wrap.innerHTML = html;
    }

    // ── Landmarks de TODAS las manos presentes ──
    function drawLandmarks(hands) {
        var canvas = document.getElementById('landmarks-canvas');
        var video = document.getElementById('camera');
        if (!canvas || !video || video.style.display === 'none') return;
        var rect = video.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = rect.height;
        var cctx = canvas.getContext('2d');
        cctx.clearRect(0, 0, canvas.width, canvas.height);
        var w = canvas.width, hgt = canvas.height;
        var tips = [4, 8, 12, 16, 20];
        for (var hi = 0; hi < hands.length; hi++) {
            var hand = hands[hi];
            var lm = hand && hand.landmarks;
            if (!lm || lm.length < 21) continue;
            cctx.strokeStyle = HAND_COLORS[hi % HAND_COLORS.length];
            cctx.lineWidth = 2;
            for (var ci = 0; ci < CONNECTIONS.length; ci++) {
                var a = CONNECTIONS[ci][0], b = CONNECTIONS[ci][1];
                cctx.beginPath();
                cctx.moveTo(lm[a][0] * w, lm[a][1] * hgt);
                cctx.lineTo(lm[b][0] * w, lm[b][1] * hgt);
                cctx.stroke();
            }
            for (var i = 0; i < lm.length; i++) {
                var isTip = tips.indexOf(i);
                var isActive = isTip >= 0 && hand.fingers && hand.fingers[isTip] === 1;
                var radius = isTip >= 0 ? 5 : 3;
                cctx.beginPath();
                cctx.arc(lm[i][0] * w, lm[i][1] * hgt, radius, 0, Math.PI * 2);
                cctx.fillStyle = isActive ? '#3ddc97' : (isTip >= 0 ? '#ffd23f' : '#00ff00');
                cctx.fill();
            }
        }
    }

    // ── Cámara ──
    function toggleCamera() {
        var videoEl = document.getElementById('camera');
        var placeholder = document.getElementById('camera-placeholder');
        var btn = document.getElementById('btn-camera');
        var statusText = document.getElementById('camera-status-text');
        if (!cameraEnabled) {
            btn.disabled = true;
            btn.textContent = 'Activando…';
            statusText.textContent = 'Inicializando cámara…';
            handInput.connect().then(function () {
                cameraEnabled = true;
                videoEl.style.display = 'block';
                placeholder.style.display = 'none';
                updateCameraButtons();
                btn.disabled = false;
            }).catch(function (err) {
                statusText.textContent = 'No se pudo acceder a la cámara';
                statusText.style.color = 'var(--danger)';
                btn.textContent = 'Reintentar';
                btn.disabled = false;
                console.error('[Camera]', err);
            });
        } else {
            cameraEnabled = false;
            handInput.disconnect();
            videoEl.style.display = 'none';
            var lc = document.getElementById('landmarks-canvas');
            if (lc) lc.getContext('2d').clearRect(0, 0, lc.width, lc.height);
            placeholder.style.display = 'flex';
            statusText.textContent = 'Cámara desactivada';
            statusText.style.color = '#94a3b8';
            btn.textContent = 'Activar cámara';
            updateCameraButtons();
        }
    }

    function updateCameraButtons() {
        var btn = document.getElementById('btn-camera');
        if (cameraEnabled) { btn.textContent = 'Desactivar cámara'; btn.classList.add('active'); }
        else { btn.textContent = 'Activar cámara'; btn.classList.remove('active'); }
    }

    // ── Fullscreen ──
    function toggleFullscreen() {
        var wrapper = document.getElementById('play-wrapper');
        var nav = document.querySelector('.pixo-nav');
        if (!document.fullscreenElement) {
            wrapper.requestFullscreen().then(function () {
                wrapper.classList.add('fullscreen');
                if (nav) nav.style.display = 'none';
            }).catch(function () {
                wrapper.classList.toggle('fullscreen');
                if (nav) nav.style.display = wrapper.classList.contains('fullscreen') ? 'none' : '';
            });
        } else {
            document.exitFullscreen().then(function () {
                wrapper.classList.remove('fullscreen');
                if (nav) nav.style.display = '';
            });
        }
    }

    document.addEventListener('fullscreenchange', function () {
        var wrapper = document.getElementById('play-wrapper');
        var nav = document.querySelector('.pixo-nav');
        if (!document.fullscreenElement) {
            wrapper.classList.remove('fullscreen');
            if (nav) nav.style.display = '';
        }
        if (adapter && adapter.onResize) setTimeout(function () { adapter.onResize(gameInstance); }, 200);
    });

    document.addEventListener('keydown', function (e) { if (e.key === 'F11') { e.preventDefault(); toggleFullscreen(); } });

    // ── Config overlay ──
    function toggleConfig() {
        var open = document.getElementById('config-overlay').classList.toggle('active');
        if (open) { startRefLoop(); updateRefCaption(); } else stopRefLoop();
    }

    function buildConfigUI() {
        buildFingerIndicators();
        buildSensitivityUI();
        buildControlsUI();
    }

    // Sección SENSIBILIDAD: 5 sliders. Si hay varias manos, un dropdown arriba
    // elige qué mano se está ajustando (en vez de apilar todas las manos).
    function buildSensitivityUI() {
        var container = document.getElementById('sens-rows');
        if (sensActiveHand > NUM_HANDS - 1) sensActiveHand = 0;
        var h = sensActiveHand;
        var html = '';
        if (NUM_HANDS > 1) {
            var opts = '';
            for (var hh = 0; hh < NUM_HANDS; hh++) {
                opts += '<option value="' + hh + '" ' + (hh === h ? 'selected' : '') + '>Mano ' + (hh + 1) + '</option>';
            }
            html += '<div class="config-row" style="grid-template-columns:1fr auto;">'
                + '<span class="config-finger-name">Mano a ajustar</span>'
                + '<select class="control-select" onchange="onSensHandChange(this.value)">' + opts + '</select>'
                + '</div>';
        }
        for (var i = 0; i < fingerNames.length; i++) {
            var hand = handInput.hands[h];
            var fingerColor = (hand && hand.fingers[i]) ? 'var(--teal)' : 'var(--brand)';
            html += '<div class="config-row">'
                + '<span class="config-finger-name" style="color:' + fingerColor + '">' + fingerNames[i] + '</span>'
                + '<div class="config-slider-wrap">'
                + '<input type="range" min="0" max="100" value="' + currentSensitivities[h][i] + '" oninput="onSensChange(' + h + ', ' + i + ', this.value)">'
                + '<span class="config-val" id="sens-val-' + h + '-' + i + '">' + currentSensitivities[h][i] + '</span>'
                + '</div></div>';
        }
        container.innerHTML = html;
    }

    // Cambia la mano que se está ajustando en la sección de Sensibilidad.
    function onSensHandChange(value) {
        sensActiveHand = parseInt(value, 10) || 0;
        refHighlightHand = sensActiveHand;
        refHighlight = -1;
        buildSensitivityUI();
        updateRefCaption();
    }

    // Sección CONTROLES: una sola lista de acciones. Cada acción tiene un único
    // dropdown que lista TODOS los dedos de TODAS las manos, diferenciados
    // ("Mano 1 · Pulgar", "Mano 2 · Índice"). Una acción = un dedo concreto.
    function buildControlsUI() {
        var container = document.getElementById('control-rows');
        var actions = actionLabels.filter(function (a) { return a.key !== 'none' && allowedActionKeys.has(a.key); });
        container.innerHTML = actions.map(function (a) {
            var cur = locationForAction(a.key); // {h, i} o null
            var opts = ['<option value="-1">— Sin asignar —</option>'];
            for (var h = 0; h < NUM_HANDS; h++) {
                for (var i = 0; i < 5; i++) {
                    var sel = (cur && cur.h === h && cur.i === i) ? 'selected' : '';
                    var label = NUM_HANDS > 1 ? ('Mano ' + (h + 1) + ' - ' + fingerNames[i]) : fingerNames[i];
                    opts.push('<option value="' + h + ':' + i + '" ' + sel + '>' + label + '</option>');
                }
            }
            return '<div class="control-row">'
                + '<span class="control-action">' + a.label + '</span>'
                + '<select class="control-select" onchange="onActionFingerChange(\'' + a.key + '\', this.value)">' + opts.join('') + '</select>'
                + '</div>';
        }).join('');
    }

    // Ubicación {h, i} (mano, dedo) asignada a una acción, o null si ninguna.
    function locationForAction(action) {
        for (var h = 0; h < NUM_HANDS; h++)
            for (var i = 0; i < 5; i++)
                if (currentFingerMaps[h][i] === action) return { h: h, i: i };
        return null;
    }

    // Vuelca los fingerMaps actuales al juego en vivo (vía adapter).
    function applyFingerMaps() {
        if (!gameInstance || !adapter.applyFingerMaps) return;
        adapter.applyFingerMaps(gameInstance, serializeFingerMaps(), currentFingerMaps);
    }

    // value = "h:i" (mano:dedo) o "-1". Una acción vive en un solo dedo: se limpia
    // de cualquier mano/dedo y se asigna al elegido (que pierde su acción previa).
    function onActionFingerChange(action, value) {
        for (var h = 0; h < NUM_HANDS; h++)
            for (var i = 0; i < 5; i++)
                if (currentFingerMaps[h][i] === action) currentFingerMaps[h][i] = 'none';
        if (value && value !== '-1') {
            var parts = String(value).split(':');
            var hh = parseInt(parts[0], 10), ii = parseInt(parts[1], 10);
            if (!isNaN(hh) && !isNaN(ii) && currentFingerMaps[hh]) currentFingerMaps[hh][ii] = action;
        }
        applyFingerMaps();
        buildControlsUI();
    }

    // ── Mano de referencia + calibración ──
    var refRaf = null;
    var refDisplayCurl = [0, 0, 0, 0, 0];
    var refHighlight = -1;
    var refHighlightHand = 0;
    var calibrating = false;

    function refTargetCurl(i) { return handInput.flexionTarget(i, refHighlightHand); }

    function startRefLoop() {
        for (var i = 0; i < 5; i++) refDisplayCurl[i] = refTargetCurl(i);
        if (refRaf) return;
        var tick = function () { drawReferenceHand(); refRaf = requestAnimationFrame(tick); };
        refRaf = requestAnimationFrame(tick);
    }

    function stopRefLoop() { if (refRaf) { cancelAnimationFrame(refRaf); refRaf = null; } }

    var POSE_OPEN = [
        [[96, 158], [78, 138], [62, 122], [48, 108]],
        [[116, 120], [114, 90], [112, 64], [110, 42]],
        [[138, 118], [137, 84], [136, 54], [135, 30]],
        [[160, 120], [161, 88], [162, 60], [163, 38]],
        [[178, 128], [181, 102], [184, 80], [187, 60]],
    ];
    var POSE_FIST = [
        [[96, 158], [84, 144], [96, 138], [110, 140]],
        [[116, 120], [116, 98], [126, 104], [120, 120]],
        [[138, 118], [138, 96], [150, 102], [142, 120]],
        [[160, 120], [160, 98], [171, 104], [164, 121]],
        [[178, 128], [179, 108], [188, 114], [182, 128]],
    ];

    function lerpPose(a, b, t) {
        return a.map(function (p, i) { return [p[0] + (b[i][0] - p[0]) * t, p[1] + (b[i][1] - p[1]) * t]; });
    }

    function drawReferenceHand() {
        var canvas = document.getElementById('ref-hand');
        if (!canvas) return;
        var c = canvas.getContext('2d');
        c.clearRect(0, 0, canvas.width, canvas.height);
        for (var i = 0; i < 5; i++) refDisplayCurl[i] += (refTargetCurl(i) - refDisplayCurl[i]) * 0.22;
        c.fillStyle = 'rgba(148,163,184,.12)';
        c.strokeStyle = 'rgba(148,163,184,.35)';
        c.lineWidth = 2;
        roundRect(c, 92, 120, 100, 84, 18);
        c.fill();
        c.stroke();
        for (var j = 0; j < 5; j++) {
            var pose = lerpPose(POSE_OPEN[j], POSE_FIST[j], refDisplayCurl[j]);
            drawFinger(c, pose, j === refHighlight);
        }
    }

    function drawFinger(c, pts, highlight) {
        var base = highlight ? '#5eead4' : 'rgba(148,163,184,.7)';
        var glow = highlight ? 'rgba(94,234,212,.55)' : 'transparent';
        c.lineCap = 'round';
        c.lineJoin = 'round';
        c.strokeStyle = glow;
        c.lineWidth = 15;
        strokePath(c, pts);
        c.strokeStyle = base;
        c.lineWidth = 9;
        strokePath(c, pts);
        for (var i = 0; i < pts.length; i++) {
            var p = pts[i];
            c.beginPath();
            c.arc(p[0], p[1], 3.2, 0, Math.PI * 2);
            c.fillStyle = highlight ? '#0f766e' : 'rgba(15,23,42,.9)';
            c.fill();
            c.strokeStyle = base;
            c.lineWidth = 1.5;
            c.stroke();
        }
    }

    function strokePath(c, pts) {
        c.beginPath();
        c.moveTo(pts[0][0], pts[0][1]);
        for (var i = 1; i < pts.length; i++) c.lineTo(pts[i][0], pts[i][1]);
        c.stroke();
    }

    function roundRect(c, x, y, w, h, r) {
        c.beginPath();
        c.moveTo(x + r, y);
        c.arcTo(x + w, y, x + w, y + h, r);
        c.arcTo(x + w, y + h, x, y + h, r);
        c.arcTo(x, y + h, x, y, r);
        c.arcTo(x, y, x + w, y, r);
        c.closePath();
    }

    function setRefCaption(msg, color) {
        var cap = document.getElementById('ref-hand-caption');
        if (!cap) return;
        cap.textContent = msg;
        cap.style.color = color || '#5eead4';
    }

    function median(arr) {
        if (!arr.length) return null;
        var s = arr.slice().sort(function (a, b) { return a - b; });
        var m = Math.floor(s.length / 2);
        return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
    }

    function wait(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

    function samplePhase(label, color) {
        return (async function () {
            for (var t = 3; t >= 1; t--) { setRefCaption(label + ' y mantén… ' + t, color); await wait(650); }
            setRefCaption(label + ' — capturando…', color);
            var samples = [[], [], [], [], []];
            var missed = 0;
            var end = Date.now() + 1800;
            while (Date.now() < end) {
                if (handInput.isHandPresent(refHighlightHand)) {
                    var d = handInput.getRawDiffs(refHighlightHand);
                    for (var i = 0; i < 5; i++) samples[i].push(d[i]);
                } else { missed++; }
                await wait(30);
            }
            return { values: samples.map(median), counts: samples.map(function (a) { return a.length; }), missed: missed };
        })();
    }

    function calibrateFingers() {
        (async function () {
            if (!cameraEnabled) { setRefCaption('Activa la cámara primero.', '#ff5c8a'); return; }
            if (calibrating) return;
            calibrating = true;
            var btn = document.getElementById('btn-calibrate');
            if (btn) { btn.disabled = true; btn.textContent = 'Calibrando…'; }

            var open = await samplePhase('Abre bien la mano', '#5eead4');
            var close = await samplePhase('Ahora cierra el puño', '#ffd23f');

            var minSamples = 12;
            if (open.counts.some(function (c) { return c < minSamples; }) || close.counts.some(function (c) { return c < minSamples; })) {
                setRefCaption('No se vio bien la mano. Acércala a la cámara y repite.', '#ff5c8a');
                if (btn) { btn.disabled = false; btn.textContent = 'Calibrar con mi mano'; }
                calibrating = false;
                return;
            }

            var calib = [];
            var bad = 0;
            for (var i = 0; i < 5; i++) {
                var lo = open.values[i], hi = close.values[i];
                if (lo == null || hi == null || hi - lo < 0.08) { calib.push(null); bad++; continue; }
                var pad = (hi - lo) * 0.06;
                calib.push({ ext: lo + pad, close: hi - pad });
            }
            handInput.applyCalibration(calib);
            try { localStorage.setItem('pixo_calib_' + PATIENT_ID, JSON.stringify(handInput.calibration)); } catch (e) { }

            if (bad === 0) setRefCaption('¡Calibrado! El dibujo ya coincide con tu mano.', '#3ddc97');
            else if (bad < 5) setRefCaption('Calibrado ' + (5 - bad) + '/5. Repite moviendo más esos dedos.', '#ffd23f');
            else setRefCaption('No se detectó recorrido. Abre y cierra más marcado.', '#ff5c8a');
            if (btn) { btn.disabled = false; btn.textContent = 'Calibrar con mi mano'; }
            calibrating = false;
        })();
    }

    function updateRefCaption() {
        if (calibrating) return;
        var cap = document.getElementById('ref-hand-caption');
        if (!cap) return;
        cap.style.color = '#5eead4';
        if (refHighlight < 0) {
            cap.textContent = 'Mueve un slider para ver cuánto debe cerrarse ese dedo.';
        } else {
            var pct = Math.round(refTargetCurl(refHighlight) * 100);
            var handLabel = NUM_HANDS > 1 ? ('Mano ' + (refHighlightHand + 1) + ' · ') : '';
            cap.textContent = handLabel + fingerNames[refHighlight] + ': debe cerrarse ~' + pct + '% para contar.';
        }
    }

    function onSensChange(hand, finger, value) {
        value = parseInt(value);
        currentSensitivities[hand][finger] = value;
        document.getElementById('sens-val-' + hand + '-' + finger).textContent = value;
        handInput.setSensitivityForHand(hand, currentSensitivities[hand]);
        refHighlight = finger;
        refHighlightHand = hand;
        updateRefCaption();
    }

    function resetConfig() {
        currentSensitivities = [];
        currentFingerMaps = [];
        for (var h = 0; h < NUM_HANDS; h++) {
            currentSensitivities.push([50, 50, 50, 50, 50]);
            var def = defaultFingerMaps[h] || {};
            var map = {};
            for (var i = 0; i < 5; i++) map[i] = def[String(i)] || def[i] || 'none';
            currentFingerMaps.push(map);
        }
        buildConfigUI();
        handInput.setSensitivities(currentSensitivities);
        applyFingerMaps();
        showStatus('Config reseteada');
    }

    function serializeFingerMaps() {
        return currentFingerMaps.map(function (map) {
            var o = {};
            for (var i = 0; i < 5; i++) o[String(i)] = map[i];
            return o;
        });
    }

    function saveConfig() {
        return (async function () {
            var fmArr = serializeFingerMaps();
            applyFingerMaps();
            handInput.setSensitivities(currentSensitivities);
            var payload = NUM_HANDS > 1
                ? { sensitivities: currentSensitivities, finger_map: fmArr }
                : { sensitivities: currentSensitivities[0], finger_map: fmArr[0] };
            await fetch('/api/games/' + GAME_ID + '/player-config/' + PATIENT_ID, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            showStatus('¡Config guardada!');
        })();
    }

    function showStatus(msg) {
        var el = document.getElementById('config-status');
        if (!el) return;
        el.textContent = msg;
        setTimeout(function () { el.textContent = ''; }, 2000);
    }

    function restartGame() {
        if (adapter && adapter.restart) adapter.restart(gameInstance);
    }

    function endGame(finalScore) {
        return (async function () {
            var score = finalScore != null ? finalScore : (adapter && adapter.getScore ? adapter.getScore(gameInstance) : 0);
            if (SESSION_ID) {
                handInput._flushEvents();
                await fetch('/api/sessions/' + SESSION_ID + '/end', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ score: score }),
                });
            }
            var isPatient = document.body.dataset.role === '3';
            window.location.href = isPatient ? '/dashboard' : (SESSION_ID ? ('/sessions/' + SESSION_ID + '/report') : '/games');
        })();
    }

    // ── Inicialización ──
    async function init(a) {
        var pctx = window.PLAY_CTX || {};
        GAME_ID = pctx.gameId;
        SESSION_ID = pctx.sessionId;
        PATIENT_ID = pctx.patientId;

        adapter = a || {};
        actionLabels = adapter.actionLabels || [];
        allowedActionKeys = new Set(actionLabels.map(function (x) { return x.key; }));

        handInput = new HandInput();
        window.handInput = handInput;

        handInput.onHands(function (hands) {
            document.querySelectorAll('.finger-ind').forEach(function (el) {
                var h = +el.dataset.hand, i = +el.dataset.finger;
                var on = hands[h] && hands[h].present && hands[h].fingers[i] === 1;
                el.classList.toggle('active', !!on);
            });
            drawLandmarks(hands);
        });
        handInput.onConnect(function () { if (SESSION_ID) handInput._sessionId = SESSION_ID; });

        try {
            var gameConfig = await fetch('/api/games/' + GAME_ID + '/config').then(function (r) { return r.json(); });
            var playerConfig = await fetch('/api/games/' + GAME_ID + '/player-config/' + PATIENT_ID).then(function (r) { return r.json(); });

            var gameControls = gameConfig.controls || {};
            // Nº de manos: solo si el adapter lo soporta (Phaser). Emulador = 1.
            NUM_HANDS = adapter.multiHand ? Math.max(1, parseInt(gameControls.hands, 10) || 1) : 1;
            handInput.setNumHands(NUM_HANDS);

            var baseMaps = Array.isArray(gameControls.fingerMaps) ? gameControls.fingerMaps : null;
            var fallbackMap = gameControls.fingerMap || { 0: 'jump', 1: 'right', 2: 'left', 3: 'none', 4: 'none' };
            defaultFingerMaps = [];
            for (var h = 0; h < NUM_HANDS; h++) defaultFingerMaps.push((baseMaps && baseMaps[h]) || fallbackMap);

            // Sensibilidad: URL param (elección del terapeuta/paciente) > player_game_config > default 50s
            var sraw = (pctx.sensitivity && pctx.sensitivity.length) ? pctx.sensitivity : playerConfig.sensitivities;
            var sNested = Array.isArray(sraw) && Array.isArray(sraw[0]);
            currentSensitivities = [];
            for (var hs = 0; hs < NUM_HANDS; hs++) {
                var arr;
                if (sNested) arr = sraw[hs] || sraw[0];
                else if (Array.isArray(sraw)) arr = sraw;
                currentSensitivities.push((arr || [50, 50, 50, 50, 50]).slice());
            }

            // Normaliza mapeo guardado (objeto = 1 mano, arreglo = varias).
            var fmRaw = playerConfig.finger_map;
            var fmIsArr = Array.isArray(fmRaw);
            currentFingerMaps = [];
            for (var hf = 0; hf < NUM_HANDS; hf++) {
                var src;
                if (fmIsArr) src = fmRaw[hf] || fmRaw[0] || defaultFingerMaps[hf];
                else if (fmRaw && Object.keys(fmRaw).length) src = (hf === 0) ? fmRaw : defaultFingerMaps[hf];
                else src = defaultFingerMaps[hf];
                var map = {};
                for (var i = 0; i < 5; i++) map[i] = src[String(i)] || src[i] || 'none';
                currentFingerMaps.push(map);
            }

            handInput.setSensitivities(currentSensitivities);

            // Calibración del paciente: primero PLAY_CTX (BD), fallback localStorage.
            var calData = pctx.calibration;
            if (!calData) {
                try {
                    var ls = localStorage.getItem('pixo_calib_' + PATIENT_ID);
                    if (ls) calData = JSON.parse(ls);
                } catch (e) {}
            }
            if (calData) handInput.applyCalibration(calData);

            // Inyecta los mapeos resueltos del paciente en la config para el loader.
            gameConfig.controls = gameConfig.controls || {};
            gameConfig.controls.hands = NUM_HANDS;
            gameConfig.controls.fingerMaps = serializeFingerMaps();
            gameConfig.controls.fingerMap = gameConfig.controls.fingerMaps[0];

            if (adapter.prepare) await adapter.prepare(gameConfig);
            if (adapter.computeAllowedActions) allowedActionKeys = adapter.computeAllowedActions(gameConfig, currentFingerMaps);

            buildConfigUI();

            gameInstance = await adapter.createGame(gameConfig, handInput, function (score) { endGame(score); });
            window.gameInstance = gameInstance;
        } catch (e) {
            console.error('[PlayUI] Error cargando el juego:', e);
            var cont = document.getElementById('game-container');
            if (cont) cont.innerHTML = '<div class="ui negative message" style="max-width:340px;margin:20px auto;">Error cargando el juego.<br><small>' + (e && e.message ? e.message : '') + '</small></div>';
        }
    }

    // API pública + handlers usados por onclick/oninput inline.
    window.PlayUI = { init: init, get handInput() { return handInput; }, get instance() { return gameInstance; } };
    window.toggleCamera = toggleCamera;
    window.toggleConfig = toggleConfig;
    window.toggleFullscreen = toggleFullscreen;
    window.resetConfig = resetConfig;
    window.saveConfig = saveConfig;
    window.calibrateFingers = calibrateFingers;
    window.restartGame = restartGame;
    window.endGame = endGame;
    window.onSensChange = onSensChange;
    window.onSensHandChange = onSensHandChange;
    window.onActionFingerChange = onActionFingerChange;
})();
