package com.corem.saas.helpers;

import java.util.HashMap;
import java.util.Map;

/**
 * Almacen de datos de prueba compartido entre steps dentro de un escenario.
 *
 * Permite que los steps de configuracion (Dado que...) guarden IDs de registros
 * creados via API para que los steps de limpieza (afterScenario) puedan
 * eliminarlos sin contaminar otros tests.
 *
 * Se usa como singleton de Cucumber (scope: escenario).
 */
public class TestDataStore {

    private static final ThreadLocal<TestDataStore> INSTANCE = ThreadLocal.withInitial(TestDataStore::new);

    private final Map<String, Object> store = new HashMap<>();

    private TestDataStore() {}

    public static TestDataStore getInstance() {
        return INSTANCE.get();
    }

    public void put(String key, Object value) {
        store.put(key, value);
    }

    @SuppressWarnings("unchecked")
    public <T> T get(String key) {
        return (T) store.get(key);
    }

    public boolean has(String key) {
        return store.containsKey(key);
    }

    public void remove(String key) {
        store.remove(key);
    }

    public void clear() {
        store.clear();
    }

    // Keys predefinidas para evitar typos
    public static final String ALUMNO_ID = "alumno_id";
    public static final String ALUMNO_DNI = "alumno_dni";
    public static final String ALUMNO_NOMBRES = "alumno_nombres";
    public static final String CLASSROOM_NAME = "classroom_display_name";
    public static final String TRANSACTION_COUNT_BEFORE = "transaction_count_before";
    public static final String DOWNLOAD_FILE_NAME = "download_file_name";
    public static final String JWT_TOKEN = "jwt_token";
}
