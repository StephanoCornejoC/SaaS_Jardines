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
  InputNumber,
} from "antd";
import {
  SearchOutlined,
  DollarOutlined,
  ArrowLeftOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  UserOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";
import api from "../services/api";

const { Title, Text } = Typography;

const MESES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

const TIPO_TAG = {
  TITULAR:  { color: "cyan",     label: "Titular"  },
  AUXILIAR: { color: "geekblue", label: "Auxiliar" },
};

const METODOS_PAGO = [
  { value: "TRANSFERENCIA", label: "Transferencia" },
  { value: "EFECTIVO",      label: "Efectivo"      },
  { value: "DEPOSITO",      label: "Depósito"      },
];

const currentYear = new Date().getFullYear();
const yearOptions = Array.from({ length: 5 }, (_, i) => ({
  value: currentYear - 2 + i,
  label: `${currentYear - 2 + i}`,
}));

export default function Sueldos() {
  const [teachers, setTeachers] = useState([]);
  const [loadingList, setLoadingList] = useState(false);
  const [search, setSearch] = useState("");
  const [anio, setAnio] = useState(currentYear);
  const [selectedTeacher, setSelectedTeacher] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [payModalOpen, setPayModalOpen] = useState(false);
  const [payingMes, setPayingMes] = useState(null);
  const [saving, setSaving] = useState(false);
  const [payForm] = Form.useForm();
  const { message } = App.useApp();

  const fetchTeachers = useCallback(async () => {
    setLoadingList(true);
    try {
      const params = {};
      if (search) params.search = search;
      const res = await api.get("/teachers/", { params });
      setTeachers(res.data.results || res.data);
    } catch {
      message.error("No se pudieron cargar los profesores");
    } finally {
      setLoadingList(false);
    }
  }, [search, message]);

  useEffect(() => { fetchTeachers(); }, [fetchTeachers]);

  const fetchDetail = useCallback(async (teacherId, year) => {
    setLoadingDetail(true);
    try {
      const res = await api.get(`/teachers/${teacherId}/sueldos/`, {
        params: { anio: year },
      });
      setDetail(res.data);
    } catch (err) {
      const e = err.response?.data?.error
        || "Error al cargar sueldos del profesor";
      message.error(e);
      setDetail(null);
    } finally {
      setLoadingDetail(false);
    }
  }, [message]);

  const selectTeacher = (teacher) => {
    setSelectedTeacher(teacher);
    fetchDetail(teacher.id, anio);
  };

  useEffect(() => {
    if (selectedTeacher) fetchDetail(selectedTeacher.id, anio);
  }, [anio, selectedTeacher, fetchDetail]);

  // Espejo del frontend de mensualidades de alumnos:
  // construimos los 12 slots del año y matcheamos con los pagos reales
  // que el backend devuelve. NO pre-creamos registros vacíos en BD
  // (TeacherPayment solo existe cuando el pago se hizo).
  const mesesView = useMemo(() => {
    if (!detail) return [];
    const pagosByMes = {};
    detail.pagos.forEach((p) => { pagosByMes[p.mes] = p; });
    return Array.from({ length: 12 }, (_, i) => {
      const mes = i + 1;
      const pago = pagosByMes[mes];
      return {
        mes,
        nombre: MESES[i],
        pagado: !!pago,
        pago,
      };
    });
  }, [detail]);

  const openPayModal = (mesItem) => {
    setPayingMes(mesItem);
    payForm.resetFields();
    payForm.setFieldsValue({
      monto: Number(detail.sueldo_mensual),
      fecha_pago: dayjs(),
      metodo_pago: "TRANSFERENCIA",
    });
    setPayModalOpen(true);
  };

  const handlePay = async () => {
    try {
      const values = await payForm.validateFields();
      setSaving(true);
      await api.post(
        `/teachers/${selectedTeacher.id}/registrar-sueldo/`,
        {
          contract: detail.contract.id,
          mes: payingMes.mes,
          anio,
          monto: String(values.monto),
          fecha_pago: values.fecha_pago.format("YYYY-MM-DD"),
          metodo_pago: values.metodo_pago,
          comprobante: values.comprobante || "",
          observaciones: values.observaciones || "",
        },
      );
      message.success("Sueldo registrado · caja actualizada");
      setPayModalOpen(false);
      fetchDetail(selectedTeacher.id, anio);
    } catch (err) {
      const e = err.response?.data?.error || "Error al registrar el pago";
      message.error(e);
    } finally {
      setSaving(false);
    }
  };

  const totalAnual = useMemo(() => {
    if (!detail) return 0;
    return Number(detail.sueldo_mensual) * 12;
  }, [detail]);
  const totalPagado = useMemo(
    () => (detail ? Number(detail.total_pagado) : 0),
    [detail],
  );
  const progreso = totalAnual ? Math.round((totalPagado / totalAnual) * 100) : 0;

  return (
    <div>
      <Title level={4} style={{ margin: 0, marginBottom: 4 }}>
        <DollarOutlined style={{ marginRight: 8, color: "#0d9488" }} />
        Sueldos del personal
      </Title>
      <Text type="secondary" style={{ fontSize: 13, marginBottom: 20, display: "block" }}>
        Seleccioná un profesor para ver y registrar los pagos de sueldo del año.
        Cada pago se registra automáticamente en el flujo de caja como egreso.
      </Text>

      {!selectedTeacher ? (
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
                value={anio}
                onChange={setAnio}
                style={{ width: 130 }}
                options={yearOptions}
              />
            </Space>
          </Card>

          {loadingList ? (
            <div style={{ textAlign: "center", padding: 60 }}><Spin /></div>
          ) : teachers.length === 0 ? (
            <Empty description="No hay profesores registrados" />
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 12 }}>
              {teachers.map((t) => {
                const tipo = TIPO_TAG[t.tipo] || TIPO_TAG.TITULAR;
                const avatarBg = t.tipo === "AUXILIAR" ? "#6366f1" : "#0d9488";
                return (
                  <Card
                    key={t.id}
                    hoverable
                    onClick={() => selectTeacher(t)}
                    styles={{ body: { padding: 16 } }}
                  >
                    <Space>
                      <Avatar
                        size={48}
                        style={{ background: avatarBg, fontSize: 20 }}
                      >
                        {t.nombres?.[0]}
                      </Avatar>
                      <div>
                        <Text strong>
                          {t.nombre_completo || `${t.apellidos}, ${t.nombres}`}
                        </Text>
                        <div style={{ marginTop: 2 }}>
                          <Tag color={tipo.color}>{tipo.label}</Tag>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            DNI {t.dni}
                          </Text>
                        </div>
                      </div>
                    </Space>
                  </Card>
                );
              })}
            </div>
          )}
        </>
      ) : (
        <div>
          <Space style={{ marginBottom: 16 }}>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => { setSelectedTeacher(null); setDetail(null); }}
            >
              Volver a la lista
            </Button>
            <Select
              value={anio}
              onChange={setAnio}
              style={{ width: 120 }}
              options={yearOptions}
            />
          </Space>

          {loadingDetail ? (
            <div style={{ textAlign: "center", padding: 60 }}><Spin /></div>
          ) : !detail ? (
            <Empty description="Sin datos de sueldos" />
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
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    flexWrap: "wrap",
                    gap: 16,
                  }}
                >
                  <Space size="middle">
                    <Avatar
                      size={64}
                      icon={<UserOutlined />}
                      style={{ background: "white", color: "#0d9488", fontSize: 28 }}
                    />
                    <div>
                      <Title level={4} style={{ color: "white", margin: 0 }}>
                        {detail.teacher.nombre}
                      </Title>
                      <Text style={{ color: "white", opacity: 0.9 }}>
                        DNI {detail.teacher.dni} · {detail.contract.tipo_display}
                        {" · "}
                        {detail.anio}
                      </Text>
                    </div>
                  </Space>
                  <Space size="large">
                    <Statistic
                      title={<Text style={{ color: "white", opacity: 0.85 }}>Sueldo mensual</Text>}
                      value={Number(detail.sueldo_mensual)}
                      precision={2}
                      prefix="S/."
                      valueStyle={{ color: "white" }}
                    />
                    <Statistic
                      title={<Text style={{ color: "white", opacity: 0.85 }}>Total pagado</Text>}
                      value={totalPagado}
                      precision={2}
                      prefix="S/."
                      valueStyle={{ color: "white" }}
                    />
                    <Statistic
                      title={<Text style={{ color: "white", opacity: 0.85 }}>Pendientes</Text>}
                      value={detail.meses_pendientes}
                      suffix="/ 12"
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
                title="Pagos del año (enero a diciembre)"
                styles={{ body: { padding: 0 } }}
              >
                <Table
                  size="middle"
                  dataSource={mesesView}
                  rowKey="mes"
                  pagination={false}
                  locale={{ emptyText: "Sin pagos registrados" }}
                  columns={[
                    {
                      title: "Mes",
                      dataIndex: "nombre",
                      key: "mes",
                      width: 140,
                      render: (n) => <Text strong>{n}</Text>,
                    },
                    {
                      title: "Estado",
                      key: "estado",
                      width: 130,
                      render: (_, item) =>
                        item.pagado ? (
                          <Tag color="green" icon={<CheckCircleOutlined />}>
                            Pagado
                          </Tag>
                        ) : (
                          <Tag color="orange" icon={<ClockCircleOutlined />}>
                            Pendiente
                          </Tag>
                        ),
                    },
                    {
                      title: "Monto",
                      key: "monto",
                      width: 130,
                      render: (_, item) =>
                        item.pagado
                          ? `S/. ${Number(item.pago.monto).toFixed(2)}`
                          : <Text type="secondary">—</Text>,
                    },
                    {
                      title: "Fecha pago",
                      key: "fecha_pago",
                      width: 180,
                      render: (_, item) =>
                        item.pagado ? (
                          <Text type="success" style={{ fontSize: 12 }}>
                            {dayjs(item.pago.fecha_pago).format("DD/MM/YYYY")}
                            {" · "}
                            {item.pago.metodo_pago}
                          </Text>
                        ) : (
                          <Text type="secondary">—</Text>
                        ),
                    },
                    {
                      title: "Comprobante",
                      key: "comprobante",
                      render: (_, item) =>
                        item.pagado
                          ? (item.pago.comprobante || <Text type="secondary">—</Text>)
                          : <Text type="secondary">—</Text>,
                    },
                    {
                      title: "Acciones",
                      key: "acciones",
                      width: 180,
                      render: (_, item) =>
                        item.pagado ? null : (
                          <Button
                            type="primary"
                            size="small"
                            icon={<DollarOutlined />}
                            onClick={() => openPayModal(item)}
                          >
                            Registrar pago
                          </Button>
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
          payingMes
            ? `Registrar sueldo — ${payingMes.nombre} ${anio}`
            : "Registrar sueldo"
        }
        open={payModalOpen}
        onOk={handlePay}
        onCancel={() => { payForm.resetFields(); setPayModalOpen(false); }}
        confirmLoading={saving}
        okText="Confirmar pago"
        cancelText="Cancelar"
      >
        {payingMes && detail && (
          <Descriptions
            size="small"
            column={2}
            bordered
            style={{ marginBottom: 16 }}
            items={[
              {
                key: "p",
                label: "Profesor",
                children: detail.teacher.nombre,
              },
              {
                key: "s",
                label: "Sueldo acordado",
                children: (
                  <Text strong style={{ color: "#0d9488" }}>
                    S/. {Number(detail.sueldo_mensual).toFixed(2)}
                  </Text>
                ),
              },
            ]}
          />
        )}
        <Text
          type="secondary"
          style={{ fontSize: 12, display: "block", marginBottom: 12 }}
        >
          El monto se pre-llena con el sueldo del contrato pero podés editarlo
          si hay bono o ajuste. Al confirmar, el pago queda registrado en el
          flujo de caja como EGRESO.
        </Text>
        <Form form={payForm} layout="vertical">
          <Form.Item
            name="monto"
            label="Monto a pagar"
            rules={[{ required: true, message: "Ingrese el monto" }]}
          >
            <InputNumber
              style={{ width: "100%" }}
              min={0}
              step={50}
              prefix="S/."
              precision={2}
            />
          </Form.Item>
          <Form.Item
            name="fecha_pago"
            label="Fecha de pago"
            rules={[{ required: true, message: "Seleccione la fecha" }]}
          >
            <DatePicker format="DD/MM/YYYY" style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item
            name="metodo_pago"
            label="Método de pago"
            rules={[{ required: true, message: "Seleccione el método" }]}
          >
            <Select placeholder="Seleccionar" options={METODOS_PAGO} />
          </Form.Item>
          <Form.Item name="comprobante" label="N° de comprobante (opcional)">
            <Input />
          </Form.Item>
          <Form.Item name="observaciones" label="Observaciones (opcional)">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
