import { useState, useEffect } from "react";
import {
  Row,
  Col,
  Card,
  Button,
  Modal,
  Form,
  Select,
  App,
  Typography,
  Space,
} from "antd";
import {
  FileExcelOutlined,
  TeamOutlined,
  CalendarOutlined,
  DollarOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import api from "../services/api";

const { Title, Text } = Typography;

const meses = [
  { value: 1, label: "Enero" },
  { value: 2, label: "Febrero" },
  { value: 3, label: "Marzo" },
  { value: 4, label: "Abril" },
  { value: 5, label: "Mayo" },
  { value: 6, label: "Junio" },
  { value: 7, label: "Julio" },
  { value: 8, label: "Agosto" },
  { value: 9, label: "Septiembre" },
  { value: 10, label: "Octubre" },
  { value: 11, label: "Noviembre" },
  { value: 12, label: "Diciembre" },
];

const currentYear = new Date().getFullYear();
const currentMonth = new Date().getMonth() + 1;
const yearOptions = Array.from({ length: 5 }, (_, i) => ({
  value: currentYear - 2 + i,
  label: `${currentYear - 2 + i}`,
}));

const reports = [
  {
    key: "morosidad",
    title: "Reporte de morosidad",
    description: "Pensiones vencidas no pagadas, agrupadas por alumno",
    icon: <WarningOutlined style={{ fontSize: 32, color: "#ef4444" }} />,
    endpoint: "/reports/morosidad-excel/",
    filename: (p) => `morosidad_${p.anio}.xlsx`,
    fields: ["anio"],
  },
  {
    key: "alumnos",
    title: "Lista de alumnos",
    description: "Alumnos activos agrupados por aula",
    icon: <TeamOutlined style={{ fontSize: 32, color: "#0d9488" }} />,
    endpoint: "/reports/alumnos-excel/",
    filename: () => "lista_alumnos.xlsx",
    fields: [],
  },
  {
    key: "asistencia",
    title: "Reporte de asistencia",
    description: "Resumen mensual de asistencia. Una hoja por aula",
    icon: <CalendarOutlined style={{ fontSize: 32, color: "#3b82f6" }} />,
    endpoint: "/reports/asistencia-excel/",
    filename: (p) => `asistencia_${p.mes}_${p.anio}.xlsx`,
    fields: ["mes", "anio", "classroom_id"],
  },
  {
    key: "caja",
    title: "Reporte de caja",
    description: "Ingresos y egresos del mes seleccionado",
    icon: <DollarOutlined style={{ fontSize: 32, color: "#7c3aed" }} />,
    endpoint: "/reports/cashflow-excel/",
    filename: (p) => `caja_${p.mes}_${p.anio}.xlsx`,
    fields: ["mes", "anio"],
  },
];

export default function Reports() {
  const [classrooms, setClassrooms] = useState([]);
  const [downloading, setDownloading] = useState({});
  const [modalReport, setModalReport] = useState(null);
  const [form] = Form.useForm();
  const { message } = App.useApp();

  useEffect(() => {
    api.get("/classrooms/").then((res) => {
      setClassrooms(res.data.results || res.data);
    }).catch(() => {});
  }, []);

  const triggerDownload = async (report, params = {}) => {
    setDownloading((prev) => ({ ...prev, [report.key]: true }));
    try {
      const res = await api.get(report.endpoint, {
        params,
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", report.filename(params));
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      message.success(`${report.title} descargado`);
    } catch (err) {
      const detail = err.response?.data?.error || `No se pudo descargar ${report.title}`;
      message.error(detail);
    } finally {
      setDownloading((prev) => ({ ...prev, [report.key]: false }));
    }
  };

  const openModal = (report) => {
    if (report.fields.length === 0) {
      triggerDownload(report);
      return;
    }
    form.resetFields();
    const defaults = {};
    if (report.fields.includes("mes")) defaults.mes = currentMonth;
    if (report.fields.includes("anio")) defaults.anio = currentYear;
    form.setFieldsValue(defaults);
    setModalReport(report);
  };

  const handleConfirm = async () => {
    const values = await form.validateFields();
    const params = {};
    modalReport.fields.forEach((f) => {
      if (values[f] !== undefined && values[f] !== null && values[f] !== "")
        params[f] = values[f];
    });
    setModalReport(null);
    triggerDownload(modalReport, params);
  };

  return (
    <div>
      <Title level={4} style={{ margin: 0 }}>
        <FileExcelOutlined style={{ marginRight: 8, color: "#0d9488" }} />
        Reportes
      </Title>
      <Text type="secondary" style={{ fontSize: 13, marginBottom: 20, display: "block" }}>
        Descarga los reportes en Excel. Selecciona el periodo cuando corresponda.
      </Text>

      <Row gutter={[16, 16]}>
        {reports.map((report) => (
          <Col xs={24} sm={12} lg={6} key={report.key}>
            <Card
              hoverable
              style={{ textAlign: "center", height: "100%" }}
              styles={{ body: { padding: 24 } }}
            >
              <div style={{ marginBottom: 16 }}>{report.icon}</div>
              <Title level={5} style={{ marginBottom: 8 }}>
                {report.title}
              </Title>
              <Text
                type="secondary"
                style={{ display: "block", marginBottom: 16, minHeight: 40 }}
              >
                {report.description}
              </Text>
              <Button
                type="primary"
                icon={<FileExcelOutlined />}
                loading={downloading[report.key]}
                onClick={() => openModal(report)}
              >
                Descargar
              </Button>
            </Card>
          </Col>
        ))}
      </Row>

      <Modal
        title={modalReport ? `${modalReport.title}` : ""}
        open={!!modalReport}
        onOk={handleConfirm}
        onCancel={() => setModalReport(null)}
        okText="Descargar"
        cancelText="Cancelar"
      >
        <Text type="secondary" style={{ display: "block", marginBottom: 16 }}>
          Selecciona el periodo del reporte.
        </Text>
        <Form form={form} layout="vertical">
          {modalReport?.fields.includes("mes") && (
            <Form.Item name="mes" label="Mes" rules={[{ required: true }]}>
              <Select options={meses} />
            </Form.Item>
          )}
          {modalReport?.fields.includes("anio") && (
            <Form.Item name="anio" label="Año" rules={[{ required: true }]}>
              <Select options={yearOptions} />
            </Form.Item>
          )}
          {modalReport?.fields.includes("classroom_id") && (
            <Form.Item
              name="classroom_id"
              label="Aula"
              tooltip="Vacío = todas las aulas, una hoja por cada una"
            >
              <Select
                allowClear
                placeholder="Todas las aulas"
                options={classrooms.map((c) => ({
                  value: c.id,
                  label: `${c.nombre} (${c.nivel_edad} años)`,
                }))}
              />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
}
