import { create } from "zustand";
import api from "../services/api";

const parseSafeJSON = (key) => {
  try {
    return JSON.parse(localStorage.getItem(key) || "null");
  } catch {
    localStorage.removeItem(key);
    return null;
  }
};

const useAuthStore = create((set) => ({
  user: parseSafeJSON("user"),
  isAuthenticated: !!localStorage.getItem("access_token"),

  login: async (email, password) => {
    const { data } = await api.post("/auth/token/", { email, password });
    localStorage.setItem("access_token", data.access);
    localStorage.setItem("refresh_token", data.refresh);
    try {
      const userRes = await api.get("/auth/users/me/");
      localStorage.setItem("user", JSON.stringify(userRes.data));
      set({ user: userRes.data, isAuthenticated: true });
    } catch {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      throw new Error("Error al obtener datos del usuario");
    }
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    set({ user: null, isAuthenticated: false });
  },
}));

export default useAuthStore;
