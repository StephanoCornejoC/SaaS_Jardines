import { useState, useEffect, useCallback, useMemo } from "react";
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

const nivelOpciones = [
  { value: 2, label: "2 años" },
  { value: 3, label: "3 años" },
  { value: 4, label: "4 años" },
  { value: 5, label: "5 años" },
];

// Helper: arma el label de un profesor para los selects.
const teacherLabel = (t) => `${t.nombres} ${t.apellidos}`.trim();

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
      profesor_auxiliar: record.profesor_auxiliar,
    });
    setModalOpen(true);
  };

  // Divido los profesores por tipo para alimentar los selects del form.
  // Compatibilidad legacy: si un Teacher no trae `tipo`, lo trato como TITULAR.
  const titulares = useMemo(
    () => teachers.filter((t) => (t.tipo ?? "TITULAR") === "TITULAR"),
    [teachers],
  );
  const auxiliares = useMemo(
    () => teachers.filter((t) => t.tipo === "AUXILIAR"),
    [teachers],
  );

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      if (
        values.profesor_auxiliar &&
        values.profesor_auxiliar === values.profesor_titular
      ) {
        message.error("El titular y el auxiliar no pueden ser la misma persona");
        return;
      }
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
      title: "Profesor(a) titular",
      dataIndex: "profesor_titular_nombre",
      key: "profesor_titular_nombre",
      render: (nombre) => nombre ?? <Text type="secondary">Sin asignar</Text>,
    },
    {
      title: "Profesor(a) auxiliar",
      dataIndex: "profesor_auxiliar_nombre",
      key: "profesor_auxiliar_nombre",
      render: (nombre) =>
        nombre ?? <Text type="secondary" italic>— sin auxiliar —</Text>,
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

          <Form.Item
            name="profesor_titular"
            label="Profesor(a) titular"
            rules={[{ required: true, message: "Seleccione el profesor titular" }]}
            tooltip="Solo se listan profesores con tipo Titular. Si no aparece quien buscás, cambiá su tipo en la sección Profesores."
          >
            <Select
              placeholder={
                titulares.length
                  ? "Seleccione un profesor titular"
                  : "No hay profesores titulares — créalos en Profesores"
              }
              options={titulares.map((t) => ({
                value: t.id,
                label: teacherLabel(t),
              }))}
              notFoundContent="Sin titulares disponibles"
            />
          </Form.Item>

          <Form.Item
            name="profesor_auxiliar"
            label="Profesor(a) auxiliar (opcional)"
            tooltip="Solo se listan profesores con tipo Auxiliar. Dejá vacío si el aula no tiene auxiliar."
          >
            <Select
              allowClear
              placeholder={
                auxiliares.length
                  ? "Seleccione un profesor auxiliar (opcional)"
                  : "Aún no hay profesores auxiliares registrados"
              }
              options={auxiliares.map((t) => ({
                value: t.id,
                label: teacherLabel(t),
              }))}
              notFoundContent="Sin auxiliares disponibles"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
