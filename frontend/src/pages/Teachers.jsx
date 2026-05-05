import { useState, useEffect, useCallback } from "react";
import {
  Table,
  Button,
  Input,
  Space,
  Modal,
  Form,
  DatePicker,
  Popconfirm,
  App,
  Typography,
} from "antd";
import { PlusOutlined, SearchOutlined, UserOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import api from "../services/api";

const { Title, Text } = Typography;

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
    form.setFieldsValue({ fecha_ingreso: dayjs() });
    setModalOpen(true);
  };

  const openEdit = (record) => {
    setEditingTeacher(record);
    form.setFieldsValue({
      dni: record.dni,
      nombres: record.nombres,
      apellidos: record.apellidos,
      especialidad: record.especialidad,
      telefono: record.telefono,
      email: record.email,
      fecha_ingreso: record.fecha_ingreso ? dayjs(record.fecha_ingreso) : null,
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
      if (editingTeacher) {
        await api.patch(`/teachers/${editingTeacher.id}/`, values);
        message.success("Datos del profesor actualizados");
      } else {
        await api.post("/teachers/", values);
        message.success("Profesor registrado correctamente");
      }
      setModalOpen(false);
      fetchTeachers();
    } catch (err) {
      if (err.response?.data) {
        const errors = Object.values(err.response.data).flat().join(", ");
        message.error(errors);
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
    { title: "Especialidad", dataIndex: "especialidad", key: "especialidad" },
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

          <Form.Item
            name="especialidad"
            label="Especialidad"
            rules={[{ required: true, message: "Ingrese la especialidad" }]}
          >
            <Input placeholder="Ej: Educación Inicial, Psicomotricidad" />
          </Form.Item>

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
        </Form>
      </Modal>
    </div>
  );
}
