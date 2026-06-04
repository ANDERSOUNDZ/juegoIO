/**
 * play-common.js - Funciones compartidas para todas las plantillas de juego
 * Incluye: camara, hand tracking, config UI, fullscreen, timer, landmarks
 */

// ─── Constantes ──────────────────────────────────────────────────
var CONNECTIONS = [
    [0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],[0,9],[9,10],[10,11],[11,12],
    [0,13],[13,14],[14,15],[15,16],[0,17],[17,18],[18,19],[19,20],
];

var fingerNames = ["Pulgar", "Indice", "Medio", "Anular", "Menique"];
var actionLabels = [
    { key: "jump", label: "SALTAR" }, { key: "right", label: "DER" }, { key: "left", label: "IZQ" },
    { key: "down", label: "BAJO" }, { key: "up", label: "ARRIBA" },
    { key: "action", label: "ACCION" }, { key: "run", label: "CORRER" },
    { key: "start", label: "INICIO" }, { key: "none", label: "NADA" },
];

// ─── Variables globales compartidas ──────────────────────────────
var currentSensitivity = [50, 50, 50, 50, 50];
var currentFingerMap = {};
var defaultFingerMap = {};
var cameraEnabled = false;
var sessionStartTime = Date.now();

// ─── Inicializar hand input ──────────────────────────────────────
var handInput = null;

// ─── Timer de sesion ─────────────────────────────────────────────
function startSessionTimer() {
    setInterval(function() {
        var elapsed = Math.floor((Date.now() - sessionStartTime) / 1000);
        var m = String(Math.floor(elapsed / 60)).padStart(2, "0");
        var s = String(elapsed % 60).padStart(2, "0");
        var el = document.getElementById("session-timer");
        if (el) el.textContent = m + ":" + s;
    }, 1000);
}

// ─── Landmarks ───────────────────────────────────────────────────
function drawLandmarks(lm, fingers) {
    var canvas = document.getElementById("landmarks-canvas");
    var video = document.getElementById("camera");
    if (!canvas || !video || video.style.display === "none") return;
    var rect = video.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
    var ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!lm || lm.length < 21) return;
    var w = canvas.width, h = canvas.height;
    ctx.strokeStyle = "rgba(0, 128, 255, 0.6)";
    ctx.lineWidth = 2;
    for (var ci = 0; ci < CONNECTIONS.length; ci++) {
        var a = CONNECTIONS[ci][0], b = CONNECTIONS[ci][1];
        ctx.beginPath();
        ctx.moveTo(lm[a][0] * w, lm[a][1] * h);
        ctx.lineTo(lm[b][0] * w, lm[b][1] * h);
        ctx.stroke();
    }
    var tips = [4, 8, 12, 16, 20];
    for (var i = 0; i < lm.length; i++) {
        var isTip = tips.indexOf(i);
        var isActive = isTip >= 0 && fingers && fingers[isTip] === 1;
        var radius = isTip >= 0 ? 5 : 3;
        ctx.beginPath();
        ctx.arc(lm[i][0] * w, lm[i][1] * h, radius, 0, Math.PI * 2);
        ctx.fillStyle = isActive ? "#3ddc97" : (isTip >= 0 ? "#ffd23f" : "#00ff00");
        ctx.fill();
    }
}

// ─── Camara ──────────────────────────────────────────────────────
function toggleCamera() {
    var videoEl = document.getElementById("camera");
    var placeholder = document.getElementById("camera-placeholder");
    var btn = document.getElementById("btn-camera");
    var statusText = document.getElementById("camera-status-text");
    if (!cameraEnabled) {
        btn.disabled = true;
        btn.textContent = "Activando...";
        statusText.textContent = "Inicializando camara...";
        handInput.connect().then(function() {
            cameraEnabled = true;
            videoEl.style.display = "block";
            placeholder.style.display = "none";
            updateCameraButtons();
            btn.disabled = false;
        }).catch(function(err) {
            statusText.textContent = "No se pudo acceder a la camara";
            statusText.style.color = "var(--danger)";
            btn.textContent = "Reintentar";
            btn.disabled = false;
            console.error("[Camera]", err);
        });
    } else {
        cameraEnabled = false;
        handInput.disconnect();
        videoEl.style.display = "none";
        var lc = document.getElementById("landmarks-canvas");
        if (lc) lc.getContext("2d").clearRect(0, 0, lc.width, lc.height);
        placeholder.style.display = "flex";
        statusText.textContent = "Camara desactivada";
        statusText.style.color = "#94a3b8";
        btn.textContent = "Activar camara";
        updateCameraButtons();
    }
}

