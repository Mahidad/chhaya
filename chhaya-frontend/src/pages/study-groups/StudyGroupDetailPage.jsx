import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import { TextField } from "../../components/ui/Field";
import {
  getStudyGroup,
  inviteStudent,
  requestToJoin,
  respondToJoinRequest,
} from "../../api/studyGroups";

export default function StudyGroupDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [group, setGroup] = useState(null);
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  function load() {
    getStudyGroup(id).then(setGroup).catch((err) => setError(err.response?.data?.detail || "Could not load this group."));
  }

  useEffect(() => {
    load();
  }, [id]);

  async function join() {
    try {
      await requestToJoin(id);
      setMessage("Your join request was sent to the group creator.");
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not send join request.");
    }
  }

  async function invite(event) {
    event.preventDefault();
    try {
      await inviteStudent(id, email);
      setEmail("");
      setMessage("Invitation sent.");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not send invitation.");
    }
  }

  async function answerRequest(requestId, status) {
    try {
      await respondToJoinRequest(id, requestId, status);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not update join request.");
    }
  }

  if (!group) return <AppShell section="Study groups" current="Loading"><div>Loading...</div></AppShell>;
  const isCreator = group.creator_id === user?.id;

  return (
    <AppShell section="Study groups" current={group.name}>
      <div className="page-head">
        <div>
          <div className="page-title">{group.name}</div>
          <div className="page-sub">Created by {group.creator_name}</div>
        </div>
        <Button variant="ghost" onClick={() => navigate("/study-groups")}>Back</Button>
      </div>
      <div className="card card-pad" style={{ marginBottom: 16 }}><p>{group.description}</p><div className="hint">{group.member_count} member{group.member_count === 1 ? "" : "s"}</div></div>
      {message && <div className="banner"><div className="banner-copy">{message}</div></div>}
      {error && <div className="error-text" style={{ marginBottom: 12 }}>{error}</div>}

      {!isCreator && !group.membership_status && <Button onClick={join}>Request to join</Button>}
      {!isCreator && group.membership_status === "requested" && <div className="hint">Your request is waiting for the creator.</div>}
      {!isCreator && group.membership_status === "member" && <div className="hint">You are a member of this group.</div>}

      <div className="split" style={{ marginTop: 16 }}>
        <div className="col-form card">
          <div className="card-head"><span className="card-title">Members</span></div>
          <div className="guide-body">
            {group.members.map((member) => <div key={member.user_id} style={{ marginBottom: 10 }}>{member.full_name} <span className="hint">({member.email})</span></div>)}
          </div>
        </div>
        {isCreator && <div className="col-side">
          <form onSubmit={invite} className="card card-pad" style={{ marginBottom: 16 }}>
            <div className="card-title" style={{ marginBottom: 12 }}>Invite a student</div>
            <TextField label="Student email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
            <Button type="submit" style={{ marginTop: 12 }}>Send invitation</Button>
          </form>
          <div className="card card-pad">
            <div className="card-title" style={{ marginBottom: 12 }}>Join requests</div>
            {group.join_requests.length === 0 ? <div className="hint">No pending requests.</div> : group.join_requests.map((request) => <div key={request.id} style={{ marginBottom: 12 }}><div>{request.full_name}</div><div className="hint">{request.email}</div><Button size="sm" onClick={() => answerRequest(request.id, "accepted")}>Accept</Button><Button size="sm" variant="ghost" onClick={() => answerRequest(request.id, "rejected")}>Reject</Button></div>)}
          </div>
        </div>}
      </div>
    </AppShell>
  );
}
