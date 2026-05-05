import { useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Layout, Menu, Button, Typography, theme, Avatar } from "antd";
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
} from "@ant-design/icons";
import useAuthStore from "../store/authStore";

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

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
        {/* Logo */}
        <div
          style={{
            height: 64,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            borderBottom: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background: "#0d9488",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              marginRight: collapsed ? 0 : 10,
              flexShrink: 0,
            }}
          >
            <Text strong style={{ color: "#fff", fontSize: 15, lineHeight: 1 }}>C</Text>
          </div>
          {!collapsed && (
            <Text strong style={{ color: "#fff", fontSize: 17, letterSpacing: 1 }}>
              COREM
            </Text>
          )}
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
            padding: 24,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
            minHeight: 360,
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
