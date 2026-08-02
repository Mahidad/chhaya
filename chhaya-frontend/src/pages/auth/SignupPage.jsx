import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { Card } from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import { TextField } from "../../components/ui/Field";
import logoWhite from "../../assets/logo-white.png";

export default function SignupPage() {
  const { signup, loading } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    try {
      await signup(fullName, email, password);
      navigate("/sources");
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === "string") {
        setError(detail);
      } else if (Array.isArray(detail) && detail.length > 0) {
        const msg = detail.map((d) => d.msg || "Invalid input").join(". ");
        setError(msg);
      } else {
        setError("Could not create your account. Please try again.");
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
              label="Full name"
              placeholder="Lamia Rahman"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />
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
              placeholder="At least 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={8}
              required
            />
            {error && <div className="error-text">{error}</div>}
            <Button type="submit" disabled={loading} style={{ justifyContent: "center" }}>
              {loading ? "Creating account..." : "Create account"}
            </Button>
          </form>
        </Card>
        <div style={{ textAlign: "center", marginTop: 16, fontSize: 13, color: "var(--muted)" }}>
          Already have an account? <Link to="/login" style={{ color: "var(--primary)", fontWeight: 600 }}>Log in</Link>
        </div>
      </div>
    </div>
  );
}
