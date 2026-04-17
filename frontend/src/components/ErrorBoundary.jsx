import { Component } from "react";
import { Button, Result } from "antd";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary:", error, errorInfo);
  }

  handleReload = () => {
    this.setState({ hasError: false });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
          <Result
            status="error"
            title="Algo salio mal"
            subTitle="Ocurrio un error inesperado. Intente recargar la pagina."
            extra={
              <Button type="primary" onClick={this.handleReload}>
                Recargar pagina
              </Button>
            }
          />
        </div>
      );
    }

    return this.props.children;
  }
}
