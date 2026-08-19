import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Badge from "../../components/ui/Badge";
import Icon from "../../components/icons/Icon";
import { getInvitations, listStudyGroups, respondToInvitation } from "../../api/studyGroups";

export default function StudyGroupsListPage() {
  const [groups, setGroups] = useState(null);
  const [invitations, setInvitations] = useState([]);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  function load() {
    listStudyGroups().then(setGroups).catch(() => setGroups([]));
    getInvitations().then(setInvitations).catch(() => setInvitations([]));
  }

  useEffect(() => {
    load();
  }, []);

  async function answerInvitation(id, status) {
    try {
      await respondToInvitation(id, status);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not update the invitation.");
    }
  }

  if (groups === null) {
    return <AppShell section="Study groups" current="Loading"><div>Loading...</div></AppShell>;
  }

  return (
    <AppShell section="Study groups" current="All groups">
      <div className="page-head">
        <div>
          <div className="page-title">Study groups</div>
          <div className="page-sub">Create a group, invite classmates, or request to join a group.</div>
        </div>
        <Button icon={<Icon name="plus" size={16} />} onClick={() => navigate("/study-groups/new")}>
          Create group
        </Button>
      </div>

      {error && <div className="error-text" style={{ marginBottom: 12 }}>{error}</div>}

      {invitations.filter((item) => item.status === "pending").length > 0 && (
        <div className="card card-pad" style={{ marginBottom: 16 }}>
          <div className="card-title" style={{ marginBottom: 12 }}>Your invitations</div>
          {invitations.filter((item) => item.status === "pending").map((item) => (
            <div key={item.id} className="prow" style={{ padding: "10px 0" }}>
              <div className="prow-id" style={{ flex: 1 }}>
                <div className="prow-name">{item.group_name}</div>
                <div className="prow-course">Invited by {item.invited_by_name}</div>
              </div>
              <Button size="sm" onClick={() => answerInvitation(item.id, "accepted")}>Accept</Button>
              <Button size="sm" variant="ghost" onClick={() => answerInvitation(item.id, "rejected")}>Reject</Button>
            </div>
          ))}
        </div>
      )}

      {groups.length === 0 ? (
        <div className="ingest-empty">
          <div className="empty-title">No study groups yet</div>
          <div className="empty-copy">Be the first student to create a study group.</div>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 16 }}>
          {groups.map((group) => (
            <Link key={group.id} to={`/study-groups/${group.id}`} style={{ textDecoration: "none", color: "inherit" }}>
              <div className="card card-pad" style={{ height: "100%" }}>
                <div className="src-title">{group.name}</div>
                <div className="src-meta" style={{ marginTop: 8 }}>{group.member_count} member{group.member_count === 1 ? "" : "s"}</div>
                <p style={{ color: "var(--muted)", fontSize: 13 }}>{group.description}</p>
                {group.membership_status === "member" && <Badge variant="ok">Member</Badge>}
                {group.membership_status === "requested" && <Badge variant="amber">Request pending</Badge>}
              </div>
            </Link>
          ))}
        </div>
      )}
    </AppShell>
  );
}
