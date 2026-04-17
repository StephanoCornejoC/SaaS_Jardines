package com.corem.saas.helpers;

import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import io.restassured.response.Response;
import io.restassured.specification.RequestSpecification;
import lombok.extern.slf4j.Slf4j;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Cliente de API REST para SAAS COREM.
 *
 * Responsabilidad: Configurar datos de prueba via API (backend Django)
 * para hacer los tests E2E independientes y rapidos.
 *
 * Multi-tenant: todas las peticiones incluyen el header Host: test.localhost
 * para que Django-tenants enrute al schema correcto.
 */
@Slf4j
public class CoremApiClient {

    private final String baseUrl;
    private final String tenantHost;
    private final String email;
    private final String password;

    // Token en cache para no hacer login en cada llamada
    private String cachedToken;

    public CoremApiClient(String baseUrl, String tenantHost, String email, String password) {
        this.baseUrl = baseUrl;
        this.tenantHost = tenantHost;
        this.email = email;
        this.password = password;
        RestAssured.enableLoggingOfRequestAndResponseIfValidationFails();
    }

    /** Constructor con valores por defecto del entorno local */
    public static CoremApiClient forLocalEnvironment() {
        return new CoremApiClient(
            "http://localhost:8000",
            "test.localhost",
            "admin@test.com",
            "TestPass1234"
        );
    }

    // ============================================================
    // AUTENTICACION
    // ============================================================

    /**
     * Obtiene el JWT token. Usa cache para evitar llamadas repetidas.
     */
    public String getAuthToken() {
        if (cachedToken != null) {
            return cachedToken;
        }

        Map<String, String> credentials = new HashMap<>();
        credentials.put("email", email);
        credentials.put("password", password);

        Response response = baseRequest()
            .body(credentials)
            .post("/api/v1/auth/login/");

        if (response.statusCode() != 200) {
            throw new RuntimeException(
                "Login fallido. Status: " + response.statusCode() +
                " Body: " + response.getBody().asString()
            );
        }

        cachedToken = response.jsonPath().getString("access");
        log.info("Token JWT obtenido para '{}'", email);
        return cachedToken;
    }

    /** Invalida el cache del token (util despues de logout) */
    public void invalidateToken() {
        cachedToken = null;
    }

    // ============================================================
    // ALUMNOS
    // ============================================================

    /**
     * Crea un alumno via API. Devuelve el mapa con los datos del alumno creado.
     */
    public Map<String, Object> createStudent(String token, Map<String, String> studentData) {
        Response response = authenticatedRequest(token)
            .body(studentData)
            .post("/api/v1/alumnos/");

        if (response.statusCode() != 201 && response.statusCode() != 200) {
            throw new RuntimeException(
                "Error al crear alumno. Status: " + response.statusCode() +
                " Body: " + response.getBody().asString()
            );
        }

        log.info("Alumno creado via API: DNI={}", studentData.get("dni"));
        return response.jsonPath().getMap("$");
    }

    /**
     * Crea un alumno con datos basicos.
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> createStudent(String dni, String nombres, String apellidos,
                                              String fechaNacimiento, String genero) {
        String token = getAuthToken();
        Map<String, String> data = new HashMap<>();
        data.put("dni", dni);
        data.put("nombres", nombres);
        data.put("apellidos", apellidos);
        data.put("fecha_nacimiento", fechaNacimiento);
        data.put("genero", genero);
        return createStudent(token, data);
    }

    /**
     * Elimina un alumno por ID.
     */
    public void deleteStudent(String token, Object studentId) {
        Response response = authenticatedRequest(token)
            .delete("/api/v1/alumnos/" + studentId + "/");

        if (response.statusCode() != 204 && response.statusCode() != 200) {
            log.warn("No se pudo eliminar alumno ID {}. Status: {}", studentId, response.statusCode());
        } else {
            log.info("Alumno ID {} eliminado via API", studentId);
        }
    }

    /**
     * Elimina un alumno usando el token cacheado.
     */
    public void deleteStudent(Object studentId) {
        deleteStudent(getAuthToken(), studentId);
    }

    // ============================================================
    // AULAS (CLASSROOMS)
    // ============================================================

    /**
     * Obtiene la lista de aulas activas.
     */
    @SuppressWarnings("unchecked")
    public List<Map<String, Object>> getClassrooms() {
        String token = getAuthToken();
        Response response = authenticatedRequest(token)
            .get("/api/v1/aulas/");

        if (response.statusCode() != 200) {
            throw new RuntimeException(
                "Error al obtener aulas. Status: " + response.statusCode()
            );
        }

        // Puede ser una lista directa o un objeto con 'results'
        Object body = response.jsonPath().get("$");
        if (body instanceof List) {
            return (List<Map<String, Object>>) body;
        }
        return response.jsonPath().getList("results");
    }

    /**
     * Devuelve el nombre de la primera aula activa, o null si no hay.
     */
    public String getFirstClassroomDisplayName() {
        List<Map<String, Object>> classrooms = getClassrooms();
        if (classrooms == null || classrooms.isEmpty()) {
            return null;
        }
        Map<String, Object> first = classrooms.get(0);
        String nombre = (String) first.get("nombre");
        String nivel = (String) first.get("nivel");
        return nombre + " (" + nivel + ")";
    }

    // ============================================================
    // UTILIDADES INTERNAS
    // ============================================================

    /**
     * Request base con Content-Type JSON y Host header del tenant.
     */
    private RequestSpecification baseRequest() {
        return RestAssured.given()
            .baseUri(baseUrl)
            .header("Host", tenantHost)
            .contentType(ContentType.JSON)
            .accept(ContentType.JSON);
    }

    /**
     * Request autenticada con Bearer token.
     */
    private RequestSpecification authenticatedRequest(String token) {
        return baseRequest()
            .header("Authorization", "Bearer " + token);
    }
}
