import { useEffect, useState } from "react";
import Button from "../../components/ui/Button";
import Icon from "../../components/icons/Icon";
import {
  listGroupMessages,
  postGroupMessage,
  setMessagePin,
} from "../../api/studyGroupMessages";

export default function GroupDiscussion({ groupId }) {
  const [messages, setMessages] = useState(null);
  const [content, setContent] = useState("");
  const [error, setError] = useState("");
  const [sending, setSending] = useState(false);

  function load() {
    listGroupMessages(groupId)
      .then(setMessages)
      .catch((err) => setError(err.response?.data?.detail || "Could not load messages."));
  }

  useEffect(() => {
    load();
  }, [groupId]);

  async function submit(event) {
    event.preventDefault();
    if (!content.trim()) return;
    setSending(true);
    setError("");
    try {
      const message = await postGroupMessage(groupId, content);
      setMessages((items) => [...(items || []), message]);
      setContent("");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not post message.");
    } finally {
      setSending(false);
    }
  }

  async function togglePin(message) {
    try {
      await setMessagePin(groupId, message.id, !message.is_pinned);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not update pin.");
    }
  }

  if (messages === null) return <div className="hint">Loading discussion...</div>;
  const pinnedMessages = messages.filter((message) => message.is_pinned);
  const allMessagesSorted = [...messages].sort(
    (a, b) => new Date(a.created_at) - new Date(b.created_at)
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Pinned Messages Section */}
      {pinnedMessages.length > 0 && (
        <div className="card">
          <div className="card-head">
            <span className="card-title">
              <Icon name="pin" size={16} /> Pinned messages ({pinnedMessages.length})
            </span>
          </div>
          <div className="guide-body">
            {pinnedMessages.map((message) => (
              <div key={message.id} style={{ borderTop: "1px solid var(--line-soft)", padding: "12px 0" }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                  <strong>{message.author_name}</strong>
                  <Button size="sm" variant="ghost" onClick={() => togglePin(message)}>
                    <Icon name="pin" size={14} /> Unpin
                  </Button>
                </div>
                <div className="hint">Pinned by {message.pinned_by_name || message.author_name}</div>
                <div style={{ whiteSpace: "pre-wrap", marginTop: 6 }}>{message.content}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Messages Section */}
      <div className="card">
        <div className="card-head"><span className="card-title">All messages</span></div>
        <div className="guide-body">
          {error && <div className="error-text">{error}</div>}
          <form onSubmit={submit} style={{ marginBottom: 16 }}>
            <textarea
              value={content}
              onChange={(event) => setContent(event.target.value)}
              placeholder="Write a message for the group..."
              rows="3"
              style={{ width: "100%", boxSizing: "border-box", marginBottom: 8 }}
            />
            <Button type="submit" disabled={sending}>{sending ? "Posting..." : "Post message"}</Button>
          </form>

          {messages.length === 0 ? (
            <div className="hint">No messages yet. Start the discussion.</div>
          ) : (
            allMessagesSorted.map((message) => (
              <div key={message.id} style={{ borderTop: "1px solid var(--line-soft)", padding: "12px 0" }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <strong>{message.author_name}</strong>
                    {message.is_pinned && (
                      <span className="hint" style={{ fontSize: 12 }}>
                        <Icon name="pin" size={12} /> pinned
                      </span>
                    )}
                  </div>
                  <Button size="sm" variant="ghost" onClick={() => togglePin(message)}>
                    <Icon name="pin" size={14} /> {message.is_pinned ? "Unpin" : "Pin"}
                  </Button>
                </div>
                <div style={{ whiteSpace: "pre-wrap", marginTop: 6 }}>{message.content}</div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
