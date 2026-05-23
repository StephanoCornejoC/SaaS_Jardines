import { useState, useEffect, useCallback } from "react";
import {
  Table,
  Button,
  Input,
  Space,
  Modal,
  Form,
  Select,
  DatePicker,
  Popconfirm,
  Tag,
  App,
  Typography,
  InputNumber,
  Divider,
} from "antd";
import { PlusOutlined, SearchOutlined, UserOutlined, DollarOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import api from "../services/api";

const { Title, Text } = Typography;

const TIPO_OPCIONES = [
  { value: "TITULAR",  label: "Titular"  },
  { value: "AUXILIAR", label: "Auxiliar" },
];

const TIPO_TAG = {
  TITULAR:  { color: "cyan",    label: "Titular"  },
  AUXILIAR: { color: "geekblue", label: "Auxiliar" },
};

const TIPO_CONTRATO_OPCIONES = [
  { value: "TIEMPO_COMPLETO", label: "Tiempo completo" },
  { value: "MEDIO_TIEMPO",    label: "Medio tiempo"    },
  { value: "POR_HORAS",       label: "Por horas"       },
];

export default function Teachers() {
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editingTeacher, setEditingTeacher] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();
  const { message } = App.useApp();

  const fetchTeachers = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (search) params.search = search;
      const res = await api.get("/teachers/", { params });
      setTeachers(res.data.results || res.data);
    } catch {
      message.error("No se pudieron cargar los profesores");
    } finally {
      setLoading(false);
    }
  }, [search, message]);

  useEffect(() => {
    fetchTeachers();
  }, [fetchTeachers]);

  const openCreate = () => {
    setEditingTeacher(null);
    form.resetFields();
    form.setFieldsValue({ fecha_ingreso: dayjs(), tipo: "TITULAR" });
    setModalOpen(true);
  };

  const openEdit = (record) => {
    setEditingTeacher(record);
    form.setFieldsValue({
      dni: record.dni,
      nombres: record.nombres,
      apellidos: record.apellidos,
      tipo: record.tipo || "TITULAR",
      especialidad: record.especialidad,
      telefono: record.telefono,
      email: record.email,
      fecha_ingreso: record.fecha_ingreso ? dayjs(record.fecha_ingreso) : null,
      // Datos del contrato activo (pre-llenados desde el listado). Si no
      // hay contrato, el backend lo crea al guardar con `actualizar-sueldo`.
      sueldo: record.sueldo_actual ? Number(record.sueldo_actual) : null,
      tipo_contrato: record.tipo_contrato || "TIEMPO_COMPLETO",
    });
    setModalOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      if (values.fecha_ingreso) {
        values.fecha_ingreso = values.fecha_ingreso.format("YYYY-MM-DD");
      }

      // Separamos los campos del profesor de los del contrato. El contrato
      // se actualiza por endpoint dedicado para que el cambio de sueldo
      // sea explícito (incluso si la directora solo cambia el sueldo).
      const { sueldo, tipo_contrato, ...teacherFields } = values;

      let teacherId;
      if (editingTeacher) {
        await api.patch(`/teachers/${editingTeacher.id}/`, teacherFields);
        teacherId = editingTeacher.id;
      } else {
        const res = await api.post("/teachers/", teacherFields);
        teacherId = res.data.id;
      }

      // Si la directora ingresó un sueldo, actualizamos/creamos el contrato.
      if (sueldo !== null && sueldo !== undefined && sueldo !== "") {
        await api.patch(`/teachers/${teacherId}/actualizar-sueldo/`, {
          sueldo: String(sueldo),
          tipo_contrato: tipo_contrato || "TIEMPO_COMPLETO",
        });
      }

      message.success(
        editingTeacher
          ? "Datos del profesor actualizados"
          : "Profesor registrado correctamente",
      );
      setModalOpen(false);
      fetchTeachers();
    } catch (err) {
      const data = err.response?.data;
      if (data) {
        const msg = data.error
          || Object.values(data).flat().join(", ");
        message.error(msg);
      } else {
        message.error("Error al guardar el profesor");
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/teachers/${id}/`);
      message.success("Profesor eliminado");
      fetchTeachers();
    } catch {
      message.error("No se pudo eliminar el profesor");
    }
  };

  const columns = [
    { title: "DNI", dataIndex: "dni", key: "dni", width: 90 },
    {
      title: "Nombre completo",
      key: "nombre",
      render: (_, record) => (
        <Text strong>{record.nombres} {record.apellidos}</Text>
      ),
    },
    {
      title: "Tipo",
      dataIndex: "tipo",
      key: "tipo",
      width: 100,
      render: (tipo) => {
        const cfg = TIPO_TAG[tipo] || TIPO_TAG.TITULAR;
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      },
    },
    { title: "Especialidad", dataIndex: "especialidad", key: "especialidad" },
    {
      title: "Sueldo",
      key: "sueldo_actual",
      width: 130,
      render: (_, record) =>
        record.sueldo_actual ? (
          <Text strong style={{ color: "#0d9488" }}>
            S/. {Number(record.sueldo_actual).toFixed(2)}
          </Text>
        ) : (
          <Text type="secondary" style={{ fontSize: 12 }}>
            sin contrato
          </Text>
        ),
    },
    { title: "Teléfono", dataIndex: "telefono", key: "telefono", width: 120 },
    { title: "Correo", dataIndex: "email", key: "email", ellipsis: true },
    {
      title: "Acciones",
      key: "acciones",
      width: 140,
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => openEdit(record)}>
            Editar
          </Button>
          <Popconfirm
            title="¿Eliminar este profesor?"
            description="Esta acción no se puede deshacer."
            onConfirm={() => handleDelete(record.id)}
            okText="Sí, eliminar"
            cancelText="Cancelar"
            okButtonProps={{ danger: true }}
          >
            <Button size="small" danger>
              Eliminar
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <Title level={4} style={{ margin: 0 }}>
            <UserOutlined style={{ marginRight: 8, color: "#1677ff" }} />
            Profesores
          </Title>
          <Text type="secondary" style={{ fontSize: 13 }}>
            Personal docente del jardín
          </Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          Nuevo Profesor
        </Button>
      </div>

      <Space style={{ marginBottom: 16 }}>
        <Input
          placeholder="Buscar por nombre o DNI"
          prefix={<SearchOutlined />}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onPressEnter={fetchTeachers}
          style={{ width: 260 }}
          allowClear
        />
      </Space>

      <Table
        columns={columns}
        dataSource={teachers}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20, hideOnSinglePage: true }}
        locale={{ emptyText: "No hay profesores registrados" }}
        scroll={{ x: true }}
      />

      <Modal
        title={editingTeacher ? "Editar profesor" : "Registrar nuevo profesor"}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => { form.resetFields(); setModalOpen(false); }}
        confirmLoading={saving}
        okText={editingTeacher ? "Guardar cambios" : "Registrar profesor"}
        cancelText="Cancelar"
        width={520}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="dni"
            label="DNI"
            rules={[
              { required: true, message: "Ingrese el DNI" },
              { len: 8, message: "El DNI debe tener 8 dígitos" },
            ]}
          >
            <Input maxLength={8} placeholder="12345678" />
          </Form.Item>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 16px" }}>
            <Form.Item
              name="nombres"
              label="Nombres"
              rules={[{ required: true, message: "Ingrese los nombres" }]}
            >
              <Input placeholder="Ana María" />
            </Form.Item>
            <Form.Item
              name="apellidos"
              label="Apellidos"
              rules={[{ required: true, message: "Ingrese los apellidos" }]}
            >
              <Input placeholder="Quispe Flores" />
            </Form.Item>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 16px" }}>
            <Form.Item
              name="tipo"
              label="Tipo de profesor"
              rules={[{ required: true, message: "Seleccione el tipo" }]}
              tooltip="Titular: a cargo del aula. Auxiliar: apoya al titular."
            >
              <Select options={TIPO_OPCIONES} placeholder="Seleccionar tipo" />
            </Form.Item>
            <Form.Item
              name="especialidad"
              label="Especialidad"
              rules={[{ required: true, message: "Ingrese la especialidad" }]}
            >
              <Input placeholder="Ej: Educación Inicial" />
            </Form.Item>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 16px" }}>
            <Form.Item
              name="telefono"
              label="Teléfono"
              rules={[{ required: true, message: "Ingrese el teléfono" }]}
            >
              <Input placeholder="999 999 999" />
            </Form.Item>
            <Form.Item
              name="email"
              label="Correo electrónico"
              rules={[{ type: "email", message: "Correo no válido" }]}
            >
              <Input placeholder="correo@ejemplo.com" />
            </Form.Item>
          </div>

          <Form.Item
            name="fecha_ingreso"
            label="Fecha de ingreso"
            rules={[{ required: true, message: "Seleccione la fecha" }]}
          >
            <DatePicker format="DD/MM/YYYY" style={{ width: "100%" }} placeholder="dd/mm/aaaa" />
          </Form.Item>

          <Divider style={{ margin: "8px 0 16px" }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              <DollarOutlined style={{ marginRight: 4 }} />
              Contrato y sueldo
            </Text>
          </Divider>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 16px" }}>
            <Form.Item
              name="sueldo"
              label="Sueldo mensual"
              tooltip="El sueldo se aplica al contrato activo del profesor. Si no existe, se crea uno nuevo."
            >
              <InputNumber
                style={{ width: "100%" }}
                min={0}
                step={50}
                prefix="S/."
                precision={2}
                placeholder="Ej. 1500.00"
              />
            </Form.Item>
            <Form.Item
              name="tipo_contrato"
              label="Tipo de contrato"
            >
              <Select options={TIPO_CONTRATO_OPCIONES} placeholder="Seleccionar" />
            </Form.Item>
          </div>
          <Text type="secondary" style={{ fontSize: 11, display: "block", marginTop: -8, marginBottom: 8 }}>
            El sueldo se usa en el módulo "Sueldos" para pre-llenar cada pago mensual.
            Podés modificarlo cuando lo necesites.
          </Text>
        </Form>
      </Modal>
    </div>
  );
}
