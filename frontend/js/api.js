const BASE_URL_API = "http://localhost:8000";

const ApiService = {
    async verificarSaludServidor() {
        const response = await fetch(`${BASE_URL_API}/`);
        if (!response.ok) throw new Error("No se pudo conectar al servidor FastAPI");
        return await response.json();
    },

    async registrarUsuario(datosRegistro) {
        const response = await fetch(`${BASE_URL_API}/auth/registro/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datosRegistro)
        });
        if (!response.ok) throw new Error("Error en el servidor al registrar usuario.");
        return await response.json();
    },

    async registrarFamiliar(datosFamiliar) {
        const response = await fetch(`${BASE_URL_API}/familia/agregar/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datosFamiliar)
        });
        if (!response.ok) throw new Error("Error al guardar familiar.");
        return await response.json();
    },

    async despacharAlerta(datosAlerta) {
        const response = await fetch(`${BASE_URL_API}/alertas/despachar/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datosAlerta)
        });
        if (!response.ok) throw new Error("Error al despachar alerta.");
        return await response.json();
    }
};