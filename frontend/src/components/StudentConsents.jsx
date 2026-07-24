import { useState, useEffect, useCallback } from "react";
import {
  Card,
  Button,
  Tag,
  Select,
  Space,
  Typography,
  Empty,
  Spin,
  Alert,
  App,
  Popconfirm,
} from "antd";
import {
  SafetyCertificateOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from "@ant-design/icons";
import api from "../services/api";

const { Text, Paragraph } = Typography;

const TIPO_COLOR = {
  DATOS_PERSONALES: "blue",
  DATOS_SALUD: "red",
  IMAGEN: "purple",
  COMUNICACIONES: "cyan",
};

/**
 * Sección de consentimientos (Ley 29733) dentro de la ficha del alumno.
 *
 * Flujo presencial-digital: la directora muestra esta pantalla al apoderado,
 * el apoderado LEE cada documento en pantalla y otorga su consentimiento ahí
 * mismo. El registro queda con el apoderado, la fecha y la IP (esto último lo
 * agrega el backend). Un consentimiento se pide UNA vez por documento; vuelve
 * a aparecer como "Pendiente" si es obligatorio y falta, o si sale una versión
 * nueva de la política.
 */
export default function StudentConsents({ studentId, apoderados = [] }) {
  const { message } = App.useApp();
  const [docs, setDocs] = useState([]);
  const [estado, setEstado] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(null); // documento id en curso
  const [selectedGuardian, setSelectedGuardian] = useState({}); // {docId: guardianId}

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [docsRes, estadoRes] = await Promise.allSettled([
        api.get("/consents/documentos/?activo=true"),
        api.get(`/consents/registros/estado-alumno/?student=${studentId}`),
      ]);
      if (docsRes.status === "fulfilled") {
        setDocs(docsRes.value.data.results || docsRes.value.data);
      }
      if (estadoRes.status === "fulfilled") {
        setEstado(estadoRes.value.data);
      }
    } catch (err) {
      console.error("Error al cargar consentimientos:", err);
      message.error("Error al cargar los consentimientos");
    } finally {
      setLoading(false);
    }
  }, [studentId, message]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  // Estado (vigente/pendiente) indexado por documento id.
  const estadoPorDoc = {};
  (estado?.documentos || []).forEach((d) => {
    estadoPorDoc[d.documento] = d;
  });

  const principalId = (apoderados.find((a) => a.es_principal) || apoderados[0])?.id;

  const guardianOptions = apoderados.map((a) => ({
    value: a.id,
    label: `${a.nombres} ${a.apellidos}${a.es_principal ? " (principal)" : ""}`,
  }));

  const registrar = async (docId, otorgado) => {
    const guardianId = selectedGuardian[docId] ?? principalId ?? null;
    setSubmitting(docId);
    try {
      await api.post("/consents/registros/", {
        documento: docId,
        student: Number(studentId),
        guardian: guardianId,
        otorgado,
      });
      message.success(otorgado ? "Consentimiento registrado" : "Consentimiento revocado");
      fetchAll();
    } catch (err) {
      const detail = err.response?.data
        ? Object.values(err.response.data).flat().join(", ")
        : "No se pudo registrar el consentimiento";
      message.error(detail);
    } finally {
      setSubmitting(null);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: 60 }}>
        <Spin />
      </div>
    );
  }

  if (!docs.length) {
    return (
      <Empty
        description={
          <span>
            Aún no hay documentos de consentimiento configurados.
            <br />
            <Text type="secondary">
              Se crean una vez por jardín (datos personales, ficha médica, imagen,
              comunicaciones) y luego se registran acá con cada apoderado.
            </Text>
          </span>
        }
      />
    );
  }

  return (
    <div>
      {estado && (
        <Alert
          type={estado.completo ? "success" : "warning"}
          showIcon
          style={{ marginBottom: 16 }}
          message={
            estado.completo
              ? "Todos los consentimientos obligatorios están al día."
              : `Faltan ${estado.pendientes} consentimiento(s) obligatorio(s).`
          }
          description="Mostrá esta pantalla al apoderado: puede leer cada documento antes de otorgar su consentimiento."
        />
      )}

      <Space direction="vertical" size="middle" style={{ width: "100%" }}>
        {docs.map((doc) => {
          const st = estadoPorDoc[doc.id];
          const vigente = st?.vigente;
          return (
            <Card
              key={doc.id}
              size="small"
              title={
                <Space wrap>
                  <SafetyCertificateOutlined style={{ color: "#028090" }} />
                  <span>{doc.titulo}</span>
                  <Tag color={TIPO_COLOR[doc.tipo] || "default"}>{doc.tipo_display}</Tag>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    v{doc.version}
                  </Text>
                  {doc.obligatorio ? <Tag color="volcano">Obligatorio</Tag> : <Tag>Opcional</Tag>}
                </Space>
              }
              extra={
                vigente ? (
                  <Tag icon={<CheckCircleOutlined />} color="green">
                    Otorgado
                  </Tag>
                ) : (
                  <Tag icon={<ClockCircleOutlined />} color="orange">
                    Pendiente
                  </Tag>
                )
              }
            >
              <Paragraph
                style={{
                  maxHeight: 180,
                  overflowY: "auto",
                  background: "#f8fafc",
                  padding: 12,
                  borderRadius: 6,
                  whiteSpace: "pre-wrap",
                  fontSize: 13,
                  marginBottom: 12,
                }}
              >
                {doc.contenido}
              </Paragraph>

              {vigente ? (
                <Space wrap>
                  <Text type="success">
                    Otorgado
                    {st?.fecha ? ` el ${new Date(st.fecha).toLocaleDateString("es-PE")}` : ""}.
                  </Text>
                  <Popconfirm
                    title="¿Revocar este consentimiento?"
                    description="Queda registrado como revocado; no se borra el historial."
                    onConfirm={() => registrar(doc.id, false)}
                    okText="Sí, revocar"
                    cancelText="Cancelar"
                    okButtonProps={{ danger: true }}
                  >
                    <Button size="small" danger loading={submitting === doc.id}>
                      Revocar
                    </Button>
                  </Popconfirm>
                </Space>
              ) : (
                <Space wrap>
                  <Select
                    style={{ minWidth: 240 }}
                    placeholder="Apoderado que otorga"
                    options={guardianOptions}
                    value={selectedGuardian[doc.id] ?? principalId}
                    onChange={(v) => setSelectedGuardian((s) => ({ ...s, [doc.id]: v }))}
                    disabled={!guardianOptions.length}
                  />
                  <Button
                    type="primary"
                    loading={submitting === doc.id}
                    disabled={!guardianOptions.length}
                    onClick={() => registrar(doc.id, true)}
                  >
                    Registrar consentimiento
                  </Button>
                  {!guardianOptions.length && (
                    <Text type="warning">Registrá primero un apoderado.</Text>
                  )}
                </Space>
              )}
            </Card>
          );
        })}
      </Space>
    </div>
  );
}
