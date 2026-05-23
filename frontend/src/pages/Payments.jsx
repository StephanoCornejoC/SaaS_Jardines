import { useState, useEffect, useCallback, useMemo } from "react";
import {
  Card,
  Input,
  Select,
  Space,
  Button,
  Tag,
  Avatar,
  Empty,
  Spin,
  Modal,
  Form,
  DatePicker,
  Statistic,
  Progress,
  Table,
  Descriptions,
  App,
  Typography,
} from "antd";
import {
  SearchOutlined,
  DollarOutlined,
  ArrowLeftOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  UserOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";
import api from "../services/api";

const { Title, Text } = Typography;

const meses = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

const currentYear = new Date().getFullYear();
const yearOptions = Array.from({ length: 5 }, (_, i) => ({
  value: currentYear - 2 + i,
  label: `${currentYear - 2 + i}`,
}));

const ESTADO_CFG = {
  PAGADO:    { color: "green",  icon: <CheckCircleOutlined />, label: "Pagado"    },
  PENDIENTE: { color: "orange", icon: <ClockCircleOutlined />, label: "Pendiente" },
  VENCIDO:   { color: "red",    icon: <WarningOutlined />,     label: "Vencido"   },
  EXONERADO: { color: "blue",   icon: <CheckCircleOutlined />, label: "Exonerado" },
};

export default function Payments() {
  const [students, setStudents] = useState([]);
  const [classrooms, setClassrooms] = useState([]);
  const [loadingList, setLoadingList] = useState(false);
  const [search, setSearch] = useState("");
  const [classroomFilter, setClassroomFilter] = useState(undefined);
  const [anio, setAnio] = useState(currentYear);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [studentDetail, setStudentDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [payModalOpen, setPayModalOpen] = useState(false);
  const [payingPayment, setPayingPayment] = useState(null);
  const [saving, setSaving] = useState(false);
  const [payForm] = Form.useForm();
  const { message } = App.useApp();

  const fetchStudents = useCallback(async () => {
    setLoadingList(true);
    try {
      const params = { estado: "ACTIVO" };
      if (search) params.search = search;
      if (classroomFilter) params.classroom = classroomFilter;
      const res = await api.get("/students/", { params });
      setStudents(res.data.results || res.data);
    } catch {
      message.error("No se pudieron cargar los alumnos");
    } finally {
      setLoadingList(false);
    }
  }, [search, classroomFilter, message]);

  useEffect(() => { fetchStudents(); }, [fetchStudents]);

  useEffect(() => {
    const fetchClassrooms = async () => {
      try {
        const res = await api.get("/classrooms/");
        setClassrooms(res.data.results || res.data);
      } catch { /* ignore */ }
    };
    fetchClassrooms();
  }, []);

  const fetchStudentDetail = useCallback(async (studentId, year) => {
    setLoadingDetail(true);
    try {
      const res = await api.get("/payments/por-alumno/", {
        params: { student: studentId, anio: year },
      });
      setStudentDetail(res.data);
    } catch (err) {
      const detail = err.response?.data?.error || "Error al cargar pensiones del alumno";
      message.error(detail);
      setStudentDetail(null);
    } finally {
      setLoadingDetail(false);
    }
  }, [message]);

  const selectStudent = (student) => {
    setSelectedStudent(student);
    fetchStudentDetail(student.id, anio);
  };

  useEffect(() => {
    if (selectedStudent) {
      fetchStudentDetail(selectedStudent.id, anio);
    }
  }, [anio, selectedStudent, fetchStudentDetail]);

  const openPayModal = (payment) => {
    setPayingPayment(payment);
    payForm.resetFields();
    payForm.setFieldsValue({
      monto: payment.monto,
      fecha_pago: dayjs(),
    });
    setPayModalOpen(true);
  };

  const handlePay = async () => {
    try {
      const values = await payForm.validateFields();
      setSaving(true);
      await api.patch(`/payments/${payingPayment.id}/registrar-pago/`, {
        estado: "PAGADO",
        metodo_pago: values.metodo_pago,
        comprobante: values.comprobante || "",
        observaciones: values.observaciones || "",
      });
      message.success("Pago registrado");
      setPayModalOpen(false);
      fetchStudentDetail(selectedStudent.id, anio);
    } catch (err) {
      const detail = err.response?.data?.detail || "Error al registrar pago";
      message.error(detail);
    } finally {
      setSaving(false);
    }
  };

  // El año escolar en Perú va de marzo a diciembre (10 meses).
  // Enero y febrero son vacaciones y NO se cobran.
  const MES_INICIO = 3;
  const MES_FIN = 12;
  const MESES_COBRABLES = MES_FIN - MES_INICIO + 1;

  const pagosCobrables = useMemo(() => {
    if (!studentDetail) return [];
    return studentDetail.pagos.filter(
      (p) => p.mes >= MES_INICIO && p.mes <= MES_FIN,
    );
  }, [studentDetail]);

  const totalAnual = useMemo(() => {
    if (!studentDetail) return 0;
    return Number(studentDetail.monto_mensual) * MESES_COBRABLES;
  }, [studentDetail]);

  const pagado = useMemo(
    () =>
      pagosCobrables
        .filter((p) => p.estado === "PAGADO")
        .reduce((acc, p) => acc + Number(p.monto), 0),
    [pagosCobrables],
  );
  const pendientesCount = useMemo(
    () => pagosCobrables.filter((p) => p.estado !== "PAGADO" && p.estado !== "EXONERADO").length,
    [pagosCobrables],
  );
  const progreso = totalAnual ? Math.round((pagado / totalAnual) * 100) : 0;

  return (
    <div>
      <Title level={4} style={{ margin: 0, marginBottom: 4 }}>
        <DollarOutlined style={{ marginRight: 8, color: "#0d9488" }} />
        Pensiones
      </Title>
      <Text type="secondary" style={{ fontSize: 13, marginBottom: 20, display: "block" }}>
        Selecciona un alumno para ver su historial de pagos del año.
      </Text>

      {!selectedStudent ? (
        <>
          <Card style={{ marginBottom: 16 }} styles={{ body: { padding: 16 } }}>
            <Space wrap>
              <Input
                placeholder="Buscar por nombre o DNI"
                prefix={<SearchOutlined />}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{ width: 280 }}
                allowClear
              />
              <Select
                placeholder="Filtrar por aula"
                value={classroomFilter}
                onChange={setClassroomFilter}
                allowClear
                style={{ width: 220 }}
                options={classrooms.map((c) => ({
                  value: c.id,
                  label: `${c.nombre} (${c.nivel_edad} años)`,
                }))}
              />
              <Select
                value={anio}
                onChange={setAnio}
                style={{ width: 130 }}
                options={yearOptions}
                prefix="Año:"
              />
            </Space>
          </Card>

          {loadingList ? (
            <div style={{ textAlign: "center", padding: 60 }}><Spin /></div>
          ) : students.length === 0 ? (
            <Empty description="No se encontraron alumnos" />
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 12 }}>
              {students.map((s) => (
                <Card
                  key={s.id}
                  hoverable
                  onClick={() => selectStudent(s)}
                  styles={{ body: { padding: 16 } }}
                >
                  <Space>
                    <Avatar
                      size={48}
                      style={{ background: s.genero === "F" ? "#f472b6" : "#60a5fa", fontSize: 20 }}
                    >
                      {s.nombres?.[0]}
                    </Avatar>
                    <div>
                      <Text strong>{s.nombres} {s.apellidos}</Text>
                      <div>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {s.classroom_nombre || "Sin aula"} · {s.edad} años
                        </Text>
                      </div>
                    </div>
                  </Space>
                </Card>
              ))}
            </div>
          )}
        </>
      ) : (
        <div>
          <Space style={{ marginBottom: 16 }}>
            <Button icon={<ArrowLeftOutlined />} onClick={() => { setSelectedStudent(null); setStudentDetail(null); }}>
              Volver a la lista
            </Button>
            <Select value={anio} onChange={setAnio} style={{ width: 120 }} options={yearOptions} />
          </Space>

          {loadingDetail ? (
            <div style={{ textAlign: "center", padding: 60 }}><Spin /></div>
          ) : !studentDetail ? (
            <Empty description="Sin datos" />
          ) : (
            <>
              <Card
                style={{
                  marginBottom: 16,
                  background: "linear-gradient(135deg, #0d9488 0%, #14b8a6 100%)",
                  border: "none",
                }}
                styles={{ body: { padding: 20 } }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 16 }}>
                  <Space size="middle">
                    <Avatar size={64} icon={<UserOutlined />} style={{ background: "white", color: "#0d9488", fontSize: 28 }} />
                    <div>
                      <Title level={4} style={{ color: "white", margin: 0 }}>
                        {studentDetail.student.nombre}
                      </Title>
                      <Text style={{ color: "white", opacity: 0.9 }}>
                        {studentDetail.student.classroom || "Sin aula"} · DNI {studentDetail.student.dni} · {studentDetail.anio_escolar}
                      </Text>
                    </div>
                  </Space>
                  <Space size="large">
                    <Statistic
                      title={<Text style={{ color: "white", opacity: 0.85 }}>Pensión mensual</Text>}
                      value={Number(studentDetail.monto_mensual)}
                      precision={2}
                      prefix="S/."
                      valueStyle={{ color: "white" }}
                    />
                    <Statistic
                      title={<Text style={{ color: "white", opacity: 0.85 }}>Pagado</Text>}
                      value={pagado}
                      precision={2}
                      prefix="S/."
                      valueStyle={{ color: "white" }}
                    />
                    <Statistic
                      title={<Text style={{ color: "white", opacity: 0.85 }}>Pendientes</Text>}
                      value={pendientesCount}
                      suffix={` / ${MESES_COBRABLES}`}
                      valueStyle={{ color: "white" }}
                    />
                  </Space>
                </div>
                <Progress
                  percent={progreso}
                  showInfo
                  strokeColor="white"
                  trailColor="rgba(255,255,255,0.3)"
                  style={{ marginTop: 12 }}
                />
              </Card>

              <Card
                title="Historial de pensiones (marzo a diciembre)"
                styles={{ body: { padding: 0 } }}
              >
                <Table
                  size="middle"
                  dataSource={pagosCobrables}
                  rowKey="id"
                  pagination={false}
                  locale={{ emptyText: "Sin pensiones registradas para este año" }}
                  columns={[
                    {
                      title: "Mes",
                      dataIndex: "mes",
                      key: "mes",
                      width: 130,
                      render: (mes) => <Text strong>{meses[mes - 1]}</Text>,
                    },
                    {
                      title: "Monto",
                      dataIndex: "monto",
                      key: "monto",
                      width: 120,
                      render: (m) => `S/. ${Number(m).toFixed(2)}`,
                    },
                    {
                      title: "Vencimiento",
                      dataIndex: "fecha_vencimiento",
                      key: "fecha_vencimiento",
                      width: 130,
                      render: (f) => dayjs(f).format("DD/MM/YYYY"),
                    },
                    {
                      title: "Estado",
                      dataIndex: "estado",
                      key: "estado",
                      width: 130,
                      render: (estado, record) => {
                        const isOverdue = record.is_overdue && estado !== "PAGADO";
                        const cfg = isOverdue
                          ? ESTADO_CFG.VENCIDO
                          : (ESTADO_CFG[estado] || ESTADO_CFG.PENDIENTE);
                        return (
                          <Tag color={cfg.color} icon={cfg.icon}>
                            {cfg.label}
                          </Tag>
                        );
                      },
                    },
                    {
                      title: "Fecha pago",
                      dataIndex: "fecha_pago",
                      key: "fecha_pago",
                      width: 140,
                      render: (f, record) =>
                        f ? (
                          <Text type="success" style={{ fontSize: 12 }}>
                            {dayjs(f).format("DD/MM/YYYY")}
                            {record.metodo_pago ? ` · ${record.metodo_pago}` : ""}
                          </Text>
                        ) : (
                          <Text type="secondary">—</Text>
                        ),
                    },
                    {
                      title: "Acciones",
                      key: "acciones",
                      width: 160,
                      render: (_, p) => (
                        p.estado !== "PAGADO" && p.estado !== "EXONERADO" ? (
                          <Button
                            type="primary"
                            size="small"
                            icon={<DollarOutlined />}
                            onClick={() => openPayModal(p)}
                          >
                            Registrar pago
                          </Button>
                        ) : null
                      ),
                    },
                  ]}
                />
              </Card>
            </>
          )}
        </div>
      )}

      <Modal
        title={
          payingPayment
            ? `Registrar pago — ${meses[payingPayment.mes - 1]} ${payingPayment.anio}`
            : "Registrar pago"
        }
        open={payModalOpen}
        onOk={handlePay}
        onCancel={() => { payForm.resetFields(); setPayModalOpen(false); }}
        confirmLoading={saving}
        okText="Confirmar pago"
        cancelText="Cancelar"
      >
        {payingPayment && (
          <Descriptions
            size="small"
            column={2}
            bordered
            style={{ marginBottom: 16 }}
            items={[
              {
                key: "monto",
                label: "Monto",
                children: (
                  <Text strong style={{ color: "#0d9488", fontSize: 16 }}>
                    S/. {Number(payingPayment.monto).toFixed(2)}
                  </Text>
                ),
              },
              {
                key: "venc",
                label: "Vencimiento",
                children: dayjs(payingPayment.fecha_vencimiento).format("DD/MM/YYYY"),
              },
            ]}
          />
        )}
        <Text type="secondary" style={{ fontSize: 12, display: "block", marginBottom: 12 }}>
          El monto se configura desde la matrícula del alumno y no es editable aquí.
        </Text>
        <Form form={payForm} layout="vertical">
          <Form.Item name="fecha_pago" label="Fecha de pago" rules={[{ required: true, message: "Seleccione la fecha" }]}>
            <DatePicker format="DD/MM/YYYY" style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item
            name="metodo_pago"
            label="Método de pago"
            rules={[{ required: true, message: "Seleccione el método" }]}
          >
            <Select
              placeholder="Seleccionar"
              options={[
                { value: "EFECTIVO",      label: "Efectivo"      },
                { value: "TRANSFERENCIA", label: "Transferencia" },
                { value: "YAPE",          label: "Yape"          },
                { value: "PLIN",          label: "Plin"          },
              ]}
            />
          </Form.Item>
          <Form.Item name="comprobante" label="N° de comprobante (opcional)">
            <Input />
          </Form.Item>
          <Form.Item name="observaciones" label="Observaciones">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
