const API_KEY_MAPS = "d055c0b4-9aad-4446-b964-ffb91a31c15a";
const tileUrl = `https://maps.geoapify.com/v1/tile/osm-bright/{z}/{x}/{y}.png?apiKey=${API_KEY_MAPS}`;

let mapInstitucion = null;
let mapCiudadano = null;
let marcadorFamiliar = null;
let cuentaRegresivaInterval = null;

document.addEventListener("DOMContentLoaded", () => {
    inicializarSistema();
});

async function inicializarSistema() {
    try {
        const res = await ApiService.verificarSaludServidor();
        console.log("Conectado al Backend:", res.mensaje);
    } catch (err) {
        console.warn("Backend FastAPI offline, operando en modo local.");
    }
}

function alternarFormularioRegistro(mostrar) {
    const loginForm = document.getElementById('form-login');
    const registroForm = document.getElementById('form-registro');
    if (mostrar) {
        loginForm.classList.add('hidden');
        registroForm.classList.remove('hidden');
    } else {
        registroForm.classList.add('hidden');
        loginForm.classList.remove('hidden');
    }
}

async function realizarRegistro(event) {
    event.preventDefault();
    const rol = document.getElementById('reg-rol').value;
    const usuario = document.getElementById('reg-usuario').value.trim();
    const password = document.getElementById('reg-password').value.trim();

    try {
        const data = await ApiService.registrarUsuario({ usuario, password, rol });
        alert(`✅ ${data.mensaje}\nTu código de enlace personal es: ${data.codigo_enlace}`);
        alternarFormularioRegistro(false);
        document.getElementById('input-usuario').value = usuario;
    } catch (err) {
        alert("Error en el registro: " + err.message);
    }
}

function realizarLogin(event) {
    event.preventDefault();
    const rol = document.getElementById('select-rol').value;
    const usuario = document.getElementById('input-usuario').value;
    const password = document.getElementById('input-password').value;

    if (!usuario.trim() || !password.trim()) {
        alert("Por favor, ingrese sus credenciales.");
        return;
    }

    document.getElementById('auth-screen').classList.add('hidden');
    document.getElementById('app-container').classList.remove('hidden');
    document.getElementById('usuario-conectado').innerText = usuario;

    if (rol === 'institucion') {
        configurarVistaInstitucion();
    } else {
        configurarVistaCiudadano();
    }
}

function cerrarSesion() {
    document.getElementById('app-container').classList.add('hidden');
    document.getElementById('auth-screen').classList.remove('hidden');
    document.getElementById('input-password').value = '';
}

function configurarVistaInstitucion() {
    document.getElementById('badge-rol').innerText = "Portal B2G (Gobierno)";
    document.getElementById('vista-institucion').classList.remove('hidden');
    document.getElementById('vista-ciudadano').classList.add('hidden');
    
    if (!mapInstitucion) {
        setTimeout(() => {
            mapInstitucion = L.map('map-institucion').setView([-7.1637, -78.5003], 13);
            L.tileLayer(tileUrl, { maxZoom: 19, attribution: 'Geoapify' }).addTo(mapInstitucion);
        }, 300);
    } else {
        setTimeout(() => { mapInstitucion.invalidateSize(); }, 300);
    }
}

function configurarVistaCiudadano() {
    document.getElementById('badge-rol').innerText = "Portal B2C (Familiar)";
    document.getElementById('vista-ciudadano').classList.remove('hidden');
    document.getElementById('vista-institucion').classList.add('hidden');
    
    if (!mapCiudadano) {
        setTimeout(() => {
            mapCiudadano = L.map('map-ciudadano').setView([-7.1637, -78.5003], 13);
            L.tileLayer(tileUrl, { maxZoom: 19, attribution: 'Geoapify' }).addTo(mapCiudadano);
        }, 300);
    } else {
        setTimeout(() => { mapCiudadano.invalidateSize(); }, 300);
    }
}

