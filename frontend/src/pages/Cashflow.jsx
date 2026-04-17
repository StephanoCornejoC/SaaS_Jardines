import { useState, useEffect, useCallback } from "react";
import {
  Tabs,
  Table,
  Button,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  DatePicker,
  Row,
  Col,
  Card,
  Statistic,
  Tag,
  App,
  Typography,
} from "antd";
import {
  PlusOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  WalletOutlined,
} from "@ant-design/icons";
import api from "../services/api";

const { Title } = Typography;

export default function Cashflow() {
  const [transactions, setTransactions] = useState([]);
  const [closures, setClosures] = useState([]);
  const [summary, setSummary] = useState({ ingresos: 0, egresos: 0, balance: 0 });
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();
  const { message } = App.useApp();

  const fetchTransactions = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get("/cashflow/cash-transactions/");
      const data = res.data.results || res.data;
      setTransactions(data);

      const ingresos = data
        .filter((t) => t.tipo === "INGRESO")
        .reduce((sum, t) => sum + Number(t.monto), 0);
      const egresos = data
        .filter((t) => t.tipo === "EGRESO")
        .reduce((sum, t) => sum + Number(t.monto), 0);
      setSummary({ ingresos, egresos, balance: ingresos - egresos });
    } catch {
      message.error("Error al cargar transacciones");
    } finally {
      setLoading(false);
    }
  }, [message]);

  const fetchClosures = useCallback(async () => {
    try {
      const res = await api.get("/cashflow/monthly-closures/");
      setClosures(res.data.results || res.data);
    } catch {
      message.error("Error al cargar cierres mensuales");
    }
  }, [message]);

  useEffect(() => {
    fetchTransactions();
    fetchClosures();
  }, [fetchTransactions, fetchClosures]);

  const openCreate = () => {
    form.resetFields();
    setModalOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      if (values.fecha) {
        values.fecha = values.fecha.format("YYYY-MM-DD");
      }
      await api.post("/cashflow/cash-transactions/", values);
      message.success("Transaccion registrada");
      setModalOpen(false);
      fetchTransactions();
    } catch (err) {
      if (err.response?.data) {
        const errors = Object.values(err.response.data).flat().join(", ");
        message.error(errors);
      }
    } finally {
      setSaving(false);
    }
  };

  const transactionColumns = [
    { title: "Fecha", dataIndex: "fecha", key: "fecha", width: 120 },
    { title: "Categoria", dataIndex: "categoria", key: "categoria" },
    { title: "Descripcion", dataIndex: "descripcion", key: "descripcion" },
    {
      title: "Tipo",
      dataIndex: "tipo",
      key: "tipo",
      render: (tipo) => (
        <Tag color={tipo === "INGRESO" ? "green" : "red"}>{tipo}</Tag>
      ),
    },
    {
      title: "Monto",
      dataIndex: "monto",
      key: "monto",
      render: (val, record) => (
        <span style={{ color: record.tipo === "INGRESO" ? "#52c41a" : "#ff4d4f" }}>
          S/. {Number(val).toFixed(2)}
        </span>
      ),
    },
    { title: "Registrado por", dataIndex: "registrado_por_nombre", key: "registrado_por_nombre" },
  ];

  const closureColumns = [
    { title: "Mes", dataIndex: "mes", key: "mes" },
    { title: "Ano", dataIndex: "anio", key: "anio" },
    {
      title: "Total Ingresos",
      dataIndex: "total_ingresos",
      key: "total_ingresos",
      render: (val) => `S/. ${Number(val).toFixed(2)}`,
    },
    {
      title: "Total Egresos",
      dataIndex: "total_egresos",
      key: "total_egresos",
      render: (val) => `S/. ${Number(val).toFixed(2)}`,
    },
    {
      title: "Balance",
      dataIndex: "balance",
      key: "balance",
      render: (val) => (
        <span style={{ color: Number(val) >= 0 ? "#52c41a" : "#ff4d4f", fontWeight: "bold" }}>
          S/. {Number(val).toFixed(2)}
        </span>
      ),
    },
    {
      title: "Estado",
      dataIndex: "estado",
      key: "estado",
      render: (estado) => (
        <Tag color={estado === "CERRADO" ? "blue" : "orange"}>{estado}</Tag>
      ),
    },
    { title: "Fecha Cierre", dataIndex: "fecha_cierre", key: "fecha_cierre" },
  ];

  const tabItems = [
    {
      key: "transactions",
      label: "Transacciones",
      children: (
        <Table
          columns={transactionColumns}
          dataSource={transactions}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20, showSizeChanger: true }}
        />
      ),
    },
    {
      key: "closures",
      label: "Cierres Mensuales",
      children: (
        <Table
          columns={closureColumns}
          dataSource={closures}
          rowKey="id"
          pagination={{ pageSize: 12 }}
        />
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>
          Caja
        </Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          Nueva Transaccion
        </Button>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Ingresos del Mes"
              value={summary.ingresos}
              precision={2}
              prefix={<ArrowUpOutlined />}
              suffix="S/."
              valueStyle={{ color: "#52c41a" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Egresos del Mes"
              value={summary.egresos}
              precision={2}
              prefix={<ArrowDownOutlined />}
              suffix="S/."
              valueStyle={{ color: "#ff4d4f" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Balance"
              value={summary.balance}
              precision={2}
              prefix={<WalletOutlined />}
              suffix="S/."
              valueStyle={{ color: summary.balance >= 0 ? "#52c41a" : "#ff4d4f" }}
            />
          </Card>
        </Col>
      </Row>

      <Tabs items={tabItems} />

      <Modal
        title="Nueva Transaccion"
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        confirmLoading={saving}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="tipo"
            label="Tipo"
            rules={[{ required: true, message: "Seleccione el tipo" }]}
          >
            <Select
              options={[
                { value: "INGRESO", label: "Ingreso" },
                { value: "EGRESO", label: "Egreso" },
              ]}
            />
          </Form.Item>
          <Form.Item
            name="categoria"
            label="Categoria"
            rules={[{ required: true, message: "Ingrese la categoria" }]}
          >
            <Select
              options={[
                { value: "PENSION", label: "Pension" },
                { value: "MATRICULA", label: "Matricula" },
                { value: "MATERIAL", label: "Material" },
                { value: "PLANILLA", label: "Planilla" },
                { value: "SERVICIOS", label: "Servicios" },
                { value: "OTROS", label: "Otros" },
              ]}
            />
          </Form.Item>
          <Form.Item
            name="descripcion"
            label="Descripcion"
            rules={[{ required: true, message: "Ingrese la descripcion" }]}
          >
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item
            name="monto"
            label="Monto (S/.)"
            rules={[{ required: true, message: "Ingrese el monto" }]}
          >
            <InputNumber min={0.01} precision={2} style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item
            name="fecha"
            label="Fecha"
            rules={[{ required: true, message: "Seleccione la fecha" }]}
          >
            <DatePicker format="DD/MM/YYYY" style={{ width: "100%" }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
