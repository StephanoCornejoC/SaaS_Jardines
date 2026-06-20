import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ConfigProvider, App as AntApp } from "antd";
import esES from "antd/locale/es_ES";
import ErrorBoundary from "./components/ErrorBoundary";
import AppRoutes from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ErrorBoundary>
      <ConfigProvider
        locale={esES}
        theme={{
          token: {
            // Paleta oficial COREM Labs
            colorPrimary: "#028090",      // Teal (hero / primary)
            colorLink: "#028090",
            colorLinkHover: "#0b5d6e",
            colorInfo: "#028090",
            colorTextHeading: "#114B5F",  // Deep Teal para títulos
            borderRadius: 8,
            borderRadiusLG: 10,
            colorBgLayout: "#E6EBE0",     // Mist (fondo de página)
            fontFamily: "Montserrat, 'Segoe UI', system-ui, -apple-system, sans-serif",
          },
          components: {
            Layout: {
              siderBg: "#114B5F",         // Deep Teal (sidebar COREM)
            },
            Menu: {
              // Sidebar deep teal con item activo en CORAL: el combo
              // "coral sobre teal" de la hoja de marca COREM.
              darkItemBg: "#114B5F",
              darkSubMenuItemBg: "#114B5F",
              darkItemColor: "rgba(255,255,255,0.78)",
              darkItemHoverBg: "rgba(255,255,255,0.10)",
              darkItemHoverColor: "#ffffff",
              darkItemSelectedBg: "#F45B69",   // Coral (CTA / activo)
              darkItemSelectedColor: "#ffffff",
              groupTitleColor: "rgba(255,255,255,0.45)",
            },
            Button: {
              borderRadius: 8,
            },
            Table: {
              borderRadius: 8,
              headerBg: "#fafafa",
            },
            Card: {
              borderRadius: 10,
            },
          },
        }}
      >
        <AntApp>
          <BrowserRouter>
            <AppRoutes />
          </BrowserRouter>
        </AntApp>
      </ConfigProvider>
    </ErrorBoundary>
  </React.StrictMode>
);
