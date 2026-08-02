import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { Card } from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import { TextField } from "../../components/ui/Field";
import logoWhite from "../../assets/logo-white.png";

/*
  Not part of the original Figma export -- the mockups start after login.
  Built to the same design tokens (colors, radii, font) so it doesn't look
  bolted on, but this specific layout is mine, not the designer's; swap it
  for a real Figma screen whenever one exists.
*/
export default function LoginPage() {
  const { login, loading } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      await login(email, password);
      navigate("/sources");
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === "string") {
        setError(detail);
      } else if (Array.isArray(detail) && detail.length > 0) {
        const msg = detail.map((d) => d.msg || "Invalid input").join(". ");
        setError(msg);
      } else {
        setError("Could not log in. Please check your credentials and try again.");
      }
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-brand">
          <div className="auth-brand-mark">
            <img src={logoWhite} alt="Chhaya" />
          </div>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700 }}>Chhaya</div>
            <div className="bn" style={{ fontSize: 11, color: "var(--muted)" }}>ছায়া</div>
          </div>
        </div>
        <Card>
          <form onSubmit={handleSubmit} className="form-grid">
            <TextField
              label="Email"
              type="email"
              placeholder="you@university.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <TextField
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            {error && <div className="error-text">{error}</div>}
            <Button type="submit" disabled={loading} style={{ justifyContent: "center" }}>
              {loading ? "Logging in..." : "Log in"}
            </Button>
          </form>
        </Card>
        <div style={{ textAlign: "center", marginTop: 16, fontSize: 13, color: "var(--muted)" }}>
          New to Chhaya? <Link to="/signup" style={{ color: "var(--primary)", fontWeight: 600 }}>Create an account</Link>
        </div>
      </div>
    </div>
  );
}
