import { useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Layout, Menu, Button, Typography, theme, Avatar, Space } from "antd";
import {
  DashboardOutlined,
  TeamOutlined,
  UserOutlined,
  HomeOutlined,
  FormOutlined,
  DollarOutlined,
  WalletOutlined,
  CheckSquareOutlined,
  MessageOutlined,
  FileTextOutlined,
  SwapOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  WhatsAppOutlined,
  MailOutlined,
} from "@ant-design/icons";
import useAuthStore from "../store/authStore";

const { Header, Sider, Content, Footer } = Layout;
const { Text, Link } = Typography;

// Branding del SaaS y datos de soporte. Definidos como constantes para que
// un cambio futuro (ej. número de WhatsApp distinto por release) sea un toque.
const APP_NAME = "Kiddo"; // nombre comercial del SaaS, visible al usuario
const SUPPORT_WHATSAPP_DISPLAY = "+51 940 183 490";
const SUPPORT_WHATSAPP_INTL = "51940183490"; // sin "+", para wa.me
const SUPPORT_EMAIL = "stephano.cornejoc@gmail.com";
const BRAND_NAME = "COREM LABS"; // empresa desarrolladora (atribución en footer)

// Altura aproximada del footer fijo, para reservar espacio inferior del Content
// y evitar que la última fila quede tapada por el footer.
const FOOTER_HEIGHT = 56;

const menuItems = [
  {
    key: "/dashboard",
    icon: <DashboardOutlined />,
    label: "Inicio",
  },
  {
    type: "group",
    label: "Gestión escolar",
    children: [
      { key: "/alumnos",    icon: <TeamOutlined />,   label: "Alumnos"    },
      { key: "/profesores", icon: <UserOutlined />,   label: "Profesores" },
      { key: "/aulas",      icon: <HomeOutlined />,   label: "Aulas"      },
    ],
  },
  {
    type: "group",
    label: "Operaciones",
    children: [
      { key: "/asistencia",     icon: <CheckSquareOutlined />, label: "Asistencia"      },
      { key: "/comunicaciones", icon: <MessageOutlined />,     label: "Comunicaciones"  },
    ],
  },
  {
    type: "group",
    label: "Finanzas",
    children: [
      { key: "/matriculas", icon: <FormOutlined />,   label: "Matrículas" },
      { key: "/pensiones",  icon: <DollarOutlined />, label: "Pensiones"  },
      { key: "/sueldos",    icon: <DollarOutlined />, label: "Sueldos"    },
      { key: "/caja",       icon: <WalletOutlined />, label: "Caja"       },
    ],
  },
  {
    type: "group",
    label: "Administración",
    children: [
      { key: "/reportes",  icon: <FileTextOutlined />, label: "Reportes"         },
      { key: "/migracion", icon: <SwapOutlined />,     label: "Migración anual"  },
    ],
  },
];

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const logout = useAuthStore((s) => s.logout);
  const user = useAuthStore((s) => s.user);
  const { token: { colorBgContainer, borderRadiusLG } } = theme.useToken();

  const selectedKey = `/${location.pathname.split("/")[1]}`;

  const userInitials = user?.nombre
    ? user.nombre.charAt(0).toUpperCase()
    : user?.email?.charAt(0).toUpperCase() ?? "U";

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        breakpoint="lg"
        onBreakpoint={(broken) => setCollapsed(broken)}
        style={{
          overflow: "auto",
          height: "100vh",
          position: "fixed",
          left: 0,
          top: 0,
          bottom: 0,
          boxShadow: "2px 0 8px rgba(0,0,0,0.15)",
        }}
      >
        {/* Logo — wordmark KIDDO en teal del SaaS, sin recuadro */}
        <div
          style={{
            height: 64,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            borderBottom: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          <Text
            strong
            style={{
              color: "#14b8a6",
              fontSize: collapsed ? 20 : 24,
              letterSpacing: collapsed ? 1 : 3,
              textTransform: "uppercase",
              lineHeight: 1,
              fontWeight: 800,
            }}
          >
            {collapsed ? APP_NAME.charAt(0) : APP_NAME}
          </Text>
        </div>

        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 0, paddingTop: 8 }}
        />
      </Sider>

      <Layout style={{ marginLeft: collapsed ? 80 : 200, transition: "margin-left 0.2s" }}>
        <Header
          style={{
            padding: "0 24px",
            background: colorBgContainer,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
            position: "sticky",
            top: 0,
            zIndex: 10,
          }}
        >
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          />
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <Avatar
              size={32}
              style={{ background: "#0d9488", fontSize: 13, cursor: "default" }}
            >
              {userInitials}
            </Avatar>
            <Text style={{ fontSize: 13 }}>{user?.email}</Text>
            <Button
              type="text"
              size="small"
              icon={<LogoutOutlined />}
              onClick={() => { logout(); navigate("/login"); }}
            >
              Salir
            </Button>
          </div>
        </Header>

        <Content
          style={{
            margin: 24,
            // marginBottom extra reserva espacio para el footer fijo, así
            // la última fila de una tabla larga no queda tapada al hacer scroll.
            marginBottom: 24 + FOOTER_HEIGHT,
            padding: 24,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
            minHeight: 360,
          }}
        >
          <Outlet />
        </Content>

        {/*
          Footer FIJO al borde inferior de la viewport (no del documento).
          - `position: fixed` lo mantiene visible aunque el contenido scrollee.
          - `left` cambia con el estado del Sider colapsado.
          - El Content reserva `FOOTER_HEIGHT` de marginBottom para que la
            última fila no quede tapada.
        */}
        <Footer
          style={{
            position: "fixed",
            bottom: 0,
            left: collapsed ? 80 : 200,
            right: 0,
            transition: "left 0.2s",
            textAlign: "center",
            background: colorBgContainer,
            borderTop: "1px solid rgba(0,0,0,0.06)",
            padding: "12px 24px",
            color: "rgba(0,0,0,0.55)",
            fontSize: 12,
            zIndex: 9,
            boxShadow: "0 -1px 4px rgba(0,0,0,0.04)",
          }}
        >
          <Space
            split={
              <span style={{ color: "rgba(0,0,0,0.18)", margin: "0 4px" }}>·</span>
            }
            wrap
            size={[32, 8]}
            style={{ justifyContent: "center", width: "100%" }}
          >
            <Text type="secondary" style={{ fontSize: 12 }}>
              Desarrollado por{" "}
              <Text strong style={{ color: "#0d9488" }}>{BRAND_NAME}</Text>
            </Text>
            <Link
              href={`https://wa.me/${SUPPORT_WHATSAPP_INTL}`}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "rgba(0,0,0,0.55)", fontSize: 12 }}
              aria-label="Soporte por WhatsApp"
            >
              <WhatsAppOutlined style={{ marginRight: 6, color: "#25d366" }} />
              {SUPPORT_WHATSAPP_DISPLAY}
            </Link>
            <Link
              href={`mailto:${SUPPORT_EMAIL}`}
              style={{ color: "rgba(0,0,0,0.55)", fontSize: 12 }}
              aria-label="Soporte por email"
            >
              <MailOutlined style={{ marginRight: 6, color: "#0d9488" }} />
              {SUPPORT_EMAIL}
            </Link>
          </Space>
        </Footer>
      </Layout>
    </Layout>
  );
}
