import { useState, useEffect } from "react";
import { Row, Col, Card, Statistic, Spin, Typography } from "antd";
import {
  TeamOutlined,
  UserOutlined,
  DollarOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title as ChartTitle,
  Tooltip,
  Legend,
} from "chart.js";
import api from "../services/api";

ChartJS.register(CategoryScale, LinearScale, BarElement, ChartTitle, Tooltip, Legend);

const { Title } = Typography;

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await api.get("/dashboard/resumen/");
        setData(res.data);
      } catch {
        setData({
          total_alumnos: 0,
          total_profesores: 0,
          ingresos_mes: 0,
          porcentaje_morosidad: 0,
          ingresos_por_mes: [],
        });
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: 100 }}>
        <Spin size="large" />
      </div>
    );
  }

  const chartData = {
    labels: (data.ingresos_por_mes || []).map((item) => item.mes),
    datasets: [
      {
        label: "Ingresos (S/.)",
        data: (data.ingresos_por_mes || []).map((item) => item.total),
        backgroundColor: "rgba(24, 144, 255, 0.6)",
        borderColor: "rgba(24, 144, 255, 1)",
        borderWidth: 1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: { position: "top" },
      title: { display: true, text: "Ingresos Mensuales" },
    },
    scales: {
      y: { beginAtZero: true },
    },
  };

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>
        Dashboard
      </Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Alumnos"
              value={data.total_alumnos}
              prefix={<TeamOutlined />}
              valueStyle={{ color: "#1890ff" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Profesores"
              value={data.total_profesores}
              prefix={<UserOutlined />}
              valueStyle={{ color: "#52c41a" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Ingresos del Mes"
              value={data.ingresos_mes}
              prefix={<DollarOutlined />}
              precision={2}
              valueStyle={{ color: "#722ed1" }}
              suffix="S/."
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="% Morosidad"
              value={data.porcentaje_morosidad}
              prefix={<WarningOutlined />}
              precision={1}
              suffix="%"
              valueStyle={{
                color: data.porcentaje_morosidad > 20 ? "#ff4d4f" : "#faad14",
              }}
            />
          </Card>
        </Col>
      </Row>

      <Card style={{ marginTop: 24 }}>
        <Bar data={chartData} options={chartOptions} />
      </Card>
    </div>
  );
}
