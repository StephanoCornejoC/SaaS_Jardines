import { useEffect, useState } from "react";
import { Alert, Button, Space } from "antd";
import { WhatsAppOutlined } from "@ant-design/icons";
import api from "../services/api";

// Mismos datos de soporte que MainLayout. Si en el futuro centralizamos
// estos valores en un módulo, importarlos desde ahí también.
const SUPPORT_WHATSAPP_INTL = "51940183490";

/**
 * Banner discreto en español neutro peruano formal que avisa a la directora
 * cuando su jardín superó el límite de alumnos del plan contratado.
 *
 * Reglas:
 *  - Solo se muestra si el backend reporta excede_limite=true.
 *  - No bloquea ninguna acción del SaaS (es soft-info, no hard-block).
 *  - El botón abre WhatsApp con un mensaje pre-llenado para que la directora
 *    no tenga que redactar nada.
 *  - Si el endpoint falla o devuelve 4xx, no renderiza nada (no alarmar al
 *    usuario por un problema de infraestructura).
 *
 * Llamada al endpoint: una sola vez al montar el layout. No hay polling.
 * Si la directora carga un alumno nuevo y supera el límite, el banner
 * aparecerá en el próximo refresh — aceptable para esta primera versión.
 */
export default function TierExcessBanner() {
  const [data, setData] = useState(null);

  useEffect(() => {
    let cancelled = false;
    api
      .get("/platform/tier-status/")
      .then((res) => {
        if (!cancelled) setData(res.data);
      })
      .catch(() => {
        // Silenciar errores: este banner es informativo. Si el endpoint
        // falla, no tiene sentido mostrarle un cartel rojo a la directora.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!data || !data.excede_limite) {
    return null;
  }

  const { plan, alumnos_activos, tier_correcto } = data;

  const sugerencia = tier_correcto
    ? ` Le sugerimos actualizar al plan ${tier_correcto.nombre} (${tier_correcto.rango}).`
    : "";

  const mensaje = (
    <>
      Su jardín registra <strong>{alumnos_activos} alumnos activos</strong>,
      por encima del límite de <strong>{plan.alumnos_max}</strong> incluidos
      en el plan <strong>{plan.nombre}</strong>.{sugerencia} Por favor coordine
      con soporte la actualización de su plan.
    </>
  );

  const whatsappTexto = encodeURIComponent(
    `Hola, le escribo desde mi jardín porque registramos ${alumnos_activos} alumnos activos y supera el límite del plan ${plan.nombre}. ` +
      `Quisiera coordinar la actualización de mi plan.`
  );
  const whatsappUrl = `https://wa.me/${SUPPORT_WHATSAPP_INTL}?text=${whatsappTexto}`;

  return (
    <Alert
      type="warning"
      showIcon
      message="Su plan actual está por debajo de la cantidad de alumnos del jardín"
      description={mensaje}
      action={
        <Space direction="vertical">
          <Button
            size="small"
            type="primary"
            icon={<WhatsAppOutlined />}
            href={whatsappUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{ background: "#25d366", borderColor: "#25d366" }}
          >
            Contactar soporte
          </Button>
        </Space>
      }
      style={{ marginBottom: 16 }}
    />
  );
}
