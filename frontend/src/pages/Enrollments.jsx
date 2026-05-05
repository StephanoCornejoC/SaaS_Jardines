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
  Alert,
  Popconfirm,
  App,
  Typography,
} from "antd";
import { PlusOutlined, FormOutlined, EditOutlined, DeleteOutlined } from "@ant-design/icons";
import api from "../services/api";

const { Title, Text } = Typography;

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
  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editingEnrollment, setEditingEnrollment] = useState(null);
  const [form] = Form.useForm();
  const { message } = App.useApp();

  const fetchEnrollments = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (anioFilter) params.anio_escolar = anioFilter;
      const res = await api.get("/enrollments/", { params });
      setEnrollments(res.data.results || res.data);
    } catch {
      message.error("No se pudieron cargar las matrículas");
    } finally {
      setLoading(false);
    }
  }, [anioFilter, message]);

  useEffect(() => {
    fetchEnrollments();
  }, [fetchEnrollments]);

  useEffect(() => {
    const fetchOptions = async () => {
      try {
        const [studRes, classRes] = await Promise.all([
          api.get("/students/", { params: { estado: "ACTIVO" } }),
          api.get("/classrooms/"),
        ]);
        setStudents(studRes.data.results || studRes.data);
        setClassrooms(classRes.data.results || classRes.data);
      } catch {
        message.error("Error al cargar opciones de matrícula");
      }
    };
    fetchOptions();
  }, [message]);

  const openCreate = () => {
    setEditingEnrollment(null);
    form.resetFields();
    form.setFieldsValue({ anio_escolar: currentYear });
    setModalOpen(true);
  };

  const openEdit = (record) => {
    setEditingEnrollment(record);
    form.resetFields();
    form.setFieldsValue({
      student: record.student,
      classroom: record.classroom,
      anio_escolar: record.anio_escolar,
      costo_matricula: Number(record.costo_matricula),
    });
    setModalOpen(true);
  };

  const handleStudentChange = async (studentId) => {
    if (!studentId || editingEnrollment) return;
    try {
      const res = await api.get(`/enrollments/?student=${studentId}`);
      const list = res.data.results || res.data;
      const ultimoAnio = list.reduce(
        (max, e) => Math.max(max, e.anio_escolar),
        currentYear - 1,
      );
      form.setFieldValue("anio_escolar", ultimoAnio + 1);
    } catch {
      // si falla, mantener default
    }
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      if (editingEnrollment) {
        await api.patch(`/enrollments/${editingEnrollment.id}/`, {
          classroom: values.classroom ?? null,
          costo_matricula: values.costo_matricula,
        });
        message.success("Matrícula actualizada");
      } else {
        await api.post("/enrollments/", values);
        message.success("Matrícula registrada correctamente");
      }
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

  const handleDelete = async (id) => {
    try {
      await api.delete(`/enrollments/${id}/`);
      message.success("Matrícula eliminada");
      fetchEnrollments();
    } catch {
      message.error("No se pudo eliminar la matrícula");
    }
  };

  const columns = [
    {
      title: "Alumno",
      dataIndex: "student_nombre",
      key: "student_nombre",
      render: (nombre) => <Text strong>{nombre}</Text>,
    },
    {
      title: "Aula",
      dataIndex: "classroom_nombre",
      key: "classroom_nombre",
      render: (nombre) => nombre ?? <Text type="secondary">Sin aula</Text>,
    },
    {
      title: "Año escolar",
      dataIndex: "anio_escolar",
      key: "anio_escolar",
      width: 180,
      render: (anio) => {
        const cfg = anio === currentYear
          ? { color: "green", label: "En curso" }
          : anio > currentYear
            ? { color: "blue",    label: "Próximo" }
            : { color: "default", label: "Histórica" };
        return (
          <Space>
            <Tag color="cyan">{anio}</Tag>
            <Tag color={cfg.color}>{cfg.label}</Tag>
          </Space>
        );
      },
    },
    {
      title: "Costo matrícula",
      dataIndex: "costo_matricula",
      key: "costo_matricula",
      render: (val) => `S/. ${Number(val || 0).toFixed(2)}`,
    },
    {
      title: "Fecha",
      dataIndex: "fecha_matricula",
      key: "fecha_matricula",
      width: 110,
    },
    {
      title: "Acciones",
      key: "acciones",
      width: 130,
      render: (_, record) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(record)} />
          <Popconfirm
            title="¿Eliminar esta matrícula?"
            description="Se eliminarán también los pagos asociados."
            onConfirm={() => handleDelete(record.id)}
            okText="Sí, eliminar"
            cancelText="Cancelar"
            okButtonProps={{ danger: true }}
          >
            <Button size="small" danger icon={<DeleteOutlined />} />
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
            <FormOutlined style={{ marginRight: 8, color: "#1677ff" }} />
            Matrículas
          </Title>
          <Text type="secondary" style={{ fontSize: 13 }}>
            Registro de matrículas por año escolar
          </Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          Nueva Matrícula
        </Button>
      </div>

      <Space style={{ marginBottom: 16 }}>
        <Select
          placeholder="Año escolar"
          value={anioFilter}
          onChange={setAnioFilter}
          allowClear
          style={{ width: 140 }}
          options={yearOptions}
        />
      </Space>

      <Table
        columns={columns}
        dataSource={enrollments}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20, hideOnSinglePage: true }}
        locale={{ emptyText: "No hay matrículas para los filtros seleccionados" }}
        scroll={{ x: true }}
      />

      <Modal
        title={editingEnrollment ? "Editar matrícula" : "Nueva Matrícula"}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => { form.resetFields(); setModalOpen(false); }}
        confirmLoading={saving}
        okText={editingEnrollment ? "Guardar cambios" : "Registrar matrícula"}
        cancelText="Cancelar"
        width={520}
      >
        <Form
          form={form}
          layout="vertical"
          onValuesChange={() => form.validateFields(["anio_escolar"]).catch(() => {})}
        >
          <Form.Item shouldUpdate noStyle>
            {({ getFieldValue }) => {
              const anio = getFieldValue("anio_escolar");
              if (!anio || editingEnrollment) return null;
              if (anio === currentYear) {
                return (
                  <Alert
                    type="success"
                    showIcon
                    message="Matrícula del año en curso"
                    description="Si el alumno aún no tiene aula asignada, esta matrícula le asignará una. Si ya tiene aula, se mantiene la actual."
                    style={{ marginBottom: 16 }}
                  />
                );
              }
              if (anio > currentYear) {
                return (
                  <Alert
                    type="info"
                    showIcon
                    message={`Matrícula adelantada para ${anio}`}
                    description="Reserva el cupo del próximo año. El alumno seguirá cursando en su aula actual hasta que ejecutes la migración anual."
                    style={{ marginBottom: 16 }}
                  />
                );
              }
              return (
                <Alert
                  type="warning"
                  showIcon
                  message="Matrícula histórica"
                  description="Estás registrando una matrícula de un año pasado. Verifica que sea correcto."
                  style={{ marginBottom: 16 }}
                />
              );
            }}
          </Form.Item>
          <Form.Item
            name="student"
            label="Alumno"
            rules={[{ required: true, message: "Seleccione un alumno" }]}
          >
            <Select
              showSearch
              placeholder="Buscar alumno por nombre o DNI"
              optionFilterProp="label"
              disabled={!!editingEnrollment}
              onChange={handleStudentChange}
              options={students.map((s) => ({
                value: s.id,
                label: `${s.nombres} ${s.apellidos} (${s.dni})`,
              }))}
            />
          </Form.Item>

          <Form.Item
            name="classroom"
            label="Aula del año matriculado"
            rules={[{ required: true, message: "Seleccione un aula" }]}
          >
            <Select
              placeholder="Seleccione el aula"
              options={classrooms.map((c) => ({
                value: c.id,
                label: `${c.nombre}${c.nivel_edad ? ` — ${c.nivel_edad} años` : ""}`,
              }))}
            />
          </Form.Item>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 16px" }}>
            <Form.Item
              name="anio_escolar"
              label="Año escolar"
              rules={[{ required: true, message: "Ingrese el año escolar" }]}
              tooltip={
                editingEnrollment
                  ? "El año escolar no se puede modificar"
                  : "Si el alumno ya tiene matrícula previa, se sugiere el siguiente año"
              }
            >
              <InputNumber
                min={2020}
                max={2040}
                style={{ width: "100%" }}
                disabled={!!editingEnrollment}
              />
            </Form.Item>
            <Form.Item
              name="costo_matricula"
              label="Costo matrícula (S/.)"
              rules={[{ required: true, message: "Ingrese el costo" }]}
            >
              <InputNumber min={0} step={50} precision={2} style={{ width: "100%" }} />
            </Form.Item>
          </div>

          {!editingEnrollment && (
            <Form.Item
              name="monto_mensual"
              label="Pensión mensual (S/.)"
              rules={[{ required: true, message: "Ingrese el monto de pensión" }]}
            >
              <InputNumber min={0} step={50} precision={2} style={{ width: "100%" }} placeholder="Ej: 350.00" />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
}
