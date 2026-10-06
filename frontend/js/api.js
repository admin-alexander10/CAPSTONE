// Servicio de conexión con la API FastAPI de QuantumGeoRescue
const ApiService = {
    async request(endpoint, options = {}) {
        let ultimoError = null;

        for (const host of CONFIG.API_HOSTS) {
            const urlConPrefijo = `${host}${CONFIG.API_PREFIX}${endpoint}`;
            const urlSinPrefijo = `${host}${endpoint}`;

            for (const url of [urlConPrefijo, urlSinPrefijo]) {
                try {
                    const response = await fetch(url, {
                        ...options,
                        headers: {
                            'Content-Type': 'application/json',
                            ...(localStorage.getItem(CONFIG.STORAGE_KEYS.TOKEN)
                                ? { Authorization: `Bearer ${localStorage.getItem(CONFIG.STORAGE_KEYS.TOKEN)}` }
                                : {}),
                            ...options.headers
                        }
                    });

                    const data = await response.json();
                    if (!response.ok) {
                        const msg = data.detail || (typeof data === 'string' ? data : "Error en el servidor");
                        throw new Error(msg);
                    }
                    return data;
                } catch (err) {
                    ultimoError = err;
                    // Si el servidor respondió con un error 4xx o 5xx (HTTP), lanzarlo de inmediato (no es error de red)
                    if (err.message && !err.message.includes("fetch") && !err.message.includes("NetworkError") && !err.message.includes("Load failed")) {
                        throw err;
                    }
                }
            }
        }

        // Si fallaron todos los hosts (servidor apagado)
        throw new Error("El servidor Backend (FastAPI) no está iniciado en el puerto 8001. Ejecuta: uvicorn main:app --reload --port 8001");
    },

    async verificarSalud() {
        for (const host of CONFIG.API_HOSTS) {
            try {
                const res = await fetch(`${host}/`);
                if (res.ok) return await res.json();
            } catch (e) {}
        }
        throw new Error("Servidor offline");
    },

    async registrarUsuario(payload) {
        return this.request('/auth/registro/', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    async loginUsuario(payload) {
        return this.request('/auth/login/', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    async verificarSesion() {
        return this.request('/auth/me/');
    },

    async aceptarInvitacionInstitucional(payload) {
        return this.request('/auth/invitaciones/aceptar/', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    async registrarFamiliar(payload) {
        return this.request('/familia/agregar/', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    async listarFamiliares(usuario) {
        return this.request(`/familia/listar/${encodeURIComponent(usuario)}`);
    },

    async despacharAlerta(payload) {
        return this.request('/alertas/despachar/', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    async alertaCoaccion(payload) {
        return this.request('/coaccion/alertar/', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    async obtenerAlertasActivas() {
        return this.request('/alertas/activas/');
    },

    async calcularRuta(payload) {
        return this.request('/rescate/calcular-ruta/', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    async enviarAlertaSeguridad(payload) {
        return this.request('/security/anti-theft-alert', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    async listarPlanes() {
        return this.request('/subscriptions/plans');
    },

    async iniciarCheckoutPlan(payload) {
        return this.request('/subscriptions/checkout', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    async agregarUsuarioInstitucional(payload) {
        return this.request('/subscriptions/institutions/members', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    async listarUsuariosInstitucionales(institutionName) {
        return this.request(`/subscriptions/institutions/${encodeURIComponent(institutionName)}/members`);
    },

    async obtenerCuentaInstitucional() {
        return this.request('/subscriptions/institutions/me');
    },

    async actualizarMiembroInstitucional(memberId, payload) {
        return this.request(`/subscriptions/institutions/me/members/${memberId}`, {
            method: 'PATCH',
            body: JSON.stringify(payload)
        });
    },

    async actualizarPlanInstitucional(planCode) {
        return this.request('/subscriptions/institutions/me/plan', {
            method: 'PUT',
            body: JSON.stringify({ plan_code: planCode })
        });
    },

    async loginPropietarios(accessKey) {
        return this.request('/admin/login', {
            method: 'POST',
            body: JSON.stringify({ access_key: accessKey })
        });
    },

    async cambiarContrasenaPropietarios(payload) {
        const token = sessionStorage.getItem('qgeo_owner_token');
        return this.request('/admin/change-password', {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` },
            body: JSON.stringify(payload)
        });
    },

    async listarSolicitudesInstitucionales(statusFilter = 'pending') {
        const token = sessionStorage.getItem('qgeo_owner_token');
        return this.request(`/admin/institution-applications?status_filter=${encodeURIComponent(statusFilter)}`, {
            headers: { Authorization: `Bearer ${token}` }
        });
    },

    async revisarSolicitudInstitucional(applicationId, action, payload) {
        const token = sessionStorage.getItem('qgeo_owner_token');
        return this.request(`/admin/institution-applications/${applicationId}/${action}`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` },
            body: JSON.stringify(payload)
        });
    }
};