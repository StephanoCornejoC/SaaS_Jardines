import { useState } from "react";
import { Row, Col, Card, Button, App, Typography } from "antd";
import {
  FileExcelOutlined,
  TeamOutlined,
  CalendarOutlined,
  DollarOutlined,
} from "@ant-design/icons";
import api from "../services/api";

const { Title } = Typography;

const reports = [
  {
    key: "morosidad",
    title: "Reporte de Morosidad",
    description: "Listado de pagos pendientes y vencidos por alumno",
    icon: <DollarOutlined style={{ fontSize: 32, color: "#ff4d4f" }} />,
    endpoint: "/reports/morosidad-excel/",
    filename: "reporte_morosidad.xlsx",
  },
  {
    key: "alumnos",
    title: "Lista de Alumnos",
    description: "Listado completo de alumnos activos con informacion de contacto",
    icon: <TeamOutlined style={{ fontSize: 32, color: "#1890ff" }} />,
    endpoint: "/reports/alumnos-excel/",
    filename: "lista_alumnos.xlsx",
  },
  {
    key: "asistencia",
    title: "Reporte de Asistencia",
    description: "Resumen de asistencia por aula y periodo",
    icon: <CalendarOutlined style={{ fontSize: 32, color: "#52c41a" }} />,
    endpoint: "/reports/asistencia-excel/",
    filename: "reporte_asistencia.xlsx",
  },
  {
    key: "caja",
    title: "Reporte de Caja",
    description: "Detalle de ingresos y egresos del periodo",
    icon: <FileExcelOutlined style={{ fontSize: 32, color: "#722ed1" }} />,
    endpoint: "/reports/cashflow-excel/",
    filename: "reporte_caja.xlsx",
  },
];

export default function Reports() {
  const [downloading, setDownloading] = useState({});
  const { message } = App.useApp();

  const handleDownload = async (report) => {
    setDownloading((prev) => ({ ...prev, [report.key]: true }));
    try {
      const res = await api.get(report.endpoint, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", report.filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      message.success(`${report.title} descargado`);
    } catch {
      message.error(`Error al descargar ${report.title}`);
    } finally {
      setDownloading((prev) => ({ ...prev, [report.key]: false }));
    }
  };

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>
        Reportes
      </Title>

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
              <Typography.Text
                type="secondary"
                style={{ display: "block", marginBottom: 16, minHeight: 40 }}
              >
                {report.description}
              </Typography.Text>
              <Button
                type="primary"
                icon={<FileExcelOutlined />}
                loading={downloading[report.key]}
                onClick={() => handleDownload(report)}
              >
                Descargar Excel
              </Button>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}
