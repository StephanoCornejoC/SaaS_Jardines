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
  Popconfirm,
  App,
  Typography,
} from "antd";
import { PlusOutlined, HomeOutlined } from "@ant-design/icons";
import api from "../services/api";

const { Title, Text } = Typography;

const currentYear = new Date().getFullYear();

const nivelOpciones = [
  { value: 2, label: "2 años" },
  { value: 3, label: "3 años" },
  { value: 4, label: "4 años" },
  { value: 5, label: "5 años" },
];

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
      message.error("No se pudieron cargar las aulas");
    } finally {
      setLoading(false);
    }
  }, [message]);

  const fetchTeachers = useCallback(async () => {
    try {
      const res = await api.get("/teachers/");
      setTeachers(res.data.results || res.data);
    } catch {
      message.error("No se pudieron cargar los profesores");
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
    form.setFieldsValue({
      nombre: record.nombre,
      nivel_edad: record.nivel_edad,
      capacidad: record.capacidad,
      profesor_titular: record.profesor_titular,
    });
    setModalOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      if (editingClassroom) {
        await api.patch(`/classrooms/${editingClassroom.id}/`, values);
        message.success("Aula actualizada correctamente");
      } else {
        await api.post("/classrooms/", values);
        message.success("Aula creada correctamente");
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
      message.error("No se pudo eliminar el aula");
    }
  };

  const columns = [
    {
      title: "Nombre",
      dataIndex: "nombre",
      key: "nombre",
      render: (nombre) => <Text strong>{nombre}</Text>,
    },
    {
      title: "Nivel",
      dataIndex: "nivel_edad",
      key: "nivel_edad",
      width: 100,
      render: (nivel) => nivel ? `${nivel} años` : "—",
    },
    {
      title: "Capacidad",
      dataIndex: "capacidad",
      key: "capacidad",
      width: 100,
      align: "center",
    },
    {
      title: "Alumnos",
      dataIndex: "alumnos_count",
      key: "alumnos_count",
      width: 90,
      align: "center",
      render: (count, record) => (
        <Text type={count >= record.capacidad ? "danger" : undefined}>
          {count ?? 0}
        </Text>
      ),
    },
    {
      title: "Profesora titular",
      dataIndex: "profesor_titular_nombre",
      key: "profesor_titular_nombre",
      render: (nombre) => nombre ?? <Text type="secondary">Sin asignar</Text>,
    },
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
            title="¿Eliminar esta aula?"
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
            <HomeOutlined style={{ marginRight: 8, color: "#1677ff" }} />
            Aulas
          </Title>
          <Text type="secondary" style={{ fontSize: 13 }}>
            Gestión de aulas y grupos del jardín
          </Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          Nueva Aula
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={classrooms}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20, hideOnSinglePage: true }}
        locale={{ emptyText: "No hay aulas registradas aún" }}
        scroll={{ x: true }}
      />

      <Modal
        title={editingClassroom ? "Editar Aula" : "Nueva Aula"}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => { form.resetFields(); setModalOpen(false); }}
        confirmLoading={saving}
        okText={editingClassroom ? "Guardar cambios" : "Crear aula"}
        cancelText="Cancelar"
        width={520}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="nombre"
            label="Nombre del aula"
            rules={[{ required: true, message: "Ingrese el nombre del aula" }]}
          >
            <Input placeholder="Ej: Aula Mariposas, Sala Azul" />
          </Form.Item>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 16px" }}>
            <Form.Item
              name="nivel_edad"
              label="Nivel (edad)"
              rules={[{ required: true, message: "Seleccione el nivel" }]}
            >
              <Select placeholder="Seleccionar nivel" options={nivelOpciones} />
            </Form.Item>
            <Form.Item
              name="capacidad"
              label="Capacidad máxima"
              rules={[{ required: true, message: "Ingrese la capacidad" }]}
            >
              <InputNumber min={1} max={50} style={{ width: "100%" }} />
            </Form.Item>
          </div>

          <Form.Item name="profesor_titular" label="Profesora titular">
            <Select
              allowClear
              placeholder="Seleccione una profesora"
              options={teachers.map((t) => ({
                value: t.id,
                label: `${t.nombres} ${t.apellidos}`,
              }))}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