function updateCameraButtons() {
    var btn = document.getElementById("btn-camera");
    if (cameraEnabled) { btn.textContent = "Desactivar camara"; btn.classList.add("active"); }
    else { btn.textContent = "Activar camara"; btn.classList.remove("active"); }
}

// ─── Fullscreen ──────────────────────────────────────────────────
function toggleFullscreen() {
    var wrapper = document.getElementById("play-wrapper");
    var nav = document.querySelector(".pixo-nav");
    if (!document.fullscreenElement) {
        wrapper.requestFullscreen().then(function() {
            wrapper.classList.add("fullscreen");
            if (nav) nav.style.display = "none";
        }).catch(function() {
            wrapper.classList.toggle("fullscreen");
            if (nav) nav.style.display = wrapper.classList.contains("fullscreen") ? "none" : "";
        });
    } else {
        document.exitFullscreen().then(function() {
            wrapper.classList.remove("fullscreen");
            if (nav) nav.style.display = "";
        });
    }
}

document.addEventListener("fullscreenchange", function() {
    var wrapper = document.getElementById("play-wrapper");
    var nav = document.querySelector(".pixo-nav");
    if (!document.fullscreenElement) {
        wrapper.classList.remove("fullscreen");
        if (nav) nav.style.display = "";
    }
});

document.addEventListener("keydown", function(e) {
    if (e.key === "F11") { e.preventDefault(); toggleFullscreen(); }
});

// ─── Config UI ───────────────────────────────────────────────────
function toggleConfig() {
    var el = document.getElementById("config-overlay");
    if (el) el.classList.toggle("active");
}

function buildConfigUI() {
    var container = document.getElementById("config-rows");
    if (!container) return;
    var html = "";
    for (var fi = 0; fi < fingerNames.length; fi++) {
        var name = fingerNames[fi];
        var actionsHtml = "";
        for (var ai = 0; ai < actionLabels.length; ai++) {
            var a = actionLabels[ai];
            var sel = currentFingerMap[fi] === a.key ? "selected" : "";
            actionsHtml += "<button data-finger=\"" + fi + "\" data-action=\"" + a.key + "\" class=\"" + sel + "\" onclick=\"onActionChange(" + fi + ",'" + a.key + "',this)\">" + a.label + "</button>";
        }
        html += "<div class=\"config-row\">";
        html += "<span class=\"config-finger-name\">" + name + "</span>";
        html += "<div class=\"config-slider-wrap\">";
        html += "<input type=\"range\" min=\"0\" max=\"100\" value=\"" + currentSensitivity[fi] + "\" oninput=\"onSensChange(" + fi + ",this.value)\">";
        html += "<span class=\"config-val\" id=\"sens-val-" + fi + "\">" + currentSensitivity[fi] + "</span>";
        html += "</div><div class=\"config-actions\">" + actionsHtml + "</div></div>";
    }
    container.innerHTML = html;
}

function onSensChange(finger, value) {
    value = parseInt(value);
    currentSensitivity[finger] = value;
    var el = document.getElementById("sens-val-" + finger);
    if (el) el.textContent = value;
    handInput.setSensitivity(currentSensitivity);
}

function onActionChange(finger, action, btn) {
    currentFingerMap[finger] = action;
    var row = btn.closest(".config-row");
    if (row) row.querySelectorAll(".config-actions button").forEach(function(b) { b.classList.remove("selected"); });
    btn.classList.add("selected");
}

function resetConfig() {
    currentSensitivity = [50, 50, 50, 50, 50];
    currentFingerMap = Object.assign({}, defaultFingerMap);
    buildConfigUI();
    handInput.setSensitivity(currentSensitivity);
    showStatus("Config reseteada");
}

function saveConfig(gameId, patientId) {
    var fingerMapObj = {};
    for (var i = 0; i < 5; i++) fingerMapObj[String(i)] = currentFingerMap[i];
    handInput.setSensitivity(currentSensitivity);
    return fetch("/api/games/" + gameId + "/player-config/" + patientId, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sensitivities: currentSensitivity, finger_map: fingerMapObj }),
    }).then(function() { showStatus("Guardada!"); });
}

function showStatus(msg) {
    var el = document.getElementById("config-status");
    if (!el) return;
    el.textContent = msg;
    setTimeout(function() { el.textContent = ""; }, 2000);
}

function restartGame() { location.reload(); }

startSessionTimer();
