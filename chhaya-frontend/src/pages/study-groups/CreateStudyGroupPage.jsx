import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import { TextField } from "../../components/ui/Field";
import { createStudyGroup } from "../../api/studyGroups";

export default function CreateStudyGroupPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const group = await createStudyGroup({ name, description });
      navigate(`/study-groups/${group.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not create the study group.");
      setSaving(false);
    }
  }

  return (
    <AppShell section="Study groups" current="Create group">
      <div className="page-head">
        <div>
          <div className="page-title">Create a study group</div>
          <div className="page-sub">You will become the group creator and first member.</div>
        </div>
      </div>
      <form onSubmit={submit} className="card" style={{ maxWidth: 580 }}>
        <div className="form-grid">
          <TextField label="Group name" value={name} onChange={(event) => setName(event.target.value)} required />
          <div className="field">
            <div className="label">Group description</div>
            <textarea value={description} onChange={(event) => setDescription(event.target.value)} rows="5" required />
          </div>
        </div>
        <div className="form-foot">
          <Button type="submit" disabled={saving}>{saving ? "Creating..." : "Create group"}</Button>
          <Button type="button" variant="ghost" onClick={() => navigate("/study-groups")}>Cancel</Button>
          {error && <div className="error-text">{error}</div>}
        </div>
      </form>
    </AppShell>
  );
}
