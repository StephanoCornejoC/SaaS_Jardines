import { useState, useEffect } from "react";
import {
  Table,
  Button,
  Card,
  Space,
  Popconfirm,
  Tag,
  Alert,
  Spin,
  App,
  Typography,
  Divider,
} from "antd";
import {
  EyeOutlined,
  ThunderboltOutlined,
  HistoryOutlined,
} from "@ant-design/icons";
import api from "../services/api";

const { Title, Text } = Typography;

export default function Migrations() {
  const [preview, setPreview] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [migrations, setMigrations] = useState([]);
  const [migrationsLoading, setMigrationsLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const { message } = App.useApp();

  const fetchMigrations = async () => {
    setMigrationsLoading(true);
    try {
      const res = await api.get("/migrations/");
      setMigrations(res.data.results || res.data);
    } catch {
      message.error("Error al cargar historial de migraciones");
    } finally {
      setMigrationsLoading(false);
    }
  };

  useEffect(() => {
    fetchMigrations();
  }, []);

  const handlePreview = async () => {
    setPreviewLoading(true);
    setPreview(null);
    try {
      const res = await api.get("/migrations/preview/");
      setPreview(res.data);
    } catch (err) {
      message.error(err.response?.data?.detail || "Error al obtener vista previa");
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleExecute = async () => {
    setExecuting(true);
    try {
      await api.post("/migrations/ejecutar/");
      message.success("Migracion ejecutada exitosamente");
      setPreview(null);
      fetchMigrations();
    } catch (err) {
      const detail = err.response?.data?.detail || "Error al ejecutar migracion";
      message.error(detail);
    } finally {
      setExecuting(false);
    }
  };

  const previewColumns = [
    { title: "Entidad", dataIndex: "entidad", key: "entidad" },
    { title: "Accion", dataIndex: "accion", key: "accion" },
    { title: "Cantidad", dataIndex: "cantidad", key: "cantidad" },
    { title: "Detalle", dataIndex: "detalle", key: "detalle" },
  ];

  const migrationColumns = [
    { title: "ID", dataIndex: "id", key: "id", width: 70 },
    { title: "Fecha", dataIndex: "fecha", key: "fecha" },
    { title: "Descripcion", dataIndex: "descripcion", key: "descripcion" },
    {
      title: "Estado",
      dataIndex: "estado",
      key: "estado",
      render: (estado) => {
        const colorMap = {
          EXITOSA: "green",
          FALLIDA: "red",
          EN_PROCESO: "orange",
        };
        return <Tag color={colorMap[estado] || "default"}>{estado}</Tag>;
      },
    },
    { title: "Registros Procesados", dataIndex: "registros_procesados", key: "registros_procesados" },
    { title: "Errores", dataIndex: "errores", key: "errores" },
    { title: "Ejecutado por", dataIndex: "ejecutado_por_nombre", key: "ejecutado_por_nombre" },
  ];

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>
        Migracion de Datos
      </Title>

      <Card style={{ marginBottom: 24 }}>
        <Title level={5}>
          <EyeOutlined /> Vista Previa de Migracion
        </Title>
        <Text type="secondary" style={{ display: "block", marginBottom: 16 }}>
          Revise los datos que seran migrados antes de ejecutar el proceso.
        </Text>

        <Space style={{ marginBottom: 16 }}>
          <Button
            type="default"
            icon={<EyeOutlined />}
            onClick={handlePreview}
            loading={previewLoading}
          >
            Vista Previa
          </Button>

          <Popconfirm
            title="Ejecutar Migracion"
            description="Esta seguro de ejecutar la migracion? Este proceso no se puede deshacer."
            onConfirm={handleExecute}
            okText="Si, ejecutar"
            cancelText="Cancelar"
            okButtonProps={{ danger: true }}
          >
            <Button
              type="primary"
              danger
              icon={<ThunderboltOutlined />}
              loading={executing}
            >
              Ejecutar Migracion
            </Button>
          </Popconfirm>
        </Space>

        {previewLoading && (
          <div style={{ textAlign: "center", padding: 24 }}>
            <Spin tip="Analizando datos..." />
          </div>
        )}

        {preview && !previewLoading && (
          <>
            {preview.warnings && preview.warnings.length > 0 && (
              <Alert
                type="warning"
                message="Advertencias"
                description={
                  <ul style={{ margin: 0, paddingLeft: 20 }}>
                    {preview.warnings.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                }
                style={{ marginBottom: 16 }}
              />
            )}
            <Table
              columns={previewColumns}
              dataSource={preview.items || preview}
              rowKey={(record, index) => `${record.entidad}-${index}`}
              pagination={false}
              size="small"
            />
          </>
        )}
      </Card>

      <Card>
        <Title level={5}>
          <HistoryOutlined /> Historial de Migraciones
        </Title>
        <Divider style={{ margin: "12px 0" }} />
        <Table
          columns={migrationColumns}
          dataSource={migrations}
          rowKey="id"
          loading={migrationsLoading}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
}
