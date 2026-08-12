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
    if (error.response?.status === 401) {
      // Don't auto-redirect for login/signup requests -- let the page
      // show the real error ("wrong password") instead of silently
      // clearing the token and bouncing to /login in a loop.
      const url = error.config?.url || "";
      const isAuthRoute = url.includes("/auth/login") || url.includes("/auth/signup");
      if (!isAuthRoute) {
        localStorage.removeItem("chhaya_token");
        localStorage.removeItem("chhaya_user");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default client;
