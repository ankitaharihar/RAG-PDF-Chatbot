import { Link } from "react-router-dom";

function Dashboard() {
  return (
    <div className="dashboard">

      {/* Sidebar */}
      <aside className="sidebar">

        <Link to="/" className="brand">
          📚 PDF AI
        </Link>

        <Link to="/dashboard" className="new-chat">
          + New Chat
        </Link>

        <div className="sidebar-section">
          <span>DOCUMENTS</span>

          <button className="sidebar-button">
            📄 Upload a PDF
          </button>
        </div>

        <div className="sidebar-section">
          <span>RECENT CHATS</span>

          <p className="empty-chat">
            No conversations yet
          </p>
        </div>

        <div className="sidebar-bottom">

          <button className="sidebar-link">
            ⚙ Settings
          </button>

          <div className="user-box">
            <div className="user-avatar">A</div>

            <div>
              <strong>Student</strong>
              <small>Free Plan</small>
            </div>
          </div>

          <Link to="/" className="logout">
            ← Log out
          </Link>

        </div>

      </aside>

      {/* Main */}
      <main className="dashboard-main">

        <header className="dashboard-header">

          <div>
            <p className="dashboard-label">
              YOUR WORKSPACE
            </p>

            <h1>What would you like to learn?</h1>

            <p>
              Upload a PDF and start asking questions,
              generating notes, or creating practice questions.
            </p>
          </div>

          <button className="upload-button">
            + Upload PDF
          </button>

        </header>

        <section className="dashboard-content">

          <div className="welcome-icon">
            🤖
          </div>

          <h2>Start with your documents</h2>

          <p className="dashboard-description">
            Your AI study assistant is ready.
            Upload a PDF to begin.
          </p>

          <div className="dashboard-actions">

            <div className="dashboard-card">
              <span>📝</span>
              <h3>Generate Notes</h3>
              <p>Create structured notes from your PDF.</p>
            </div>

            <div className="dashboard-card">
              <span>✨</span>
              <h3>Summarize</h3>
              <p>Get a quick summary of your document.</p>
            </div>

            <div className="dashboard-card">
              <span>🎯</span>
              <h3>Generate MCQs</h3>
              <p>Create practice questions from your PDF.</p>
            </div>

            <div className="dashboard-card">
              <span>🎤</span>
              <h3>Interview Questions</h3>
              <p>Prepare interview questions from your material.</p>
            </div>

          </div>

        </section>

        <div className="chat-input">
          <input
            placeholder="Ask anything about your PDF..."
          />

          <button>
            Send →
          </button>
        </div>

      </main>
    </div>
  );
}

export default Dashboard;