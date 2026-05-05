import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Tabs,
  Table,
  Form,
  Input,
  InputNumber,
  Select,
  DatePicker,
  Button,
  Spin,
  Card,
  Tag,
  Space,
  Avatar,
  Descriptions,
  Empty,
  Modal,
  Popconfirm,
  Alert,
  Upload,
  App,
  Typography,
} from "antd";
import {
  ArrowLeftOutlined,
  EditOutlined,
  SaveOutlined,
  CloseOutlined,
  DeleteOutlined,
  PlusOutlined,
  UserOutlined,
  HeartOutlined,
  TeamOutlined,
  DollarOutlined,
  FilePdfOutlined,
  UploadOutlined,
  FileDoneOutlined,
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
  { value: "PADRE", label: "Padre" },
  { value: "MADRE", label: "Madre" },
  { value: "TUTOR", label: "Tutor/a" },
  { value: "OTRO",  label: "Otro" },
];

const TIPO_SANGRE = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].map((v) => ({
  value: v,
  label: v,
}));

const minBirthDate = dayjs().subtract(6, "year").startOf("day");
const maxBirthDate = dayjs().subtract(1, "year").endOf("day");
const disabledBirthDate = (current) =>
  !!current && (current.isBefore(minBirthDate) || current.isAfter(maxBirthDate));

