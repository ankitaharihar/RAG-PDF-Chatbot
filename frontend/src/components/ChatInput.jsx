import { useRef, useState } from "react";

function ChatInput({ onSend, onUpload }) {
  const [message, setMessage] = useState("");
  const [fileName, setFileName] = useState("");
  const fileInputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!message.trim()) return;

    onSend?.(message.trim());
    setMessage("");
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];

    if (!file) return;

    if (file.type !== "application/pdf") {
      alert("Please upload a PDF file.");
      return;
    }

    setFileName(file.name);
    onUpload?.(file);
  };

  return (
    <div className="chat-input-wrapper">
      {fileName && (
        <div className="selected-file">
          <span className="file-icon">📄</span>
          <span>{fileName}</span>

          <button
            type="button"
            onClick={() => {
              setFileName("");
              if (fileInputRef.current) {
                fileInputRef.current.value = "";
              }
            }}
          >
            ×
          </button>
        </div>
      )}

      <form className="chat-input-box" onSubmit={handleSubmit}>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          hidden
          onChange={handleFileChange}
        />

        <button
          type="button"
          className="upload-icon-btn"
          onClick={() => fileInputRef.current?.click()}
          title="Upload PDF"
        >
          <svg
            width="21"
            height="21"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </button>

        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask anything about your PDF..."
          rows="1"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        />

        <button
          type="submit"
          className="send-btn"
          disabled={!message.trim()}
        >
          Send
          <span>→</span>
        </button>
      </form>
    </div>
  );
}

export default ChatInput;