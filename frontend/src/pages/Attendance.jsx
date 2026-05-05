import { useState, useEffect, useCallback } from "react";
import {
  Table,
  Button,
  Select,
  DatePicker,
  Space,
  Card,
  Tag,
  Alert,
  App,
  Typography,
} from "antd";
import {
  SaveOutlined,
  EditOutlined,
  CheckCircleOutlined,
  LockOutlined,
  CalendarOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";
import api from "../services/api";

const { Title, Text } = Typography;

const ESTADO_CONFIG = {
  PRESENTE:    { color: "green",  label: "Presente"    },
  AUSENTE:     { color: "red",    label: "Ausente"     },
  TARDANZA:    { color: "orange", label: "Tardanza"    },
  JUSTIFICADO: { color: "blue",   label: "Justificado" },
};

const estadoOptions = Object.entries(ESTADO_CONFIG).map(([value, { label }]) => ({
  value,
  label,
}));

export default function Attendance() {
  const [classrooms, setClassrooms] = useState([]);
  const [selectedClassroom, setSelectedClassroom] = useState(undefined);
  const [selectedDate, setSelectedDate] = useState(dayjs());
  const [students, setStudents] = useState([]);
  const [attendanceData, setAttendanceData] = useState({});
  const [hasRecords, setHasRecords] = useState(false);
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const { message } = App.useApp();

  useEffect(() => {
    const fetchClassrooms = async () => {
      try {
        const res = await api.get("/classrooms/");
        setClassrooms(res.data.results || res.data);
      } catch {
        message.error("Error al cargar aulas");
      }
    };
    fetchClassrooms();
  }, [message]);

  const fetchAttendance = useCallback(async () => {
    if (!selectedClassroom || !selectedDate) return;
    setLoading(true);
    try {
      const fecha = selectedDate.format("YYYY-MM-DD");
      const [resAtt, resStud] = await Promise.all([
        api.get("/attendance/", { params: { classroom: selectedClassroom, fecha } }),
        api.get("/students/", { params: { classroom: selectedClassroom, estado: "ACTIVO" } }),
      ]);
      const data = resAtt.data.results || resAtt.data;
      const map = {};
      data.forEach((record) => {
        map[record.student] = record.estado;
      });
      setAttendanceData(map);
      setHasRecords(data.length > 0);
      setEditing(data.length === 0);   // si no hay registros aún, comienza en modo edición
      setStudents(resStud.data.results || resStud.data);
    } catch {
      message.error("Error al cargar asistencia");
    } finally {
      setLoading(false);
    }
  }, [selectedClassroom, selectedDate, message]);

  useEffect(() => { fetchAttendance(); }, [fetchAttendance]);

  const handleEstadoChange = (studentId, value) => {
    setAttendanceData((prev) => ({ ...prev, [studentId]: value }));
  };

  const handleSave = async () => {
    if (!selectedClassroom || !selectedDate) {
      message.warning("Seleccione aula y fecha");
      return;
    }
    const asistencias = students.map((s) => ({
      student_id: s.id,
      estado: attendanceData[s.id] || "PRESENTE",
    }));
    setSaving(true);
    try {
      await api.post("/attendance/registro-masivo/", {
        classroom_id: selectedClassroom,
        fecha: selectedDate.format("YYYY-MM-DD"),
        asistencias,
      });
      message.success(hasRecords ? "Asistencia actualizada" : "Asistencia registrada");
      setEditing(false);
      fetchAttendance();
    } catch (err) {
      const detail = err.response?.data?.detail || "Error al guardar asistencia";
      message.error(detail);
    } finally {
      setSaving(false);
    }
  };

  const columns = [
    {
      title: "#",
      key: "index",
      width: 50,
      render: (_, __, index) => index + 1,
    },
    { title: "DNI", dataIndex: "dni", key: "dni", width: 110 },
    {
      title: "Alumno",
      key: "nombre",
      render: (_, record) => `${record.apellidos}, ${record.nombres}`,
    },
    {
      title: "Estado",
      key: "estado",
      width: 200,
      render: (_, record) => {
        const value = attendanceData[record.id] || "PRESENTE";
        if (!editing) {
          const cfg = ESTADO_CONFIG[value] || { color: "default", label: value };
          return <Tag color={cfg.color}>{cfg.label}</Tag>;
        }
        return (
          <Select
            value={value}
            onChange={(v) => handleEstadoChange(record.id, v)}
            options={estadoOptions}
            style={{ width: 170 }}
          />
        );
      },
    },
  ];

  const isToday = selectedDate?.isSame(dayjs(), "day");

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>
          <CalendarOutlined style={{ marginRight: 8, color: "#0d9488" }} />
          Asistencia
        </Title>
        <Text type="secondary" style={{ fontSize: 13 }}>
          Marca la asistencia diaria del aula. Una vez guardada, queda bloqueada hasta que pulses "Editar".
        </Text>
      </div>

      <Card style={{ marginBottom: 16 }} styles={{ body: { padding: 16 } }}>
        <Space size="large" wrap>
          <div>
            <Text strong style={{ display: "block", marginBottom: 4, fontSize: 12 }}>
              Aula
            </Text>
            <Select
              placeholder="Seleccione aula"
              value={selectedClassroom}
              onChange={setSelectedClassroom}
              style={{ width: 240 }}
              options={classrooms.map((c) => ({
                value: c.id,
                label: `${c.nombre} (${c.nivel_edad} años)`,
              }))}
            />
          </div>
          <div>
            <Text strong style={{ display: "block", marginBottom: 4, fontSize: 12 }}>
              Fecha
            </Text>
            <DatePicker
              value={selectedDate}
              onChange={setSelectedDate}
              format="DD/MM/YYYY"
              allowClear={false}
            />
          </div>
          <div style={{ alignSelf: "flex-end" }}>
            {!editing && hasRecords ? (
              <Button icon={<EditOutlined />} onClick={() => setEditing(true)}>
                Editar asistencia
              </Button>
            ) : (
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleSave}
                loading={saving}
                disabled={!selectedClassroom || students.length === 0}
              >
                Guardar asistencia
              </Button>
            )}
          </div>
        </Space>
      </Card>

      {hasRecords && !editing && (
        <Alert
          type="success"
          showIcon
          icon={<CheckCircleOutlined />}
          message={
            <span>
              Asistencia registrada para <b>{selectedDate?.format("DD/MM/YYYY")}</b>{isToday ? " (hoy)" : ""}.
              Pulsa <b>"Editar asistencia"</b> si necesitas justificar tardanzas o ausencias.
            </span>
          }
          style={{ marginBottom: 16 }}
        />
      )}

      {!hasRecords && !loading && students.length > 0 && (
        <Alert
          type="info"
          showIcon
          icon={<LockOutlined />}
          message="Aún no se ha registrado asistencia para esta fecha. Marca a cada alumno y pulsa Guardar."
          style={{ marginBottom: 16 }}
        />
      )}

      <Table
        columns={columns}
        dataSource={students}
        rowKey="id"
        loading={loading}
        pagination={false}
        locale={{ emptyText: selectedClassroom ? "El aula no tiene alumnos" : "Seleccione un aula para ver los alumnos" }}
      />
    </div>
  );
}
