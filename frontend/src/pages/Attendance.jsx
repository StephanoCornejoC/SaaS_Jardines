import { useState, useEffect } from "react";
import {
  Table,
  Button,
  Select,
  DatePicker,
  Space,
  Card,
  App,
  Typography,
} from "antd";
import { SaveOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import api from "../services/api";

const { Title } = Typography;

const estadoOptions = [
  { value: "PRESENTE", label: "Presente" },
  { value: "AUSENTE", label: "Ausente" },
  { value: "TARDANZA", label: "Tardanza" },
  { value: "JUSTIFICADO", label: "Justificado" },
];

export default function Attendance() {
  const [classrooms, setClassrooms] = useState([]);
  const [selectedClassroom, setSelectedClassroom] = useState(undefined);
  const [selectedDate, setSelectedDate] = useState(dayjs());
  const [students, setStudents] = useState([]);
  const [attendanceData, setAttendanceData] = useState({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const { message } = App.useApp();

  useEffect(() => {
    const fetchClassrooms = async () => {
      try {
        const res = await api.get("/classrooms/", { params: { estado: "ACTIVO" } });
        setClassrooms(res.data.results || res.data);
      } catch {
        message.error("Error al cargar aulas");
      }
    };
    fetchClassrooms();
  }, [message]);

  useEffect(() => {
    if (!selectedClassroom || !selectedDate) return;

    const fetchAttendance = async () => {
      setLoading(true);
      try {
        const fecha = selectedDate.format("YYYY-MM-DD");
        const res = await api.get("/attendance/", {
          params: { classroom: selectedClassroom, fecha },
        });
        const data = res.data.results || res.data;

        // Build attendance map from existing records
        const map = {};
        data.forEach((record) => {
          map[record.alumno] = record.estado;
        });
        setAttendanceData(map);

        // Get students for the classroom
        const studRes = await api.get("/students/", {
          params: { classroom: selectedClassroom, estado: "ACTIVO" },
        });
        setStudents(studRes.data.results || studRes.data);
      } catch {
        message.error("Error al cargar asistencia");
      } finally {
        setLoading(false);
      }
    };
    fetchAttendance();
  }, [selectedClassroom, selectedDate, message]);

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
      message.success("Asistencia guardada");
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
    { title: "DNI", dataIndex: "dni", key: "dni", width: 100 },
    {
      title: "Alumno",
      key: "nombre",
      render: (_, record) => `${record.nombres} ${record.apellidos}`,
    },
    {
      title: "Estado",
      key: "estado",
      width: 180,
      render: (_, record) => (
        <Select
          value={attendanceData[record.id] || "PRESENTE"}
          onChange={(value) => handleEstadoChange(record.id, value)}
          options={estadoOptions}
          style={{ width: 160 }}
        />
      ),
    },
  ];

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>
        Asistencia
      </Title>

      <Card style={{ marginBottom: 16 }}>
        <Space size="large">
          <div>
            <Typography.Text strong style={{ display: "block", marginBottom: 4 }}>
              Aula
            </Typography.Text>
            <Select
              placeholder="Seleccione aula"
              value={selectedClassroom}
              onChange={setSelectedClassroom}
              style={{ width: 250 }}
              options={classrooms.map((c) => ({
                value: c.id,
                label: `${c.nombre} (${c.nivel})`,
              }))}
            />
          </div>
          <div>
            <Typography.Text strong style={{ display: "block", marginBottom: 4 }}>
              Fecha
            </Typography.Text>
            <DatePicker
              value={selectedDate}
              onChange={setSelectedDate}
              format="DD/MM/YYYY"
            />
          </div>
          <div style={{ alignSelf: "flex-end" }}>
            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={handleSave}
              loading={saving}
              disabled={!selectedClassroom || students.length === 0}
            >
              Guardar Asistencia
            </Button>
          </div>
        </Space>
      </Card>

      <Table
        columns={columns}
        dataSource={students}
        rowKey="id"
        loading={loading}
        pagination={false}
        locale={{ emptyText: "Seleccione un aula para ver los alumnos" }}
      />
    </div>
  );
}
