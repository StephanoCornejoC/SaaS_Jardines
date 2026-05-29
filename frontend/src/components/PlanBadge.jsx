import { useEffect, useState } from "react";
import { Skeleton, Space, Tooltip, Typography } from "antd";
import { CrownOutlined } from "@ant-design/icons";
import api from "../services/api";

const { Text } = Typography;

/**
 * Píldora elegante con el plan vigente del jardín, pensada para mostrarse
 * en el header al lado del botón de despliegue del menú.
 *
 * - Llama una sola vez al endpoint `/platform/tier-status/` al montar.
 * - Si falla o aún no resolvió: skeleton sutil, no rompe el layout.
 * - El color cambia según el tier para que sea reconocible de un vistazo
 *   sin saturar visualmente.
 * - Al hacer hover muestra detalle: alumnos actuales / límite del plan.
 */

const TIER_STYLES = {
  mini: { color: "#0d9488", bg: "#ccfbf1", border: "#5eead4" },
  plus: { color: "#1d4ed8", bg: "#dbeafe", border: "#93c5fd" },
  pro:  { color: "#7c3aed", bg: "#ede9fe", border: "#c4b5fd" },
  max:  { color: "#b45309", bg: "#fef3c7", border: "#fcd34d" },
  default: { color: "#475569", bg: "#f1f5f9", border: "#cbd5e1" },
};

export default function PlanBadge() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    api
      .get("/platform/tier-status/")
      .then((res) => {
        if (!cancelled) setData(res.data);
      })
      .catch(() => {
        // Silenciar: si el endpoint no resuelve, simplemente no mostramos
        // la pildora. No queremos ensuciar el header con un mensaje de
        // error técnico para la directora.
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <Skeleton.Button
        active
        size="small"
        style={{ width: 110, height: 28, borderRadius: 14 }}
      />
    );
  }

  if (!data || !data.plan || !data.plan.nombre) {
    return null;
  }

  const style = TIER_STYLES[data.plan.slug] || TIER_STYLES.default;
  const limite = data.plan.alumnos_max ? `${data.alumnos_activos}/${data.plan.alumnos_max}` : data.alumnos_activos;
  const tooltipTexto = data.plan.alumnos_max
    ? `${data.alumnos_activos} de ${data.plan.alumnos_max} alumnos · S/${data.plan.precio_acordado}/mes`
    : `${data.alumnos_activos} alumnos · S/${data.plan.precio_acordado}/mes`;

  return (
    <Tooltip title={tooltipTexto} placement="bottom">
      <Space
        size={6}
        align="center"
        style={{
          background: style.bg,
          color: style.color,
          border: `1px solid ${style.border}`,
          padding: "4px 12px",
          borderRadius: 999,
          fontSize: 12,
          fontWeight: 600,
          lineHeight: 1.2,
          cursor: "default",
          userSelect: "none",
        }}
      >
        <CrownOutlined style={{ fontSize: 12, color: style.color }} />
        <Text style={{ color: style.color, fontWeight: 600, fontSize: 12 }}>
          Plan {data.plan.nombre}
        </Text>
        <Text style={{ color: style.color, opacity: 0.7, fontSize: 11 }}>
          · {limite}
        </Text>
      </Space>
    </Tooltip>
  );
}