async function dispararAlertaPrueba() {
    const latDesvio = -7.1637 + (Math.random() - 0.5) * 0.02;
    const lngDesvio = -78.5003 + (Math.random() - 0.5) * 0.02;

    const datosAlerta = {
        dispositivo_id: document.getElementById('input-usuario').value || "DEVICE_GOV_01",
        tipo_emergencia: "Alerta Sísmica Inercial",
        nivel_gravedad: 5,
        latitud: latDesvio,
        longitud: lngDesvio,
        timestamp_dispositivo: new Date().toISOString()
    };

    try {
        const data = await ApiService.despacharAlerta(datosAlerta);
        
        if (mapInstitucion) {
            L.marker([latDesvio, lngDesvio]).addTo(mapInstitucion)
                .bindPopup(`<b>🚨 Alerta en BD</b><br>Recurso asignado: ${data.recurso_asignado.unidad}`)
                .openPopup();
        }

        const listaAlertas = document.getElementById('lista-alertas-institucion');
        if(listaAlertas) {
            listaAlertas.innerHTML = `
                <div class="bg-red-950/40 border border-red-800/50 p-3 rounded-xl text-xs space-y-1">
                    <div class="flex justify-between font-bold text-red-400">
                        <span>🚨 Sismo Detectado</span>
                        <span>Grav: 5</span>
                    </div>
                    <p class="text-slate-300 text-[11px]">Lat: ${latDesvio.toFixed(4)}, Lng: ${lngDesvio.toFixed(4)}</p>
                    <p class="text-[10px] text-slate-400">Unidad: ${data.recurso_asignado.unidad}</p>
                </div>
            ` + listaAlertas.innerHTML;
        }

        if (mapCiudadano) {
            mapCiudadano.setView([latDesvio, lngDesvio], 15);
            if (marcadorFamiliar) mapCiudadano.removeLayer(marcadorFamiliar);
            
            marcadorFamiliar = L.marker([latDesvio, lngDesvio]).addTo(mapCiudadano)
                .bindPopup(`<b>🚨 EMERGENCIA ACTIVA</b><br>Ubicación compartida con autoridades.`)
                .openPopup();
            
            document.getElementById('estado-radar').innerText = "⚠️ Ubicación Revelada (Emergencia)";
            document.getElementById('estado-radar').className = "text-red-400 text-[10px] bg-red-950/50 px-2.5 py-1 rounded-lg border border-red-800";
        }
    } catch (err) {
        console.error("Error al despachar alerta:", err);
    }
}

function simularSismo() {
    document.getElementById('estado-inercial').innerText = "⚠️ ¡Movimiento Sísmico Detectado!";
    document.getElementById('estado-inercial').className = "text-sm sm:text-base font-black text-red-500 animate-pulse";
    document.getElementById('contador-seguridad').classList.remove('hidden');
    document.getElementById('btn-estoy-bien').classList.remove('hidden');
    
    let segundos = 10;
    document.getElementById('tiempo-restante').innerText = segundos;
    
    clearInterval(cuentaRegresivaInterval);
    cuentaRegresivaInterval = setInterval(() => {
        segundos--;
        document.getElementById('tiempo-restante').innerText = segundos;
        if(segundos <= 0) {
            clearInterval(cuentaRegresivaInterval);
            document.getElementById('estado-inercial').innerText = "🚨 Alerta Zero-Touch Enviada a BD";
            document.getElementById('estado-inercial').className = "text-sm sm:text-base font-black text-red-600";
            document.getElementById('contador-seguridad').classList.add('hidden');
            document.getElementById('btn-estoy-bien').classList.add('hidden');
            dispararAlertaPrueba();
        }
    }, 1000);
}

function confirmarBien() {
    clearInterval(cuentaRegresivaInterval);
    document.getElementById('estado-inercial').innerText = "Sensores Activos (Seguro)";
    document.getElementById('estado-inercial').className = "text-sm sm:text-base font-black text-emerald-400";
    document.getElementById('contador-seguridad').classList.add('hidden');
    document.getElementById('btn-estoy-bien').classList.add('hidden');
    document.getElementById('estado-radar').innerText = "Modo Seguro (Ubicación Oculta)";
    document.getElementById('estado-radar').className = "text-slate-400 text-[10px] bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800";
}

function abrirModalFamiliar() { 
    document.getElementById('modal-familiar').classList.remove('hidden');
    document.getElementById('fam-nombre').value = '';
    document.getElementById('fam-parentesco').value = '';
    document.getElementById('fam-dispositivo').value = '';
}

function cerrarModalFamiliar() { 
    document.getElementById('modal-familiar').classList.add('hidden'); 
}

async function registrarFamiliarReal(event) {
    event.preventDefault();
    const codigoIngresado = document.getElementById('fam-dispositivo').value.trim().toUpperCase();
    
    const nuevoFamiliar = {
        usuario_responsable: document.getElementById('input-usuario').value,
        nombre: document.getElementById('fam-nombre').value,
        parentesco: document.getElementById('fam-parentesco').value,
        dispositivo_id: codigoIngresado
    };

    try {
        const data = await ApiService.registrarFamiliar(nuevoFamiliar);
        
        const contenedor = document.getElementById('contenedor-familiares');
        if(contenedor.innerHTML.includes("Sin familiares")) {
            contenedor.innerHTML = "";
        }

        contenedor.innerHTML = `
            <div class="flex justify-between items-center text-xs bg-slate-950 p-3 rounded-xl border border-slate-800">
                <div>
                    <span class="text-slate-200 font-bold">${nuevoFamiliar.nombre}</span>
                    <span class="text-slate-400 text-[10px] block">${nuevoFamiliar.parentesco} • Código: ${nuevoFamiliar.dispositivo_id}</span>
                </div>
                <div class="text-right">
                    <span class="inline-block w-2 h-2 rounded-full bg-emerald-500 mr-1"></span>
                    <span class="text-emerald-400 font-semibold text-[11px]">Activo (Privado)</span>
                </div>
            </div>
        ` + contenedor.innerHTML;

        cerrarModalFamiliar();
        alert("✅ " + data.mensaje);
    } catch (err) {
        alert("Error al guardar en base de datos: " + err.message);
    }
}