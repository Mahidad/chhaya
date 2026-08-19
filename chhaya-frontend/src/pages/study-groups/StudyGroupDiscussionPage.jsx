import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import GroupDiscussion from "./GroupDiscussion";
import { getStudyGroup } from "../../api/studyGroups";

export default function StudyGroupDiscussionPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [group, setGroup] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getStudyGroup(id)
      .then(setGroup)
      .catch((err) => setError(err.response?.data?.detail || "Could not load this group."));
  }, [id]);

  if (!group) {
    return (
      <AppShell section="Study groups" current="Discussion">
        <div>Loading discussion...</div>
      </AppShell>
    );
  }

  return (
    <AppShell section="Study groups" current={`${group.name} - Discussion`}>
      <div className="page-head">
        <div>
          <div className="page-title">{group.name} — Discussion</div>
          <div className="page-sub">Messages and pinned notes for {group.name}</div>
        </div>
        <div className="page-actions">
          <Button variant="ghost" onClick={() => navigate(`/study-groups/${id}`)}>
            Back to group
          </Button>
        </div>
      </div>

      {error && <div className="error-text" style={{ marginBottom: 12 }}>{error}</div>}

      {group.membership_status !== "member" ? (
        <div className="card card-pad">
          <div className="hint">You must be a member of this study group to participate in the discussion.</div>
          <Button style={{ marginTop: 12 }} onClick={() => navigate(`/study-groups/${id}`)}>
            View group details
          </Button>
        </div>
      ) : (
        <GroupDiscussion groupId={id} />
      )}
    </AppShell>
  );
}
