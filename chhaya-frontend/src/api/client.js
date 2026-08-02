import axios from "axios";

/*
  One axios instance, imported everywhere else. Two jobs done here so no
  other file has to think about them again:
    1. baseURL -- comes from VITE_API_BASE_URL so switching from local dev
       to a deployed backend is a one-line .env change, not a find/replace.
    2. auth header -- every outgoing request automatically gets the saved
       JWT attached, and a 401 response automatically logs the user out.
*/

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("chhaya_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("chhaya_token");
      localStorage.removeItem("chhaya_user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default client;