export default function StudentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { message } = App.useApp();

  const [student, setStudent] = useState(null);
  const [classrooms, setClassrooms] = useState([]);
  const [enrollments, setEnrollments] = useState([]);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingDatos, setEditingDatos] = useState(false);
  const [editingApoderados, setEditingApoderados] = useState(false);
  const [savingDatos, setSavingDatos] = useState(false);
  const [savingApoderados, setSavingApoderados] = useState(false);
  const [savingFicha, setSavingFicha] = useState(false);
  const [uploadingPdf, setUploadingPdf] = useState(false);
  const [matriculaModalOpen, setMatriculaModalOpen] = useState(false);
  const [editingMatricula, setEditingMatricula] = useState(null);
  const [savingMatricula, setSavingMatricula] = useState(false);
  const [matriculaForm] = Form.useForm();
  const [datosForm] = Form.useForm();
  const [apoderadosForm] = Form.useForm();
  const [fichaForm] = Form.useForm();

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [studentRes, classroomsRes, enrollmentsRes, paymentsRes] =
        await Promise.allSettled([
          api.get(`/students/${id}/`),
          api.get("/classrooms/"),
          api.get(`/enrollments/?student=${id}`),
          api.get(`/payments/?student=${id}`),
        ]);

      if (studentRes.status === "fulfilled") {
        setStudent(studentRes.value.data);
      }
      if (classroomsRes.status === "fulfilled") {
        setClassrooms(classroomsRes.value.data.results || classroomsRes.value.data);
      }
      if (enrollmentsRes.status === "fulfilled") {
        setEnrollments(enrollmentsRes.value.data.results || enrollmentsRes.value.data);
      }
      if (paymentsRes.status === "fulfilled") {
        setPayments(paymentsRes.value.data.results || paymentsRes.value.data);
      }
    } catch {
      message.error("Error al cargar datos del alumno");
    } finally {
      setLoading(false);
    }
  }, [id, message]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  // Hidratar formularios DESPUÉS de que student esté cargado y los Form estén montados.
  useEffect(() => {
    if (!student) return;
    datosForm.setFieldsValue({
      dni: student.dni,
      nombres: student.nombres,
      apellidos: student.apellidos,
      fecha_nacimiento: student.fecha_nacimiento ? dayjs(student.fecha_nacimiento) : null,
      genero: student.genero,
      classroom: student.classroom,
      estado: student.estado,
    });
    apoderadosForm.setFieldsValue({
      apoderados: (student.apoderados || []).map((a) => ({ ...a })),
    });
    fichaForm.setFieldsValue(student.ficha_medica || {});
  }, [student, datosForm, apoderadosForm, fichaForm]);

  const saveDatos = async () => {
    try {
      const values = await datosForm.validateFields();
      setSavingDatos(true);
      const payload = {
        dni: values.dni,
        nombres: values.nombres,
        apellidos: values.apellidos,
        fecha_nacimiento: values.fecha_nacimiento.format("YYYY-MM-DD"),
        genero: values.genero,
        classroom: values.classroom ?? null,
        estado: values.estado,
      };
      await api.patch(`/students/${id}/`, payload);
      message.success("Datos del alumno actualizados");
      setEditingDatos(false);
      fetchAll();
    } catch (err) {
      if (err.response?.data) {
        const flat = Object.values(err.response.data).flat().join(", ");
        message.error(flat);
      }
    } finally {
      setSavingDatos(false);
    }
  };

  const saveApoderados = async () => {
    try {
      const values = await apoderadosForm.validateFields();
      setSavingApoderados(true);
      const payload = {
        apoderados: values.apoderados.map((a, idx) => ({
          ...(a.id ? { id: a.id } : {}),
          dni: a.dni,
          nombres: a.nombres,
          apellidos: a.apellidos,
          telefono: a.telefono,
          email: a.email || null,
          parentesco: a.parentesco,
          es_principal: idx === 0,
        })),
      };
      await api.patch(`/students/${id}/`, payload);
      message.success("Apoderados actualizados");
      setEditingApoderados(false);
      fetchAll();
    } catch (err) {
      if (err.response?.data) {
        const flat = Object.values(err.response.data).flat().join(", ");
        message.error(flat);
      }
    } finally {
      setSavingApoderados(false);
    }
  };

  const fetchPdfBlobUrl = async () => {
    if (!student?.ficha_matricula) return null;
    // Convertir URL absoluta a relativa para que pase por el proxy con JWT
    const path = student.ficha_matricula.replace(/^https?:\/\/[^/]+/, "");
    const res = await api.get(path, { baseURL: "", responseType: "blob" });
    return window.URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
  };

  const handleViewPdf = async () => {
    try {
      const url = await fetchPdfBlobUrl();
      if (!url) return;
      window.open(url, "_blank", "noopener");
      setTimeout(() => window.URL.revokeObjectURL(url), 60000);
    } catch {
      message.error("No se pudo abrir la ficha");
    }
  };

  const handleDownloadPdf = async () => {
    try {
      const url = await fetchPdfBlobUrl();
      if (!url) return;
      const link = document.createElement("a");
      link.href = url;
      link.download = `ficha_matricula_${student.dni}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => window.URL.revokeObjectURL(url), 1000);
      message.success("Ficha descargada");
    } catch {
      message.error("No se pudo descargar la ficha");
    }
  };

  const handleUploadPdf = async (file) => {
    setUploadingPdf(true);
    try {
      const formData = new FormData();
      formData.append("ficha_matricula", file);
      await api.patch(`/students/${id}/`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      message.success("Ficha de matrícula cargada");
      fetchAll();
    } catch (err) {
      const detail = err.response?.data?.detail || "No se pudo subir el PDF";
      message.error(detail);
    } finally {
      setUploadingPdf(false);
    }
    return false; // evita upload automático de Antd
  };

  const handleRemovePdf = async () => {
    setUploadingPdf(true);
    try {
      const formData = new FormData();
      formData.append("ficha_matricula", "");
      await api.patch(`/students/${id}/`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      message.success("Ficha eliminada");
      fetchAll();
    } catch {
      message.error("No se pudo eliminar la ficha");
    } finally {
      setUploadingPdf(false);
    }
  };

  const saveFicha = async () => {
    try {
      const values = await fichaForm.validateFields();
      setSavingFicha(true);
      if (student.ficha_medica?.id) {
        await api.patch(`/students/${id}/medical-record/${student.ficha_medica.id}/`, values);
      } else {
        await api.post(`/students/${id}/medical-record/`, values);
      }
      message.success("Ficha médica guardada");
      fetchAll();
    } catch (err) {
      if (err.response?.data) {
        const flat = Object.values(err.response.data).flat().join(", ");
        message.error(flat);
      }
    } finally {
      setSavingFicha(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: 100 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!student) {
    return (
      <Card>
        <Empty description="Alumno no encontrado" />
        <Button onClick={() => navigate("/alumnos")} style={{ marginTop: 12 }}>
          Volver a la lista
        </Button>
      </Card>
    );
  }

  const estadoCfg = ESTADO_CONFIG[student.estado] || { color: "default", label: student.estado };

  /* ───── Tab: Datos ───── */
  const datosTab = (
    <div>
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 12 }}>
        {!editingDatos ? (
          <Button icon={<EditOutlined />} onClick={() => setEditingDatos(true)}>
            Editar datos
          </Button>
        ) : (
          <Space>
            <Button icon={<CloseOutlined />} onClick={() => {
              setEditingDatos(false);
              datosForm.setFieldsValue({
                dni: student.dni,
                nombres: student.nombres,
                apellidos: student.apellidos,
                fecha_nacimiento: student.fecha_nacimiento ? dayjs(student.fecha_nacimiento) : null,
                genero: student.genero,
                classroom: student.classroom,
                estado: student.estado,
              });
            }}>
              Cancelar
            </Button>
            <Button type="primary" icon={<SaveOutlined />} onClick={saveDatos} loading={savingDatos}>
              Guardar
            </Button>
          </Space>
        )}
      </div>
      <Form form={datosForm} layout="vertical" disabled={!editingDatos}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0 16px" }}>
          <Form.Item name="dni" label="DNI" rules={[{ required: true }, { len: 8, message: "8 dígitos" }]}>
            <Input maxLength={8} />
          </Form.Item>
          <Form.Item name="nombres" label="Nombres" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="apellidos" label="Apellidos" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: "0 16px" }}>
          <Form.Item
            name="fecha_nacimiento"
            label="Fecha de nacimiento"
            rules={[
              { required: true },
              () => ({
                validator(_, value) {
                  if (!value) return Promise.resolve();
                  const edad = dayjs().diff(value, "year");
                  if (edad < 1 || edad > 6) {
                    return Promise.reject(new Error("Edad debe estar entre 1 y 6 años"));
                  }
                  return Promise.resolve();
                },
              }),
            ]}
          >
            <DatePicker format="DD/MM/YYYY" style={{ width: "100%" }} disabledDate={disabledBirthDate} />
          </Form.Item>
          <Form.Item name="genero" label="Género" rules={[{ required: true }]}>
            <Select options={[{ value: "M", label: "Masculino" }, { value: "F", label: "Femenino" }]} />
          </Form.Item>
          <Form.Item name="classroom" label="Aula">
            <Select
              allowClear
              options={classrooms.map((c) => ({
                value: c.id,
                label: `${c.nombre} (${c.nivel_edad} años)`,
              }))}
            />
          </Form.Item>
          <Form.Item name="estado" label="Estado">
            <Select
              options={Object.entries(ESTADO_CONFIG).map(([value, { label }]) => ({ value, label }))}
            />
          </Form.Item>
        </div>
      </Form>

      <Card
        size="small"
        title={
          <Space>
            <FilePdfOutlined style={{ color: "#dc2626" }} />
            <span>Ficha de matrícula (PDF)</span>
          </Space>
        }
        style={{ marginTop: 16 }}
      >
        {student.ficha_matricula ? (
          <Space size="middle" wrap>
            <Button
              type="primary"
              icon={<FileDoneOutlined />}
              onClick={handleViewPdf}
            >
              Ver ficha
            </Button>
            <Button icon={<FilePdfOutlined />} onClick={handleDownloadPdf}>
              Descargar
            </Button>
            <Upload
              accept="application/pdf"
              maxCount={1}
              showUploadList={false}
              beforeUpload={handleUploadPdf}
            >
              <Button icon={<UploadOutlined />} loading={uploadingPdf}>
                Reemplazar
              </Button>
            </Upload>
            <Popconfirm
              title="¿Eliminar la ficha?"
              description="Se borrará el PDF cargado. Podrás subir uno nuevo después."
              onConfirm={handleRemovePdf}
              okText="Sí, eliminar"
              cancelText="Cancelar"
              okButtonProps={{ danger: true }}
            >
              <Button danger icon={<DeleteOutlined />} loading={uploadingPdf}>
                Eliminar
              </Button>
            </Popconfirm>
          </Space>
        ) : (
          <Space direction="vertical" style={{ width: "100%" }}>
            <Text type="secondary" style={{ fontSize: 13 }}>
              Aún no se ha cargado la ficha de matrícula. Sube el PDF firmado por el apoderado.
            </Text>
            <Upload
              accept="application/pdf"
              maxCount={1}
              showUploadList={false}
              beforeUpload={handleUploadPdf}
            >
              <Button type="primary" icon={<UploadOutlined />} loading={uploadingPdf}>
                Subir PDF
              </Button>
            </Upload>
          </Space>
        )}
      </Card>
    </div>
  );

  /* ───── Tab: Apoderados ───── */
  const apoderadosTab = (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
        <Text type="secondary">Mínimo 1, máximo 2. El primero es el contacto principal.</Text>
        {!editingApoderados ? (
          <Button icon={<EditOutlined />} onClick={() => setEditingApoderados(true)}>
            Editar apoderados
          </Button>
        ) : (
          <Space>
            <Button icon={<CloseOutlined />} onClick={() => {
              setEditingApoderados(false);
              apoderadosForm.setFieldsValue({ apoderados: student.apoderados });
            }}>
              Cancelar
            </Button>
            <Button type="primary" icon={<SaveOutlined />} onClick={saveApoderados} loading={savingApoderados}>
              Guardar
            </Button>
          </Space>
        )}
      </div>

      <div style={{ display: editingApoderados ? "none" : "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {(student.apoderados || []).map((a, idx) => (
          <Card
            key={a.id}
            size="small"
            title={
              <Space>
                <Avatar style={{ background: idx === 0 ? "#0d9488" : "#60a5fa" }} icon={<UserOutlined />} />
                <span>{a.nombres} {a.apellidos}</span>
                {idx === 0 && <Tag color="green">Principal</Tag>}
              </Space>
            }
          >
            <Descriptions size="small" column={1}>
              <Descriptions.Item label="DNI">{a.dni}</Descriptions.Item>
              <Descriptions.Item label="Parentesco">
                {PARENTESCO_OPTIONS.find((p) => p.value === a.parentesco)?.label || a.parentesco}
              </Descriptions.Item>
              <Descriptions.Item label="Teléfono">{a.telefono}</Descriptions.Item>
              <Descriptions.Item label="Correo">{a.email || "—"}</Descriptions.Item>
            </Descriptions>
          </Card>
        ))}
        {(!student.apoderados || student.apoderados.length === 0) && (
          <Empty description="Sin apoderados registrados" />
        )}
      </div>

      <Form
        form={apoderadosForm}
        layout="vertical"
        style={{ display: editingApoderados ? "block" : "none" }}
      >
        <Form.List name="apoderados">
          {(fields, { add, remove }) => (
            <>
              {fields.map((field, idx) => (
                <Card
                  key={field.key}
                  size="small"
                  title={
                    <Tag color={idx === 0 ? "green" : "blue"}>
                      {idx === 0 ? "Apoderado principal" : "Segundo apoderado"}
                    </Tag>
                  }
                  extra={
                    fields.length > 1 && (
                      <Button
                        type="text"
                        danger
                        size="small"
                        icon={<DeleteOutlined />}
                        onClick={() => remove(field.name)}
                      />
                    )
                  }
                  style={{ marginBottom: 12 }}
                >
                  <Form.Item name={[field.name, "id"]} hidden><Input /></Form.Item>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 16px" }}>
                    <Form.Item name={[field.name, "dni"]} label="DNI" rules={[{ required: true }, { len: 8, message: "8 dígitos" }]}>
                      <Input maxLength={8} />
                    </Form.Item>
                    <Form.Item name={[field.name, "parentesco"]} label="Parentesco" rules={[{ required: true }]}>
                      <Select options={PARENTESCO_OPTIONS} />
                    </Form.Item>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 16px" }}>
                    <Form.Item name={[field.name, "nombres"]} label="Nombres" rules={[{ required: true }]}>
                      <Input />
                    </Form.Item>
                    <Form.Item name={[field.name, "apellidos"]} label="Apellidos" rules={[{ required: true }]}>
                      <Input />
                    </Form.Item>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 16px" }}>
                    <Form.Item name={[field.name, "telefono"]} label="Teléfono / WhatsApp" rules={[{ required: true }]}>
                      <Input />
                    </Form.Item>
                    <Form.Item name={[field.name, "email"]} label="Correo" rules={[{ type: "email", message: "Correo inválido" }]}>
                      <Input />
                    </Form.Item>
                  </div>
                </Card>
              ))}
              {fields.length < 2 && (
                <Button type="dashed" onClick={() => add({ parentesco: "PADRE" })} block icon={<PlusOutlined />}>
                  Agregar apoderado
                </Button>
              )}
            </>
          )}
        </Form.List>
      </Form>
    </div>
  );

  /* ───── Tab: Ficha Médica ───── */
  const fichaTab = (
    <Form form={fichaForm} layout="vertical" style={{ maxWidth: 720 }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 16px" }}>
        <Form.Item name="tipo_sangre" label="Tipo de sangre">
          <Select allowClear options={TIPO_SANGRE} />
        </Form.Item>
        <Form.Item name="seguro" label="Seguro médico">
          <Input placeholder="Ej: SIS, EsSalud, Pacífico" />
        </Form.Item>
      </div>
      <Form.Item name="hospital_referencia" label="Hospital de referencia">
        <Input />
      </Form.Item>
      <Form.Item name="alergias" label="Alergias">
        <Input.TextArea rows={2} />
      </Form.Item>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 16px" }}>
        <Form.Item name="contacto_emergencia_nombre" label="Contacto de emergencia (nombre)" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="contacto_emergencia_telefono" label="Teléfono de emergencia" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
      </div>
      <Form.Item name="observaciones" label="Observaciones">
        <Input.TextArea rows={3} />
      </Form.Item>
      <Button type="primary" onClick={saveFicha} loading={savingFicha} icon={<SaveOutlined />}>
        Guardar ficha médica
      </Button>
    </Form>
  );

  /* ───── Tab: Matrículas ───── */
  const openNuevaMatricula = () => {
    setEditingMatricula(null);
    matriculaForm.resetFields();
    const ultimoAnio = enrollments.reduce(
      (max, e) => Math.max(max, e.anio_escolar),
      new Date().getFullYear() - 1,
    );
    matriculaForm.setFieldsValue({
      anio_escolar: ultimoAnio + 1,
      classroom: student?.classroom ?? null,
    });
    setMatriculaModalOpen(true);
  };

  const openEditMatricula = (record) => {
    setEditingMatricula(record);
    matriculaForm.resetFields();
    matriculaForm.setFieldsValue({
      anio_escolar: record.anio_escolar,
      classroom: record.classroom,
      costo_matricula: Number(record.costo_matricula),
    });
    setMatriculaModalOpen(true);
  };

  const handleSaveMatricula = async () => {
    try {
      const values = await matriculaForm.validateFields();
      setSavingMatricula(true);
      if (editingMatricula) {
        await api.patch(`/enrollments/${editingMatricula.id}/`, {
          classroom: values.classroom ?? null,
          costo_matricula: values.costo_matricula,
        });
        message.success("Matrícula actualizada");
      } else {
        await api.post(`/enrollments/`, {
          student: Number(id),
          classroom: values.classroom ?? null,
          anio_escolar: values.anio_escolar,
          costo_matricula: values.costo_matricula,
          monto_mensual: values.monto_mensual,
        });
        message.success("Matrícula registrada");
      }
      setMatriculaModalOpen(false);
      fetchAll();
    } catch (err) {
      if (err.response?.data) {
        const flat = Object.values(err.response.data).flat().join(", ");
        message.error(flat || "No se pudo guardar la matrícula");
      }
    } finally {
      setSavingMatricula(false);
    }
  };

  const handleDeleteMatricula = async (record) => {
    try {
      await api.delete(`/enrollments/${record.id}/`);
      message.success("Matrícula eliminada");
      fetchAll();
    } catch {
      message.error("No se pudo eliminar la matrícula");
    }
  };

  const matriculasTab = (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
        <Text type="secondary">
          Matrículas del alumno por año escolar. La nueva matrícula se asigna al próximo año.
        </Text>
        <Button type="primary" icon={<PlusOutlined />} onClick={openNuevaMatricula}>
          Nueva matrícula
        </Button>
      </div>
      <Table
        size="small"
        columns={[
          {
            title: "Año escolar",
            dataIndex: "anio_escolar",
            key: "anio",
            width: 200,
            render: (anio) => {
              const cy = new Date().getFullYear();
              const cfg = anio === cy
                ? { color: "green",   label: "En curso" }
                : anio > cy
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
            title: "Aula",
            dataIndex: "classroom_nombre",
            key: "aula",
            render: (n) => n || <Text type="secondary">Sin aula</Text>,
          },
          {
            title: "Costo matrícula",
            dataIndex: "costo_matricula",
            key: "costo",
            render: (v) => `S/. ${Number(v || 0).toFixed(2)}`,
          },
          {
            title: "Fecha",
            dataIndex: "fecha_matricula",
            key: "fecha",
            width: 110,
          },
          {
            title: "Acciones",
            key: "acciones",
            width: 140,
            render: (_, record) => (
              <Space>
                <Button size="small" icon={<EditOutlined />} onClick={() => openEditMatricula(record)} />
                <Popconfirm
                  title="¿Eliminar esta matrícula?"
                  description="También se eliminarán los pagos asociados."
                  onConfirm={() => handleDeleteMatricula(record)}
                  okText="Sí, eliminar"
                  cancelText="Cancelar"
                  okButtonProps={{ danger: true }}
                >
                  <Button size="small" danger icon={<DeleteOutlined />} />
                </Popconfirm>
              </Space>
            ),
          },
        ]}
        dataSource={enrollments}
        rowKey="id"
        pagination={false}
        locale={{ emptyText: "Sin matrículas registradas" }}
      />
    </div>
  );

  /* ───── Tab: Pensiones ───── */
  const pagosTab = (
    <Table
      size="small"
      columns={[
        { title: "Mes", dataIndex: "mes", key: "mes" },
        { title: "Año", dataIndex: "anio", key: "anio" },
        {
          title: "Monto",
          dataIndex: "monto",
          key: "monto",
          render: (v) => `S/. ${Number(v).toFixed(2)}`,
        },
        {
          title: "Estado",
          dataIndex: "estado",
          key: "estado",
          render: (e) => (
            <Tag color={e === "PAGADO" ? "green" : e === "VENCIDO" ? "red" : "orange"}>{e}</Tag>
          ),
        },
        { title: "Fecha pago", dataIndex: "fecha_pago", key: "fecha_pago", render: (v) => v || "—" },
      ]}
      dataSource={payments}
      rowKey="id"
      pagination={false}
      locale={{ emptyText: "Sin pensiones registradas" }}
    />
  );

  return (
    <div>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate("/alumnos")}
        style={{ marginBottom: 16 }}
      >
        Volver a la lista
      </Button>

      <Card
        style={{
          marginBottom: 16,
          background: "linear-gradient(135deg, #0d9488 0%, #14b8a6 100%)",
          border: "none",
        }}
        styles={{ body: { padding: 24 } }}
      >
        <Space size="large" align="start" style={{ width: "100%" }}>
          <Avatar
            size={88}
            style={{
              background: student.genero === "F" ? "#f472b6" : "#60a5fa",
              fontSize: 36,
              border: "3px solid white",
            }}
          >
            {student.nombres?.[0]}
          </Avatar>
          <div style={{ flex: 1 }}>
            <Title level={3} style={{ color: "white", margin: 0 }}>
              {student.nombres} {student.apellidos}
            </Title>
            <Space size="middle" wrap style={{ marginTop: 8 }}>
              <Tag color="white" style={{ color: "#0d9488", fontWeight: 600 }}>
                DNI {student.dni}
              </Tag>
              <Tag color="white" style={{ color: "#0d9488", fontWeight: 600 }}>
                {student.edad} años
              </Tag>
              <Tag color={estadoCfg.color}>{estadoCfg.label}</Tag>
              {student.classroom_nombre && (
                <Tag color="white" style={{ color: "#0d9488", fontWeight: 600 }}>
                  Aula: {student.classroom_nombre}
                </Tag>
              )}
            </Space>
          </div>
        </Space>
      </Card>

      <Card>
        <Tabs
          defaultActiveKey="datos"
          items={[
            { key: "datos",       forceRender: true, label: <span><UserOutlined /> Datos del alumno</span>, children: datosTab },
            { key: "apoderados",  forceRender: true, label: <span><TeamOutlined /> Apoderados</span>,        children: apoderadosTab },
            { key: "ficha",       forceRender: true, label: <span><HeartOutlined /> Ficha médica</span>,     children: fichaTab },
            { key: "matriculas",  forceRender: true, label: <span><DollarOutlined /> Matrículas</span>,      children: matriculasTab },
            { key: "pagos",       forceRender: true, label: <span><DollarOutlined /> Pensiones</span>,       children: pagosTab },
          ]}
        />
      </Card>

      <Modal
        title={editingMatricula ? "Editar matrícula" : "Nueva matrícula"}
        open={matriculaModalOpen}
        onOk={handleSaveMatricula}
        onCancel={() => { matriculaForm.resetFields(); setMatriculaModalOpen(false); }}
        confirmLoading={savingMatricula}
        okText={editingMatricula ? "Guardar cambios" : "Registrar matrícula"}
        cancelText="Cancelar"
      >
        <Form form={matriculaForm} layout="vertical">
          <Form.Item shouldUpdate noStyle>
            {({ getFieldValue }) => {
              const anio = getFieldValue("anio_escolar");
              const cy = new Date().getFullYear();
              if (!anio || editingMatricula) return null;
              if (anio === cy) {
                return (
                  <Alert
                    type="success"
                    showIcon
                    message="Matrícula del año en curso"
                    description="Si el alumno aún no tiene aula asignada, esta matrícula le asignará una. El aula actual no cambia."
                    style={{ marginBottom: 16 }}
                  />
                );
              }
              if (anio > cy) {
                return (
                  <Alert
                    type="info"
                    showIcon
                    message={`Matrícula adelantada para ${anio}`}
                    description="Reserva el cupo del próximo año. El alumno seguirá en su aula actual hasta que ejecutes la migración anual."
                    style={{ marginBottom: 16 }}
                  />
                );
              }
              return null;
            }}
          </Form.Item>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 16px" }}>
            <Form.Item
              name="anio_escolar"
              label="Año escolar"
              rules={[{ required: true, message: "Ingrese el año" }]}
            >
              <InputNumber
                min={2020}
                max={2040}
                style={{ width: "100%" }}
                disabled={!!editingMatricula}
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
          <Form.Item
            name="classroom"
            label="Aula del año matriculado"
            tooltip="Es el aula donde el alumno cursará ese año escolar. El aula del alumno se actualizará al ejecutar la migración anual."
          >
            <Select
              allowClear
              options={classrooms.map((c) => ({
                value: c.id,
                label: `${c.nombre} (${c.nivel_edad} años)`,
              }))}
            />
          </Form.Item>
          {!editingMatricula && (
            <Form.Item
              name="monto_mensual"
              label="Pensión mensual (S/.)"
              rules={[{ required: true, message: "Ingrese la pensión" }]}
              tooltip="Lo que pagará cada mes durante ese año"
            >
              <InputNumber min={0} step={50} precision={2} style={{ width: "100%" }} />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
}
