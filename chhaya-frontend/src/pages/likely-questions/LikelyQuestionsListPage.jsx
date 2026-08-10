import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Badge from "../../components/ui/Badge";
import Icon from "../../components/icons/Icon";
import { deleteLikelyQuestionSet, listLikelyQuestionSets } from "../../api/likelyQuestions";

const STATUS = {
  pending: { label: "Pending" }, analyzing: { label: "Analysing", variant: "amber" },
  ready: { label: "Ready", variant: "ok" }, failed: { label: "Failed", variant: "danger" },
};

export default function LikelyQuestionsListPage() {
  const [sets, setSets] = useState(null);
  const navigate = useNavigate();
  useEffect(() => { listLikelyQuestionSets().then(setSets).catch(() => setSets([])); }, []);

  async function remove(event, id) {
    event.preventDefault(); event.stopPropagation();
    if (!window.confirm("Delete this likely-question set?")) return;
    await deleteLikelyQuestionSet(id);
    setSets((previous) => previous.filter((item) => item.id !== id));
  }

  if (sets === null) return <AppShell section="Likely questions" current="Loading"><div>Loading...</div></AppShell>;
  return (
    <AppShell section="Likely questions" current="All predictions">
      <div className="page-head"><div><div className="page-title">Likely exam questions</div><div className="page-sub">Generate study-practice predictions from the patterns in your past papers.</div></div><Button icon={<Icon name="plus" size={16} />} onClick={() => navigate("/likely-questions/new")}>Generate questions</Button></div>
      {sets.length === 0 ? <div className="ingest-empty"><div className="empty-title">No predictions yet</div><div className="empty-copy">Choose ready OCR papers and Gemini will analyse their exam patterns.</div><div className="empty-actions"><Button onClick={() => navigate("/likely-questions/new")}>Generate likely questions</Button></div></div> : <div className="list-card">{sets.map((item) => { const state = STATUS[item.status] || STATUS.pending; return <div key={item.id} style={{ display: "flex", alignItems: "center" }}><Link to={`/likely-questions/${item.id}`} className="prow" style={{ flex: 1, textDecoration: "none", color: "inherit" }}><div className="avatar av-ink"><Icon name="fileText" size={15} /></div><div className="prow-id" style={{ flex: 1 }}><div className="prow-name">{item.title}</div><div className="prow-course">{item.source_paper_count} source paper{item.source_paper_count === 1 ? "" : "s"}{item.course ? ` · ${item.course}` : ""}</div></div><Badge variant={state.variant}>{state.label}</Badge></Link><button type="button" title="Delete likely-question set" onClick={(event) => remove(event, item.id)} style={{ background: "none", border: "none", cursor: "pointer", padding: "8px 12px" }}><Icon name="trash" size={16} /></button></div>; })}</div>}
    </AppShell>
  );
}
