import client from "./client";

export async function signup({ fullName, email, password }) {
  const { data } = await client.post("/auth/signup", {
    full_name: fullName,
    email,
    password,
  });
  return data;
}

export async function login({ email, password }) {
  // The backend's /auth/login expects OAuth2 form fields (username, password),
  // not JSON -- see the comment in app/api/v1/endpoints/auth.py for why.
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);
  const { data } = await client.post("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data; // { access_token, token_type }
}

export async function fetchMe() {
  const { data } = await client.get("/auth/me");
  return data;
}
