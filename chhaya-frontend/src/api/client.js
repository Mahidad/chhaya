import axios from "axios";   // library used to make http requests. Axios also automatically converts JSON responses into JavaScript objects. It is also used for sending HTTP requests to a server and receiving responses.

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",  //This reads an environment variable from your .env file.
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
    if (error.response?.status === 401) {      //"You are not logged in."
      localStorage.removeItem("chhaya_token");
      localStorage.removeItem("chhaya_user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default client;
