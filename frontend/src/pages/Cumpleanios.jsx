import { useEffect, useMemo, useState } from "react";
import {
  Card,
  Col,
  DatePicker,
  Empty,
  Row,
  Skeleton,
  Space,
  Tag,
  Typography,
} from "antd";
import { GiftOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import "dayjs/locale/es";
import api from "../services/api";

dayjs.locale("es");

const { Title, Text } = Typography;

/**
 * Módulo "Cumpleaños del mes".
 *
 * Lista los alumnos activos que cumplen años en un mes determinado,
 * ordenados por día. Pensado como módulo personal de la directora para
 * mantener un detalle con los apoderados (saludar, organizar paseo, etc.).
 *
 * El backend filtra solo alumnos activos y devuelve un payload simple
 * (`/api/v1/students/cumpleanios/?mes=N`). No es accesible para profesoras.
 */
export default function Cumpleanios() {
  const [mes, setMes] = useState(dayjs());
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .get("/students/cumpleanios/", { params: { mes: mes.month() + 1 } })
      .then((res) => setData(res.data))
      .catch((err) => {
        setError(
          err?.response?.data?.detail || "No se pudo cargar la lista de cumpleaños."
        );
        setData(null);
      })
      .finally(() => setLoading(false));
  }, [mes]);

  const hoy = useMemo(() => dayjs(), []);

  return (
    <div>
      <Space style={{ marginBottom: 16 }} align="center">
        <GiftOutlined style={{ fontSize: 24, color: "#0d9488" }} />
        <Title level={3} style={{ margin: 0 }}>
          Cumpleaños del mes
        </Title>
      </Space>

      <Card style={{ marginBottom: 16 }}>
        <Space direction="vertical" size={4}>
          <Text type="secondary">Mes a consultar</Text>
          <DatePicker.MonthPicker
            value={mes}
            onChange={(v) => v && setMes(v)}
            allowClear={false}
            format="MMMM YYYY"
          />
        </Space>
      </Card>

      {loading && (
        <Card>
          <Skeleton active paragraph={{ rows: 4 }} />
        </Card>
      )}

      {!loading && error && (
        <Card>
          <Text type="danger">{error}</Text>
        </Card>
      )}

      {!loading && !error && data && data.total === 0 && (
        <Card>
          <Empty
            description={`No hay alumnos que cumplan en ${data.mes_nombre}.`}
          />
        </Card>
      )}

      {!loading && !error && data && data.total > 0 && (
        <>
          <Text type="secondary" style={{ display: "block", marginBottom: 12 }}>
            {data.total} alumno(s) cumplen en {data.mes_nombre}.
          </Text>
          <Row gutter={[16, 16]}>
            {data.cumpleanios.map((alumno) => {
              const fechaEsteAnio = dayjs(alumno.cumple_este_anio);
              const esHoy = fechaEsteAnio.isSame(hoy, "day");
              const yaPaso = fechaEsteAnio.isBefore(hoy, "day");
              return (
                <Col key={alumno.id} xs={24} sm={12} md={8} lg={6}>
                  <Card
                    hoverable
                    style={{
                      borderColor: esHoy ? "#0d9488" : undefined,
                      borderWidth: esHoy ? 2 : 1,
                    }}
                    styles={{ body: { padding: 16 } }}
                  >
                    <Space direction="vertical" size={4} style={{ width: "100%" }}>
                      <Space style={{ width: "100%", justifyContent: "space-between" }}>
                        <Text strong style={{ fontSize: 16 }}>
                          {alumno.nombres} {alumno.apellidos}
                        </Text>
                        {esHoy && <Tag color="#0d9488">¡Hoy!</Tag>}
                        {yaPaso && !esHoy && <Tag color="default">Ya pasó</Tag>}
                      </Space>
                      <Text type="secondary">
                        {fechaEsteAnio.format("DD [de] MMMM")}
                      </Text>
                      <Text>
                        Cumple <strong>{alumno.edad_que_cumple}</strong> años
                      </Text>
                      {alumno.classroom_nombre && (
                        <Tag color="blue">{alumno.classroom_nombre}</Tag>
                      )}
                    </Space>
                  </Card>
                </Col>
              );
            })}
          </Row>
        </>
      )}
    </div>
  );
}
