import { useState, useEffect, useCallback, useMemo } from "react";
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
  Space,
  Tag,
  App,
  Typography,
} from "antd";
import {
  PlusOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  WalletOutlined,
  FilterOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";
import api from "../services/api";

const { Title, Text } = Typography;

const meses = [
  { value: 1,  label: "Enero" },
  { value: 2,  label: "Febrero" },
  { value: 3,  label: "Marzo" },
  { value: 4,  label: "Abril" },
  { value: 5,  label: "Mayo" },
  { value: 6,  label: "Junio" },
  { value: 7,  label: "Julio" },
  { value: 8,  label: "Agosto" },
  { value: 9,  label: "Septiembre" },
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

export default function Cashflow() {
  const [transactions, setTransactions] = useState([]);
  const [closures, setClosures] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [tipoValue, setTipoValue] = useState(undefined);
  const [mesFilter, setMesFilter] = useState(currentMonth);
  const [anioFilter, setAnioFilter] = useState(currentYear);
  const [form] = Form.useForm();
  const { message } = App.useApp();

  const fetchTransactions = useCallback(async () => {
    setLoading(true);
    try {
      const params = { mes: mesFilter, anio: anioFilter };
      const res = await api.get("/cashflow/cash-transactions/", { params });
      const data = res.data.results || res.data;
      setTransactions(data);
    } catch {
      message.error("Error al cargar transacciones");
    } finally {
      setLoading(false);
    }
  }, [mesFilter, anioFilter, message]);

  const fetchClosures = useCallback(async () => {
    try {
      const res = await api.get("/cashflow/monthly-closures/");
      setClosures(res.data.results || res.data);
    } catch {
      message.error("Error al cargar cierres mensuales");
    }
  }, [message]);

  const fetchCategories = useCallback(async () => {
    try {
      const res = await api.get("/cashflow/cash-categories/");
      setCategories(res.data.results || res.data);
    } catch {
      message.error("Error al cargar categorias");
    }
  }, [message]);

  useEffect(() => { fetchTransactions(); }, [fetchTransactions]);
  useEffect(() => { fetchClosures(); fetchCategories(); }, [fetchClosures, fetchCategories]);

  const summary = useMemo(() => {
    const ingresos = transactions
      .filter((t) => t.tipo === "INGRESO")
      .reduce((sum, t) => sum + Number(t.monto), 0);
    const egresos = transactions
      .filter((t) => t.tipo === "EGRESO")
      .reduce((sum, t) => sum + Number(t.monto), 0);
    return { ingresos, egresos, balance: ingresos - egresos };
  }, [transactions]);

  const openCreate = () => {
    form.resetFields();
    form.setFieldsValue({ fecha: dayjs() });
    setTipoValue(undefined);
    setModalOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      if (values.fecha) values.fecha = values.fecha.format("YYYY-MM-DD");
      await api.post("/cashflow/cash-transactions/", values);
      message.success("Transacción registrada");
      form.resetFields();
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
    {
      title: "Fecha",
      dataIndex: "fecha",
      key: "fecha",
      width: 110,
      render: (f) => dayjs(f).format("DD/MM/YYYY"),
    },
    {
      title: "Tipo",
      dataIndex: "tipo",
      key: "tipo",
      width: 100,
      render: (tipo) => (
        <Tag color={tipo === "INGRESO" ? "green" : "red"}>
          {tipo === "INGRESO" ? "Ingreso" : "Egreso"}
        </Tag>
      ),
    },
    {
      title: "Categoría",
      dataIndex: "categoria_nombre",
      key: "categoria_nombre",
      render: (n, record) => n || record.categoria,
    },
    { title: "Descripción", dataIndex: "descripcion", key: "descripcion" },
    {
      title: "Monto",
      dataIndex: "monto",
      key: "monto",
      width: 130,
      align: "right",
      render: (val, record) => (
        <Text strong style={{ color: record.tipo === "INGRESO" ? "#10b981" : "#ef4444" }}>
          {record.tipo === "INGRESO" ? "+" : "-"} S/. {Number(val).toFixed(2)}
        </Text>
      ),
    },
    { title: "Registrado por", dataIndex: "creado_por_nombre", key: "creado_por_nombre" },
  ];

  const closureColumns = [
    { title: "Mes", dataIndex: "mes", key: "mes", width: 80 },
    { title: "Año", dataIndex: "anio", key: "anio", width: 80 },
    {
      title: "Total ingresos",
      dataIndex: "total_ingresos",
      key: "total_ingresos",
      render: (val) => `S/. ${Number(val).toFixed(2)}`,
    },
    {
      title: "Total egresos",
      dataIndex: "total_egresos",
      key: "total_egresos",
      render: (val) => `S/. ${Number(val).toFixed(2)}`,
    },
    {
      title: "Balance",
      dataIndex: "balance",
      key: "balance",
      render: (val) => (
        <Text strong style={{ color: Number(val) >= 0 ? "#10b981" : "#ef4444" }}>
          S/. {Number(val).toFixed(2)}
        </Text>
      ),
    },
    { title: "Fecha cierre", dataIndex: "fecha_cierre", key: "fecha_cierre", render: (f) => f ? dayjs(f).format("DD/MM/YYYY") : "—" },
  ];

  const periodoLabel = `${meses.find((m) => m.value === mesFilter)?.label} de ${anioFilter}`;

  const tabItems = [
    {
      key: "transactions",
      label: "Transacciones",
      children: (
        <>
          <Card style={{ marginBottom: 16 }} styles={{ body: { padding: 12 } }}>
            <Space wrap>
              <FilterOutlined style={{ color: "#0d9488" }} />
              <Text>Mostrando:</Text>
              <Select
                value={mesFilter}
                onChange={setMesFilter}
                style={{ width: 140 }}
                options={meses}
              />
              <Select
                value={anioFilter}
                onChange={setAnioFilter}
                style={{ width: 110 }}
                options={yearOptions}
              />
              <Tag color="cyan">{transactions.length} movimientos</Tag>
            </Space>
          </Card>
          <Table
            columns={transactionColumns}
            dataSource={transactions}
            rowKey="id"
            loading={loading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              pageSizeOptions: [10, 20, 50, 100],
              showTotal: (total) => `${total} movimientos`,
            }}
            locale={{ emptyText: `No hay movimientos en ${periodoLabel}` }}
          />
        </>
      ),
    },
    {
      key: "closures",
      label: "Cierres mensuales",
      children: (
        <Table
          columns={closureColumns}
          dataSource={closures}
          rowKey="id"
          pagination={{ pageSize: 12, hideOnSinglePage: true }}
          locale={{ emptyText: "Sin cierres registrados" }}
        />
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <Title level={4} style={{ margin: 0 }}>
            <WalletOutlined style={{ marginRight: 8, color: "#0d9488" }} />
            Caja
          </Title>
          <Text type="secondary" style={{ fontSize: 13 }}>
            Movimientos de {periodoLabel}
          </Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          Nueva transacción
        </Button>
      </div>

      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={8}>
          <Card styles={{ body: { padding: 16 } }}>
            <Statistic
              title={`Ingresos · ${periodoLabel}`}
              value={summary.ingresos}
              precision={2}
              prefix={<ArrowUpOutlined />}
              suffix="S/."
              valueStyle={{ color: "#10b981", fontSize: 22 }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card styles={{ body: { padding: 16 } }}>
            <Statistic
              title={`Egresos · ${periodoLabel}`}
              value={summary.egresos}
              precision={2}
              prefix={<ArrowDownOutlined />}
              suffix="S/."
              valueStyle={{ color: "#ef4444", fontSize: 22 }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card styles={{ body: { padding: 16 } }}>
            <Statistic
              title="Balance del mes"
              value={summary.balance}
              precision={2}
              prefix={<WalletOutlined />}
              suffix="S/."
              valueStyle={{ color: summary.balance >= 0 ? "#10b981" : "#ef4444", fontSize: 22 }}
            />
          </Card>
        </Col>
      </Row>

      <Tabs items={tabItems} />

      <Modal
        title="Nueva transacción"
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => { form.resetFields(); setModalOpen(false); }}
        confirmLoading={saving}
        okText="Registrar"
        cancelText="Cancelar"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="tipo"
            label="Tipo"
            rules={[{ required: true, message: "Seleccione el tipo" }]}
          >
            <Select
              onChange={(val) => {
                setTipoValue(val);
                form.setFieldValue("categoria", undefined);
              }}
              options={[
                { value: "INGRESO", label: "Ingreso" },
                { value: "EGRESO",  label: "Egreso"  },
              ]}
            />
          </Form.Item>
          <Form.Item
            name="categoria"
            label="Categoría"
            rules={[{ required: true, message: "Seleccione la categoría" }]}
          >
            <Select
              placeholder="Seleccione categoría"
              options={categories
                // Las categorías sin tipo (ej. "Otros") son bidireccionales:
                // aparecen tanto al elegir INGRESO como EGRESO.
                .filter((c) => !tipoValue || !c.tipo || c.tipo === tipoValue)
                .map((c) => ({ value: c.id, label: c.nombre }))}
            />
          </Form.Item>
          <Form.Item
            name="descripcion"
            label="Descripción"
            rules={[{ required: true, message: "Ingrese la descripción" }]}
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
