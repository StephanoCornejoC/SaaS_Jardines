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
            colorPrimary: "#0d9488",
            colorLink: "#0d9488",
            colorLinkHover: "#0f766e",
            borderRadius: 8,
            borderRadiusLG: 10,
            colorBgLayout: "#f0f2f5",
          },
          components: {
            Menu: {
              darkItemSelectedBg: "#0d9488",
              darkItemSelectedColor: "#ffffff",
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
