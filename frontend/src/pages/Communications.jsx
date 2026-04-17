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
import { PlusOutlined, SendOutlined } from "@ant-design/icons";
import api from "../services/api";

const { Title } = Typography;

export default function Communications() {
  const [communications, setCommunications] = useState([]);
  const [classrooms, setClassrooms] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
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
        const res = await api.get("/classrooms/", { params: { estado: "ACTIVO" } });
        setClassrooms(res.data.results || res.data);
      } catch {
        message.error("Error al cargar aulas");
      }
    };
    fetchClassrooms();
  }, [fetchCommunications, message]);

  const openCreate = () => {
    form.resetFields();
    setTipoValue("GENERAL");
    setModalOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      await api.post("/communications/", values);
      message.success("Comunicacion creada");
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

  const handleSend = async (id) => {
    try {
      await api.post(`/communications/${id}/enviar/`);
      message.success("Comunicacion enviada");
      fetchCommunications();
    } catch {
      message.error("Error al enviar comunicacion");
    }
  };

  const columns = [
    { title: "Titulo", dataIndex: "titulo", key: "titulo" },
    {
      title: "Tipo",
      dataIndex: "tipo",
      key: "tipo",
      render: (tipo) => (
        <Tag color={tipo === "GENERAL" ? "blue" : "purple"}>{tipo}</Tag>
      ),
    },
    { title: "Aula", dataIndex: "aula_nombre", key: "aula_nombre" },
    {
      title: "Estado",
      dataIndex: "estado",
      key: "estado",
      render: (estado) => (
        <Tag color={estado === "ENVIADO" ? "green" : "orange"}>{estado}</Tag>
      ),
    },
    { title: "Fecha", dataIndex: "fecha_creacion", key: "fecha_creacion" },
    { title: "Creado por", dataIndex: "creado_por_nombre", key: "creado_por_nombre" },
    {
      title: "Acciones",
      key: "acciones",
      render: (_, record) => (
        <Space>
          {record.estado !== "ENVIADO" && (
            <Popconfirm
              title="Enviar esta comunicacion?"
              onConfirm={() => handleSend(record.id)}
            >
              <Button type="primary" size="small" icon={<SendOutlined />}>
                Enviar
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>
          Comunicaciones
        </Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          Nueva Comunicacion
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={communications}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20 }}
      />

      <Modal
        title="Nueva Comunicacion"
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        confirmLoading={saving}
        destroyOnClose
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="titulo"
            label="Titulo"
            rules={[{ required: true, message: "Ingrese el titulo" }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="contenido"
            label="Contenido"
            rules={[{ required: true, message: "Ingrese el contenido" }]}
          >
            <Input.TextArea rows={4} />
          </Form.Item>
          <Form.Item
            name="tipo"
            label="Tipo"
            rules={[{ required: true, message: "Seleccione el tipo" }]}
            initialValue="GENERAL"
          >
            <Select
              onChange={(val) => setTipoValue(val)}
              options={[
                { value: "GENERAL", label: "General" },
                { value: "POR_AULA", label: "Por Aula" },
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
                  label: `${c.nombre} (${c.nivel})`,
                }))}
              />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
}
