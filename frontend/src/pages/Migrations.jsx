import { useState, useEffect, useCallback } from "react";
import {
  Table,
  Button,
  Card,
  Space,
  Popconfirm,
  Tag,
  Alert,
  Spin,
  Select,
  Statistic,
  Row,
  Col,
  App,
  Typography,
  Divider,
} from "antd";
import {
  EyeOutlined,
  ThunderboltOutlined,
  HistoryOutlined,
  InfoCircleOutlined,
  SwapOutlined,
  RiseOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  DeleteOutlined,
  DatabaseOutlined,
} from "@ant-design/icons";
import { InputNumber } from "antd";
import api from "../services/api";

const { Title, Text, Paragraph } = Typography;

const currentYear = new Date().getFullYear();
const yearOptions = Array.from({ length: 5 }, (_, i) => ({
  value: currentYear - 2 + i,
  label: `${currentYear - 2 + i}`,
}));

export default function Migrations() {
  const [anioOrigen, setAnioOrigen] = useState(currentYear);
  const [preview, setPreview] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [migrations, setMigrations] = useState([]);
  const [migrationsLoading, setMigrationsLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [cleanupYears, setCleanupYears] = useState(2);
  const [cleaning, setCleaning] = useState(false);
  const { message } = App.useApp();

  const handleCleanup = async () => {
    setCleaning(true);
    try {
      const res = await api.post("/migrations/cleanup-antiguos/", {
        years_to_keep: cleanupYears,
      });
      message.success(res.data?.message || "Limpieza completada");
    } catch (err) {
      const detail = err.response?.data?.error || "Error al ejecutar la limpieza";
      message.error(detail);
    } finally {
      setCleaning(false);
    }
  };

  const fetchMigrations = useCallback(async () => {
    setMigrationsLoading(true);
    try {
      const res = await api.get("/migrations/");
      setMigrations(res.data.results || res.data);
    } catch {
      message.error("Error al cargar historial de migraciones");
    } finally {
      setMigrationsLoading(false);
    }
  }, [message]);

  useEffect(() => { fetchMigrations(); }, [fetchMigrations]);

  const handlePreview = async () => {
    setPreviewLoading(true);
    setPreview(null);
    try {
      const res = await api.get("/migrations/preview/", {
        params: { anio_origen: anioOrigen },
      });
      setPreview(res.data);
    } catch (err) {
      const detail = err.response?.data?.error || "Error al obtener vista previa";
      message.error(detail);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleExecute = async () => {
    setExecuting(true);
    try {
      await api.post("/migrations/ejecutar/", { anio_origen: anioOrigen });
      message.success(`Migración de ${anioOrigen} a ${anioOrigen + 1} ejecutada correctamente`);
      setPreview(null);
      fetchMigrations();
    } catch (err) {
      const detail = err.response?.data?.error || "Error al ejecutar migración";
      message.error(detail);
    } finally {
      setExecuting(false);
    }
  };

  const migrationColumns = [
    { title: "ID", dataIndex: "id", key: "id", width: 60 },
    {
      title: "Origen → Destino",
      key: "anios",
      render: (_, r) => (
        <span>{r.anio_origen} → {r.anio_destino}</span>
      ),
    },
    { title: "Fecha", dataIndex: "fecha", key: "fecha" },
    {
      title: "Estado",
      dataIndex: "status",
      key: "status",
      render: (estado) => (
        <Tag color={estado === "EJECUTADO" ? "green" : "orange"}>{estado || "—"}</Tag>
      ),
    },
    { title: "Total migrados", dataIndex: "total_migrados", key: "total_migrados" },
    {
      title: "Ejecutado por",
      dataIndex: "ejecutado_por_nombre",
      key: "ejecutado_por_nombre",
      render: (n) => n || "—",
    },
  ];

  return (
    <div>
      <Title level={4} style={{ margin: 0 }}>
        <SwapOutlined style={{ marginRight: 8, color: "#0d9488" }} />
        Migración anual
      </Title>
      <Text type="secondary" style={{ fontSize: 13, marginBottom: 20, display: "block" }}>
        Promueve a los alumnos al siguiente año escolar.
      </Text>

      <Alert
        type="info"
        showIcon
        icon={<InfoCircleOutlined />}
        message="¿Qué hace este botón?"
        description={
          <div>
            <Paragraph style={{ marginBottom: 8 }}>
              Al iniciar un nuevo año escolar, todos los alumnos deben pasar al aula que les corresponde por edad.
              En lugar de moverlos uno por uno, esta función lo hace para todos a la vez:
            </Paragraph>
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              <li>Alumnos del aula de <b>2 años</b> → aula de <b>3 años</b>.</li>
              <li>Alumnos del aula de <b>3 años</b> → aula de <b>4 años</b>.</li>
              <li>Alumnos del aula de <b>4 años</b> → aula de <b>5 años</b>.</li>
              <li>Alumnos del aula de <b>5 años</b> → marcados como <b>EGRESADOS</b>.</li>
            </ul>
            <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>
              <b>Cuándo usarlo:</b> al final/inicio de cada año escolar (diciembre o marzo).
              Siempre revisa primero la <b>vista previa</b>.
            </Paragraph>
          </div>
        }
        style={{ marginBottom: 24 }}
      />

      <Card style={{ marginBottom: 24 }}>
        <Space size="large" wrap style={{ marginBottom: 16 }}>
          <div>
            <Text strong style={{ display: "block", marginBottom: 4, fontSize: 12 }}>Año origen</Text>
            <Select
              value={anioOrigen}
              onChange={(v) => { setAnioOrigen(v); setPreview(null); }}
              options={yearOptions}
              style={{ width: 140 }}
            />
          </div>
          <div>
            <Text strong style={{ display: "block", marginBottom: 4, fontSize: 12 }}>Año destino</Text>
            <Tag color="cyan" style={{ fontSize: 14, padding: "4px 12px" }}>{anioOrigen + 1}</Tag>
          </div>
          <div style={{ alignSelf: "flex-end" }}>
            <Space>
              <Button icon={<EyeOutlined />} onClick={handlePreview} loading={previewLoading}>
                Vista previa
              </Button>
              <Popconfirm
                title="Ejecutar migración"
                description={`Promoverá a los alumnos de ${anioOrigen} a ${anioOrigen + 1}. Esta acción no se puede deshacer.`}
                onConfirm={handleExecute}
                okText="Sí, ejecutar"
                cancelText="Cancelar"
                okButtonProps={{ danger: true }}
                disabled={!preview}
              >
                <Button
                  type="primary"
                  danger
                  icon={<ThunderboltOutlined />}
                  loading={executing}
                  disabled={!preview}
                >
                  Ejecutar migración
                </Button>
              </Popconfirm>
            </Space>
          </div>
        </Space>

        {!preview && !previewLoading && (
          <Alert
            type="warning"
            message="Pulsa Vista previa primero"
            description="Para evitar errores, primero genera la vista previa. Solo después podrás ejecutar la migración."
          />
        )}

        {previewLoading && (
          <div style={{ textAlign: "center", padding: 32 }}>
            <Spin tip="Analizando alumnos..." />
          </div>
        )}

        {preview && !previewLoading && (
          <PreviewView preview={preview} />
        )}
      </Card>

      <Card style={{ marginBottom: 24 }}>
        <Title level={5}>
          <DatabaseOutlined /> Limpieza de datos antiguos
        </Title>
        <Alert
          type="warning"
          showIcon
          message="Esta acción elimina permanentemente"
          description={
            <div>
              <Paragraph style={{ marginBottom: 8 }}>
                Borra <b>por completo</b> a los alumnos egresados hace más de <b>{cleanupYears} año(s)</b>:
                sus datos personales, apoderados, ficha médica, matrículas, pagos y asistencias.
              </Paragraph>
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                <li>Se conservan los <b>cierres mensuales</b> (totales agregados de ingresos y egresos por mes), así no pierdes los reportes históricos del jardín.</li>
                <li>Antes de eliminar, los meses sin cierre se sellan automáticamente.</li>
                <li>La acción es <b>irreversible</b>.</li>
              </ul>
              <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>
                <b>Cuándo usarlo:</b> al iniciar cada año escolar, después de la migración anual.
                Mantiene la base de datos liviana y reduce costos de hosting.
              </Paragraph>
            </div>
          }
          style={{ marginBottom: 16 }}
        />
        <Space wrap>
          <div>
            <Text strong style={{ display: "block", marginBottom: 4, fontSize: 12 }}>
              Conservar últimos
            </Text>
            <InputNumber
              min={1}
              max={10}
              value={cleanupYears}
              onChange={(v) => setCleanupYears(v ?? 2)}
              addonAfter="años"
              style={{ width: 130 }}
            />
          </div>
          <div style={{ alignSelf: "flex-end" }}>
            <Popconfirm
              title="¿Eliminar datos antiguos?"
              description={`Se eliminarán permanentemente alumnos egresados de hace más de ${cleanupYears} año(s) y sus datos asociados.`}
              onConfirm={handleCleanup}
              okText="Sí, eliminar"
              cancelText="Cancelar"
              okButtonProps={{ danger: true }}
            >
              <Button danger icon={<DeleteOutlined />} loading={cleaning}>
                Ejecutar limpieza
              </Button>
            </Popconfirm>
          </div>
        </Space>
      </Card>

      <Card>
        <Title level={5}>
          <HistoryOutlined /> Historial de migraciones
        </Title>
        <Divider style={{ margin: "12px 0" }} />
        <Table
          columns={migrationColumns}
          dataSource={migrations}
          rowKey="id"
          loading={migrationsLoading}
          pagination={{ pageSize: 10, hideOnSinglePage: true }}
          locale={{ emptyText: "Aún no se ha ejecutado ninguna migración" }}
        />
      </Card>
    </div>
  );
}

function PreviewView({ preview }) {
  const { anio_origen, anio_destino, total_alumnos, por_nivel = [], promueven = [], egresan = [], sin_aula_destino = [] } = preview;
  const haySinAulaDestino = sin_aula_destino.length > 0;

  return (
    <div>
      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Total alumnos"
              value={total_alumnos}
              valueStyle={{ color: "#0d9488" }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Promueven"
              value={promueven.length}
              prefix={<RiseOutlined />}
              valueStyle={{ color: "#10b981" }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Egresan"
              value={egresan.length}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: "#3b82f6" }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Sin aula destino"
              value={sin_aula_destino.length}
              prefix={<WarningOutlined />}
              valueStyle={{ color: sin_aula_destino.length ? "#ef4444" : "#94a3b8" }}
            />
          </Card>
        </Col>
      </Row>

      {haySinAulaDestino && (
        <Alert
          type="error"
          showIcon
          message={`${sin_aula_destino.length} alumno(s) no pueden migrarse`}
          description={
            <span>
              No existe el aula del nivel destino para el año <b>{anio_destino}</b>.
              Crea las aulas correspondientes desde el módulo <b>Aulas</b> antes de ejecutar la migración.
            </span>
          }
          style={{ marginBottom: 16 }}
        />
      )}

      {por_nivel.length > 0 && (
        <Card size="small" title={`Resumen por nivel · ${anio_origen} → ${anio_destino}`} style={{ marginBottom: 12 }}>
          <Table
            size="small"
            dataSource={por_nivel}
            rowKey="nivel"
            pagination={false}
            columns={[
              { title: "Nivel actual",  dataIndex: "nivel",    key: "nivel",    render: (n) => `${n} años` },
              { title: "Cantidad",      dataIndex: "cantidad", key: "cantidad" },
              { title: "Acción",        dataIndex: "accion",   key: "accion",
                render: (a) => <Tag color={a === "EGRESA" ? "blue" : "green"}>{a}</Tag>,
              },
            ]}
          />
        </Card>
      )}

      {promueven.length > 0 && (
        <DetailTable title={`Alumnos que promueven (${promueven.length})`} data={promueven} color="green" showAulaDestino />
      )}
      {egresan.length > 0 && (
        <DetailTable title={`Alumnos que egresan (${egresan.length})`} data={egresan} color="blue" />
      )}
      {haySinAulaDestino && (
        <DetailTable title={`Alumnos sin aula destino (${sin_aula_destino.length})`} data={sin_aula_destino} color="red" warning />
      )}
    </div>
  );
}

function DetailTable({ title, data, color, showAulaDestino, warning }) {
  const columns = [
    { title: "Alumno", dataIndex: "student_nombre", key: "student_nombre" },
    { title: "Aula origen", dataIndex: "aula_origen", key: "aula_origen" },
    { title: "Nivel actual", dataIndex: "nivel_actual", key: "nivel_actual", render: (n) => `${n} años` },
  ];
  if (showAulaDestino) {
    columns.push({
      title: "Aula destino",
      dataIndex: "aula_destino",
      key: "aula_destino",
      render: (a) => a || <Tag color="red">No existe</Tag>,
    });
  }
  return (
    <Card
      size="small"
      title={<span style={{ color: warning ? "#ef4444" : undefined }}>{title}</span>}
      style={{ marginBottom: 12, borderColor: warning ? "#fecaca" : undefined }}
    >
      <Table
        size="small"
        dataSource={data}
        rowKey="student_id"
        pagination={{ pageSize: 5, hideOnSinglePage: true }}
        columns={columns}
      />
    </Card>
  );
}
