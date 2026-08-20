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
  const [focusMode, setFocusMode] = useState(false);
 const storedUser = localStorage.getItem("user");

let user = null;

try {
  user = storedUser && storedUser !== "undefined"
    ? JSON.parse(storedUser)
    : null;
} catch (error) {
  console.error("Invalid user data in localStorage:", error);
  localStorage.removeItem("user");
}
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
 <div
  className={`dashboard ${
    focusMode && messages.length > 0 ? "focus-mode" : ""
  }`}
>

      {/* SIDEBAR */}
      <aside className="sidebar">
<button
  className="close-focus-btn"
  onClick={() => setFocusMode(true)}
  title="Focus mode"
>
  ✕
</button>
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
              <strong>{user?.username || "Student"}</strong>
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
<button
  className="open-focus-btn"
  onClick={() => setFocusMode(false)}
>
  ☰
</button>
        {/* HEADER */}
        <header className="dashboard-header">

          <div>
            <p className="dashboard-label">
              YOUR WORKSPACE
            </p>

            <h1>Ask your PDF anything</h1>

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