import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Table,
  Button,
  Input,
  Select,
  Space,
  Modal,
  Form,
  DatePicker,
  Tag,
  Popconfirm,
  App,
  Typography,
} from "antd";
import { PlusOutlined, SearchOutlined, EyeOutlined } from "@ant-design/icons";
import api from "../services/api";

const { Title } = Typography;

export default function Students() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [estadoFilter, setEstadoFilter] = useState(undefined);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const { message } = App.useApp();

  const fetchStudents = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (search) params.search = search;
      if (estadoFilter) params.estado = estadoFilter;
      const res = await api.get("/students/", { params });
      setStudents(res.data.results || res.data);
    } catch {
      message.error("Error al cargar alumnos");
    } finally {
      setLoading(false);
    }
  }, [search, estadoFilter, message]);

  useEffect(() => {
    fetchStudents();
  }, [fetchStudents]);

  const openCreate = () => {
    setEditingStudent(null);
    form.resetFields();
    setModalOpen(true);
  };

  const openEdit = (record) => {
    setEditingStudent(record);
    form.setFieldsValue({
      ...record,
      fecha_nacimiento: undefined,
    });
    setModalOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      if (values.fecha_nacimiento) {
        values.fecha_nacimiento = values.fecha_nacimiento.format("YYYY-MM-DD");
      }
      if (editingStudent) {
        await api.patch(`/students/${editingStudent.id}/`, values);
        message.success("Alumno actualizado");
      } else {
        await api.post("/students/", values);
        message.success("Alumno creado");
      }
      setModalOpen(false);
      fetchStudents();
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
      await api.delete(`/students/${id}/`);
      message.success("Alumno eliminado");
      fetchStudents();
    } catch {
      message.error("Error al eliminar");
    }
  };

  const columns = [
    { title: "DNI", dataIndex: "dni", key: "dni", width: 100 },
    { title: "Nombres", dataIndex: "nombres", key: "nombres" },
    { title: "Apellidos", dataIndex: "apellidos", key: "apellidos" },
    { title: "Edad", dataIndex: "edad", key: "edad", width: 70 },
    { title: "Aula", dataIndex: "classroom_nombre", key: "classroom_nombre" },
    {
      title: "Estado",
      dataIndex: "estado",
      key: "estado",
      render: (estado) => (
        <Tag color={estado === "ACTIVO" ? "green" : estado === "RETIRADO" ? "red" : "default"}>
          {estado}
        </Tag>
      ),
    },
    {
      title: "Acciones",
      key: "acciones",
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/alumnos/${record.id}`)}
          />
          <Button type="link" onClick={() => openEdit(record)}>
            Editar
          </Button>
          <Popconfirm
            title="Eliminar alumno"
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
          Alumnos
        </Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          Nuevo Alumno
        </Button>
      </div>

      <Space style={{ marginBottom: 16 }}>
        <Input
          placeholder="Buscar por nombre o DNI"
          prefix={<SearchOutlined />}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onPressEnter={fetchStudents}
          style={{ width: 250 }}
          allowClear
        />
        <Select
          placeholder="Estado"
          value={estadoFilter}
          onChange={setEstadoFilter}
          allowClear
          style={{ width: 150 }}
          options={[
            { value: "ACTIVO", label: "Activo" },
            { value: "RETIRADO", label: "Retirado" },
            { value: "EGRESADO", label: "Egresado" },
          ]}
        />
      </Space>

      <Table
        columns={columns}
        dataSource={students}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20, showSizeChanger: true }}
      />

      <Modal
        title={editingStudent ? "Editar Alumno" : "Nuevo Alumno"}
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
            name="fecha_nacimiento"
            label="Fecha de Nacimiento"
            rules={[{ required: true, message: "Seleccione la fecha" }]}
          >
            <DatePicker format="DD/MM/YYYY" style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item
            name="genero"
            label="Genero"
            rules={[{ required: true, message: "Seleccione genero" }]}
          >
            <Select
              options={[
                { value: "M", label: "Masculino" },
                { value: "F", label: "Femenino" },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
