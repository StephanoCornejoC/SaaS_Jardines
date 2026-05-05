import { useState, useEffect, useCallback } from "react";
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  Tag,
  Popconfirm,
  App,
  Typography,
} from "antd";
import {
  PlusOutlined,
  SendOutlined,
  EditOutlined,
  MessageOutlined,
  WhatsAppOutlined,
  MailOutlined,
} from "@ant-design/icons";
import api from "../services/api";

const { Title, Text } = Typography;

export default function Communications() {
  const [communications, setCommunications] = useState([]);
  const [classrooms, setClassrooms] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingCommunication, setEditingCommunication] = useState(null);
  const [saving, setSaving] = useState(false);
  const [tipoValue, setTipoValue] = useState("GENERAL");
  const [form] = Form.useForm();
  const { message } = App.useApp();

  const fetchCommunications = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get("/communications/");
      setCommunications(res.data.results || res.data);
    } catch {
      message.error("Error al cargar comunicaciones");
    } finally {
      setLoading(false);
    }
  }, [message]);

  useEffect(() => {
    fetchCommunications();
    const fetchClassrooms = async () => {
      try {
        const res = await api.get("/classrooms/");
        setClassrooms(res.data.results || res.data);
      } catch {
        message.error("Error al cargar aulas");
      }
    };
    fetchClassrooms();
  }, [fetchCommunications, message]);

  const openCreate = () => {
    setEditingCommunication(null);
    form.resetFields();
    form.setFieldsValue({ tipo: "GENERAL" });
    setTipoValue("GENERAL");
    setModalOpen(true);
  };

  const openEdit = (record) => {
    setEditingCommunication(record);
    form.setFieldsValue({
      titulo: record.titulo,
      contenido: record.contenido,
      tipo: record.tipo,
      aula: record.classroom,
    });
    setTipoValue(record.tipo);
    setModalOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      const payload = {
        titulo: values.titulo,
        contenido: values.contenido,
        tipo: values.tipo,
        classroom: values.tipo === "POR_AULA" ? values.aula : null,
      };
      if (editingCommunication) {
        await api.patch(`/communications/${editingCommunication.id}/`, payload);
        message.success("Comunicación actualizada");
      } else {
        await api.post("/communications/", payload);
        message.success("Comunicación creada");
      }
      form.resetFields();
      setModalOpen(false);
      fetchCommunications();
    } catch (err) {
      if (err.response?.data) {
        const errors = Object.values(err.response.data).flat().join(", ");
        message.error(errors);
      }
    } finally {
      setSaving(false);
    }
  };

  const handleSendEmail = async (id) => {
    try {
      const res = await api.post(`/communications/${id}/enviar/`);
      message.success(res.data?.mensaje || "Comunicación enviada por email");
      fetchCommunications();
    } catch (err) {
      const detail = err.response?.data?.error || "Error al enviar la comunicación";
      message.error(detail);
    }
  };

  const handleSendWhatsApp = async (id) => {
    try {
      const res = await api.post(`/communications/${id}/whatsapp/`);
      const enlaces = res.data?.enlaces || [];
      if (enlaces.length === 0) {
        message.warning("No hay teléfonos válidos para enviar");
        return;
      }
      message.success(`Abriendo ${enlaces.length} chat(s) de WhatsApp`);
      enlaces.forEach((e, idx) => {
        setTimeout(() => window.open(e.url, "_blank", "noopener"), idx * 250);
      });
      fetchCommunications();
    } catch (err) {
      const detail = err.response?.data?.error || "Error al generar los enlaces de WhatsApp";
      message.error(detail);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/communications/${id}/`);
      message.success("Comunicación eliminada");
      fetchCommunications();
    } catch {
      message.error("No se pudo eliminar la comunicación");
    }
  };

  const columns = [
    {
      title: "Título",
      dataIndex: "titulo",
      key: "titulo",
      render: (titulo) => <Text strong>{titulo}</Text>,
    },
    {
      title: "Tipo",
      dataIndex: "tipo",
      key: "tipo",
      width: 120,
      render: (tipo) => (
        <Tag color={tipo === "GENERAL" ? "blue" : "purple"}>
          {tipo === "GENERAL" ? "General" : "Por aula"}
        </Tag>
      ),
    },
    {
      title: "Aula",
      dataIndex: "classroom_nombre",
      key: "classroom_nombre",
      render: (nombre) => nombre ?? <Text type="secondary">—</Text>,
    },
    {
      title: "Estado",
      dataIndex: "enviado",
      key: "enviado",
      width: 110,
      render: (enviado) => (
        <Tag color={enviado ? "green" : "orange"}>{enviado ? "Enviado" : "Borrador"}</Tag>
      ),
    },
    {
      title: "Fecha",
      dataIndex: "created_at",
      key: "created_at",
      width: 170,
      render: (val) => val ? new Date(val).toLocaleDateString("es-PE") : "—",
    },
    {
      title: "Creado por",
      dataIndex: "enviado_por_nombre",
      key: "enviado_por_nombre",
      render: (nombre) => nombre ?? <Text type="secondary">—</Text>,
    },
    {
      title: "Acciones",
      key: "acciones",
      width: 280,
      render: (_, record) => (
        <Space wrap>
          {!record.enviado && (
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={() => openEdit(record)}
            >
              Editar
            </Button>
          )}
          <Popconfirm
            title="¿Enviar por correo?"
            description="Se enviará un email a los apoderados con correo registrado."
            onConfirm={() => handleSendEmail(record.id)}
            okText="Enviar"
            cancelText="Cancelar"
            disabled={record.enviado}
          >
            <Button
              type="primary"
              size="small"
              icon={<MailOutlined />}
              disabled={record.enviado}
            >
              Email
            </Button>
          </Popconfirm>
          <Popconfirm
            title="¿Abrir WhatsApp?"
            description="Se abrirá un chat por cada apoderado en pestañas nuevas."
            onConfirm={() => handleSendWhatsApp(record.id)}
            okText="Abrir"
            cancelText="Cancelar"
          >
            <Button
              size="small"
              icon={<WhatsAppOutlined />}
              style={{ background: "#25D366", color: "white", borderColor: "#25D366" }}
            >
              WhatsApp
            </Button>
          </Popconfirm>
          {!record.enviado && (
            <Popconfirm
              title="¿Eliminar esta comunicación?"
              onConfirm={() => handleDelete(record.id)}
              okText="Sí"
              cancelText="No"
              okButtonProps={{ danger: true }}
            >
              <Button size="small" danger>
                Eliminar
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <Title level={4} style={{ margin: 0 }}>
            <MessageOutlined style={{ marginRight: 8, color: "#1677ff" }} />
            Comunicaciones
          </Title>
          <Text type="secondary" style={{ fontSize: 13 }}>
            Avisos y comunicados para los apoderados
          </Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          Nueva Comunicación
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={communications}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20, hideOnSinglePage: true }}
        locale={{ emptyText: "No hay comunicaciones registradas" }}
        scroll={{ x: true }}
      />

      <Modal
        title={editingCommunication ? "Editar comunicación" : "Nueva comunicación"}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => { form.resetFields(); setModalOpen(false); }}
        confirmLoading={saving}
        okText={editingCommunication ? "Guardar cambios" : "Crear"}
        cancelText="Cancelar"
        width={600}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="titulo"
            label="Título"
            rules={[{ required: true, message: "Ingrese el título" }]}
          >
            <Input placeholder="Ej: Reunión de padres - Aula Mariposas" />
          </Form.Item>
          <Form.Item
            name="contenido"
            label="Contenido"
            rules={[{ required: true, message: "Ingrese el contenido" }]}
          >
            <Input.TextArea rows={4} placeholder="Escriba el mensaje que recibirán los apoderados..." />
          </Form.Item>
          <Form.Item
            name="tipo"
            label="Destinatarios"
            rules={[{ required: true, message: "Seleccione el tipo" }]}
          >
            <Select
              onChange={(val) => {
                setTipoValue(val);
                if (val === "GENERAL") {
                  form.setFieldValue("aula", undefined);
                }
              }}
              options={[
                { value: "GENERAL", label: "Todos los apoderados" },
                { value: "POR_AULA", label: "Solo un aula" },
              ]}
            />
          </Form.Item>
          {tipoValue === "POR_AULA" && (
            <Form.Item
              name="aula"
              label="Aula"
              rules={[{ required: true, message: "Seleccione un aula" }]}
            >
              <Select
                placeholder="Seleccione aula"
                options={classrooms.map((c) => ({
                  value: c.id,
                  label: `${c.nombre}${c.nivel_edad ? ` (${c.nivel_edad} años)` : ""}`,
                }))}
              />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
}
