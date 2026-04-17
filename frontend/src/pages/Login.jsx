import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Form, Input, Button, Card, Typography, App } from "antd";
import { UserOutlined, LockOutlined } from "@ant-design/icons";
import useAuthStore from "../store/authStore";

const { Title } = Typography;

export default function Login() {
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();
  const { message } = App.useApp();

  const onFinish = async (values) => {
    setLoading(true);
    try {
      await login(values.email, values.password);
      message.success("Bienvenido");
      navigate("/dashboard", { replace: true });
    } catch (err) {
      if (!err.response) {
        message.error("Error de conexion. Verifique su internet.");
      } else if (err.response.status === 401) {
        message.error(err.response.data?.detail || "Credenciales incorrectas");
      } else {
        message.error("Error del servidor. Intente nuevamente.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "100vh",
        background: "#f0f2f5",
      }}
    >
      <Card style={{ width: 400, boxShadow: "0 2px 8px rgba(0,0,0,0.15)" }}>
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <Title level={3} style={{ marginBottom: 4 }}>
            SAAS COREM
          </Title>
          <Typography.Text type="secondary">
            Sistema de Gestion de Centro Educativo
          </Typography.Text>
        </div>

        <Form
          name="login"
          layout="vertical"
          onFinish={onFinish}
          autoComplete="off"
        >
          <Form.Item
            name="email"
            label="Correo electronico"
            rules={[
              { required: true, message: "Ingrese su correo" },
              { type: "email", message: "Correo no valido" },
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="correo@ejemplo.com"
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="password"
            label="Contrasena"
            rules={[{ required: true, message: "Ingrese su contrasena" }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Contrasena"
              size="large"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              size="large"
            >
              Iniciar Sesion
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
