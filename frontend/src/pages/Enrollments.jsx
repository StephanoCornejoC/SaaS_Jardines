import { useState, useEffect, useCallback } from "react";
import {
  Table,
  Button,
  Select,
  Space,
  Modal,
  Form,
  InputNumber,
  Tag,
  App,
  Typography,
} from "antd";
import { PlusOutlined } from "@ant-design/icons";
import api from "../services/api";

const { Title } = Typography;

const currentYear = new Date().getFullYear();
const yearOptions = Array.from({ length: 5 }, (_, i) => ({
  value: currentYear - 2 + i,
  label: `${currentYear - 2 + i}`,
}));

export default function Enrollments() {
  const [enrollments, setEnrollments] = useState([]);
  const [students, setStudents] = useState([]);
  const [classrooms, setClassrooms] = useState([]);
  const [loading, setLoading] = useState(false);
  const [anioFilter, setAnioFilter] = useState(currentYear);
  const [estadoFilter, setEstadoFilter] = useState(undefined);
  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();
  const { message } = App.useApp();

  const fetchEnrollments = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (anioFilter) params.anio_escolar = anioFilter;
      if (estadoFilter) params.estado = estadoFilter;
      const res = await api.get("/enrollments/", { params });
      setEnrollments(res.data.results || res.data);
    } catch {
      message.error("Error al cargar matriculas");
    } finally {
      setLoading(false);
    }
  }, [anioFilter, estadoFilter, message]);

  useEffect(() => {
    fetchEnrollments();
  }, [fetchEnrollments]);

  useEffect(() => {
    const fetchOptions = async () => {
      try {
        const [studRes, classRes] = await Promise.all([
          api.get("/students/", { params: { estado: "ACTIVO" } }),
          api.get("/classrooms/", { params: { estado: "ACTIVO" } }),
        ]);
        setStudents(studRes.data.results || studRes.data);
        setClassrooms(classRes.data.results || classRes.data);
      } catch {
        message.error("Error al cargar opciones de matricula");
      }
    };
    fetchOptions();
  }, [message]);

  const openCreate = () => {
    form.resetFields();
    form.setFieldsValue({ anio_escolar: currentYear });
    setModalOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      await api.post("/enrollments/", values);
      message.success("Matricula creada");
      setModalOpen(false);
      fetchEnrollments();
    } catch (err) {
      if (err.response?.data) {
        const errors = Object.values(err.response.data).flat().join(", ");
        message.error(errors);
      }
    } finally {
      setSaving(false);
    }
  };

  const columns = [
    { title: "Alumno", dataIndex: "alumno_nombre", key: "alumno_nombre" },
    { title: "Aula", dataIndex: "aula_nombre", key: "aula_nombre" },
    { title: "Ano Escolar", dataIndex: "anio_escolar", key: "anio_escolar", width: 120 },
    {
      title: "Costo",
      dataIndex: "costo_mensual",
      key: "costo_mensual",
      render: (val) => `S/. ${Number(val).toFixed(2)}`,
    },
    {
      title: "Estado",
      dataIndex: "estado",
      key: "estado",
      render: (estado) => {
        const colorMap = { ACTIVA: "green", CANCELADA: "red", FINALIZADA: "blue" };
        return <Tag color={colorMap[estado] || "default"}>{estado}</Tag>;
      },
    },
    { title: "Fecha", dataIndex: "fecha_matricula", key: "fecha_matricula" },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>
          Matriculas
        </Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          Nueva Matricula
        </Button>
      </div>

      <Space style={{ marginBottom: 16 }}>
        <Select
          placeholder="Ano Escolar"
          value={anioFilter}
          onChange={setAnioFilter}
          allowClear
          style={{ width: 150 }}
          options={yearOptions}
        />
        <Select
          placeholder="Estado"
          value={estadoFilter}
          onChange={setEstadoFilter}
          allowClear
          style={{ width: 150 }}
          options={[
            { value: "ACTIVA", label: "Activa" },
            { value: "CANCELADA", label: "Cancelada" },
            { value: "FINALIZADA", label: "Finalizada" },
          ]}
        />
      </Space>

      <Table
        columns={columns}
        dataSource={enrollments}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20, showSizeChanger: true }}
      />

      <Modal
        title="Nueva Matricula"
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        confirmLoading={saving}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="alumno"
            label="Alumno"
            rules={[{ required: true, message: "Seleccione un alumno" }]}
          >
            <Select
              showSearch
              placeholder="Buscar alumno"
              optionFilterProp="label"
              options={students.map((s) => ({
                value: s.id,
                label: `${s.dni} - ${s.nombres} ${s.apellidos}`,
              }))}
            />
          </Form.Item>
          <Form.Item
            name="aula"
            label="Aula"
            rules={[{ required: true, message: "Seleccione un aula" }]}
          >
            <Select
              placeholder="Seleccione aula"
              options={classrooms.map((c) => ({
                value: c.id,
                label: `${c.nombre} (${c.nivel})`,
              }))}
            />
          </Form.Item>
          <Form.Item
            name="anio_escolar"
            label="Ano Escolar"
            rules={[{ required: true, message: "Ingrese el ano escolar" }]}
          >
            <InputNumber min={2020} max={2040} style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item
            name="costo_mensual"
            label="Costo Mensual (S/.)"
            rules={[{ required: true, message: "Ingrese el costo" }]}
          >
            <InputNumber min={0} step={50} precision={2} style={{ width: "100%" }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
