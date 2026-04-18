import { useState, useEffect, useCallback } from "react";
import {
  Table,
  Button,
  Select,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  InputNumber,
  DatePicker,
  App,
  Typography,
} from "antd";
import { DollarOutlined, QrcodeOutlined } from "@ant-design/icons";
import api from "../services/api";

const { Title } = Typography;

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
const yearOptions = Array.from({ length: 5 }, (_, i) => ({
  value: currentYear - 2 + i,
  label: `${currentYear - 2 + i}`,
}));

const estadoColorMap = {
  PAGADO: "green",
  VENCIDO: "red",
  PENDIENTE: "orange",
};

export default function Payments() {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [mesFilter, setMesFilter] = useState(undefined);
  const [anioFilter, setAnioFilter] = useState(currentYear);
  const [estadoFilter, setEstadoFilter] = useState(undefined);
  const [payModalOpen, setPayModalOpen] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [saving, setSaving] = useState(false);
  const [payForm] = Form.useForm();
  const { message, modal } = App.useApp();

  const fetchPayments = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (mesFilter) params.mes = mesFilter;
      if (anioFilter) params.anio = anioFilter;
      if (estadoFilter) params.estado = estadoFilter;
      const res = await api.get("/payments/", { params });
      setPayments(res.data.results || res.data);
    } catch {
      message.error("Error al cargar pensiones");
    } finally {
      setLoading(false);
    }
  }, [mesFilter, anioFilter, estadoFilter, message]);

  useEffect(() => {
    fetchPayments();
  }, [fetchPayments]);

  const openPayModal = (record) => {
    setSelectedPayment(record);
    payForm.resetFields();
    payForm.setFieldsValue({ monto: record.monto });
    setPayModalOpen(true);
  };

  const handlePay = async () => {
    try {
      const values = await payForm.validateFields();
      setSaving(true);
      if (values.fecha_pago) {
        values.fecha_pago = values.fecha_pago.format("YYYY-MM-DD");
      }
      await api.patch(`/payments/${selectedPayment.id}/registrar-pago/`, {
        estado: "PAGADO",
        ...values,
      });
      message.success("Pago registrado");
      setPayModalOpen(false);
      fetchPayments();
    } catch (err) {
      const detail = err.response?.data?.detail || "Error al registrar pago";
      message.error(detail);
    } finally {
      setSaving(false);
    }
  };

  const handleGenerateQR = async (record) => {
    try {
      const res = await api.get(`/payments/${record.id}/generar-qr/`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      modal.info({
        title: "QR de Pago",
        content: (
          <div style={{ textAlign: "center" }}>
            <img src={url} alt="QR Code" style={{ maxWidth: 300 }} />
          </div>
        ),
        width: 400,
      });
    } catch {
      message.error("Error al generar QR");
    }
  };

  const columns = [
    { title: "Alumno", dataIndex: "alumno_nombre", key: "alumno_nombre" },
    {
      title: "Mes",
      dataIndex: "mes",
      key: "mes",
      render: (mes) => meses.find((m) => m.value === mes)?.label || mes,
    },
    { title: "Ano", dataIndex: "anio", key: "anio", width: 80 },
    {
      title: "Monto",
      dataIndex: "monto",
      key: "monto",
      render: (val) => `S/. ${Number(val).toFixed(2)}`,
    },
    {
      title: "Estado",
      dataIndex: "estado",
      key: "estado",
      render: (estado) => (
        <Tag color={estadoColorMap[estado] || "default"}>{estado}</Tag>
      ),
    },
    {
      title: "Fecha Vencimiento",
      dataIndex: "fecha_vencimiento",
      key: "fecha_vencimiento",
    },
    { title: "Fecha Pago", dataIndex: "fecha_pago", key: "fecha_pago" },
    {
      title: "Acciones",
      key: "acciones",
      render: (_, record) => (
        <Space>
          {record.estado !== "PAGADO" && (
            <Button
              type="primary"
              size="small"
              icon={<DollarOutlined />}
              onClick={() => openPayModal(record)}
            >
              Registrar Pago
            </Button>
          )}
          <Button
            size="small"
            icon={<QrcodeOutlined />}
            onClick={() => handleGenerateQR(record)}
          >
            QR
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>
        Pensiones
      </Title>

      <Space style={{ marginBottom: 16 }}>
        <Select
          placeholder="Mes"
          value={mesFilter}
          onChange={setMesFilter}
          allowClear
          style={{ width: 150 }}
          options={meses}
        />
        <Select
          placeholder="Ano"
          value={anioFilter}
          onChange={setAnioFilter}
          allowClear
          style={{ width: 120 }}
          options={yearOptions}
        />
        <Select
          placeholder="Estado"
          value={estadoFilter}
          onChange={setEstadoFilter}
          allowClear
          style={{ width: 150 }}
          options={[
            { value: "PENDIENTE", label: "Pendiente" },
            { value: "PAGADO", label: "Pagado" },
            { value: "VENCIDO", label: "Vencido" },
          ]}
        />
      </Space>

      <Table
        columns={columns}
        dataSource={payments}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20, showSizeChanger: true }}
        scroll={{ x: 900 }}
      />

      <Modal
        title="Registrar Pago"
        open={payModalOpen}
        onOk={handlePay}
        onCancel={() => setPayModalOpen(false)}
        confirmLoading={saving}
        destroyOnClose
      >
        <Form form={payForm} layout="vertical">
          <Form.Item
            name="monto"
            label="Monto (S/.)"
            rules={[{ required: true, message: "Ingrese el monto" }]}
          >
            <InputNumber min={0} precision={2} style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item name="fecha_pago" label="Fecha de Pago">
            <DatePicker format="DD/MM/YYYY" style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item name="metodo_pago" label="Metodo de Pago">
            <Select
              options={[
                { value: "EFECTIVO", label: "Efectivo" },
                { value: "TRANSFERENCIA", label: "Transferencia" },
                { value: "YAPE", label: "Yape" },
                { value: "PLIN", label: "Plin" },
              ]}
            />
          </Form.Item>
          <Form.Item name="observaciones" label="Observaciones">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
