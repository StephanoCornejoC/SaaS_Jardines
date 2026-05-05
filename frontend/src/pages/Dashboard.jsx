import { useState, useEffect } from "react";
import { Row, Col, Card, Spin, Typography, Avatar, Tag, Empty } from "antd";
import {
  TeamOutlined,
  UserOutlined,
  DollarOutlined,
  WarningOutlined,
  RiseOutlined,
  FallOutlined,
} from "@ant-design/icons";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from "chart.js";
import api from "../services/api";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

const { Title, Text } = Typography;

const MES_LABELS = [
  "Ene", "Feb", "Mar", "Abr", "May", "Jun",
  "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
];

function MetricCard({ title, value, suffix, icon, color, bg, hint }) {
  return (
    <Card
      bordered={false}
      styles={{ body: { padding: 16 } }}
      style={{ height: "100%", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <Text type="secondary" style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: 0.5 }}>
            {title}
          </Text>
          <div style={{ fontSize: 26, fontWeight: 600, color, lineHeight: 1.1, marginTop: 4 }}>
            {value}
            {suffix && <Text style={{ fontSize: 14, marginLeft: 4, color: "#94a3b8" }}>{suffix}</Text>}
          </div>
          {hint && (
            <Text type="secondary" style={{ fontSize: 11 }}>{hint}</Text>
          )}
        </div>
        <Avatar
          size={44}
          style={{ background: bg, color, fontSize: 20 }}
          icon={icon}
        />
      </div>
    </Card>
  );
}

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
      <div style={{ textAlign: "center", padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  const seriesIngresos = Array.from({ length: 12 }, (_, i) => {
    const found = (data.ingresos_por_mes || []).find(
      (x) => Number(x.mes) === i + 1,
    );
    return found ? Number(found.total) : 0;
  });

  const totalAnio = seriesIngresos.reduce((a, b) => a + b, 0);
  const ingresoMes = Number(data.ingresos_mes || 0);
  const tendencia = totalAnio > 0 ? Math.round((ingresoMes / (totalAnio / 12 || 1)) * 100 - 100) : 0;

  const chartData = {
    labels: MES_LABELS,
    datasets: [
      {
        label: "Ingresos",
        data: seriesIngresos,
        borderColor: "#0d9488",
        backgroundColor: (ctx) => {
          const chart = ctx.chart;
          const { ctx: c, chartArea } = chart;
          if (!chartArea) return "rgba(13,148,136,0.15)";
          const grad = c.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
          grad.addColorStop(0, "rgba(13,148,136,0.35)");
          grad.addColorStop(1, "rgba(13,148,136,0.02)");
          return grad;
        },
        fill: true,
        tension: 0.35,
        pointRadius: 3,
        pointBackgroundColor: "#0d9488",
        pointHoverRadius: 5,
        borderWidth: 2,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { intersect: false, mode: "index" },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx) => `S/. ${Number(ctx.parsed.y).toFixed(2)}`,
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: "#64748b", font: { size: 11 } },
      },
      y: {
        beginAtZero: true,
        grid: { color: "rgba(148,163,184,0.15)" },
        ticks: {
          color: "#64748b",
          font: { size: 11 },
          callback: (v) => `S/.${v}`,
        },
      },
    },
  };

  const morosidad = Number(data.porcentaje_morosidad || 0);
  const morosidadColor =
    morosidad > 20 ? "#ef4444" : morosidad > 10 ? "#f59e0b" : "#10b981";

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>Inicio</Title>
        <Text type="secondary" style={{ fontSize: 13 }}>
          Resumen del jardín en tiempo real.
        </Text>
      </div>

      <Row gutter={[12, 12]}>
        <Col xs={12} sm={12} md={6}>
          <MetricCard
            title="Alumnos activos"
            value={data.total_alumnos}
            icon={<TeamOutlined />}
            color="#0d9488"
            bg="rgba(13,148,136,0.12)"
            hint="Matriculados"
          />
        </Col>
        <Col xs={12} sm={12} md={6}>
          <MetricCard
            title="Profesores"
            value={data.total_profesores}
            icon={<UserOutlined />}
            color="#3b82f6"
            bg="rgba(59,130,246,0.12)"
            hint="Personal docente"
          />
        </Col>
        <Col xs={12} sm={12} md={6}>
          <MetricCard
            title="Ingresos del mes"
            value={`S/. ${ingresoMes.toFixed(2)}`}
            icon={<DollarOutlined />}
            color="#7c3aed"
            bg="rgba(124,58,237,0.12)"
            hint={
              tendencia >= 0
                ? <><RiseOutlined style={{ color: "#10b981" }}/> {tendencia}% vs promedio</>
                : <><FallOutlined style={{ color: "#ef4444" }}/> {Math.abs(tendencia)}% vs promedio</>
            }
          />
        </Col>
        <Col xs={12} sm={12} md={6}>
          <MetricCard
            title="Morosidad"
            value={morosidad.toFixed(1)}
            suffix="%"
            icon={<WarningOutlined />}
            color={morosidadColor}
            bg={`${morosidadColor}1f`}
            hint={morosidad > 20 ? "Alta" : morosidad > 10 ? "Moderada" : "Baja"}
          />
        </Col>
      </Row>

      <Row gutter={[12, 12]} style={{ marginTop: 12 }}>
        <Col xs={24} lg={16}>
          <Card
            title={<span><DollarOutlined style={{ color: "#0d9488", marginRight: 6 }}/>Ingresos mensuales del año</span>}
            extra={<Tag color="cyan">Total: S/. {totalAnio.toFixed(2)}</Tag>}
            styles={{ body: { padding: 12 } }}
          >
            <div style={{ height: 240 }}>
              {totalAnio > 0 ? (
                <Line data={chartData} options={chartOptions} />
              ) : (
                <Empty description="Sin ingresos registrados aún" style={{ paddingTop: 50 }} />
              )}
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card
            title="Distribución por nivel"
            styles={{ body: { padding: 16 } }}
            style={{ height: "100%" }}
          >
            <NivelDistribucion alumnos_por_nivel={data.alumnos_por_nivel} />
          </Card>
        </Col>
      </Row>
    </div>
  );
}

function NivelDistribucion({ alumnos_por_nivel }) {
  const niveles = [
    { key: "2_anios", label: "2 años", color: "#fbbf24" },
    { key: "3_anios", label: "3 años", color: "#3b82f6" },
    { key: "4_anios", label: "4 años", color: "#8b5cf6" },
    { key: "5_anios", label: "5 años", color: "#ec4899" },
  ];

  const total = niveles.reduce(
    (acc, n) => acc + Number((alumnos_por_nivel || {})[n.key] || 0),
    0,
  );

  if (total === 0) {
    return <Empty description="Sin alumnos asignados a aulas" />;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {niveles.map((n) => {
        const count = Number((alumnos_por_nivel || {})[n.key] || 0);
        const pct = total ? Math.round((count / total) * 100) : 0;
        return (
          <div key={n.key}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <Text style={{ fontSize: 13, fontWeight: 500 }}>{n.label}</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>{count} alumnos · {pct}%</Text>
            </div>
            <div style={{ height: 8, background: "#f1f5f9", borderRadius: 4, overflow: "hidden" }}>
              <div
                style={{
                  height: "100%",
                  width: `${pct}%`,
                  background: n.color,
                  transition: "width .4s ease",
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
