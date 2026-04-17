import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Descriptions,
  Tabs,
  Table,
  Form,
  Input,
  Button,
  Spin,
  Card,
  Tag,
  Space,
  App,
  Typography,
} from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import api from "../services/api";

const { Title } = Typography;

export default function StudentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { message } = App.useApp();

  const [student, setStudent] = useState(null);
  const [apoderados, setApoderados] = useState([]);
  const [fichaMedica, setFichaMedica] = useState({});
  const [historial, setHistorial] = useState([]);
  const [loading, setLoading] = useState(true);
  const [savingFicha, setSavingFicha] = useState(false);
  const [fichaForm] = Form.useForm();

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      try {
        const [studentRes, apoderadosRes, fichaRes] =
          await Promise.allSettled([
            api.get(`/students/${id}/`),
            api.get(`/students/${id}/guardians/`),
            api.get(`/students/${id}/medical-record/`),
          ]);

        if (studentRes.status === "fulfilled") setStudent(studentRes.value.data);
        if (apoderadosRes.status === "fulfilled")
          setApoderados(apoderadosRes.value.data.results || apoderadosRes.value.data);
        if (fichaRes.status === "fulfilled") {
          setFichaMedica(fichaRes.value.data);
          fichaForm.setFieldsValue(fichaRes.value.data);
        }
        // historial endpoint removed - not available in backend
      } catch {
        message.error("Error al cargar datos del alumno");
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, [id, message, fichaForm]);

  const saveFichaMedica = async () => {
    try {
      const values = await fichaForm.validateFields();
      setSavingFicha(true);
      if (fichaMedica.id) {
        await api.patch(`/students/${id}/medical-record/`, values);
      } else {
        await api.post(`/students/${id}/medical-record/`, values);
      }
      message.success("Ficha medica guardada");
    } catch {
      message.error("Error al guardar ficha medica");
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
    return <Typography.Text type="danger">Alumno no encontrado</Typography.Text>;
  }

  const apoderadoColumns = [
    { title: "DNI", dataIndex: "dni", key: "dni" },
    { title: "Nombres", dataIndex: "nombres", key: "nombres" },
    { title: "Apellidos", dataIndex: "apellidos", key: "apellidos" },
    { title: "Parentesco", dataIndex: "parentesco", key: "parentesco" },
    { title: "Telefono", dataIndex: "telefono", key: "telefono" },
    { title: "Email", dataIndex: "email", key: "email" },
  ];

  const historialColumns = [
    { title: "Fecha", dataIndex: "fecha", key: "fecha" },
    { title: "Tipo", dataIndex: "tipo", key: "tipo" },
    { title: "Descripcion", dataIndex: "descripcion", key: "descripcion" },
    { title: "Usuario", dataIndex: "usuario", key: "usuario" },
  ];

  const tabItems = [
    {
      key: "apoderados",
      label: "Apoderados",
      children: (
        <Table
          columns={apoderadoColumns}
          dataSource={apoderados}
          rowKey="id"
          pagination={false}
        />
      ),
    },
    {
      key: "ficha-medica",
      label: "Ficha Medica",
      children: (
        <Form form={fichaForm} layout="vertical" style={{ maxWidth: 600 }}>
          <Form.Item name="alergias" label="Alergias">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="condiciones_medicas" label="Condiciones Medicas">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="medicamentos" label="Medicamentos">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="tipo_sangre" label="Tipo de Sangre">
            <Input style={{ width: 120 }} />
          </Form.Item>
          <Form.Item name="contacto_emergencia" label="Contacto de Emergencia">
            <Input />
          </Form.Item>
          <Form.Item name="telefono_emergencia" label="Telefono Emergencia">
            <Input />
          </Form.Item>
          <Form.Item name="observaciones" label="Observaciones">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" onClick={saveFichaMedica} loading={savingFicha}>
              Guardar Ficha Medica
            </Button>
          </Form.Item>
        </Form>
      ),
    },
    {
      key: "historial",
      label: "Historial",
      children: (
        <Table
          columns={historialColumns}
          dataSource={historial}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      ),
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/alumnos")}>
          Volver
        </Button>
        <Title level={4} style={{ margin: 0 }}>
          {student.nombres} {student.apellidos}
        </Title>
      </Space>

      <Card style={{ marginBottom: 24 }}>
        <Descriptions bordered column={{ xs: 1, sm: 2, lg: 3 }}>
          <Descriptions.Item label="DNI">{student.dni}</Descriptions.Item>
          <Descriptions.Item label="Nombres">{student.nombres}</Descriptions.Item>
          <Descriptions.Item label="Apellidos">{student.apellidos}</Descriptions.Item>
          <Descriptions.Item label="Fecha de Nacimiento">
            {student.fecha_nacimiento}
          </Descriptions.Item>
          <Descriptions.Item label="Edad">{student.edad}</Descriptions.Item>
          <Descriptions.Item label="Genero">{student.genero}</Descriptions.Item>
          <Descriptions.Item label="Aula">{student.aula_nombre}</Descriptions.Item>
          <Descriptions.Item label="Estado">
            <Tag color={student.estado === "ACTIVO" ? "green" : "red"}>
              {student.estado}
            </Tag>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card>
        <Tabs items={tabItems} />
      </Card>
    </div>
  );
}
