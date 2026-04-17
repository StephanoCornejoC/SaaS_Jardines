import { useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Layout, Menu, Button, Typography, theme } from "antd";
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
  { key: "/dashboard", icon: <DashboardOutlined />, label: "Dashboard" },
  { key: "/alumnos", icon: <TeamOutlined />, label: "Alumnos" },
  { key: "/profesores", icon: <UserOutlined />, label: "Profesores" },
  { key: "/aulas", icon: <HomeOutlined />, label: "Aulas" },
  { key: "/matriculas", icon: <FormOutlined />, label: "Matriculas" },
  { key: "/pensiones", icon: <DollarOutlined />, label: "Pensiones" },
  { key: "/caja", icon: <WalletOutlined />, label: "Flujo de Caja" },
  { key: "/asistencia", icon: <CheckSquareOutlined />, label: "Asistencia" },
  { key: "/comunicaciones", icon: <MessageOutlined />, label: "Comunicaciones" },
  { key: "/reportes", icon: <FileTextOutlined />, label: "Reportes" },
  { key: "/migracion", icon: <SwapOutlined />, label: "Migracion" },
];

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const logout = useAuthStore((s) => s.logout);
  const user = useAuthStore((s) => s.user);
  const { token: { colorBgContainer, borderRadiusLG } } = theme.useToken();

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        breakpoint="lg"
        onBreakpoint={(broken) => setCollapsed(broken)}
        style={{ overflow: "auto", height: "100vh", position: "fixed", left: 0, top: 0, bottom: 0 }}
      >
        <div style={{ height: 64, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff" }}>
          <Text strong style={{ color: "#fff", fontSize: collapsed ? 14 : 18 }}>
            {collapsed ? "C" : "COREM"}
          </Text>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[`/${location.pathname.split("/")[1]}`]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 200, transition: "all 0.2s" }}>
        <Header
          style={{
            padding: "0 24px",
            background: colorBgContainer,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          />
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <Text>{user?.email}</Text>
            <Button
              type="text"
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
