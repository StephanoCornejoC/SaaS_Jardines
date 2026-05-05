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
  InputNumber,
  Tag,
  Popconfirm,
  Steps,
  Card,
  Avatar,
  Tooltip,
  Upload,
  App,
  Typography,
} from "antd";
import {
  PlusOutlined,
  SearchOutlined,
  EyeOutlined,
  TeamOutlined,
  UserAddOutlined,
  DeleteOutlined,
  WarningOutlined,
  UploadOutlined,
  FilePdfOutlined,
  StopOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";
import api from "../services/api";

const { Title, Text } = Typography;

const ESTADO_CONFIG = {
  ACTIVO:   { color: "green",   label: "Activo"   },
  RETIRADO: { color: "red",     label: "Retirado" },
  EGRESADO: { color: "blue",    label: "Egresado" },
};

const PARENTESCO_OPTIONS = [
  { value: "PADRE",  label: "Padre"  },
  { value: "MADRE",  label: "Madre"  },
  { value: "TUTOR",  label: "Tutor/a" },
  { value: "OTRO",   label: "Otro"   },
];

const currentYear = new Date().getFullYear();
const yearOptions = Array.from({ length: 5 }, (_, i) => ({
  value: currentYear - 1 + i,
  label: `${currentYear - 1 + i}`,
}));

const minBirthDate = dayjs().subtract(6, "year").startOf("day");
const maxBirthDate = dayjs().subtract(1, "year").endOf("day");

const disabledBirthDate = (current) => {
  if (!current) return false;
  return current.isBefore(minBirthDate) || current.isAfter(maxBirthDate);
};

export default function Students() {
  const [students, setStudents] = useState([]);
  const [classrooms, setClassrooms] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [estadoFilter, setEstadoFilter] = useState(undefined);
  const [classroomFilter, setClassroomFilter] = useState(undefined);
  const [modalOpen, setModalOpen] = useState(false);
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [guardiansCount, setGuardiansCount] = useState(1);
  const [pdfFile, setPdfFile] = useState(null);
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const { message } = App.useApp();

  const fetchStudents = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (search) params.search = search;
      if (estadoFilter) params.estado = estadoFilter;
      if (classroomFilter) params.classroom = classroomFilter;
      const res = await api.get("/students/", { params });
      setStudents(res.data.results || res.data);
    } catch {
      message.error("No se pudieron cargar los alumnos");
    } finally {
      setLoading(false);
    }
  }, [search, estadoFilter, classroomFilter, message]);

  useEffect(() => {
    fetchStudents();
  }, [fetchStudents]);

  useEffect(() => {
    const fetchClassrooms = async () => {
      try {
        const res = await api.get("/classrooms/");
        setClassrooms(res.data.results || res.data);
      } catch {
        message.error("No se pudieron cargar las aulas");
      }
    };
    fetchClassrooms();
  }, [message]);

  const resetWizard = () => {
    form.resetFields();
    form.setFieldsValue({
      genero: "M",
      apoderados: [{ parentesco: "MADRE" }],
      matricula: { anio_escolar: currentYear },
    });
    setGuardiansCount(1);
    setStep(0);
    setPdfFile(null);
  };

  const openCreate = () => {
    resetWizard();
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    form.resetFields();
    setStep(0);
    setPdfFile(null);
  };

  const stepFields = [
    ["dni", "nombres", "apellidos", "fecha_nacimiento", "genero", "classroom"],
    ["apoderados"],
    ["matricula"],
  ];

  const goNext = async () => {
    try {
      await form.validateFields(stepFields[step]);
      setStep(step + 1);
    } catch {
      // form muestra los errores
    }
  };

  const goBack = () => setStep((s) => Math.max(0, s - 1));

  const addGuardian = () => {
    const apoderados = form.getFieldValue("apoderados") || [];
    if (apoderados.length >= 2) return;
    form.setFieldsValue({
      apoderados: [...apoderados, { parentesco: "PADRE" }],
    });
    setGuardiansCount(apoderados.length + 1);
  };

  const removeGuardian = (idx) => {
    const apoderados = form.getFieldValue("apoderados") || [];
    if (apoderados.length <= 1) return;
    const next = apoderados.filter((_, i) => i !== idx);
    form.setFieldsValue({ apoderados: next });
    setGuardiansCount(next.length);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      const payload = {
        dni: values.dni,
        nombres: values.nombres,
        apellidos: values.apellidos,
        fecha_nacimiento: values.fecha_nacimiento.format("YYYY-MM-DD"),
        genero: values.genero,
        classroom: values.classroom ?? null,
        apoderados: values.apoderados.map((a, idx) => ({
          dni: a.dni,
          nombres: a.nombres,
          apellidos: a.apellidos,
          telefono: a.telefono,
          email: a.email || null,
          parentesco: a.parentesco,
          es_principal: idx === 0,
        })),
        matricula: values.matricula
          ? {
              anio_escolar: values.matricula.anio_escolar,
              costo_matricula: values.matricula.costo_matricula,
              monto_mensual: values.matricula.monto_mensual,
            }
          : undefined,
      };
      const res = await api.post("/students/", payload);
      const newId = res.data?.id;
      // Si el usuario adjuntó un PDF, hacemos un PATCH multipart adicional
      if (newId && pdfFile) {
        const fd = new FormData();
        fd.append("ficha_matricula", pdfFile);
        try {
          await api.patch(`/students/${newId}/`, fd, {
            headers: { "Content-Type": "multipart/form-data" },
          });
        } catch {
          message.warning("Alumno creado, pero no se pudo subir el PDF. Puedes intentarlo desde su detalle.");
        }
      }
      message.success("Alumno registrado correctamente");
      closeModal();
      fetchStudents();
    } catch (err) {
      if (err.response?.data) {
        const data = err.response.data;
        const flat = Array.isArray(data)
          ? data.join(", ")
          : Object.values(data)
              .flatMap((v) => (Array.isArray(v) ? v : [JSON.stringify(v)]))
              .join(", ");
        message.error(flat || "No se pudo registrar el alumno");
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
      message.error("No se pudo eliminar el alumno");
    }
  };

  const handleChangeEstado = async (record, nuevoEstado) => {
    try {
      await api.patch(`/students/${record.id}/`, { estado: nuevoEstado });
      message.success(`${record.nombres} marcado(a) como ${ESTADO_CONFIG[nuevoEstado]?.label || nuevoEstado}`);
      fetchStudents();
    } catch {
      message.error("No se pudo cambiar el estado");
    }
  };

  const columns = [
    { title: "DNI", dataIndex: "dni", key: "dni", width: 100 },
    {
      title: "Nombre completo",
      key: "nombre",
      render: (_, record) => (
        <Space>
          <Avatar
            size={32}
            style={{ background: record.genero === "F" ? "#f472b6" : "#60a5fa" }}
          >
            {record.nombres?.[0]}
          </Avatar>
          <div>
            <Text strong>{record.nombres} {record.apellidos}</Text>
            {record.apoderado_principal?.telefono && (
              <div>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {record.apoderado_principal.parentesco === "MADRE" ? "Mamá" :
                   record.apoderado_principal.parentesco === "PADRE" ? "Papá" :
                   "Tutor/a"}: {record.apoderado_principal.telefono}
                </Text>
              </div>
            )}
          </div>
        </Space>
      ),
    },
    {
      title: "Edad",
      dataIndex: "edad",
      key: "edad",
      width: 80,
      align: "center",
      render: (e) => `${e} ${e === 1 ? "año" : "años"}`,
    },
    {
      title: "Aula",
      key: "classroom",
      render: (_, record) => {
        if (!record.classroom_nombre) return <Text type="secondary">Sin aula</Text>;
        const aula = classrooms.find((c) => c.id === record.classroom);
        const inconsistente = aula && record.edad !== aula.nivel_edad;
        return (
          <Space size={4}>
            <Tag color={inconsistente ? "orange" : "cyan"}>{record.classroom_nombre}</Tag>
            {inconsistente && (
              <Tooltip title={`El alumno tiene ${record.edad} años pero está en aula de ${aula.nivel_edad} años`}>
                <WarningOutlined style={{ color: "#f59e0b" }} />
              </Tooltip>
            )}
          </Space>
        );
      },
    },
    {
      title: "Estado",
      dataIndex: "estado",
      key: "estado",
      width: 100,
      render: (estado) => {
        const cfg = ESTADO_CONFIG[estado] || { color: "default", label: estado };
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      },
    },
    {
      title: "Acciones",
      key: "acciones",
      width: 220,
      render: (_, record) => (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/alumnos/${record.id}`)}
          >
            Ver detalles
          </Button>
          {record.estado === "ACTIVO" && (
            <Popconfirm
              title="¿Marcar como retirado?"
              description={`${record.nombres} ya no continuará en el jardín. No se incluirá en la próxima migración anual. Podrás reactivarlo desde su detalle.`}
              onConfirm={() => handleChangeEstado(record, "RETIRADO")}
              okText="Sí, retirar"
              cancelText="Cancelar"
            >
              <Tooltip title="Marcar como retirado">
                <Button size="small" icon={<StopOutlined />} />
              </Tooltip>
            </Popconfirm>
          )}
          <Popconfirm
            title="¿Eliminar este alumno?"
            description="Esta acción no se puede deshacer."
            onConfirm={() => handleDelete(record.id)}
            okText="Sí, eliminar"
            cancelText="Cancelar"
            okButtonProps={{ danger: true }}
          >
            <Tooltip title="Eliminar">
              <Button size="small" danger icon={<DeleteOutlined />} />
            </Tooltip>
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
            <TeamOutlined style={{ marginRight: 8, color: "#0d9488" }} />
            Alumnos
          </Title>
          <Text type="secondary" style={{ fontSize: 13 }}>
            Lista de alumnos matriculados en el jardín
          </Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          Nuevo Alumno
        </Button>
      </div>

      <Card style={{ marginBottom: 16 }} styles={{ body: { padding: 16 } }}>
        <Space wrap>
          <Input
            placeholder="Buscar por nombre o DNI"
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onPressEnter={fetchStudents}
            style={{ width: 260 }}
            allowClear
          />
          <Select
            placeholder="Filtrar por aula"
            value={classroomFilter}
            onChange={setClassroomFilter}
            allowClear
            style={{ width: 200 }}
            options={classrooms.map((c) => ({
              value: c.id,
              label: `${c.nombre} (${c.nivel_edad} años)`,
            }))}
          />
          <Select
            placeholder="Filtrar por estado"
            value={estadoFilter}
            onChange={setEstadoFilter}
            allowClear
            style={{ width: 160 }}
            options={Object.entries(ESTADO_CONFIG).map(([value, { label }]) => ({ value, label }))}
          />
        </Space>
      </Card>

      <Table
        columns={columns}
        dataSource={students}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20, hideOnSinglePage: true }}
        locale={{ emptyText: "No se encontraron alumnos" }}
        scroll={{ x: true }}
      />

      <Modal
        title={
          <Space>
            <UserAddOutlined style={{ color: "#0d9488" }} />
            <span>Registrar nuevo alumno</span>
          </Space>
        }
        open={modalOpen}
        onCancel={closeModal}
        footer={null}
        width={720}
      >
        <Steps
          current={step}
          size="small"
          style={{ margin: "16px 0 24px" }}
          items={[
            { title: "Datos del alumno" },
            { title: "Apoderados" },
            { title: "Matrícula" },
          ]}
        />

        <Form form={form} layout="vertical" preserve>
          <div style={{ display: step === 0 ? "block" : "none" }}>
            <Form.Item
              name="dni"
              label="DNI del alumno"
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
                <Input placeholder="María Fernanda" />
              </Form.Item>
              <Form.Item
                name="apellidos"
                label="Apellidos"
                rules={[{ required: true, message: "Ingrese los apellidos" }]}
              >
                <Input placeholder="García López" />
              </Form.Item>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 16px" }}>
              <Form.Item
                name="fecha_nacimiento"
                label="Fecha de nacimiento"
                rules={[
                  { required: true, message: "Seleccione la fecha" },
                  () => ({
                    validator(_, value) {
                      if (!value) return Promise.resolve();
                      const edad = dayjs().diff(value, "year");
                      if (edad < 1 || edad > 6) {
                        return Promise.reject(
                          new Error("La edad del alumno debe estar entre 1 y 6 años"),
                        );
                      }
                      return Promise.resolve();
                    },
                  }),
                ]}
              >
                <DatePicker
                  format="DD/MM/YYYY"
                  style={{ width: "100%" }}
                  placeholder="dd/mm/aaaa"
                  disabledDate={disabledBirthDate}
                />
              </Form.Item>
              <Form.Item
                name="genero"
                label="Género"
                rules={[{ required: true, message: "Seleccione el género" }]}
              >
                <Select
                  options={[
                    { value: "M", label: "Masculino" },
                    { value: "F", label: "Femenino" },
                  ]}
                />
              </Form.Item>
            </div>

            <Form.Item
              name="classroom"
              label="Aula asignada"
              tooltip="Puedes dejarla vacía si aún no asignas aula"
            >
              <Select
                allowClear
                placeholder="Seleccione el aula del alumno"
                options={classrooms.map((c) => ({
                  value: c.id,
                  label: `${c.nombre} (${c.nivel_edad} años)`,
                }))}
              />
            </Form.Item>
          </div>

          <div style={{ display: step === 1 ? "block" : "none" }}>
            <Text type="secondary" style={{ marginBottom: 12, display: "block" }}>
              Mínimo 1 apoderado, máximo 2. El primero será el contacto principal.
            </Text>
            <Form.List name="apoderados">
              {(fields) => (
                <>
                  {fields.map((field, idx) => (
                    <Card
                      key={field.key}
                      size="small"
                      title={
                        <Space>
                          <Tag color={idx === 0 ? "green" : "blue"}>
                            {idx === 0 ? "Apoderado principal" : "Segundo apoderado"}
                          </Tag>
                        </Space>
                      }
                      extra={
                        guardiansCount > 1 && (
                          <Button
                            type="text"
                            danger
                            size="small"
                            icon={<DeleteOutlined />}
                            onClick={() => removeGuardian(idx)}
                          />
                        )
                      }
                      style={{ marginBottom: 12 }}
                    >
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 16px" }}>
                        <Form.Item
                          name={[field.name, "dni"]}
                          label="DNI"
                          rules={[
                            { required: true, message: "Ingrese el DNI" },
                            { len: 8, message: "8 dígitos" },
                          ]}
                        >
                          <Input maxLength={8} />
                        </Form.Item>
                        <Form.Item
                          name={[field.name, "parentesco"]}
                          label="Parentesco"
                          rules={[{ required: true, message: "Seleccione" }]}
                        >
                          <Select options={PARENTESCO_OPTIONS} />
                        </Form.Item>
                      </div>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 16px" }}>
                        <Form.Item
                          name={[field.name, "nombres"]}
                          label="Nombres"
                          rules={[{ required: true, message: "Ingrese los nombres" }]}
                        >
                          <Input />
                        </Form.Item>
                        <Form.Item
                          name={[field.name, "apellidos"]}
                          label="Apellidos"
                          rules={[{ required: true, message: "Ingrese los apellidos" }]}
                        >
                          <Input />
                        </Form.Item>
                      </div>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 16px" }}>
                        <Form.Item
                          name={[field.name, "telefono"]}
                          label="Teléfono / WhatsApp"
                          rules={[{ required: true, message: "Ingrese el teléfono" }]}
                          tooltip="Se usará para enviar comunicados por WhatsApp"
                        >
                          <Input placeholder="999 999 999" />
                        </Form.Item>
                        <Form.Item
                          name={[field.name, "email"]}
                          label="Correo electrónico"
                          rules={[
                            { type: "email", message: "Correo no válido" },
                          ]}
                          tooltip="Se usará para enviar comunicados por email"
                        >
                          <Input placeholder="correo@ejemplo.com" />
                        </Form.Item>
                      </div>
                    </Card>
                  ))}
                </>
              )}
            </Form.List>
            {guardiansCount < 2 && (
              <Button
                type="dashed"
                onClick={addGuardian}
                icon={<PlusOutlined />}
                block
              >
                Agregar segundo apoderado
              </Button>
            )}
          </div>

          <div style={{ display: step === 2 ? "block" : "none" }}>
            <Text type="secondary" style={{ marginBottom: 12, display: "block" }}>
              Año al que se matricula y montos. La matrícula se registra como ingreso en caja.
            </Text>
            <Card size="small">
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 16px" }}>
                <Form.Item
                  name={["matricula", "anio_escolar"]}
                  label="Año escolar"
                  rules={[{ required: true, message: "Seleccione el año" }]}
                >
                  <Select options={yearOptions} />
                </Form.Item>
                <Form.Item
                  name={["matricula", "costo_matricula"]}
                  label="Costo de matrícula (S/.)"
                  rules={[{ required: true, message: "Ingrese el costo" }]}
                >
                  <InputNumber
                    min={0}
                    step={50}
                    precision={2}
                    style={{ width: "100%" }}
                    placeholder="Ej: 250.00"
                  />
                </Form.Item>
              </div>
              <Form.Item
                name={["matricula", "monto_mensual"]}
                label="Pensión mensual (S/.)"
                rules={[{ required: true, message: "Ingrese el monto" }]}
                tooltip="Lo que pagará cada mes durante el año escolar"
              >
                <InputNumber
                  min={0}
                  step={50}
                  precision={2}
                  style={{ width: "100%" }}
                  placeholder="Ej: 350.00"
                />
              </Form.Item>
            </Card>

            <Card
              size="small"
              style={{ marginTop: 12 }}
              title={
                <Space>
                  <FilePdfOutlined style={{ color: "#dc2626" }} />
                  <span>Ficha de matrícula (opcional)</span>
                </Space>
              }
            >
              <Text type="secondary" style={{ display: "block", marginBottom: 8, fontSize: 12 }}>
                Si tienes el PDF firmado por el apoderado, súbelo ahora. También puedes hacerlo después desde el detalle del alumno.
              </Text>
              <Upload
                accept="application/pdf"
                maxCount={1}
                beforeUpload={(file) => { setPdfFile(file); return false; }}
                onRemove={() => setPdfFile(null)}
                fileList={pdfFile ? [{ uid: "-1", name: pdfFile.name, status: "done" }] : []}
              >
                <Button icon={<UploadOutlined />}>Seleccionar PDF</Button>
              </Upload>
            </Card>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 24 }}>
            <Button onClick={closeModal}>Cancelar</Button>
            <Space>
              {step > 0 && <Button onClick={goBack}>Atrás</Button>}
              {step < 2 && (
                <Button type="primary" onClick={goNext}>
                  Siguiente
                </Button>
              )}
              {step === 2 && (
                <Button type="primary" loading={saving} onClick={handleSave}>
                  Registrar alumno
                </Button>
              )}
            </Space>
          </div>
        </Form>
      </Modal>
    </div>
  );
}
