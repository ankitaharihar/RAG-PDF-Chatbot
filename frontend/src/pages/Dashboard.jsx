import { useState } from "react";
import { Link } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import ChatInput from "../components/ChatInput/ChatInput";
import "./Dashboard.css";
import remarkGfm from "remark-gfm";

function Dashboard() {
  const [pdfId, setPdfId] = useState(null);
  const [pdfName, setPdfName] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleUpload = (file, data) => {
    console.log("PDF uploaded:", file);
    console.log("Upload response:", data);

    const uploadedPdf = data?.uploaded?.[0];

    if (uploadedPdf?.pdf_id) {
      setPdfId(uploadedPdf.pdf_id);
      setPdfName(uploadedPdf.original_name || file?.name || "PDF");

      console.log("PDF ID:", uploadedPdf.pdf_id);
    }
  };

  const handleSend = async (message) => {
    if (!pdfId) {
      alert("Please upload a PDF first.");
      return;
    }

    const userMessage = {
      role: "user",
      content: message,
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: 1,
          question: message,
          pdf_ids: [pdfId],
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        const errorMessage =
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail);

        throw new Error(errorMessage || "Chat request failed.");
      }

      console.log("Chat response:", data);

      const assistantMessage = {
        role: "assistant",
        content: data.answer || "I couldn't generate an answer.",
        citations: data.citations || [],
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Chat error:", error);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Sorry, something went wrong.\n\n**Error:** ${error.message}`,
          citations: [],
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setLoading(false);
  };

  const openUpload = () => {
    document.querySelector(".upload-icon-btn")?.click();
  };

  return (
    <div className="dashboard">

      {/* SIDEBAR */}
      <aside className="sidebar">

        <Link to="/" className="brand">
          📚 PDF AI
        </Link>

        <button
          className="new-chat"
          onClick={handleNewChat}
        >
          + New Chat
        </button>

        <div className="sidebar-section">
          <span>DOCUMENTS</span>

          <button
            className="sidebar-button"
            onClick={openUpload}
          >
            📄 Upload a PDF
          </button>

          {pdfName && (
            <div className="sidebar-pdf">
              📄 {pdfName}
            </div>
          )}
        </div>

        <div className="sidebar-section">
          <span>RECENT CHATS</span>

          {messages.length === 0 ? (
            <p className="empty-chat">
              No conversations yet
            </p>
          ) : (
            <button className="recent-chat">
              💬 Current conversation
            </button>
          )}
        </div>

        <div className="sidebar-bottom">

          <button className="sidebar-link">
            ⚙ Settings
          </button>

          <div className="user-box">
            <div className="user-avatar">
              A
            </div>

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


      {/* MAIN */}
      <main className="dashboard-main">

        {/* HEADER */}
        <header className="dashboard-header">

          <div>
            <p className="dashboard-label">
              YOUR WORKSPACE
            </p>

            <h1>
              {messages.length > 0
                ? "Ask your PDF anything"
                : "What would you like to learn?"}
            </h1>

            <p>
              {pdfName
                ? `You're chatting with ${pdfName}`
                : "Upload a PDF and start asking questions, generating notes, or creating practice questions."}
            </p>
          </div>

          <button
            className="upload-button"
            onClick={openUpload}
          >
            + Upload PDF
          </button>

        </header>


        {/* CONTENT */}
        <section className="dashboard-content">

          {/* EMPTY STATE */}
          {messages.length === 0 && !loading && (
            <>
              <div className="welcome-icon">
                🤖
              </div>

              <h2>
                Start with your documents
              </h2>

              <p className="dashboard-description">
                {pdfName
                  ? "Your PDF is ready. Ask your first question."
                  : "Your AI study assistant is ready. Upload a PDF to begin."}
              </p>

              <div className="dashboard-actions">

                <div className="dashboard-card">
                  <span>📝</span>
                  <h3>Generate Notes</h3>
                  <p>
                    Create structured notes from your PDF.
                  </p>
                </div>

                <div className="dashboard-card">
                  <span>✨</span>
                  <h3>Summarize</h3>
                  <p>
                    Get a quick summary of your document.
                  </p>
                </div>

                <div className="dashboard-card">
                  <span>🎯</span>
                  <h3>Generate MCQs</h3>
                  <p>
                    Create practice questions from your PDF.
                  </p>
                </div>

                <div className="dashboard-card">
                  <span>🎤</span>
                  <h3>Interview Questions</h3>
                  <p>
                    Prepare interview questions from your material.
                  </p>
                </div>

              </div>
            </>
          )}


          {/* CHAT */}
          {messages.length > 0 && (
            <div className="chat-container">

              {messages.map((message, index) => (

                <div
                  key={index}
                  className={`chat-message ${
                    message.role === "user"
                      ? "user-message"
                      : "assistant-message"
                  }`}
                >

                  <div className="message-avatar">
                    {message.role === "user"
                      ? "A"
                      : "🤖"}
                  </div>

                  <div className="message-content">

                    <div className="message-name">
                      {message.role === "user"
                        ? "You"
                        : "PDF AI"}
                    </div>
<div className="message-text markdown-content">
  <ReactMarkdown remarkPlugins={[remarkGfm]}>
    {message.content}
  </ReactMarkdown>
</div>


                    {/* SOURCES */}
                    {message.role === "assistant" &&
                      message.citations?.length > 0 && (

                        <details className="sources">

                          <summary>
                            📚 {message.citations.length} Sources
                          </summary>

                          <div className="sources-list">

                            {message.citations.map(
                              (item, citationIndex) => (

                                <div
                                  className="citation-item"
                                  key={citationIndex}
                                >
                                  <strong>
                                    {item.citation}
                                  </strong>

                                  <p>
                                    {item.excerpt}
                                  </p>
                                </div>

                              )
                            )}

                          </div>

                        </details>
                      )}

                  </div>

                </div>

              ))}


              {/* THINKING */}
              {loading && (
                <div className="chat-message assistant-message">

                  <div className="message-avatar">
                    🤖
                  </div>

                  <div className="message-content">

                    <div className="message-name">
                      PDF AI
                    </div>

                    <div className="thinking">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>

                    <p className="thinking-text">
                      Searching your PDF and generating an answer...
                    </p>

                  </div>

                </div>
              )}

            </div>
          )}

        </section>


        {/* CHAT INPUT */}
        <ChatInput
          onSend={handleSend}
          onUpload={handleUpload}
        />

      </main>
    </div>
  );
}

export default Dashboard;