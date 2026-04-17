import { useState, useEffect, useCallback } from "react";
import {
  Table,
  Button,
  Input,
  Space,
  Modal,
  Form,
  Tag,
  Switch,
  Popconfirm,
  App,
  Typography,
} from "antd";
import { PlusOutlined, SearchOutlined } from "@ant-design/icons";
import api from "../services/api";

const { Title } = Typography;

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
      message.error("Error al cargar profesores");
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
    setModalOpen(true);
  };

  const openEdit = (record) => {
    setEditingTeacher(record);
    form.setFieldsValue(record);
    setModalOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      if (editingTeacher) {
        await api.patch(`/teachers/${editingTeacher.id}/`, values);
        message.success("Profesor actualizado");
      } else {
        await api.post("/teachers/", values);
        message.success("Profesor creado");
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
      message.error("Error al eliminar");
    }
  };

  const columns = [
    { title: "DNI", dataIndex: "dni", key: "dni", width: 100 },
    { title: "Nombres", dataIndex: "nombres", key: "nombres" },
    { title: "Apellidos", dataIndex: "apellidos", key: "apellidos" },
    { title: "Especialidad", dataIndex: "especialidad", key: "especialidad" },
    {
      title: "Activo",
      dataIndex: "activo",
      key: "activo",
      render: (activo) => (
        <Tag color={activo ? "green" : "default"}>{activo ? "Si" : "No"}</Tag>
      ),
    },
    {
      title: "Acciones",
      key: "acciones",
      render: (_, record) => (
        <Space>
          <Button type="link" onClick={() => openEdit(record)}>
            Editar
          </Button>
          <Popconfirm
            title="Eliminar profesor"
            description="Esta seguro? Esta accion no se puede deshacer."
            onConfirm={() => handleDelete(record.id)}
            okText="Si, eliminar"
            cancelText="Cancelar"
            okButtonProps={{ danger: true }}
          >
            <Button type="link" danger>
              Eliminar
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>
          Profesores
        </Title>
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
          style={{ width: 250 }}
          allowClear
        />
      </Space>

      <Table
        columns={columns}
        dataSource={teachers}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20, showSizeChanger: true }}
      />

      <Modal
        title={editingTeacher ? "Editar Profesor" : "Nuevo Profesor"}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        confirmLoading={saving}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="dni"
            label="DNI"
            rules={[{ required: true, message: "Ingrese el DNI" }]}
          >
            <Input maxLength={8} />
          </Form.Item>
          <Form.Item
            name="nombres"
            label="Nombres"
            rules={[{ required: true, message: "Ingrese los nombres" }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="apellidos"
            label="Apellidos"
            rules={[{ required: true, message: "Ingrese los apellidos" }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="especialidad"
            label="Especialidad"
            rules={[{ required: true, message: "Ingrese la especialidad" }]}
          >
            <Input />
          </Form.Item>
          <Form.Item name="telefono" label="Telefono">
            <Input />
          </Form.Item>
          <Form.Item name="email" label="Email" rules={[{ type: "email", message: "Email no valido" }]}>
            <Input type="email" />
          </Form.Item>
          <Form.Item name="activo" label="Activo" valuePropName="checked" initialValue={true}>
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
