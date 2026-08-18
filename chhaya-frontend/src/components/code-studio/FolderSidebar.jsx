import { useState } from "react";
import Icon from "../icons/Icon";

/*
  The organization layer for Code Studio: a flat list of folders (no
  nesting -- see the backend schema comment on code_workspace_folders for
  why), shared across the Converter, Solver, and Visualizer's saved work.
  "Working" always returns to the active tool; every other entry shows
  that folder's saved items instead (see CodeStudioPage.jsx's `view` state).
*/
export default function FolderSidebar({ folders, activeView, onSelectView, itemCounts, onCreateFolder, onDeleteFolder }) {
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");

  async function handleCreate() {
    if (!newName.trim()) return;
    await onCreateFolder(newName.trim());
    setNewName("");
    setCreating(false);
  }

  return (
    <div className="folder-sidebar card">
      <div className="card-head">
        <span className="card-title">Saved work</span>
      </div>
      <div style={{ padding: 6 }}>
        <div
          className={`folder-item ${activeView === "working" ? "folder-item-on" : ""}`}
          onClick={() => onSelectView("working")}
        >
          <Icon name="wand" size={14} /> Working
        </div>
        <div
          className={`folder-item ${activeView === "unfiled" ? "folder-item-on" : ""}`}
          onClick={() => onSelectView("unfiled")}
        >
          <Icon name="fileText" size={14} /> Unfiled
          <span className="folder-count">{itemCounts.unfiled ?? 0}</span>
        </div>
        {folders.map((f) => (
          <div
            key={f.id}
            className={`folder-item ${activeView === f.id ? "folder-item-on" : ""}`}
            onClick={() => onSelectView(f.id)}
          >
            <Icon name="folder" size={14} /> {f.name}
            <span className="folder-count">{itemCounts[f.id] ?? 0}</span>
            <button
              className="mini-btn"
              style={{ width: 22, height: 22 }}
              onClick={(e) => {
                e.stopPropagation();
                onDeleteFolder(f);
              }}
              title="Delete folder (contents stay, just un-filed)"
            >
              <Icon name="trash" size={11} />
            </button>
          </div>
        ))}

        {creating ? (
          <div style={{ display: "flex", gap: 4, padding: "6px 4px" }}>
            <input
              autoFocus
              className="save-title-input"
              placeholder="Folder name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreate()}
            />
            <button className="mini-btn" onClick={handleCreate} title="Create">
              <Icon name="check" size={13} />
            </button>
          </div>
        ) : (
          <div className="folder-item" onClick={() => setCreating(true)}>
            <Icon name="plus" size={14} /> New folder
          </div>
        )}
      </div>
    </div>
  );
}
