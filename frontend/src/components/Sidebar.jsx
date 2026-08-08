function Sidebar() {
  return (
    <aside className="sidebar">
      <div>
        <div className="sidebar-header">
          <h2>📚 PDF AI</h2>
        </div>

        <button className="new-chat-btn">＋ New Chat</button>

        <div className="sidebar-section">
          <div className="section-title">Documents</div>

          <div className="pdf-item">
            <span>📄</span>
            <span>Upload a PDF</span>
          </div>
        </div>

        <div className="sidebar-section">
          <div className="section-title">Recent Chats</div>

          <div className="chat-item">
            No conversations yet
          </div>
        </div>
      </div>

      <div className="sidebar-bottom">
        <div>⚙️ Settings</div>
        <div>👤 Account</div>
      </div>
    </aside>
  );
}

export default Sidebar;