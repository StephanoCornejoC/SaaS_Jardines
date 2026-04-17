import { useState, useEffect, useCallback } from "react";
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  Tag,
  Popconfirm,
  App,
  Typography,
} from "antd";
import { PlusOutlined } from "@ant-design/icons";
import api from "../services/api";

const { Title } = Typography;

export default function Classrooms() {
  const [classrooms, setClassrooms] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingClassroom, setEditingClassroom] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();
  const { message } = App.useApp();

  const fetchClassrooms = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get("/classrooms/");
      setClassrooms(res.data.results || res.data);
    } catch {
      message.error("Error al cargar aulas");
    } finally {
      setLoading(false);
    }
  }, [message]);

  const fetchTeachers = useCallback(async () => {
    try {
      const res = await api.get("/teachers/", { params: { activo: true } });
      setTeachers(res.data.results || res.data);
    } catch {
      message.error("Error al cargar profesores");
    }
  }, [message]);

  useEffect(() => {
    fetchClassrooms();
    fetchTeachers();
  }, [fetchClassrooms, fetchTeachers]);

  const openCreate = () => {
    setEditingClassroom(null);
    form.resetFields();
    setModalOpen(true);
  };

  const openEdit = (record) => {
    setEditingClassroom(record);
    form.setFieldsValue(record);
    setModalOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      if (editingClassroom) {
        await api.patch(`/classrooms/${editingClassroom.id}/`, values);
        message.success("Aula actualizada");
      } else {
        await api.post("/classrooms/", values);
        message.success("Aula creada");
      }
      setModalOpen(false);
      fetchClassrooms();
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
      await api.delete(`/classrooms/${id}/`);
      message.success("Aula eliminada");
      fetchClassrooms();
    } catch {
      message.error("Error al eliminar");
    }
  };

  const columns = [
    { title: "Nombre", dataIndex: "nombre", key: "nombre" },
    { title: "Nivel (Edad)", dataIndex: "nivel", key: "nivel" },
    { title: "Capacidad", dataIndex: "capacidad", key: "capacidad", width: 100 },
    { title: "Alumnos", dataIndex: "cantidad_alumnos", key: "cantidad_alumnos", width: 100 },
    {
      title: "Profesor Titular",
      dataIndex: "profesor_titular_nombre",
      key: "profesor_titular_nombre",
    },
    {
      title: "Estado",
      dataIndex: "estado",
      key: "estado",
      render: (estado) => (
        <Tag color={estado === "ACTIVO" ? "green" : "default"}>{estado}</Tag>
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
            title="Eliminar aula"
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
          Aulas
        </Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          Nueva Aula
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={classrooms}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20 }}
      />

      <Modal
        title={editingClassroom ? "Editar Aula" : "Nueva Aula"}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        confirmLoading={saving}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="nombre"
            label="Nombre"
            rules={[{ required: true, message: "Ingrese el nombre" }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="nivel"
            label="Nivel (Edad)"
            rules={[{ required: true, message: "Ingrese el nivel" }]}
          >
            <Input placeholder="Ej: 3 anios, 4 anios" />
          </Form.Item>
          <Form.Item
            name="capacidad"
            label="Capacidad"
            rules={[{ required: true, message: "Ingrese la capacidad" }]}
          >
            <InputNumber min={1} max={50} style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item name="profesor_titular" label="Profesor Titular">
            <Select
              allowClear
              placeholder="Seleccione un profesor"
              options={teachers.map((t) => ({
                value: t.id,
                label: `${t.nombres} ${t.apellidos}`,
              }))}
            />
          </Form.Item>
          <Form.Item name="estado" label="Estado" initialValue="ACTIVO">
            <Select
              options={[
                { value: "ACTIVO", label: "Activo" },
                { value: "INACTIVO", label: "Inactivo" },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
